from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from .assets import verify_bundle
from .protocol import Line, OcrResult, Point, Quad
from .recognizer import GocrLineRecognizer

LOG = logging.getLogger("gocr-worker")


def _quad(value):
    if value is None:
        return None
    if len(value) != 4:
        raise ValueError("source_quad must contain four [x,y] points")
    p = [Point(float(x), float(y)) for x, y in value]
    return Quad(*p)


class GocrWorker:
    def __init__(self, assets: Path, threads: int = 2):
        self.assets = assets
        self.asset_status = verify_bundle(assets)
        self.recognizer = GocrLineRecognizer(assets, threads=threads)

    def recognize_crop(self, image: Image.Image, meta: dict | None = None) -> dict:
        meta = meta or {}
        r = self.recognizer.recognize(image)
        line = Line(
            line_id=str(meta.get("line_id", "0")),
            text=r["text"],
            source_quad=_quad(meta.get("source_quad")),
            angle=float(meta.get("angle", 0.0)),
            detector_confidence=(None if meta.get("detector_confidence") is None else float(meta["detector_confidence"])),
            recognizer_confidence=None,
            timings_ms={"recognizer": r["total_ms"], "tflite_invoke": r["invoke_ms"]},
        )
        result = OcrResult(
            schema="gocr.worker.v1",
            width=image.width,
            height=image.height,
            mode="crop",
            lines=[line],
            timings_ms={"recognizer": r["total_ms"]},
            parity={
                "detector": "external_google_crop",
                "recognizer_model": "google_original",
                "recognizer_decoder": r["decoder"],
                "production_lm_fst_applied": r["production_lm_fst_applied"],
                "window_contract": "google_config_16_136_16",
            },
        )
        return result.to_dict()

    def recognize_image(self, image: Image.Image) -> dict:
        # Exact portable GroupRPN grouping is intentionally not faked here.
        raise NotImplementedError(
            "full-image GOCR detector parity is not finished yet; "
            "use crop mode with Google crops until GroupRPN grouping parity is closed"
        )


def _decode_image_b64(value: str) -> Image.Image:
    raw = base64.b64decode(value, validate=True)
    image = Image.open(io.BytesIO(raw))
    image.load()
    return image


def make_handler(worker: GocrWorker):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GOCRWorker/0.1"

        def _send(self, status, obj):
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/v1/health":
                self._send(200, {"status": "ok", "schema": "gocr.worker.v1"})
            elif self.path == "/v1/assets":
                self._send(200, worker.asset_status)
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > 16 * 1024 * 1024:
                    return self._send(413, {"error": "body must be 1..16777216 bytes"})
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                image = _decode_image_b64(body["image_b64"])
                if self.path == "/v1/recognize-crop":
                    return self._send(200, worker.recognize_crop(image, body.get("meta")))
                if self.path == "/v1/ocr":
                    try:
                        return self._send(200, worker.recognize_image(image))
                    except NotImplementedError as exc:
                        return self._send(501, {"error": str(exc), "parity": "detector_pending"})
                self._send(404, {"error": "not found"})
            except Exception as exc:
                LOG.exception("request failed")
                self._send(400, {"error": f"{type(exc).__name__}: {exc}"})

        def log_message(self, fmt, *args):
            LOG.info(fmt, *args)

    return Handler


def main():
    parser = argparse.ArgumentParser(description="GOCR worker")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=max(1, int(os.environ.get("GOCR_THREADS", "2"))))
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crop")
    c.add_argument("image", type=Path)
    c.add_argument("--meta-json")
    s = sub.add_parser("serve")
    s.add_argument("--bind", default=os.environ.get("GOCR_BIND", "127.0.0.1"))
    s.add_argument("--port", type=int, default=int(os.environ.get("GOCR_PORT", "8770")))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    worker = GocrWorker(args.assets, threads=args.threads)
    if args.cmd == "crop":
        meta = json.loads(args.meta_json) if args.meta_json else {}
        with Image.open(args.image) as image:
            result = worker.recognize_crop(image, meta)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    server = ThreadingHTTPServer((args.bind, args.port), make_handler(worker))
    LOG.info("GOCR worker listening on %s:%d", args.bind, args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
