#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.runner_config import decode_detector_binarypb


def main():
    ap = argparse.ArgumentParser(
        description="Decode the original Google GroupRPN TFLite runner contract"
    )
    ap.add_argument("binarypb", type=Path)
    ap.add_argument("--assert-current-android-contract", action="store_true")
    args = ap.parse_args()

    config = decode_detector_binarypb(args.binarypb)
    print(json.dumps(config, indent=2, ensure_ascii=False))

    if args.assert_current_android_contract:
        assert config["model_path"].endswith(
            "gocr_group_rpn_text_detection_model_2024_q4.tflite"
        )
        assert config["interpreter_num_threads"] == 4
        assert config["multiple_inputs"] is True
        assert config["cache_max_size"] == 5
        assert config["use_xnnpack_delegate"] is True
        assert config["input_names"] == [
            "input_features",
            "input_features_1",
            "input_features_2",
            "input_features_3",
        ]
        assert config["output_names"] == [
            "Identity",
            "Identity_1",
            "Identity_2",
            "Identity_3",
            "Identity_4",
            "Identity_5",
            "Identity_6",
            "Identity_7",
            "Identity_8",
            "Identity_9",
            "Identity_10",
        ]


if __name__ == "__main__":
    main()
