"""Isolated reference versus forwarding probe; never installs a runtime or changes settings."""
import argparse
import gzip
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.native_postprocess import NativePostprocess
from gocr_worker.runner_diagnostics import snapshot, tensor_hashes
from gocr_worker.worker_full import FullGocrWorker
from gocr_worker.assets import DETECTOR_MODEL, locate
from gocr_worker.model_operator_metadata import operator_metadata

SYSTEM = Path("/usr/lib/libtensorflow-lite.so")
SYSTEM_SHA = "cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138"


def identity(result):
    return [{k: v for k, v in line.items() if k != "timings_ms"}
            for line in result["lines"]]


def child(args):
    if hashlib.sha256(SYSTEM.read_bytes()).hexdigest() != SYSTEM_SHA:
        raise RuntimeError("system reference identity changed")
    os.environ.update(GOCR_PROFILE="strict", GOCR_DETECTOR="native",
                      GOCR_RECOGNIZER="native", GOCR_TFLITE_C_LIBRARY=str(SYSTEM),
                      GOCR_DETECTOR_TFLITE_LIBRARY=str(SYSTEM))
    os.environ.pop("GOCR_DETECTOR_PROFILE", None)
    worker = FullGocrWorker(args.assets, detector_threads=2, recognizer_threads=2)
    try:
        if worker.native_full is None or worker.detector.native.xnnpack:
            raise RuntimeError("native strict required")
        post = NativePostprocess()
        rows = []
        for frame in args.frames:
            image = Image.open(frame).convert("RGB")
            if image.size != (1280, 720):
                raise RuntimeError("unexpected frame size")
            worker.ocr(image)
            samples = []
            for _ in range(args.repeats):
                result = worker.ocr(image)
                samples.append({"identity": identity(result),
                                "tensors": tensor_hashes(worker.detector.native),
                                "timings_ms": result["timings_ms"]})
            rows.append({"frame": str(frame), "samples": samples,
                         "diagnostics": snapshot(worker.detector.native, args.assets, post)})
            print(json.dumps({"frame": str(frame), "completed": True}), flush=True)
        args.output.write_text(json.dumps({"system_sha256": SYSTEM_SHA, "pid": os.getpid(),
                                          "task_ids": sorted(int(p.name) for p in Path("/proc/self/task").iterdir()),
                                          "runs": rows}, ensure_ascii=False))
    finally:
        worker.close()


def compare(reference, probe):
    gates = []
    if not reference["runs"] or len(reference["runs"]) != len(probe["runs"]):
        raise ValueError("corpus length mismatch")
    for left, right in zip(reference["runs"], probe["runs"]):
        same_frame = left["frame"] == right["frame"]
        target = left["samples"][0]
        all_samples = left["samples"] + right["samples"]
        gates.append({"frame": left["frame"], "same_frame": same_frame,
                      "all_4_inputs_11_outputs_exact": all(
                          s["tensors"] == target["tensors"] for s in all_samples),
                      "quads_crops_windows_utf8_exact": all(
                          s["identity"] == target["identity"] for s in all_samples),
                      "proposals_dedupe_components_exact":
                          left["diagnostics"] == right["diagnostics"]})
    return gates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("frames", nargs="+", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or (not args.child and args.probe is None):
        parser.error("positive repeats and probe required")
    if args.child:
        child(args)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name in ("reference", "probe"):
        path = args.output / f"{name}.json"
        env = os.environ.copy()
        env.pop("LD_PRELOAD", None)
        env.pop("GOCR_CONV_PROBE", None)
        if name == "probe":
            env["LD_PRELOAD"] = str(args.probe.resolve())
            env["GOCR_CONV_PROBE"] = str((args.output / "dispatch.json").resolve())
        command = [sys.executable, "-B", __file__, "--child", "--assets", str(args.assets),
                   "--output", str(path), "--repeats", str(args.repeats),
                   *map(str, args.frames)]
        subprocess.run(command, env=env, check=True)
        reports[name] = json.loads(path.read_text())
        with gzip.open(path.with_suffix(".json.gz"), "wt", encoding="utf-8") as out:
            json.dump(reports[name], out, ensure_ascii=False)
        path.unlink()
    gates = compare(reports["reference"], reports["probe"])
    dispatch_path = args.output / "dispatch.json"
    dispatch = json.loads(dispatch_path.read_text())
    metadata = operator_metadata(locate(args.assets, DETECTOR_MODEL))
    # Detector has 167 CONV nodes. Do not confuse recognizer tensor indices
    # with detector indices: require the full set of input/output pairs.
    expected = {(row["input_tensor_indices"][0], row["output_tensor_indices"][0]): index
                for (_, index), row in metadata.items() if row["input_tensor_indices"]}
    contexts = {row["context"] for row in dispatch["nodes"]}
    detector_contexts = []
    for context in contexts:
        rows = [row for row in dispatch["nodes"] if row["context"] == context]
        if len(rows) == 167 and all((r["input_tensor"], r["output_tensor"]) in expected for r in rows):
            detector_contexts.append(context)
            for row in rows:
                row["node_index"] = expected[row["input_tensor"], row["output_tensor"]]
    if len(detector_contexts) != 1:
        raise RuntimeError("detector context could not be unambiguously mapped")
    dispatch["detector_context"] = detector_contexts[0]
    dispatch_path.write_text(json.dumps(dispatch, indent=2))
    passed = all(all(value for key, value in row.items() if key != "frame") for row in gates)
    summary = {"system_sha256": SYSTEM_SHA, "detector_threads": 2,
               "recognizer_threads": 2, "xnnpack": False, "warmup_per_frame": 1,
               "measured_per_frame": args.repeats, "parity_passed": passed, "gates": gates}
    (args.output / "parity.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
