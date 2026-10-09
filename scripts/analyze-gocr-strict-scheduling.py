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


def analyze(path):
    data = load(path)
    result = {k: data.get(k) for k in ("variant", "roles", "persistent_tid_set", "restore_errors", "unsupported")}
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
