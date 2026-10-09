"""Quality-first RKNN experiment; original models, inputs and decoder stay fixed."""
import argparse
import ctypes as C
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--profile-reference", type=Path)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime/"assets")]
    from PIL import Image
    from runtime import Runtime
    from ocr.ppocr_codec import preprocess, decode
    from ocr.recognizer_config import load
    name, directory, layout, characters = load(args.runtime/"assets")
    cases = json.loads((args.corpus/"manifest.json").read_text())
    report = {"recognizer": name, "model_changes": False, "cases": [],
              "scope": "recognizer only; warmed calls; production remains running",
              "model_sha256": {filename: hashlib.sha256((directory/filename).read_bytes()).hexdigest()
                               for filename in ("recognizer.rknn", "recognizer-2560.rknn")},
              "characters_sha256": hashlib.sha256((directory/"characters.json").read_bytes()).hexdigest()}
    runtimes = {"installed": Runtime(args.runtime/"assets/libnpu_bridge.so")}
    for label, path in (("profile_reference", args.profile_reference), ("prealloc", args.candidate)):
        if path:
            runtimes[label] = Runtime(path)
            runtimes[label].lib.npu_profile_ms.argtypes = [C.c_int]
            runtimes[label].lib.npu_profile_ms.restype = C.c_double
    models = {}
    try:
        for case in cases:
            with Image.open(args.corpus/case["file"]) as source:
                image = source.convert("L")
            width = 640 if math.ceil(image.width*48/image.height) <= 640 else 2560
            values = preprocess(image, width)
            input_sha = hashlib.sha256(values.tobytes()).hexdigest()
            for label, runtime in runtimes.items():
                if (label, width) not in models:
                    filename = "recognizer.rknn" if width == 640 else "recognizer-2560.rknn"
                    models[label, width] = runtime.model(directory/filename)
                models[label, width](x=values)
            samples = {label: [] for label in runtimes}
            for repeat in range(5):
                order = list(runtimes) if repeat % 2 == 0 else list(reversed(runtimes))
                for label in order:
                    start = time.perf_counter()
                    scores = models[label, width](x=values)[0]
                    completed = time.perf_counter()
                    text, confidence = decode(scores, characters, layout)
                    decoded = time.perf_counter()
                    row = {"text": text, "confidence": confidence,
                           "output_sha256": hashlib.sha256(scores.tobytes()).hexdigest(),
                           "recognizer_ms": (completed-start)*1000,
                           "decode_ms": (decoded-completed)*1000}
                    if label != "installed":
                        keys = ("inputs_set", "run", "outputs_get", "memcpy", "outputs_release", "bridge_total")
                        row["native_ms"] = {k: runtimes[label].lib.npu_profile_ms(i)
                                            for i, k in enumerate(keys)}
                    samples[label].append(row)
            original = samples["installed"][0]
            hashes = [r["output_sha256"] for rows in samples.values() for r in rows]
            exact = all(h == original["output_sha256"] for h in hashes)
            result = {**case, "input_sha256": input_sha, "width": width,
                      "crop_gray_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
                      "source_file_sha256": hashlib.sha256((args.corpus/case["file"]).read_bytes()).hexdigest(),
                      "quality_exact": original["text"] == case["expected"],
                      "all_raw_outputs_exact": exact, "samples": samples,
                      "median_ms": {label: statistics.median(r["recognizer_ms"] for r in rows)
                                    for label, rows in samples.items()}}
            report["cases"].append(result)
            args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"case": case["id"], "expected": case["expected"],
                              "actual": original["text"], "quality_exact": result["quality_exact"],
                              "raw_exact": exact, "median_ms": result["median_ms"]}, ensure_ascii=False), flush=True)
    finally:
        for model in models.values():
            model.close()
    if args.candidate and not all(case["all_raw_outputs_exact"] for case in report["cases"]):
        raise SystemExit("Candidate rejected: raw output mismatch")


if __name__ == "__main__":
    main()
