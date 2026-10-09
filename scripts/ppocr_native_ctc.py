"""Native token scan; original Unicode mapping and exact statistics.mean remain."""
import ctypes as C
from pathlib import Path
import statistics
import numpy as np


class NativeCtc:
    def __init__(self, library):
        self.lib = C.CDLL(str(Path(library).resolve()))
        self.lib.ppocr_class_major_ctc.argtypes = [C.c_void_p, C.c_int, C.c_int,
                                                  C.c_void_p, C.c_void_p, C.c_int]
        self.lib.ppocr_class_major_ctc.restype = C.c_int

    def decode(self, scores, characters, layout="class-major"):
        if layout != "class-major":
            raise ValueError("Native CTC is only admitted for class-major float32 output")
        scores = np.asarray(scores)
        if scores.dtype != np.float32 or not scores.flags.c_contiguous or not scores.flags.aligned:
            raise ValueError("Native CTC requires unchanged contiguous float32 scores")
        classes = len(characters)
        if classes < 2 or scores.size % classes:
            raise ValueError("Invalid class-major tensor shape")
        steps = scores.size//classes
        if not 1 <= steps <= 4096 or classes > 65536 or scores.size > 64000000:
            raise ValueError("Native CTC tensor exceeds admitted limits")
        tokens = np.empty(steps, dtype=np.int32)
        probabilities = np.empty(steps, dtype=np.float32)
        n = self.lib.ppocr_class_major_ctc(scores.ctypes.data, classes, steps,
                                          tokens.ctypes.data, probabilities.ctypes.data, steps)
        if n == -2:
            raise RuntimeError("Nonfinite OCR output")
        if not 0 <= n <= steps:
            raise ValueError("Native CTC rejected shape/capacity")
        text = "".join(characters[int(token)] for token in tokens[:n])
        # Keep the same exact summation, clamping and empty-sequence behavior.
        quality = statistics.mean(float(p) for p in probabilities[:n]) if n else 0
        return text, min(1.0, max(0.0, quality))


def select_decoder(owner, library):
    """Explicit startup selection for existing Engines; other layouts stay reference."""
    native = NativeCtc(library)
    reference = owner.decode
    def decode(scores, characters, layout="time-major"):
        if layout == "class-major":
            return native.decode(scores, characters, layout)
        return reference(scores, characters, layout)
    owner.decode = decode
    return native
