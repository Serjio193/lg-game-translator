"""Replay saved frames through authenticated ORANGE_FULL and compare local OCR."""
import argparse
import gzip
import json
from pathlib import Path
import statistics
import sys

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_client import FrameClient
from gocr_worker.http_security import read_token


def identity(result):
    return [(line["text"], line["source_quad"], line["crop_sha256"],
             line["recognizer_input_sha256"]) for line in result["lines"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    with gzip.open(args.reference, "rt", encoding="utf-8") as stream:
        references = json.load(stream)["frames"]
    client = FrameClient(args.endpoint, read_token(args.token_file))
    report = {"scope": "relay vs same Orange runtime; not TV STRICT parity", "frames": []}
    try:
        for index, reference in enumerate(references):
            with Image.open(args.corpus/reference["frame"]) as source:
                image = source.convert("RGB")
            client.ocr(image, index, 0)
            results = [client.ocr(image, index, 0)[0] for _ in range(args.repeats)]
            row = {"frame": reference["frame"], "exact_local_ocr": all(
                identity(result) == identity(reference["samples"][0]) for result in results),
                "timings_ms": {key: statistics.median(r["timings_ms"][key] for r in results)
                               for key in results[0]["timings_ms"]}, "samples": results}
            report["frames"].append(row)
            with gzip.open(args.output, "wt", encoding="utf-8") as stream:
                json.dump(report, stream, ensure_ascii=False)
            print(json.dumps({key: value for key, value in row.items() if key != "samples"}), flush=True)
    finally:
        client.close()
    return 0 if all(row["exact_local_ocr"] for row in report["frames"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
