"""Paired TV-detector/crop-RPC vs Orange-full replay, excluding translation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import socket
import statistics
import struct
import sys
import threading
import time

import numpy as np
from PIL import Image
from ppocr_frame_replay import Detector, Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_client import FrameClient
from gocr_worker.http_security import read_token


def read_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise EOFError("Crop connection closed")
        data.extend(part)
    return bytes(data)


class RemoteEngines:
    def __init__(self, config):
        self.host, port, token = Path(config).read_text().split()
        self.port, self.token = int(port), token.encode()
        if len(self.token) != 64:
            raise ValueError("Invalid crop credential")
        self.local = threading.local()
        self.sockets = []
        self.lock = threading.Lock()

    def recognize(self, mode, pixels, width, height):
        if not hasattr(self.local, "socket"):
            sock = socket.create_connection((self.host, self.port), timeout=30)
            self.local.socket = sock
            with self.lock:
                self.sockets.append(sock)
        sock = self.local.socket
        body = struct.pack("!4sHHB3x64s", b"OCR1", width, height, mode, self.token) + pixels
        sock.sendall(struct.pack("!I", len(body)) + body)
        raw = read_exact(sock, struct.unpack("!I", read_exact(sock, 4))[0])
        if not raw or raw[0] not in (0, 1):
            raise ValueError("Crop recognition failed")
        return raw[0], raw[1:].decode()

    def close(self):
        for sock in self.sockets:
            sock.close()


def identity(result):
    return [(r["box"], [(a["box"], a["text"]) for a in r["lines"]])
            for r in result["regions"]]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library", required=True)
    p.add_argument("--detector-prefix", required=True)
    p.add_argument("--crop-config", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--frames", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    detector = Detector(args.library, args.detector_prefix)
    engines = RemoteEngines(args.crop_config)
    remote = FrameClient(args.address, read_token(args.token_file))
    report = {"scope": "paired saved-frame OCR; no cache/suppression/translation/OSD",
              "crop_clients": 2, "frames": []}
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            pipeline = Pipeline(detector, engines, pool=pool)
            for path in args.frames:
                with Image.open(path) as source:
                    image = source.convert("RGB")
                pipeline.ocr(image)
                remote.ocr(image)
                samples = {"tv_detector": [], "orange_full": []}
                for repeat in range(5):
                    for mode in (("tv_detector", "orange_full") if repeat % 2 == 0
                                 else ("orange_full", "tv_detector")):
                        start = time.perf_counter()
                        result = (pipeline.ocr(image) if mode == "tv_detector"
                                  else remote.ocr(image, repeat + 1)[0])
                        samples[mode].append({"wall_ms": (time.perf_counter()-start)*1000,
                                              "result": result})
                row = {"frame": path.name, "samples": samples,
                       "median_ms": {k: statistics.median(s["wall_ms"] for s in v)
                                     for k, v in samples.items()}}
                row["all_text_geometry_equal"] = all(
                    identity(s["result"]) == identity(samples["tv_detector"][0]["result"])
                    for values in samples.values() for s in values)
                report["frames"].append(row)
                print(json.dumps({k: v for k, v in row.items() if k != "samples"}), flush=True)
    finally:
        engines.close()
        detector.close()
        remote.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
