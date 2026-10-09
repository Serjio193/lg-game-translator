"""Explicit experimental execution selection; never changes Google parameters."""
import os


def execution_profile():
    value = os.environ.get("GOCR_PROFILE", "strict")
    if value not in ("strict", "fast_xnnpack", "google_runner_experimental"):
        raise ValueError("GOCR_PROFILE must be strict, fast_xnnpack or google_runner_experimental")
    return value


def google_runner_contract(assets):
    from .assets import DETECTOR_CONFIG, locate
    from .runner_config import decode_detector_binarypb
    config=decode_detector_binarypb(locate(assets,DETECTOR_CONFIG))
    expected={"interpreter_num_threads":4,"multiple_inputs":True,"cache_max_size":5,
              "use_xnnpack_delegate":True,
              "input_names":["input_features"]+[f"input_features_{i}" for i in range(1,4)],
              "output_names":["Identity"]+[f"Identity_{i}" for i in range(1,11)]}
    if any(config[k]!=v for k,v in expected.items()):
        raise ValueError("original Google runner config no longer matches recovered contract")
    return config
