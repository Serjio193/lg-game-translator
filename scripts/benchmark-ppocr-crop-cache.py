"""Exact cache gate on frozen crops and saved full-frame repeat passes."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from ppocr_crop_cache import ExactCropCache
from ppocr_frame_replay import Detector, Pipeline


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--ctc-library", required=True)
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
    engine = owner.Engines(args.runtime/"assets")
    cache = ExactCropCache(engine)
    report = {"scope": "exact installed mode-4 TSV cache; saved repeats; production remains running",
              "crops": [], "frames": []}
    for corpus in args.corpus:
        for case in json.loads((corpus/"manifest.json").read_text()):
            with Image.open(corpus/case["file"]) as source:
                image = source.convert("L")
            pixels = image.tobytes()
            reference = engine.recognize(4, pixels, image.width, image.height)
            first = cache.recognize(4, pixels, image.width, image.height)
            assert first == reference, "First cache pass changed TSV"
            samples = {"uncached": [], "cached": []}
            calls = cache.cache_stats()["recognize_calls"]
            for repeat in range(5):
                for label in (("uncached", "cached") if repeat % 2 == 0 else ("cached", "uncached")):
                    start = time.perf_counter()
                    result = (engine if label == "uncached" else cache).recognize(
                        4, pixels, image.width, image.height)
                    samples[label].append((time.perf_counter()-start)*1000)
                    assert result == reference, "Repeated recognition/TSV differs"
            assert cache.cache_stats()["recognize_calls"] == calls, "Cache hit invoked engine"
            altered = bytes([pixels[0]^1])+pixels[1:]
            cache.recognize(4, altered, image.width, image.height)
            assert cache.cache_stats()["recognize_calls"] == calls+1, "Single-pixel mutation not recognized"
            report["crops"].append({"id": case["id"], "expected": case["expected"],
                "pixels_sha256": hashlib.sha256(pixels).hexdigest(), "tsv": reference[1],
                "status": reference[0], "exact_reference": True, "changed_pixel_miss": True,
                "samples_ms": samples,
                "median_ms": {k: statistics.median(v) for k, v in samples.items()}})
    detector = Detector(args.detector_library, args.detector_prefix)
    try:
        plain = Pipeline(detector, engine)
        for path in args.frames:
            with Image.open(path) as source:
                image = source.convert("RGB")
            baseline = plain.ocr(image)
            fresh = Pipeline(detector, ExactCropCache(engine))
            first = fresh.ocr(image)
            assert first["regions"] == baseline["regions"]
            samples = {"uncached": [], "cached": []}
            for repeat in range(5):
                for label in (("uncached", "cached") if repeat % 2 == 0 else ("cached", "uncached")):
                    result = (plain if label == "uncached" else fresh).ocr(image)
                    assert result["regions"] == baseline["regions"]
                    samples[label].append(result)
            report["frames"].append({"frame": path.name, "exact_reference": True,
                "first_pass": first, "samples": samples,
                "median_ms": {k: statistics.median(r["timings_ms"]["full_ocr"] for r in v)
                              for k, v in samples.items()}})
            print(path.name, report["frames"][-1]["median_ms"], flush=True)
    finally:
        detector.close()
        for model in engine.npu.values():
            model.close()
        for model, _ in getattr(engine.local, "models", {}).values():
            model.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
