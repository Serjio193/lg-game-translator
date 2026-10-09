"""Reuse the existing translation API; never replace or initialize its models."""
import json
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class TranslationClient:
    def __init__(self, address, provider="madlad", timeout=30):
        parsed = urlsplit(address)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
            raise ValueError("invalid translator address")
        self.address = address.rstrip("/") + "/api/translate"
        self.provider = provider
        self.timeout = timeout

    def translate(self, text):
        if not text.strip():
            return {"translation": "", "request_ms": 0.0, "bytes_sent": 0}
        payload = json.dumps({"text": text, "provider": self.provider}, ensure_ascii=False).encode()
        started = time.perf_counter()
        request = Request(self.address, data=payload, method="POST",
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            if response.status != 200:
                raise RuntimeError("translator returned an unsuccessful status")
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("translator response is too large")
        result = json.loads(raw)
        if not isinstance(result.get("translation"), str):
            raise ValueError("translator returned no translation")
        return {**result, "request_ms": (time.perf_counter()-started)*1000,
                "bytes_sent": len(payload)}
