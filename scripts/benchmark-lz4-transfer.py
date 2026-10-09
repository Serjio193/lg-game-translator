"""TV compression plus actual LAN round trip, alternating raw and LZ4."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import statistics
import sys
import time

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_transport import encode_frame
from gocr_worker.http_security import read_token
from gocr_worker.lz4_block import Lz4Block


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=18777)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--library", required=True)
    p.add_argument("--frames", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    codec = Lz4Block(args.library)
    token = read_token(args.token_file)
    connection = http.client.HTTPConnection(args.host, args.port, timeout=15)
    report = {"scope": "pre-materialized GFR1 RGB → compress/upload/decompress/ack; no OCR",
              "frames": []}
    try:
        for path in args.frames:
            with Image.open(path) as image:
                raw = encode_frame(image.convert("RGB"))
            expected = hashlib.sha256(raw).hexdigest()
            samples = {"raw": [], "lz4_1": [], "lz4_4": []}
            for repeat in range(11):
                order = list(samples) if repeat % 2 == 0 else list(reversed(samples))
                for mode in order:
                    start = time.perf_counter()
                    body = raw if mode == "raw" else codec.compress(raw, int(mode[-1]))
                    packed = time.perf_counter()
                    connection.request("POST", "/v1/transfer-probe", body, {
                        "Authorization": "Bearer " + token,
                        "Content-Encoding": "identity" if mode == "raw" else "lz4-block"})
                    response = connection.getresponse()
                    answer = json.loads(response.read(4096))
                    completed = time.perf_counter()
                    if response.status != 200 or answer.get("sha256") != expected:
                        raise ValueError("Lossless selected frame identity failed")
                    row = {"bytes": len(body), "compress_ms": (packed-start)*1000,
                           "rpc_ms": (completed-packed)*1000,
                           "total_ms": (completed-start)*1000, **answer}
                    if repeat:
                        samples[mode].append(row)
            summary = {mode: {k: statistics.median(r[k] for r in rows)
                              for k in ("bytes", "compress_ms", "rpc_ms", "total_ms", "decompress_ms")}
                       for mode, rows in samples.items()}
            report["frames"].append({"frame": path.name, "sha256": expected,
                                     "summary": summary, "samples": samples})
            print(json.dumps({"frame": path.name, "summary": summary}), flush=True)
    finally:
        connection.close()
    args.output.write_text(json.dumps(report), encoding="utf-8")


if __name__ == "__main__":
    main()
