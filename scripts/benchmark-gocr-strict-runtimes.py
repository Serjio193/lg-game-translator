"""Exact detector-runtime gate; unchanged native recognizer always uses system TFLite."""
import argparse
import itertools
import json
import os
import statistics
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker
from gocr_worker.native_postprocess import NativePostprocess
from gocr_worker.runner_diagnostics import snapshot, tensor_hashes, tensor_differences


def identity(result):
    # Include scores, words and symbols too; only clocks are non-semantic.
    return [{key: value for key, value in line.items() if key != "timings_ms"}
            for line in result["lines"]]


def diagnostic_identity(diagnostics):
    # Tensor equality has its own gate; do not label an identical empty
    # proposal/component result unequal merely because raw heads differ.
    return {key: value for key, value in diagnostics.items() if key != "tensors"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime", action="append", required=True, help="NAME=absolute library")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("frames", nargs="+", type=Path)
    args = parser.parse_args()
    runtimes = dict(item.split("=", 1) for item in args.runtime)
    if "system" not in runtimes or args.repeats < 5:
        parser.error("system reference and at least five measurements required")
    os.environ.update(GOCR_PROFILE="strict", GOCR_DETECTOR="native", GOCR_RECOGNIZER="native",
                      GOCR_TFLITE_C_LIBRARY=runtimes["system"])
    os.environ.pop("GOCR_DETECTOR_PROFILE", None)
    report = {"runtimes": runtimes, "detector_threads": 2, "recognizer_threads": 2,
              "xnnpack": False, "warmups_per_frame": 1, "repeats": args.repeats, "runs": []}
    workers = {}
    try:
        for name, library in runtimes.items():
            os.environ["GOCR_DETECTOR_TFLITE_LIBRARY"] = library
            workers[name] = FullGocrWorker(args.assets, detector_threads=2, recognizer_threads=2)
            if workers[name].native_full is None or workers[name].detector.native.xnnpack:
                raise RuntimeError("native STRICT required; no fallback/delegate allowed")
        orders = list(itertools.permutations(workers))
        post = NativePostprocess()
        for frame_index, frame in enumerate(args.frames):
            image = Image.open(frame).convert("RGB")
            if image.size != (1280, 720):
                raise ValueError("selected frame dimensions changed")
            for name in orders[frame_index % len(orders)]:
                workers[name].ocr(image)
            samples = {name: [] for name in workers}
            observed_orders = []
            for repeat in range(args.repeats):
                order = orders[(frame_index + repeat) % len(orders)]
                observed_orders.append(order)
                for name in order:
                    result = workers[name].ocr(image)
                    result["raw_tensor_hashes"] = tensor_hashes(workers[name].detector.native)
                    samples[name].append(result)
            diagnostics = {name: snapshot(worker.detector.native, args.assets, post)
                           for name, worker in workers.items()}
            reference = samples["system"][-1]
            parity = {}
            for name, worker in workers.items():
                stable = all(identity(row) == identity(samples[name][0]) and
                             row["raw_tensor_hashes"] == samples[name][0]["raw_tensor_hashes"]
                             for row in samples[name])
                parity[name] = {
                    "repeat_stable": stable,
                    "raw_tensors_equal": samples[name][-1]["raw_tensor_hashes"] == reference["raw_tensor_hashes"],
                    "decoded_deduped_components_equal": diagnostic_identity(diagnostics[name]) == diagnostic_identity(diagnostics["system"]),
                    "quads_crops_windows_text_equal": identity(samples[name][-1]) == identity(reference),
                    "head_differences": tensor_differences(workers["system"].detector.native, worker.detector.native),
                }
                parity[name]["eligible_exact"] = all(parity[name][key] for key in (
                    "repeat_stable", "raw_tensors_equal", "decoded_deduped_components_equal",
                    "quads_crops_windows_text_equal"))
            medians = {name: {key: statistics.median(row["timings_ms"][key] for row in rows)
                              for key in rows[0]["timings_ms"]} for name, rows in samples.items()}
            report["runs"].append({"frame": str(frame), "orders": observed_orders,
                                   "samples": samples, "diagnostics": diagnostics,
                                   "median_ms": medians, "parity": parity})
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"frame": str(frame), "median_ms": medians,
                              "eligible_exact": {n: p["eligible_exact"] for n, p in parity.items()}}), flush=True)
    finally:
        for worker in workers.values():
            worker.close()


if __name__ == "__main__":
    main()
