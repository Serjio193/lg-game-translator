"""Native strict Invoke profiling; warmups excluded, shapes queried after allocation."""
import argparse
import ctypes as C
import json
import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.assets import DETECTOR_MODEL, locate
from gocr_worker.native_detector import NativeDetector
from gocr_worker.model_operator_metadata import operator_metadata
from gocr_worker.runner_diagnostics import tensor_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--runtime", default="/usr/lib/libtensorflow-lite.so")
    parser.add_argument("frame", type=Path)
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("iterations must be positive")
    raw_path = args.output.with_suffix(".raw.json")
    os.environ.update(GOCR_PROFILE="strict", GOCR_DETECTOR_PROFILE=str(raw_path))
    detector = NativeDetector(args.assets, threads=2, runtime=args.runtime, xnnpack=False)
    try:
        detector.detect(Image.open(args.frame).convert("RGB"))
        before = tensor_hashes(detector)
        reset = detector.lib.gocr_detector_reset_profile
        reset.argtypes = [C.c_void_p]
        reset.restype = None
        reset(detector.context)
        for _ in range(args.iterations):
            if detector.lib.gocr_detector_invoke(detector.context):
                raise RuntimeError("strict Invoke failed")
        after = tensor_hashes(detector)
        dims = detector.lib.gocr_detector_tensor_dims
        dims.argtypes = [C.c_void_p, C.c_int, C.POINTER(C.c_int), C.c_int]
        dims.restype = C.c_int

        def shape(index):
            if index < 0:
                return None
            values = (C.c_int * 16)()
            size = dims(detector.context, index, values, len(values))
            if size < 0 or size > len(values):
                raise RuntimeError("allocated tensor shape unavailable")
            return list(values[:size])

        metadata = operator_metadata(locate(args.assets, DETECTOR_MODEL))
        for row in metadata.values():
            row["input_shapes"] = [shape(i) for i in row["input_tensor_indices"]]
            row["output_shapes"] = [shape(i) for i in row["output_tensor_indices"]]
    finally:
        detector.close()
    report = json.loads(raw_path.read_text(encoding="utf-8"))
    for row in report["operators"]:
        row.update(metadata.get((row["subgraph_index"], row["node_index"]), {}))
        row["kernel_backend"] = "not exposed by public telemetry C API"
    report.update(runtime=args.runtime, threads=2, xnnpack=False,
                  warmups=1, frame=str(args.frame), raw_tensors_repeat_equal=before == after,
                  tensor_hashes=after)
    report["operators"].sort(key=lambda row: row["total_ms"], reverse=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("invoke_count", "invoke_total_ms", "raw_tensors_repeat_equal")}))


if __name__ == "__main__":
    main()
