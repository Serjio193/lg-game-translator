"""Temporary authenticated raw/LZ4 upload probe; no OCR or production changes."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_transport import HEADER, WIDTH, HEIGHT
from gocr_worker.http_security import authorized, read_token, require_private_bind
from gocr_worker.lz4_block import Lz4Block


def handler(codec, token):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connection.settimeout(15)

        def reply(self, status, value):
            raw = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            if not authorized(self.headers, token):
                self.close_connection = True
                return self.reply(401, {"error": "authentication required"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if (self.path != "/v1/transfer-probe" or not 0 < n <= codec.bound
                        or self.headers.get("Transfer-Encoding")):
                    raise ValueError("Invalid request contract")
                raw = self.rfile.read(n)
                if len(raw) != n:
                    raise ValueError("Truncated upload")
                start = time.perf_counter()
                encoding = self.headers.get("Content-Encoding", "identity")
                if encoding == "lz4-block":
                    raw = codec.decompress(raw)
                elif encoding != "identity" or len(raw) != codec.size:
                    raise ValueError("Invalid raw frame")
                decode_ms = (time.perf_counter()-start)*1000
                magic, w, h, _, _, size = HEADER.unpack_from(raw)
                if (magic, w, h, size) != (b"GFR1", WIDTH, HEIGHT, WIDTH*HEIGHT*3):
                    raise ValueError("Changed selected frame contract")
                self.reply(200, {"sha256": hashlib.sha256(raw).hexdigest(),
                                 "decompress_ms": decode_ms,
                                 "server_after_upload_ms": (time.perf_counter()-start)*1000})
            except (ValueError, OSError):
                self.close_connection = True
                self.reply(400, {"error": "invalid frame block"})

        def log_message(self, *args):
            pass
    return Handler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bind", required=True)
    p.add_argument("--port", type=int, default=18777)
    p.add_argument("--token-file", type=Path, required=True)
    args = p.parse_args()
    token = read_token(args.token_file)
    require_private_bind(args.bind, token)
    with HTTPServer((args.bind, args.port), handler(Lz4Block(), token)) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
