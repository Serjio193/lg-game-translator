"""Summarize scheduling evidence; unavailable counters remain null, never zero."""
import argparse
import gzip
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def timing(values):
    ordered = sorted(values)
    return {"n": len(values), "median_ms": statistics.median(values),
            "p95_ms": ordered[math.ceil(len(values) * .95) - 1]}


def counters(rows):
    keys = ("migrations", "voluntary", "involuntary", "runtime_ns", "runqueue_ns")
    tids = set().union(*(r["delta"] for r in rows))
    result = {}
    for tid in sorted(tids, key=int):
        values = [r["delta"].get(tid, {}) for r in rows]
        result[tid] = {}
        for key in keys:
            data = [v.get(key) for v in values]
            result[tid][key] = statistics.mean(data) if all(v is not None for v in data) else None
    result["total"] = {key: sum(result[t][key] for t in tids)
                       if all(result[t][key] is not None for t in tids) else None for key in keys}
    return result


def trace_summary(path, events):
    groups = {}
    observer_cpu = None
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if "observer_cpu_seconds" in row:
                observer_cpu = row["observer_cpu_seconds"]
                continue
            event = next((e for e in events if e["start"] <= row["monotonic"] <= e["end"]), None)
            if event is None:
                continue
            key = event["mode"] + "/" + event["variant"]
            group = groups.setdefault(key, {})
            for tid, value in row["tasks"].items():
                item = group.setdefault(tid, {"cores": Counter(), "states": Counter(), "wchan": Counter(),
                                             "sampled_core_transitions": 0, "previous": None,
                                             "affinity_masks": set(), "last_event": None})
                item["cores"][str(value["core"])] += 1
                item["states"][value["state"]] += 1
                item["wchan"][value["wchan"]] += 1
                item["affinity_masks"].add(tuple(value["affinity"]))
                # A lower bound from polling, not an exact migration count.
                if item["last_event"] == event["start"] and item["previous"] != value["core"]:
                    item["sampled_core_transitions"] += 1
                item["previous"] = value["core"]
                item["last_event"] = event["start"]
    for group in groups.values():
        for item in group.values():
            del item["previous"]
            del item["last_event"]
            item["affinity_masks"] = sorted(map(list, item["affinity_masks"]))
    return {"groups": groups, "observer_cpu_seconds": observer_cpu}


def load(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as file:
        return json.load(file)


def series_summary(data):
    names = ("baseline", "nice_-5")
    pooled = {name: [] for name in names}
    minute_rows = {}
    frame_ratios = {}
    pairs = 0
    start = data["series_start_monotonic"]
    for frame in data["frames"]:
        telemetry = frame["modes"]["full"]["telemetry"]
        event_times = {(e["repeat"], e["variant"]): e["start"] for e in frame["events"]}
        ratios = []
        for index, (baseline, candidate) in enumerate(zip(telemetry["baseline"], telemetry["nice_-5"])):
            minute = int((min(event_times[index, name] for name in names) - start) // 60)
            bucket = minute_rows.setdefault(minute, {name: [] for name in names})
            for name, sample in zip(names, (baseline, candidate)):
                item = {"invoke": sample["detector_invoke_ms"],
                        "full": frame["modes"]["full"]["timing"][name]["samples_ms"][index]}
                bucket[name].append(item)
                pooled[name].append(item)
            ratios.append(baseline["detector_invoke_ms"] / candidate["detector_invoke_ms"])
            pairs += 1
        frame_ratios[Path(frame["frame"]).name] = {
            "pairs": len(ratios), "paired_invoke_speedup_median": statistics.median(ratios)}
    def aggregate(group):
        return {name: {metric: timing([r[metric] for r in group[name]]) for metric in ("invoke", "full")}
                for name in names}
    return {"elapsed_seconds": data.get("series_end_monotonic", start + data["series_elapsed_seconds"]) - start,
            "pairs": pairs, "calls": 2 * pairs, "per_frame": frame_ratios,
            "pooled": aggregate(pooled), "minutes": {str(m): aggregate(rows) for m, rows in minute_rows.items()}}


def analyze(path):
    data = load(path)
    result = {k: data.get(k) for k in ("variant", "roles", "persistent_tid_set", "restore_errors", "unsupported")}
    if "series_start_monotonic" in data:
        result["duration_series"] = series_summary(data)
    result["evidence_file"] = str(path)
    result["frames"] = []
    events = []
    for row in data["frames"]:
        frame = {"frame": Path(row["frame"]).name, "parity": row["parity"], "modes": {}}
        events.extend(row["events"])
        for mode, evidence in row["modes"].items():
            modes = {}
            for name, samples in evidence["telemetry"].items():
                invoke = [r["detector_invoke_ms"] for r in samples]
                values = evidence["timing"][name]["samples_ms"]
                masks = all(r["before"][t]["affinity"] == r["after"][t]["affinity"]
                            for r in samples for t in r["before"] if t in r["after"])
                modes[name] = {"invoke": timing(values if mode == "invoke" else invoke),
                               "full": timing(values) if mode == "full" else None,
                               "counters_per_observation": counters(samples),
                               "affinity_unchanged_during_invoke": masks,
                               "frequencies_khz": sorted({v for r in samples for v in r["environment"]["frequency_khz"].values()}),
                               "tensor_exact": all(r["tensor_equal"] for r in samples),
                               "semantic_exact": all(r["semantic_lines_equal"] for r in samples)}
            frame["modes"][mode] = modes
        result["frames"].append(frame)
    trace = path.with_name(path.name.removesuffix(".gz")).with_suffix(".trace.jsonl.gz")
    if trace.exists():
        result["trace_summary"] = trace_summary(trace, events)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted([*args.root.rglob("*.json"), *args.root.rglob("*.json.gz")])
    reports = [analyze(path) for path in paths
               if isinstance(load(path), dict) and "variant" in load(path)]
    args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    for report in reports:
        for frame in report["frames"]:
            for mode, variants in frame["modes"].items():
                print(report["variant"], frame["frame"], mode,
                      {v: round(r["invoke"]["median_ms"], 2) for v, r in variants.items()}, frame["parity"])


if __name__ == "__main__":
    main()
