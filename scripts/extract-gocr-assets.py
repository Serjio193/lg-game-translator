#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

WANTED = {
    "gocr_group_rpn_text_detection_model_2024_q4.tflite",
    "gocr_group_rpn_text_detection_config_2024_q4.binarypb",
    "recognizer_latn_vi_cyrl_lm_retrained.tflite",
    "recognizer_latn_vi_cyrl_label_map.pb",
    "recognizer_cyrl_config.pb",
    "recognizer_cyrl_lm.compact_fst.gz",
    "recognizer_cyrl_lm.syms",
    "recognizer_latn_vi_cyrl_prior.pb",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description="Extract original GOCR assets from Google App APK")
    p.add_argument("apk", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    found = {}
    with zipfile.ZipFile(args.apk) as z:
        for name in z.namelist():
            base = Path(name).name
            if base not in WANTED or base in found:
                continue
            target = args.output / base
            with z.open(name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            found[base] = {"source": name, "sha256": sha(target), "bytes": target.stat().st_size}
    missing = sorted(WANTED - set(found))
    manifest = {"source_apk": str(args.apk), "files": found, "missing_optional_or_version_specific": missing}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for k, v in found.items():
        print(f"{k}: {v['bytes']} bytes {v['sha256']}")
    if not {"gocr_group_rpn_text_detection_model_2024_q4.tflite", "recognizer_latn_vi_cyrl_lm_retrained.tflite", "recognizer_latn_vi_cyrl_label_map.pb"}.issubset(found):
        raise SystemExit("required GOCR assets are missing from this APK")


if __name__ == "__main__":
    main()
