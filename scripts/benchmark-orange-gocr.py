"""Isolated Orange CPU experiment; never changes worker production settings."""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--detector-threads", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--recognizer-threads", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--delegate", choices=("off", "default"), default="off")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    os.environ.update(GOCR_PROFILE="strict", GOCR_DETECTOR="python",
                      GOCR_RECOGNIZER="python", GOCR_POSTPROCESS="native")
    # Override only this experiment process. Production interpreter.py is unchanged.
    import gocr_worker.interpreter as binding
    from ai_edge_litert.interpreter import Interpreter, OpResolverType

    def create(model_path, num_threads):
        options = {}
        if args.delegate == "off":
            options["experimental_op_resolver_type"] = (
                OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
        return Interpreter(model_path=str(model_path), num_threads=num_threads, **options)

    binding.create_interpreter = create
    from gocr_worker.worker_full import FullGocrWorker
    start = time.perf_counter()
    worker = FullGocrWorker(args.assets, detector_threads=args.detector_threads,
                            recognizer_threads=args.recognizer_threads)
    if worker.detector.native_postprocess is None:
        raise RuntimeError("experiment requires native postprocess")
    report = {"scope": "local frame to text; excludes transfer/translation/OSD",
              "runtime": importlib.metadata.version("ai-edge-litert"),
              "machine": platform.machine(), "delegate": args.delegate,
              "detector_threads": args.detector_threads,
              "recognizer_threads": args.recognizer_threads,
              "initialization_ms": (time.perf_counter()-start)*1000,
              "frames": []}

    def save():
        with gzip.open(args.output, "wt", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False)

    try:
        for path in sorted(args.corpus.glob("*.png")):
            with Image.open(path) as source:
                image = source.convert("RGB")
            if image.size != (1280, 720):
                raise ValueError(f"unexpected corpus frame size: {path}: {image.size}")
            warmup = worker.ocr(image)
            samples = [worker.ocr(image) for _ in range(args.repeats)]
            summary = {key: {"median": statistics.median(r["timings_ms"][key] for r in samples),
                             "min": min(r["timings_ms"][key] for r in samples),
                             "max": max(r["timings_ms"][key] for r in samples)}
                       for key in samples[0]["timings_ms"]}
            identities = [[(line["text"], line["source_quad"], line["crop_sha256"],
                            line["recognizer_input_sha256"]) for line in r["lines"]]
                          for r in samples]
            row = {"frame": path.name, "frame_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "warmup_ms": warmup["timings_ms"], "summary": summary,
                   "repeat_identity": all(i == identities[0] for i in identities),
                   "samples": samples}
            report["frames"].append(row)
            save()
            print(json.dumps({key: row[key] for key in ("frame", "summary", "repeat_identity")}),
                  flush=True)
    finally:
        worker.close()


if __name__ == "__main__":
    main()
