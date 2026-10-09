"""Decode identical RKNN tensors with current Python and experimental native CTC."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from ppocr_native_ctc import NativeCtc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--corpus", type=Path, nargs="+", required=True)
    p.add_argument("--library", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime/"assets")]
    from PIL import Image
    from runtime import Runtime
    from ocr.ppocr_codec import preprocess, decode
    from ocr.recognizer_config import load
    name, directory, layout, characters = load(args.runtime/"assets")
    native = NativeCtc(args.library)
    runtime = Runtime(args.runtime/"assets/libnpu_bridge.so")
    models, cases = {}, []
    report = {"scope": "decode only on identical original outputs", "recognizer": name, "cases": cases}
    try:
        for corpus in args.corpus:
            for case in json.loads((corpus/"manifest.json").read_text()):
                with Image.open(corpus/case["file"]) as source:
                    image = source.convert("L")
                width = 640 if math.ceil(image.width*48/image.height) <= 640 else 2560
                if width not in models:
                    filename = "recognizer.rknn" if width == 640 else "recognizer-2560.rknn"
                    models[width] = runtime.model(directory/filename)
                values = preprocess(image, width)
                models[width](x=values)
                scores = models[width](x=values)[0]
                reference = decode(scores, characters, layout)
                samples = {"python": [], "native": []}
                outputs = []
                native.decode(scores, characters, layout)
                for repeat in range(10):
                    for label in (("python", "native") if repeat % 2 == 0 else ("native", "python")):
                        start = time.perf_counter()
                        result = (decode(scores, characters, layout) if label == "python"
                                  else native.decode(scores, characters, layout))
                        samples[label].append((time.perf_counter()-start)*1000)
                        assert result == reference, "Native text or confidence differs"
                        outputs.append(result)
                row = {**case, "width": width, "actual": reference[0], "confidence": reference[1],
                       "quality_exact": reference[0] == case["expected"], "reference_exact": True,
                       "output_sha256": hashlib.sha256(scores.tobytes()).hexdigest(),
                       "input_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
                       "median_ms": {k: statistics.median(v) for k, v in samples.items()},
                       "samples_ms": samples}
                cases.append(row)
                args.output.write_text(json.dumps(report, ensure_ascii=False))
                print(json.dumps({k: row[k] for k in ("id", "reference_exact", "median_ms")}), flush=True)
    finally:
        for model in models.values():
            model.close()


if __name__ == "__main__":
    main()
