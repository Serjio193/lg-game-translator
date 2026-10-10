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

        def reject(self, status, reason, body_consumed=False):
            # Unread request bodies must not become a second persistent request.
            self.close_connection = True
            # Drain only tiny malformed bodies so closing TCP does not discard
            # the error response with a reset. Never buffer an untrusted frame.
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if (not body_consumed and 0 < length <= 4096
                        and not self.headers.get("Transfer-Encoding")):
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
            body_consumed = False
            streaming = False
            stream_bytes = 0
            def event(value):
                nonlocal stream_bytes
                raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()+b"\n"
                stream_bytes += len(raw)
                if stream_bytes > MAX_REPLY:
                    raise ValueError("region stream exceeds reply budget")
                self.wfile.write(f"{len(raw):x}\r\n".encode()+raw+b"\r\n")
                self.wfile.flush()
            try:
                size = int(self.headers.get("Content-Length", "0"))
                expected_size = HEADER.size+WIDTH*HEIGHT*3
                encoding = self.headers.get("Content-Encoding", "identity")
                if encoding == "lz4-block":
                    from .lz4_block import Lz4Block
                    if not hasattr(self, "lz4_codec"):
                        self.lz4_codec = Lz4Block()
                    valid_size = 0 < size <= self.lz4_codec.bound
                else:
                    valid_size = encoding == "identity" and size == expected_size
                if (not valid_size or self.headers.get("Content-Type") != "application/x-gocr-frame"
                        or self.headers.get("Transfer-Encoding")):
                    return self.reject(413, "invalid frame body contract")
                payload = self.rfile.read(size)
                body_consumed = True
                started = time.perf_counter()
                if encoding == "lz4-block":
                    payload = self.lz4_codec.decompress(payload)
                decompress_ms = (time.perf_counter()-started)*1000
                image, sequence, captured = receive_frame(ByteStream(payload))
                decode_ms = (time.perf_counter()-started)*1000
                frame_hash = fingerprint(image)
                context = {"sequence": sequence, "capture_ts": captured, "frame_sha256": frame_hash}
                if self.headers.get("Accept") == "application/x-ndjson":
                    if not getattr(worker, "supports_region_events", False):
                        return self.reject(400, "region events unsupported", True)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    streaming = True
                    result = worker.ocr(image, on_region=lambda line: event(
                        {"event": "region", **context, "line": line}))
                else:
                    result = worker.ocr(image)
                result.update(sequence=sequence, capture_ts=captured, frame_sha256=frame_hash,
                              execution_location="orange", experimental=True)
                result["timings_ms"].update(frame_decode=decode_ms,
                    frame_decompress=decompress_ms,
                    orange_request=(time.perf_counter()-started)*1000)
                completed = result["timings_ms"].get("detector_completed_monotonic_ms")
                if completed is not None:
                    result["timings_ms"]["after_detector_to_reply_ms"] = (
                        time.perf_counter()*1000-completed)
                if streaming:
                    event({"event": "final", **context, "result": result})
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
                else:
                    self.send_json(200, result)
            except Exception:
                logging.exception("Orange full-frame OCR failed")
                if streaming:
                    self.close_connection = True
                    try:
                        event({"event": "error", "error": "full-frame OCR failed"})
                        self.wfile.write(b"0\r\n\r\n")
                        self.wfile.flush()
                    except (OSError, ValueError):
                        pass
                else:
                    self.reject(400, "full-frame OCR failed", body_consumed)

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
