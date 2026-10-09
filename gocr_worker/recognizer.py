from __future__ import annotations

import itertools
import hashlib
import math
import time
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import RECOGNIZER_LABELS, RECOGNIZER_MODEL, locate


def _read_varint(data: bytes, pos: int):
    value = 0
    for shift in range(0, 70, 7):
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
    raise ValueError("invalid protobuf varint")


def _fields(data: bytes):
    pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        field, wire = tag >> 3, tag & 7
        if wire == 0:
            value, pos = _read_varint(data, pos)
        elif wire == 2:
            size, pos = _read_varint(data, pos)
            value = data[pos:pos + size]
            pos += size
        elif wire == 1:
            value = data[pos:pos + 8]
            pos += 8
        elif wire == 5:
            value = data[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire}")
        yield field, wire, value


def load_label_map(path: Path) -> dict[int, str]:
    labels: dict[int, str] = {}
    for field, wire, value in _fields(path.read_bytes()):
        if field != 1 or wire != 2:
            continue
        entry = {f: v for f, _, v in _fields(value)}
        label = entry.get(1, b"").decode("utf-8")
        idx = int(entry.get(2, 0))
        labels[idx] = label
    if set(labels) != set(range(len(labels))):
        raise ValueError("GOCR label IDs are not contiguous from zero")
    return labels


class GocrLineRecognizer:
    """Standalone Google GOCR Latin/Vietnamese/Cyrillic line recognizer.

    Model and label map are original Google assets. Window values 16/136/16 are
    preserved from the production config. The exact native LM/FST decoder is not
    yet reproduced; current text decoding is greedy CTC and is reported as such.
    """

    INPUT_HEIGHT = 32
    INPUT_WIDTH = 168
    LEFT_CONTEXT = 16
    USEFUL_WIDTH = 136
    RIGHT_CONTEXT = 16

    def __init__(self, asset_root: Path, threads: int = 2):
        from .interpreter import create_interpreter
        self.model_path = locate(asset_root, RECOGNIZER_MODEL)
        self.labels_path = locate(asset_root, RECOGNIZER_LABELS)
        self.labels = load_label_map(self.labels_path)
        self.blank_id = len(self.labels)
        self.interpreter = create_interpreter(self.model_path, threads)
        self.interpreter.allocate_tensors()
        self.input = self.interpreter.get_input_details()[0]
        if list(self.input["shape"])[1:] != [32, 168, 1]:
            raise RuntimeError(f"unexpected GOCR input shape: {self.input['shape']}")
        outputs = self.interpreter.get_output_details()
        self.logits_output = next(
            o for o in outputs
            if len(o["shape"]) == 3 and int(o["shape"][-1]) == self.blank_id + 1
        )
        self.aux_outputs = [o for o in outputs if o["index"] != self.logits_output["index"]]

    def _decode(self, ids: list[int]) -> str:
        text = "".join(
            self.labels[i]
            for i, _ in itertools.groupby(ids)
            if i != self.blank_id
        )
        return unicodedata.normalize("NFC", text).strip()

    def _infer_window(self, image: Image.Image):
        arr = np.asarray(image, dtype=np.uint8)[None, :, :, None]
        self.interpreter.set_tensor(self.input["index"], arr)
        start = time.perf_counter()
        self.interpreter.invoke()
        invoke_ms = (time.perf_counter() - start) * 1000.0
        logits = self.interpreter.get_tensor(self.logits_output["index"])[0]
        ids = np.argmax(logits, axis=-1).astype(np.int32).tolist()
        # Scalar quantization means argmax is invariant; use top-two gap only as
        # a lightweight diagnostic, not as Google's production confidence.
        q = np.partition(logits.astype(np.int16), -2, axis=-1)
        margin = float(np.mean(q[:, -1] - q[:, -2]))
        return ids, invoke_ms, margin

    def recognize(self, crop: Image.Image) -> dict:
        started = time.perf_counter()
        gray = crop.convert("L")
        if gray.height <= 0 or gray.width <= 0:
            raise ValueError("empty crop")
        normalized_width = max(1, round(gray.width * self.INPUT_HEIGHT / gray.height))
        gray = gray.resize((normalized_width, self.INPUT_HEIGHT), Image.Resampling.LANCZOS)

        # Preserve Google's production window constants rather than tuning them.
        padded = Image.new(
            "L",
            (normalized_width + self.LEFT_CONTEXT + self.RIGHT_CONTEXT, self.INPUT_HEIGHT),
            255,
        )
        padded.paste(gray, (self.LEFT_CONTEXT, 0))

        stitched: list[int] = []
        invoke_ms = 0.0
        margins: list[float] = []
        left_steps = self.LEFT_CONTEXT // 4
        useful_steps = self.USEFUL_WIDTH // 4
        windows = 0
        input_hash = hashlib.sha256()
        for x in range(0, normalized_width, self.USEFUL_WIDTH):
            window = padded.crop((x, 0, x + self.INPUT_WIDTH, self.INPUT_HEIGHT))
            input_hash.update(window.tobytes())
            ids, ms, margin = self._infer_window(window)
            remain = max(0, normalized_width - x)
            keep = min(useful_steps, math.ceil(remain / 4))
            stitched.extend(ids[left_steps:left_steps + keep])
            invoke_ms += ms
            margins.append(margin)
            windows += 1

        return {
            "text": self._decode(stitched),
            "decoder": "greedy_ctc",
            "blank_id": self.blank_id,
            "windows": windows,
            "normalized_size": [normalized_width, self.INPUT_HEIGHT],
            "invoke_ms": round(invoke_ms, 3),
            "total_ms": round((time.perf_counter() - started) * 1000.0, 3),
            "diagnostic_logit_margin_q": round(float(np.mean(margins)) if margins else 0.0, 3),
            "production_lm_fst_applied": False,
            "input_windows_sha256": input_hash.hexdigest(),
        }
