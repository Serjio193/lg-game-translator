"""Replay complete PP-OCR on Orange without altering production or invoking translation."""
import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

from PIL import Image
from ppocr_frame_replay import Detector, Pipeline


def signature(result):
    return [(r["box"], [(a["box"], a["text"]) for a in r["lines"]])
            for r in result["regions"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--detector-prefix", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--frames", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    sys.path[:0] = [str(args.runtime), str(args.runtime / "assets")]
    from ocr.engines import Engines
    engines = Engines(args.runtime / "assets")
    detector = Detector(args.library, args.detector_prefix)
    report = {"scope": "Orange full-frame to text; transfer/translation/OSD excluded",
              "recognizer": engines.model_name, "mode": 4, "warmups": 1, "frames": []}
    try:
        pipeline = Pipeline(detector, engines)
        for path in args.frames:
            with Image.open(path) as source:
                image = source.convert("RGB")
            pipeline.ocr(image)
            results = [pipeline.ocr(image) for _ in range(args.repeats)]
            row = {"frame": path.name, "rgb_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
                   "repeat_identical": all(signature(r) == signature(results[0]) for r in results),
                   "median_ms": {name: statistics.median(r["timings_ms"][name] for r in results)
                                 for name in results[0]["timings_ms"]}, "runs": results}
            report["frames"].append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "runs"}), flush=True)
    finally:
        detector.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
