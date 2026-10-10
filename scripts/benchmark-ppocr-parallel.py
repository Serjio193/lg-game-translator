"""Exact raw/TSV gate and alternating full-frame serial/three-core benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import threading

from ppocr_frame_replay import Detector, Pipeline
from ppocr_recognizer_pool import RecognizerPool, close_engine, pinned_engine


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--ctc-library", required=True)
    p.add_argument("--core-library", required=True)
    p.add_argument("--detector-library", required=True)
    p.add_argument("--detector-prefix", required=True)
    p.add_argument("--corpus", type=Path, nargs="+", required=True)
    p.add_argument("--frames", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime/"assets")]
    from PIL import Image
    import ocr.engines as owner
    from ppocr_native_ctc import select_decoder
    select_decoder(owner, args.ctc_library)
    reference = owner.Engines(args.runtime/"assets")
    trace = threading.local()
    original_decode = owner.decode

    def decode(outputs, *parameters):
        trace.hashes.append(hashlib.sha256(outputs.tobytes()).hexdigest())
        return original_decode(outputs, *parameters)

    owner.decode = decode

    def recognize(engine, pixels, width, height):
        trace.hashes = []
        result = engine.recognize(4, pixels, width, height)
        return {"status": result[0], "tsv": result[1], "raw_sha256": trace.hashes}

    report = {"scope": "same models/IO/decoder; core placement only; translation excluded",
              "crops": [], "frames": []}
    inputs = []
    candidates = [pinned_engine(args.runtime/"assets", args.core_library, m) for m in (1, 2, 4)]
    try:
        for corpus in args.corpus:
            for case in json.loads((corpus/"manifest.json").read_text()):
                with Image.open(corpus/case["file"]) as source:
                    image = source.convert("L")
                pixels = image.tobytes()
                inputs.append((pixels, image.width, image.height))
                base = recognize(reference, pixels, image.width, image.height)
                runs = [recognize(e, pixels, image.width, image.height) for e in candidates]
                report["crops"].append({"id": case["id"], "expected": case["expected"],
                                        "reference": base, "cores": runs,
                                        "exact": all(run == base for run in runs)})
        report["raw_gate"] = all(case["exact"] for case in report["crops"])
        print("Raw/TSV gate:", report["raw_gate"], flush=True)
    finally:
        for engine in candidates:
            close_engine(engine)
        owner.decode = original_decode
    if not report["raw_gate"]:
        args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        raise RuntimeError("Core placement changed raw outputs/TSV; no deployment")
    pool = RecognizerPool(lambda mask: pinned_engine(args.runtime/"assets", args.core_library, mask))
    owner.decode = decode
    concurrent_runs = [pool.submit(recognize, pool, *values) for values in inputs]
    concurrent_results = [job.result() for job in concurrent_runs]
    report["concurrent_raw_gate"] = all(run == case["reference"]
        for run, case in zip(concurrent_results, report["crops"]))
    owner.decode = original_decode
    if not report["concurrent_raw_gate"]:
        pool.close()
        args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        raise RuntimeError("Concurrent raw outputs/TSV differ; no deployment")
    detector = Detector(args.detector_library, args.detector_prefix)
    serial = Pipeline(detector, reference)
    parallel = Pipeline(detector, pool, pool)
    try:
        for path in args.frames:
            with Image.open(path) as source:
                image = source.convert("RGB")
            base = serial.ocr(image)
            assert parallel.ocr(image)["regions"] == base["regions"]
            samples = {"serial": [], "parallel": []}
            for repeat in range(5):
                order = ("serial", "parallel") if repeat % 2 == 0 else ("parallel", "serial")
                for label in order:
                    result = (serial if label == "serial" else parallel).ocr(image)
                    assert result["regions"] == base["regions"], "Full frame recognition differs"
                    samples[label].append(result)
            report["frames"].append({"frame": path.name, "exact": True, "samples": samples,
                "median_ms": {k: statistics.median(r["timings_ms"]["full_ocr"] for r in v)
                              for k, v in samples.items()}})
            print(path.name, report["frames"][-1]["median_ms"], flush=True)
        report["workers"] = pool.worker_stats()
    finally:
        pool.close()
        close_engine(reference)
        detector.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
