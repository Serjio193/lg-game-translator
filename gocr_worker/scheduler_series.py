"""Persistent, duration-bounded A/B series using the existing strict benchmark handles."""
import json
import os
import time
from .runner_diagnostics import tensor_hashes, snapshot
from .scheduler_observation import tasks, delta, environment


def pair_order(round_index, frame_index):
    names = ["baseline", "nice_-5"]
    return list(reversed(names)) if (round_index + frame_index) % 2 else names


def finished(elapsed, duration, counts, minimum):
    return elapsed >= duration and all(count >= minimum for count in counts)


def run_series(args, images, detector, full, post, placement, report, semantic, summarize):
    report.update(duration_requested_seconds=args.duration_seconds,
                  series_protocol="round-robin corpus; alternating AB/BA; persistent 2/2 interpreters",
                  reference_reused_across_rounds=True)
    for path, image in images:
        placement.apply("baseline")
        lines, _ = full.run(image)
        tensors = tensor_hashes(detector)
        diagnostics = snapshot(detector, args.assets, post)
        report["frames"].append({"frame": str(path), "reference_tensors": tensors,
                                 "reference_lines": lines, "reference_diagnostics": diagnostics,
                                 "parity": True, "events": [], "modes": {"full": {
                                     "timing": {}, "telemetry": {"baseline": [], "nice_-5": []},
                                     "final_diagnostics_equal": True}}})
        for name in ("baseline", "nice_-5"):
            placement.apply(name)
            warm, _ = full.run(image)
            if (tensor_hashes(detector) != tensors or semantic(warm) != semantic(lines)
                    or snapshot(detector, args.assets, post) != diagnostics):
                raise RuntimeError("warmup strict parity failed")
    started = time.monotonic()
    round_index = 0
    counts = [0] * len(images)
    values = [{name: [] for name in ("baseline", "nice_-5")} for _ in images]
    report["series_start_monotonic"] = started
    while not finished(time.monotonic() - started, args.duration_seconds, counts, args.repeats):
        for index, (_, image) in enumerate(images):
            if finished(time.monotonic() - started, args.duration_seconds, counts, args.repeats):
                break
            row = report["frames"][index]
            mode = row["modes"]["full"]
            for name in pair_order(round_index, index):
                placement.apply(name)
                before = tasks(os.getpid())
                call_start = time.monotonic()
                lines, stats = full.run(image)
                call_end = time.monotonic()
                after = tasks(os.getpid())
                hashes = tensor_hashes(detector)
                diagnostics = snapshot(detector, args.assets, post)
                tensor_equal = hashes == row["reference_tensors"]
                line_equal = semantic(lines) == semantic(row["reference_lines"])
                post_equal = diagnostics == row["reference_diagnostics"]
                row["parity"] &= tensor_equal and line_equal and post_equal
                values[index][name].append(stats.total_ms)
                mode["telemetry"][name].append({"before": before, "after": after,
                    "delta": delta(before, after), "environment": environment(), "tensors": hashes,
                    "tensor_equal": tensor_equal, "semantic_lines_equal": line_equal,
                    "postprocess_exact": post_equal, "detector_invoke_ms": stats.detector.invoke_ms})
                row["events"].append({"mode": "full", "variant": name, "repeat": counts[index],
                                       "start": call_start, "end": call_end,
                                       "elapsed_seconds": call_start - started, "round": round_index})
                row["final_lines"], row["final_diagnostics"] = lines, diagnostics
                mode["final_diagnostics_equal"] &= post_equal
                if not row["parity"]:
                    raise RuntimeError("duration series strict parity failed")
            counts[index] += 1
            mode["timing"] = {name: summarize(samples) for name, samples in values[index].items()}
        round_index += 1
        report["series_elapsed_seconds"] = time.monotonic() - started
        report["pairs_per_frame"] = counts[:]
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"elapsed_seconds": report["series_elapsed_seconds"],
                          "rounds": round_index, "pairs_per_frame": counts,
                          "parity": all(row["parity"] for row in report["frames"])}), flush=True)
    report["series_end_monotonic"] = time.monotonic()
    report["series_elapsed_seconds"] = report["series_end_monotonic"] - started
