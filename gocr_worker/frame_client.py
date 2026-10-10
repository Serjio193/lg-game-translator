"""Authenticated lossless full-frame relay; no OCR models are loaded on TV."""
import http.client
import json
import time
import os
from urllib.parse import urlsplit

from .frame_transport import MAX_REPLY, encode_frame
from .image_contract import fingerprint, quad_points


def reject_nonfinite(value):
    raise ValueError("nonfinite JSON value")


class FrameClient:
    def __init__(self, address, token=None, timeout=30):
        parsed = urlsplit(address)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("invalid Orange frame worker address")
        self.host, self.port = parsed.hostname, parsed.port
        self.connection_type = (http.client.HTTPSConnection if parsed.scheme == "https"
                                else http.client.HTTPConnection)
        self.token, self.timeout, self.connection = token, timeout, None
        self.early_translation = os.environ.get("PP_OCR_EARLY_TRANSLATION") == "1"
        mode = os.environ.get("PP_OCR_FRAME_COMPRESSION", "raw")
        if mode not in ("raw", "lz4"):
            raise ValueError("PP_OCR_FRAME_COMPRESSION must be raw or lz4")
        self.codec = None
        if mode == "lz4":
            from .lz4_block import Lz4Block
            self.codec = Lz4Block(os.environ.get("PP_OCR_LZ4_LIBRARY", "liblz4.so.1"))

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def ocr(self, image, sequence=0, capture_ts=None, on_region=None):
        started = time.perf_counter()
        captured = 0 if capture_ts is None else capture_ts
        payload = encode_frame(image, sequence, captured)
        frame_hash = fingerprint(image)
        encoding = "identity"
        compress_ms = 0
        if self.codec is not None:
            tick = time.perf_counter()
            compressed = self.codec.compress(payload)
            compress_ms = (time.perf_counter()-tick)*1000
            if len(compressed) < len(payload):
                payload, encoding = compressed, "lz4-block"
        encode_ms = (time.perf_counter()-started)*1000
        headers = {"Content-Type": "application/x-gocr-frame", "Content-Encoding": encoding}
        scope = self.translation_scope()
        headers["X-PP-OCR-Policy"] = scope
        if on_region is not None:
            headers["Accept"] = "application/x-ndjson"
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.connection is None:
            self.connection = self.connection_type(self.host, self.port, timeout=self.timeout)
        started = time.perf_counter()
        try:
            self.connection.request("POST", "/v1/ocr-frame", body=payload, headers=headers)
            response = self.connection.getresponse()
            if response.status != 200:
                raise ValueError("Orange frame worker failed or exceeded response budget")
            if on_region is not None:
                result = self.read_events(response, sequence, captured, frame_hash, on_region)
            else:
                raw = response.read(MAX_REPLY+1)
                if len(raw) > MAX_REPLY:
                    raise ValueError("Orange exceeded response budget")
                result = json.loads(raw, parse_constant=reject_nonfinite)
            if (result.get("schema") != "gocr.worker.v1"
                    or (result.get("width"), result.get("height")) != image.size
                    or result.get("sequence") != sequence or result.get("capture_ts") != captured
                    or result.get("frame_sha256") != frame_hash
                    or not isinstance(result.get("lines"), list)):
                raise ValueError("Orange changed selected-frame identity")
            if result.get("translation_scope", "normal") != scope:
                raise ValueError("Orange changed translation scope")
            for line in result["lines"]:
                quad_points(line["source_quad"])
                if not isinstance(line.get("text"), str):
                    raise ValueError("invalid OCR line text")
            elapsed = (time.perf_counter()-started)*1000
            timings = result["timings_ms"]
            timings.update(frame_encode=encode_ms, frame_rpc=elapsed,
                           frame_compress=compress_ms,
                           frame_network=max(0, elapsed-timings["orange_request"]),
                           frame_to_text=encode_ms+elapsed)
            if "after_detector_to_reply_ms" in timings:
                timings["relay_to_detector_upper_ms"] = max(
                    0, encode_ms+elapsed-timings["after_detector_to_reply_ms"])
            return result, len(payload)
        except Exception:
            self.close()
            raise

    @staticmethod
    def translation_scope():
        try:
            with open("/media/developer/game-translator-layers.json", encoding="utf-8") as stream:
                value = json.load(stream).get("translationScope", "normal")
            return "all" if value == "all" else "normal"
        except (OSError, ValueError, AttributeError):
            return "normal"

    def read_events(self, response, sequence, captured, frame_hash, on_region):
        if response.getheader("Content-Type", "").split(";", 1)[0] != "application/x-ndjson":
            raise ValueError("Orange did not supply region events")
        used, final = 0, None
        seen = set()
        while True:
            raw = response.readline(MAX_REPLY+1-used)
            if not raw:
                break
            used += len(raw)
            if used > MAX_REPLY or not raw.endswith(b"\n") or final is not None:
                raise ValueError("Invalid region stream framing/budget")
            value = json.loads(raw, parse_constant=reject_nonfinite)
            if any(value.get(k) != expected for k, expected in (
                ("sequence", sequence), ("capture_ts", captured), ("frame_sha256", frame_hash))):
                raise ValueError("Region event changed frame identity")
            if value.get("event") == "region":
                line = value["line"]
                if (not isinstance(line.get("line_id"), str) or line["line_id"] in seen
                        or not isinstance(line.get("text"), str)
                        or line.get("translation_allowed") is not True):
                    raise ValueError("Invalid/duplicate early region")
                quad_points(line["source_quad"])
                seen.add(line["line_id"])
                on_region(line)
            elif value.get("event") == "final":
                final = value["result"]
            else:
                raise ValueError("Failed/unknown region stream event")
        if final is None:
            raise ValueError("Missing final OCR frame")
        return final
