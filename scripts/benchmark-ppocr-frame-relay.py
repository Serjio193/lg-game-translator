"""TV lossless frame → authenticated Orange PP-OCR → validated UTF-8 reply."""
import argparse
import json
from pathlib import Path
import statistics
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_client import FrameClient
from gocr_worker.http_security import read_token


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--address", required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--frames", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repeats", type=int, default=5)
    args = p.parse_args()
    if args.repeats < 1:
        p.error("repeats must be positive")
    client = FrameClient(args.address, read_token(args.token_file))
    report = {"scope": "selected RGB frame on TV to PP-OCR text returned; no translation/OSD",
              "frames": []}
    sequence = 0
    try:
        for path in args.frames:
            with Image.open(path) as source:
                image = source.convert("RGB")
            client.ocr(image)
            runs = []
            for _ in range(args.repeats):
                sequence += 1
                result, sent = client.ocr(image, sequence, 0)
                if result.get("engine") != "ppocr":
                    raise ValueError("Probe did not run PP-OCR")
                result["bytes_sent"] = sent
                runs.append(result)
            identities = [[(a["source_quad"], a["text"]) for a in r["lines"]] for r in runs]
            row = {"frame": path.name, "repeat_identical": all(i == identities[0] for i in identities),
                   "median_ms": {k: statistics.median(r["timings_ms"][k] for r in runs)
                                 for k in runs[0]["timings_ms"]}, "runs": runs}
            report["frames"].append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "runs"}), flush=True)
    finally:
        client.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
