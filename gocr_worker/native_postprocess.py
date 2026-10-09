"""One bulk ABI call; the Python reference remains available for regression."""
from __future__ import annotations

import ctypes as C
import os
import warnings
from pathlib import Path

import numpy as np

from .detector import _bbox


class Proposal(C.Structure):
    _fields_ = [("quad", C.c_double*8), ("center", C.c_double*2),
                ("width", C.c_double), ("height", C.c_double),
                ("angle", C.c_double), ("score", C.c_double), ("head", C.c_int32)]


class Config(C.Structure):
    _fields_ = [(name, C.c_double) for name in (
        "max_height_ratio", "search_radius_factor", "max_angle_difference",
        "max_centers_relative_distance", "optimal_centers_relative_distance",
        "min_overlap", "min_overlap_optimal", "duplicate_horizontal_overlap",
        "duplicate_iou", "group_across_factor")]


class Line(C.Structure):
    _fields_ = Proposal._fields_[:-1] + [("piece_count", C.c_int32)]


class Stats(C.Structure):
    _fields_ = [(name, C.c_double) for name in
                ("dedupe_ms", "pairwise_ms", "fit_ms", "refine_ms", "total_ms")] + [
        ("deduped_count", C.c_int32), ("component_count", C.c_int32), ("pair_tests", C.c_int64)]


class NativePostprocess:
    def __init__(self, path=None):
        path = path or os.environ.get("GOCR_POSTPROCESS_LIBRARY")
        if not path:
            local = Path(__file__).resolve().parents[1]/"native/gocr_postprocess/libgocr_postprocess.so"
            path = str(local) if local.is_file() else "libgocr_postprocess.so"
        if Path(path).is_file():
            path = str(Path(path).resolve())
        self.lib = C.CDLL(str(path))
        self.lib.gocr_postprocess_abi.restype = C.c_int
        if self.lib.gocr_postprocess_abi() != 1:
            raise RuntimeError("unsupported GOCR postprocess ABI")
        self.lib.gocr_postprocess.argtypes = [C.POINTER(Proposal), C.c_int, C.POINTER(Config),
            C.POINTER(Line), C.c_int, C.POINTER(C.c_int32), C.POINTER(Stats)]
        self.lib.gocr_postprocess.restype = C.c_int

    def run(self, detector, pieces, groups):
        boxes = pieces + groups
        proposals = (Proposal*len(boxes))()
        for out, box in zip(proposals, boxes):
            out.quad[:] = np.asarray(box["quad"]).ravel()
            out.center[:] = box["center"]
            out.width, out.height = box["width"], box["height"]
            out.angle, out.score, out.head = box["angle"], box["score"], box["head"]
        cfg = Config(detector.MAX_HEIGHT_RATIO, detector.SEARCH_RADIUS_FACTOR,
            detector.MAX_ANGLE_DIFF_DEG, detector.MAX_CENTERS_RELATIVE_DISTANCE,
            detector.OPTIMAL_CENTERS_RELATIVE_DISTANCE, detector.MIN_OVERLAP,
            detector.MIN_OVERLAP_OPTIMAL, detector.DUP_HORIZONTAL_OVERLAP,
            detector.REFERENCE_DUPLICATE_IOU, detector.REFERENCE_GROUP_ACROSS_FACTOR)
        output = (Line*len(boxes))()
        membership = (C.c_int32*len(boxes))()
        stats = Stats()
        count = self.lib.gocr_postprocess(proposals, len(boxes), C.byref(cfg), output,
            len(output), membership, C.byref(stats))
        if count < 0:
            raise RuntimeError(f"GOCR native postprocess failed: {count}")
        lines = []
        for out in output[:count]:
            q = np.asarray(list(out.quad), dtype=np.float64).reshape(4, 2)
            lines.append({"quad": q, "bbox": _bbox(q), "center": np.asarray(out.center),
                "width": out.width, "height": out.height, "angle": out.angle,
                "score": out.score, "pieces": out.piece_count})
        detector.cluster_timings = {"piece_dedupe": stats.dedupe_ms,
            "pairwise_connections": stats.pairwise_ms, "component_fit": stats.fit_ms,
            "group_refine_dedupe": stats.refine_ms, "native_total_postprocess": stats.total_ms}
        detector.cluster_counts = {"pieces_after_dedupe": stats.deduped_count,
            "pair_tests": stats.pair_tests, "components": stats.component_count}
        detector.component_membership = list(membership)[:len(pieces)]
        return lines


def select_backend():
    mode = os.environ.get("GOCR_POSTPROCESS", "native")
    if mode == "python":
        return None
    if mode != "native":
        raise ValueError("GOCR_POSTPROCESS must be native or python")
    try:
        return NativePostprocess()
    except (OSError, RuntimeError) as exc:
        warnings.warn(f"GOCR native unavailable; using Python reference: {exc}", RuntimeWarning)
        return None
