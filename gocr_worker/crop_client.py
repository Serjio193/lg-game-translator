import base64
import io
import json
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .image_contract import fingerprint, quad_points


class CropClient:
    def __init__(self, address, token=None, timeout=30, translate=True):
        parsed = urlsplit(address)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
            raise ValueError("invalid recognizer address")
        endpoint = "/v1/recognize-translate" if translate else "/v1/recognize-crop"
        self.address = address.rstrip("/") + endpoint
        self.token, self.timeout = token, timeout

    def recognize(self, crop, meta):
        started = time.perf_counter()
        buffer = io.BytesIO()
        crop.save(buffer, format="PNG")
        meta = {**meta, "crop_sha256": fingerprint(crop)}
        payload = json.dumps({"image_b64": base64.b64encode(buffer.getvalue()).decode(),
                              "meta": meta}, allow_nan=False).encode()
        encoding_ms = (time.perf_counter()-started)*1000
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        started = time.perf_counter()
        with urlopen(Request(self.address, data=payload, headers=headers, method="POST"),
                     timeout=self.timeout) as response:
            raw = response.read(1048577)
        if len(raw) > 1048576:
            raise ValueError("GOCR response is too large")
        network_ms = (time.perf_counter()-started)*1000
        result = json.loads(raw)
        if result.get("schema") != "gocr.worker.v1" or len(result.get("lines", [])) != 1:
            raise ValueError("unexpected crop response schema")
        line = result["lines"][0]
        if (line.get("line_id") != str(meta["line_id"])
                or quad_points(line.get("source_quad")) != quad_points(meta["source_quad"])
                or line.get("angle") != meta["angle"]
                or line.get("detector_confidence") != meta["detector_confidence"]
                or line.get("crop_sha256") != meta["crop_sha256"]):
            raise ValueError("Orange changed the original crop identity/geometry")
        timings = line.get("timings_ms", {})
        remote_ms = timings.get("recognizer", 0)+line.get("translation", {}).get("request_ms", 0)
        line["timings_ms"] = {**timings, "encode": encoding_ms,
                              "crop_rpc": network_ms, "network": max(0, network_ms-remote_ms)}
        return line, len(payload)
