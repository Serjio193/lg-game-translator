"""Saved-frame stage profile preserving original calls/results; no translation."""
import argparse
import json
from pathlib import Path
import statistics
import sys
from PIL import Image
from ppocr_frame_replay import Detector, Pipeline
from ppocr_stage_profiler import StageProfiler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--library", required=True)
    p.add_argument("--detector-prefix", required=True)
    p.add_argument("--frames", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime/"assets")]
    from ocr.engines import Engines
    pipeline = Pipeline(Detector(args.library, args.detector_prefix), Engines(args.runtime/"assets"))
    profiler = None
    report = {"scope": "warmed saved-frame stages; no transport/translation/OSD",
              "production_service_remains_running": True, "frames": []}
    try:
        # Warm both model buckets and icon helper before installing wrappers.
        images = []
        for path in args.frames:
            with Image.open(path) as source:
                image = source.convert("RGB")
            images.append((path, image, pipeline.ocr(image)))
        profiler = StageProfiler(pipeline)
        for path, image, reference in images:
            samples = []
            for _ in range(5):
                profiler.begin()
                result = pipeline.ocr(image)
                assert result["regions"] == reference["regions"], "Profiling changed text/geometry/confidence"
                samples.append({"timings_ms": result["timings_ms"], **profiler.snapshot()})
            stages = sorted(set().union(*(s["totals_ms"] for s in samples)))
            row = {"frame": path.name, "regions": len(reference["regions"]),
                   "crops": sum(len(r["lines"]) for r in reference["regions"]),
                   "exact_reference": True, "samples": samples,
                   "stage_median_ms": {k: statistics.median(s["totals_ms"].get(k, 0) for s in samples)
                                       for k in stages},
                   "frame_median_ms": {k: statistics.median(s["timings_ms"][k] for s in samples)
                                       for k in ("gray", "detector", "full_ocr")}}
            report["frames"].append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "samples"}), flush=True)
    finally:
        if profiler:
            profiler.close()
        pipeline.detector.close()
    args.output.write_text(json.dumps(report), encoding="utf-8")


if __name__ == "__main__":
    main()
