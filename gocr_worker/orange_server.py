"""Explicit experimental full-frame GOCR worker on Orange, with lossless input."""
import argparse
import io
import json
import logging
import os
from pathlib import Path
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .frame_transport import HEADER, WIDTH, HEIGHT, MAX_REPLY, receive_frame
from .http_security import authorized, read_token, require_private_bind
from .image_contract import fingerprint
from .assets import verify_bundle


class ByteStream:
    def __init__(self, raw):
        self.stream = io.BytesIO(raw)

    def recv(self, length):
        return self.stream.read(length)


def make_handler(worker, token):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connection.settimeout(30)

        def send_json(self, status, value):
            raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            if len(raw) > MAX_REPLY:
                raise ValueError("response exceeds frame budget")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)

        def reject(self, status, reason):
            # Unread request bodies must not become a second persistent request.
            self.close_connection = True
            # Drain only tiny malformed bodies so closing TCP does not discard
            # the error response with a reset. Never buffer an untrusted frame.
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if 0 < length <= 4096 and not self.headers.get("Transfer-Encoding"):
                    self.rfile.read(length)
            except (ValueError, OSError):
                pass
            self.send_json(status, {"error": reason})

        def do_GET(self):
            if not authorized(self.headers, token):
                return self.reject(401, "authentication required")
            if self.path != "/v1/health":
                return self.reject(404, "not found")
            self.send_json(200, {"status": "ok", "mode": "ORANGE_FULL",
                                 "experimental": True, "production_equivalence": False})

        def do_POST(self):
            if not authorized(self.headers, token):
                return self.reject(401, "authentication required")
            if self.path != "/v1/ocr-frame":
                return self.reject(404, "not found")
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if (size != HEADER.size+WIDTH*HEIGHT*3
                        or self.headers.get("Content-Type") != "application/x-gocr-frame"
                        or self.headers.get("Transfer-Encoding")):
                    return self.reject(413, "invalid frame body contract")
                payload = self.rfile.read(size)
                started = time.perf_counter()
                image, sequence, captured = receive_frame(ByteStream(payload))
                decode_ms = (time.perf_counter()-started)*1000
                frame_hash = fingerprint(image)
                result = worker.ocr(image)
                result.update(sequence=sequence, capture_ts=captured, frame_sha256=frame_hash,
                              execution_location="orange", experimental=True)
                result["timings_ms"].update(frame_decode=decode_ms,
                    orange_request=(time.perf_counter()-started)*1000)
                self.send_json(200, result)
            except Exception:
                logging.exception("Orange full-frame OCR failed")
                self.reject(400, "full-frame OCR failed")

        def log_message(self, *args):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8772)
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--detector-threads", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--recognizer-threads", type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    token = read_token(args.token_file)
    require_private_bind(args.bind, token)
    # Match the measured delegates-off Orange experiment, not TV system STRICT.
    os.environ.update(GOCR_PROFILE="strict", GOCR_DETECTOR="python",
                      GOCR_RECOGNIZER="python", GOCR_LITERT_DELEGATES="off")
    from .worker_full import FullGocrWorker
    verify_bundle(args.assets, "full", require_support_files=True)
    worker = FullGocrWorker(args.assets, detector_threads=args.detector_threads,
                           recognizer_threads=args.recognizer_threads)
    if worker.detector.native_postprocess is None:
        worker.close()
        raise RuntimeError("Orange worker requires the built native postprocess")
    try:
        with ThreadingHTTPServer((args.bind, args.port), make_handler(worker, token)) as server:
            server.daemon_threads = True
            server.serve_forever()
    finally:
        worker.close()


if __name__ == "__main__":
    main()
