"""Recovered Google protobuf runner config; no heuristic OCR settings."""
from pathlib import Path

def vi(data, pos):
    value = 0
    shift = 0
    for _ in range(10):
        if pos >= len(data):
            raise ValueError("truncated varint")
        b = data[pos]
        pos += 1
        value |= (b & 0x7f) << shift
        if b < 0x80:
            return value, pos
        shift += 7
    raise ValueError("bad varint")


def fields(data):
    pos = 0
    while pos < len(data):
        tag, pos = vi(data, pos)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, pos = vi(data, pos)
        elif wire == 1:
            value = data[pos:pos + 8]
            pos += 8
        elif wire == 2:
            n, pos = vi(data, pos)
            value = data[pos:pos + n]
            pos += n
        elif wire == 5:
            value = data[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"unsupported wire type {wire}")
        yield number, wire, value


def one_message(data, number):
    vals = [v for f, w, v in fields(data) if f == number and w == 2]
    return vals[-1] if vals else None


def decode_cached_runner(data):
    out = {
        "runner_type": "tflite_model_pooled_cached_runner_config",
        "model_path": None,
        "num_inference_threads": None,
        "interpreter_num_threads": None,
        "multiple_inputs": False,
        "add_custom_ops": False,
        "output_names": [],
        "input_names": [],
        "needs_custom_delegate": False,
        "num_channels": None,
        "batch_size": None,
        "cache_max_size": None,
        "use_xnnpack_delegate": False,
        "use_darwinn_delegate": False,
        "darwinn_inference_priority": None,
    }
    for f, w, v in fields(data):
        if f == 1 and w == 2:
            out["model_path"] = v.decode("utf-8")
        elif f == 2 and w == 0:
            out["num_inference_threads"] = int(v)
        elif f == 3 and w == 0:
            out["interpreter_num_threads"] = int(v)
        elif f == 6 and w == 0:
            out["multiple_inputs"] = bool(v)
        elif f == 7 and w == 0:
            out["add_custom_ops"] = bool(v)
        elif f == 8 and w == 2:
            out["output_names"].append(v.decode("utf-8"))
        elif f == 12 and w == 2:
            out["input_names"].append(v.decode("utf-8"))
        elif f == 13 and w == 0:
            out["needs_custom_delegate"] = bool(v)
        elif f == 14 and w == 0:
            out["num_channels"] = int(v)
        elif f == 15 and w == 0:
            out["batch_size"] = int(v)
        elif f == 16 and w == 0:
            out["cache_max_size"] = int(v)
        elif f == 17 and w == 0:
            out["use_xnnpack_delegate"] = bool(v)
        elif f == 19 and w == 0:
            out["use_darwinn_delegate"] = bool(v)
        elif f == 20 and w == 0:
            out["darwinn_inference_priority"] = int(v)
    return out


def decode_detector_binarypb(path):
    outer = path.read_bytes()
    any_value = one_message(outer, 2)
    if any_value is None:
        raise ValueError("missing Any.value")
    model_runner = one_message(any_value, 1)
    if model_runner is None:
        raise ValueError("missing GroupRPN model_runner_config")

    # Recovered Google schema:
    # TensorFlowModelRunnerConfig.field 7 =
    # TfliteModelPooledCachedRunnerConfig.
    cached = one_message(model_runner, 7)
    if cached is None:
        present = [f for f, _, _ in fields(model_runner)]
        raise ValueError(
            "runner is not field 7 pooled-cached TFLite config; "
            f"present TensorFlowModelRunnerConfig fields={present}"
        )
    return decode_cached_runner(cached)
