"""Native windowing/CTC and one-call detector → rectification → recognition."""
import ctypes as C
import os
from pathlib import Path

from .assets import RECOGNIZER_LABELS, RECOGNIZER_MODEL, locate
from .native_detector import Stats as DetectorStats
from .native_postprocess import Line as DetectorLine
from .recognizer import GocrLineRecognizer


class Config(C.Structure):
    _fields_ = [(n, C.c_int32) for n in (
        "height", "width", "left_context", "useful_width", "right_context", "step", "blank")]


class Recognition(C.Structure):
    _fields_ = [(n, C.c_double) for n in (
        "prepare_ms", "invoke_ms", "decode_ms", "total_ms", "margin")] + [
        ("windows", C.c_int32), ("normalized_width", C.c_int32),
        ("windows_sha256", C.c_char * 65), ("text", C.c_char_p)]


class RecognizedLine(C.Structure):
    _fields_ = [("source", DetectorLine), ("line_id", C.c_int32),
               ("crop_width", C.c_int32), ("crop_height", C.c_int32),
               ("rectify_ms", C.c_double), ("crop_sha256", C.c_char * 65),
               ("recognition", Recognition)]


class FullStats(C.Structure):
    _fields_ = [("detector", DetectorStats)] + [
        (n, C.c_double) for n in ("rectify_ms", "recognizer_ms", "total_ms")]


def as_dict(r):
    return {"text": r.text.decode("utf-8"), "decoder": "greedy_ctc", "blank_id": 1292,
            "windows": r.windows, "normalized_size": [r.normalized_width, 32],
            "invoke_ms": round(r.invoke_ms, 3), "total_ms": round(r.total_ms, 3),
            "diagnostic_logit_margin_q": round(r.margin, 3),
            "production_lm_fst_applied": False,
            "input_windows_sha256": r.windows_sha256.decode(),
            "stages_ms": {"prepare": r.prepare_ms, "invoke": r.invoke_ms, "decode": r.decode_ms}}


class NativeRecognizer:
    def __init__(self, assets, threads=2, library=None):
        library = library or os.environ.get("GOCR_RECOGNIZER_LIBRARY") or str(
            Path(__file__).resolve().parents[1] / "native/gocr_recognizer_native/libgocr_recognizer_native.so")
        self.context = None
        self.lib = C.CDLL(str(Path(library).resolve()))
        self.lib.gocr_recognizer_abi.restype = C.c_int
        if self.lib.gocr_recognizer_abi() != 1:
            raise RuntimeError("unsupported recognizer ABI")
        signatures = {
            "gocr_recognizer_create": (C.c_void_p, [C.c_char_p, C.c_char_p, C.c_char_p,
                C.c_int, C.POINTER(Config), C.c_char_p, C.c_size_t]),
            "gocr_recognizer_destroy": (None, [C.c_void_p]),
            "gocr_recognizer_error": (C.c_char_p, [C.c_void_p]),
            "gocr_recognizer_recognize": (C.c_int, [C.c_void_p, C.c_void_p, C.c_size_t,
                C.c_int, C.c_int, C.c_int, C.POINTER(Recognition)]),
            "gocr_recognizer_copy_windows": (C.c_size_t, [C.c_void_p, C.c_void_p, C.c_size_t]),
            "gocr_rectify_rgb": (C.c_int, [C.c_void_p, C.c_size_t, C.c_int, C.c_int,
                C.POINTER(C.c_double), C.c_void_p, C.c_size_t, C.POINTER(C.c_int), C.POINTER(C.c_int)]),
            "gocr_full_create": (C.c_void_p, [C.c_void_p, C.c_void_p]),
            "gocr_full_destroy": (None, [C.c_void_p]),
            "gocr_full_error": (C.c_char_p, [C.c_void_p]),
            "gocr_full_ocr": (C.c_int, [C.c_void_p, C.c_void_p, C.c_size_t,
                C.POINTER(RecognizedLine), C.c_int, C.POINTER(FullStats)])}
        for name, (result, args) in signatures.items():
            f = getattr(self.lib, name)
            f.restype, f.argtypes = result, args
        ref = GocrLineRecognizer
        config = Config(ref.INPUT_HEIGHT, ref.INPUT_WIDTH, ref.LEFT_CONTEXT,
                        ref.USEFUL_WIDTH, ref.RIGHT_CONTEXT, 4, 1292)
        error = C.create_string_buffer(512)
        runtime = os.environ.get("GOCR_TFLITE_C_LIBRARY", "/usr/lib/libtensorflow-lite.so")
        self.context = self.lib.gocr_recognizer_create(
            str(locate(assets, RECOGNIZER_MODEL)).encode(),
            str(locate(assets, RECOGNIZER_LABELS)).encode(), runtime.encode(), threads,
            C.byref(config), error, len(error))
        if not self.context:
            raise RuntimeError(error.value.decode())

    def recognize(self, crop):
        if crop.mode not in ("RGB", "L"):
            crop = crop.convert("RGB")
        pixels = crop.tobytes()
        result = Recognition()
        if self.lib.gocr_recognizer_recognize(self.context, pixels, len(pixels),
                crop.width, crop.height, 3 if crop.mode == "RGB" else 1, C.byref(result)):
            raise RuntimeError(self.lib.gocr_recognizer_error(self.context).decode())
        return as_dict(result)

    def windows_bytes(self):
        size = self.lib.gocr_recognizer_copy_windows(self.context, None, 0)
        buf = C.create_string_buffer(size)
        self.lib.gocr_recognizer_copy_windows(self.context, buf, size)
        return buf.raw

    def rectify(self, image, quad):
        from PIL import Image
        pixels = image.tobytes()
        q = (C.c_double * 8)(*(v for p in quad for v in p))
        w, h = C.c_int(), C.c_int()
        n = self.lib.gocr_rectify_rgb(pixels, len(pixels), image.width, image.height,
                                    q, None, 0, C.byref(w), C.byref(h))
        if n < 0:
            raise ValueError("native rectification failed")
        buf = C.create_string_buffer(n)
        if self.lib.gocr_rectify_rgb(pixels, len(pixels), image.width, image.height,
                q, buf, n, C.byref(w), C.byref(h)) != n:
            raise RuntimeError("native rectification buffer mismatch")
        return Image.frombytes("RGB", (w.value, h.value), buf.raw)

    def close(self):
        if getattr(self, "context", None):
            self.lib.gocr_recognizer_destroy(self.context)
            self.context = None

    def __del__(self):
        self.close()


class NativeFull:
    def __init__(self, detector, recognizer):
        self.detector, self.recognizer = detector, recognizer
        self.lib = recognizer.lib
        self.context = self.lib.gocr_full_create(detector.context, recognizer.context)
        if not self.context:
            raise RuntimeError("cannot create native full pipeline")
        self.output = (RecognizedLine * 4096)()
        self.stats = FullStats()

    def run(self, image):
        if image.mode != "RGB" or image.size != (1280, 720):
            raise ValueError("native full requires selected RGB1280x720")
        pixels = image.tobytes()
        n = self.lib.gocr_full_ocr(self.context, pixels, len(pixels), self.output,
                                  len(self.output), C.byref(self.stats))
        if n < 0:
            raise RuntimeError(self.lib.gocr_full_error(self.context).decode())
        rows = []
        for item in self.output[:n]:
            source = item.source
            rows.append({"line_id": str(item.line_id), "text": item.recognition.text.decode(),
                "quad": [[source.quad[2*k], source.quad[2*k+1]] for k in range(4)],
                "angle": source.angle, "score": source.score,
                "crop_sha256": item.crop_sha256.decode(),
                "recognizer": as_dict(item.recognition)})
        return rows, self.stats

    def close(self):
        if getattr(self, "context", None):
            self.lib.gocr_full_destroy(self.context)
            self.context = None

    def __del__(self):
        self.close()
