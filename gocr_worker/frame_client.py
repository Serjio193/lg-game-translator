"""Authenticated lossless full-frame relay; no OCR models are loaded on TV."""
import http.client
import json
import time
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

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def ocr(self, image, sequence=0, capture_ts=None):
        started = time.perf_counter()
        captured = 0 if capture_ts is None else capture_ts
        payload = encode_frame(image, sequence, captured)
        frame_hash = fingerprint(image)
        encode_ms = (time.perf_counter()-started)*1000
        headers = {"Content-Type": "application/x-gocr-frame"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.connection is None:
            self.connection = self.connection_type(self.host, self.port, timeout=self.timeout)
        started = time.perf_counter()
        try:
            self.connection.request("POST", "/v1/ocr-frame", body=payload, headers=headers)
            response = self.connection.getresponse()
            raw = response.read(MAX_REPLY+1)
            if response.status != 200 or len(raw) > MAX_REPLY:
                raise ValueError("Orange frame worker failed or exceeded response budget")
            result = json.loads(raw, parse_constant=reject_nonfinite)
            if (result.get("schema") != "gocr.worker.v1"
                    or (result.get("width"), result.get("height")) != image.size
                    or result.get("sequence") != sequence or result.get("capture_ts") != captured
                    or result.get("frame_sha256") != frame_hash
                    or not isinstance(result.get("lines"), list)):
                raise ValueError("Orange changed selected-frame identity")
            for line in result["lines"]:
                quad_points(line["source_quad"])
                if not isinstance(line.get("text"), str):
                    raise ValueError("invalid OCR line text")
            elapsed = (time.perf_counter()-started)*1000
            timings = result["timings_ms"]
            timings.update(frame_encode=encode_ms, frame_rpc=elapsed,
                           frame_network=max(0, elapsed-timings["orange_request"]),
                           frame_to_text=encode_ms+elapsed)
            return result, len(payload)
        except Exception:
            self.close()
            raise
