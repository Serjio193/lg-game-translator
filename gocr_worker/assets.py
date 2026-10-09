from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetSpec:
    filename: str
    sha256: str | None = None


DETECTOR_MODEL = AssetSpec(
    "gocr_group_rpn_text_detection_model_2024_q4.tflite",
    "55ab1290b1b481d71c65636d93570f4e48ae0d2c0a748f773d93b9cd13126a51",
)
DETECTOR_CONFIG = AssetSpec(
    "gocr_group_rpn_text_detection_config_2024_q4.binarypb",
    "45033fc42999a90e9fae90ef8303ee76e013f575ca1caa811d315a1e0107481c",
)
RECOGNIZER_MODEL = AssetSpec(
    "recognizer_latn_vi_cyrl_lm_retrained.tflite",
    "23501a73630270f22ad7fc9b54a6daa566db4b492eb7addaa160b88afba6d002",
)
RECOGNIZER_LABELS = AssetSpec(
    "recognizer_latn_vi_cyrl_label_map.pb",
    "d41cea501ff409954bc29e7e83eb6992e475312cfa15040066cd222a98dc3192",
)
OPTIONAL_RECOGNIZER_FILES = (
    AssetSpec("recognizer_cyrl_config.pb", "8c94445f2cb706f983ecbcc7d939f3f97e5d48f7ca07df8a875f07efd4191b25"),
    AssetSpec("recognizer_cyrl_lm.compact_fst.gz", "43783be2a70b75806ed2aa8d71b0094153b508106a9a7ecd85b87649c470bfbb"),
    AssetSpec("recognizer_cyrl_lm.syms", "64adce4c1e99f42863dc5087374eed44a0ecb321b83cfec8a42a272a0d473fd3"),
    AssetSpec("recognizer_latn_vi_cyrl_prior.pb", "5d00da2091c16b3b22311fe3446348438a68026c07ef5e6113614a3cb4a7e543"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def locate(root: Path, spec: AssetSpec, required: bool = True) -> Path | None:
    matches = list(root.rglob(spec.filename))
    if not matches:
        if required:
            raise FileNotFoundError(f"missing GOCR asset: {spec.filename}")
        return None
    path = matches[0]
    if spec.sha256:
        actual = sha256(path)
        if actual != spec.sha256:
            raise RuntimeError(
                f"GOCR asset hash mismatch for {spec.filename}: {actual} != {spec.sha256}"
            )
    return path


def verify_bundle(root: Path, role: str = "full", require_support_files: bool = False) -> dict:
    if role not in ("full", "detector", "recognizer"):
        raise ValueError("unknown GOCR asset role")
    out = {}
    required = ((DETECTOR_MODEL, DETECTOR_CONFIG) if role == "detector" else
                (RECOGNIZER_MODEL, RECOGNIZER_LABELS) if role == "recognizer" else
                (DETECTOR_MODEL, DETECTOR_CONFIG, RECOGNIZER_MODEL, RECOGNIZER_LABELS))
    for spec in required:
        p = locate(root, spec)
        out[spec.filename] = {"path": str(p), "sha256": sha256(p)}
    for spec in OPTIONAL_RECOGNIZER_FILES if role != "detector" else ():
        p = locate(root, spec, required=require_support_files)
        out[spec.filename] = None if p is None else {"path": str(p), "sha256": sha256(p)}
    return out
