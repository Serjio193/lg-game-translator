"""Bounded per-engine exact-pixel OCR cache; never caches empty/error responses."""
from collections import OrderedDict
import hashlib
import threading


class ExactCropCache:
    def __init__(self, engine, max_bytes=16*1024*1024, max_entries=256):
        if max_bytes < 1 or max_entries < 1:
            raise ValueError("Cache limits must be positive")
        self.engine = engine
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.items = OrderedDict()
        self.bytes = self.hits = self.misses = self.recognize_calls = self.evictions = 0
        self.lock = threading.Lock()
        self.identity = self.namespace()

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def namespace(self):
        return (getattr(self.engine, "model_name", None),
                str(getattr(self.engine, "model_directory", "")),
                getattr(self.engine, "output_layout", None))

    def recognize(self, mode, pixels, width, height):
        if not isinstance(pixels, bytes) or len(pixels) != width*height:
            raise ValueError("Cache requires exact immutable grayscale crop bytes")
        identity = self.namespace()
        key = (identity, mode, width, height, hashlib.sha256(pixels).digest())
        with self.lock:
            if identity != self.identity:
                self.items.clear()
                self.bytes = 0
                self.identity = identity
            cached = self.items.get(key)
            # Hash is an index, never the sole proof of pixel equality.
            if cached and cached[0] == pixels:
                self.items.move_to_end(key)
                self.hits += 1
                return cached[1]
            self.misses += 1
            self.recognize_calls += 1
        result = self.engine.recognize(mode, pixels, width, height)
        status, tsv = result
        words = [line.split("\t", 11) for line in tsv.splitlines()]
        has_text = any(len(row) == 12 and row[0] == "5" and row[11].strip() for row in words)
        if status != 0 or not has_text:
            return result
        cost = len(pixels)+len(tsv.encode("utf-8"))
        if cost > self.max_bytes:
            return result
        with self.lock:
            if identity != self.identity:
                return result
            prior = self.items.pop(key, None)
            if prior:
                self.bytes -= prior[2]
            self.items[key] = (pixels, result, cost)
            self.bytes += cost
            while self.bytes > self.max_bytes or len(self.items) > self.max_entries:
                _, removed = self.items.popitem(last=False)
                self.bytes -= removed[2]
                self.evictions += 1
        return result

    def cache_stats(self):
        with self.lock:
            return {"hits": self.hits, "misses": self.misses,
                    "recognize_calls": self.recognize_calls, "evictions": self.evictions,
                    "entries": len(self.items), "payload_bytes": self.bytes,
                    "max_payload_bytes": self.max_bytes, "max_entries": self.max_entries}
