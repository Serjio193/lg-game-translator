"""Summarize observed per-node dispatch; do not infer inner packing timings."""
import argparse
import gzip
import json
import statistics
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--operators", type=Path, required=True)
    args = parser.parse_args()
    dispatch = json.loads((args.evidence / "dispatch.json").read_text())
    nodes = {row["node_index"]: row for row in dispatch["nodes"]
             if row["context"] == dispatch["detector_context"]}
    operators = json.loads(args.operators.read_text())["operators"]
    top = []
    for op in operators:
        if op["name"] != "CONV_2D":
            continue
        row = nodes[op["node_index"]]
        count = row["eval_calls"]
        top.append({"node": op["node_index"], "reference_median_ms": op["median_ms"],
                    "input_shapes": op["input_shapes"], "output_shapes": op["output_shapes"],
                    "observed_path": "Eigen float32" if row["eigen_calls"] else
                        "gemmlowp per-channel int8" if row["gemmlowp_dispatch_calls"] else "unresolved",
                    "probe_mean_eval_ms_including_warmup": row["eval_total_ms"] / count,
                    "gemmlowp_fraction_of_eval": row["gemmlowp_total_ms"] / row["eval_total_ms"],
                    "prepare_calls": row["prepare_calls"], "eval_calls": count,
                    "transpose_calls": row["transpose_calls"],
                    "malloc_calls_per_eval_mean": row["malloc_calls"] / count,
                    "requested_bytes_per_eval_mean": row["allocated_bytes"] / count,
                    "temporaries": row["temporaries"]})
        if len(top) == 20:
            break
    summary = {"registration_bytes": dispatch["registration_bytes"],
               "prepare_offset": hex(dispatch["prepare_offset"]),
               "eval_offset": hex(dispatch["eval_offset"]), "conv_nodes": len(nodes),
               "eigen_nodes": sum(bool(r["eigen_calls"]) for r in nodes.values()),
               "gemmlowp_nodes": sum(bool(r["gemmlowp_dispatch_calls"]) for r in nodes.values()),
               "ruy_observed_calls": sum(r["ruy_trmul_calls"] for r in nodes.values()),
               "top20": top, "reference_timings": []}
    with gzip.open(args.evidence / "reference.json.gz", "rt", encoding="utf-8") as source:
        reference = json.load(source)
    for run in reference["runs"]:
        summary["reference_timings"].append({"frame": run["frame"], "median_ms": {
            key: statistics.median(s["timings_ms"][key] for s in run["samples"])
            for key in run["samples"][0]["timings_ms"]}})
    (args.evidence / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ("top20", "reference_timings")}))


if __name__ == "__main__":
    main()
