"""Isolated full-frame replay using existing PicCap detector and Orange engines."""
import ctypes as C
import time
from pathlib import Path

import numpy as np


class Region(C.Structure):
    _fields_ = [(name, C.c_int) for name in ("x", "y", "width", "height")] + [
        ("score", C.c_float), ("kind", C.c_int)]

    def box(self):
        return {name: getattr(self, name) for name in ("x", "y", "width", "height")}


class Detector:
    def __init__(self, library, prefix):
        self.lib = C.CDLL(str(Path(library).resolve()))
        self.lib.text_detector_create.argtypes = [C.c_char_p]
        self.lib.text_detector_create.restype = C.c_void_p
        self.lib.text_detector_detect.argtypes = [C.c_void_p, C.c_void_p, C.c_int,
                                                 C.c_int, C.POINTER(Region), C.c_int]
        self.lib.text_detector_detect.restype = C.c_int
        self.lib.text_detector_region_lines.argtypes = [C.c_void_p, C.POINTER(Region),
                                                       C.POINTER(Region), C.c_int]
        self.lib.text_detector_region_lines.restype = C.c_int
        self.lib.text_detector_destroy.argtypes = [C.c_void_p]
        self.lib.text_detector_destroy.restype = None
        self.context = self.lib.text_detector_create(str(prefix).encode())
        if not self.context:
            raise RuntimeError("Existing detector could not load")

    def detect(self, gray):
        boxes = (Region * 24)()
        n = self.lib.text_detector_detect(self.context, gray.ctypes.data, gray.shape[1],
                                         gray.shape[0], boxes, len(boxes))
        if not 0 <= n <= len(boxes):
            raise RuntimeError("Detector failed or exceeded existing region capacity")
        return list(boxes[:n])

    def lines(self, box):
        rows = (Region * 24)()
        n = self.lib.text_detector_region_lines(self.context, C.byref(box), rows, len(rows))
        if not 0 <= n <= len(rows):
            raise RuntimeError("Existing line extraction failed")
        return list(rows[:n])

    def close(self):
        if self.context:
            self.lib.text_detector_destroy(self.context)
            self.context = None


def gray_frame(image):
    if image.mode != "RGB" or image.size != (1280, 720):
        raise ValueError("Expected lossless selected RGB 1280x720 frame")
    rgb = np.asarray(image, dtype=np.uint16)
    return np.ascontiguousarray(((77 * rgb[:, :, 0] + 150 * rgb[:, :, 1]
                                 + 29 * rgb[:, :, 2]) >> 8).astype(np.uint8))


def parse_tsv(tsv):
    words = []
    for row in tsv.splitlines()[1:]:
        fields = row.split("\t", 11)
        if len(fields) == 12 and fields[0] == "5" and fields[11]:
            words.append(fields[11])
    return " ".join(words)


def tsv_confidence(tsv):
    values = []
    for row in tsv.splitlines()[1:]:
        fields = row.split("\t", 11)
        if len(fields) == 12 and fields[0] == "5" and fields[11]:
            values.append(float(fields[10]))
    return {"minimum_confidence": min(values, default=0),
            "average_confidence": sum(values)/len(values) if values else 0,
            "ocr_word_count": len(values)}


class Pipeline:
    def __init__(self, detector, engines, pool=None):
        self.detector, self.engines = detector, engines
        self.pool = pool
        self.profiler = None

    def recognize_line(self, row, gray):
        started = time.perf_counter()
        crop = np.ascontiguousarray(gray[row.y:row.y + row.height,
                                         row.x:row.x + row.width])
        if crop.shape != (row.height, row.width):
            raise ValueError("Detector crop outside selected frame")
        pixels = crop.tobytes()
        if self.profiler is not None:
            self.profiler.add("crop_extract", (time.perf_counter()-started)*1000)
        status, tsv = self.engines.recognize(4, pixels, row.width, row.height)
        if status not in (0, 1):
            raise RuntimeError("Installed recognition engine failed")
        started = time.perf_counter()
        result = {"box": row.box(), "text": parse_tsv(tsv), **tsv_confidence(tsv)}
        if self.profiler is not None:
            self.profiler.add("tsv_assembly", (time.perf_counter()-started)*1000)
        return result

    def ocr(self, image):
        stats = getattr(self.engines, "cache_stats", None)
        cache_before = stats() if stats is not None else None
        start = time.perf_counter()
        gray = gray_frame(image)
        converted = time.perf_counter()
        boxes = self.detector.detect(gray)
        detected = time.perf_counter()
        regions = []
        for box in boxes:
            rows = self.detector.lines(box)
            if self.pool is None:
                lines = [self.recognize_line(row, gray) for row in rows]
            else:
                jobs = [self.pool.submit(self.recognize_line, row, gray) for row in rows]
                lines = [job.result() for job in jobs]
            regions.append({"box": box.box(), "score": box.score, "lines": lines,
                            "text": " ".join(row["text"] for row in lines if row["text"])})
        finished = time.perf_counter()
        result = {"regions": regions, "timings_ms": {
            "detector_completed_monotonic_ms": detected*1000,
            "gray": (converted - start) * 1000,
            "detector": (detected - converted) * 1000,
            "lines_crop_recognition": (finished - detected) * 1000,
            "full_ocr": (finished - start) * 1000}}
        if cache_before is not None:
            cache_after = stats()
            result["crop_cache"] = {**cache_after, "frame": {
                k: cache_after[k]-cache_before[k]
                for k in ("hits", "misses", "recognize_calls", "evictions")}}
        return result
