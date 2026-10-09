# Android GroupRPN execution contract

Recovered 2026-10-09 from the current Google App detector config plus Google's
protobuf descriptor recovered independently from Chromium ScreenAI.

This document describes the model-runner contract encoded by Google. It does
not claim that the LG/webOS runtime is numerically identical to Google's
Android runtime.

## Key result

The Android detector config does **not** select plain TFLite CPU execution.

The top-level detector config contains:

```text
GroupRpnTextDetectionMutatorConfig
  model_runner_config:
    TensorFlowModelRunnerConfig
      field 7
```

The recovered Google protobuf schema maps
`TensorFlowModelRunnerConfig.field 7` to:

```text
tflite_model_pooled_cached_runner_config
  : google_ocr.TfliteModelPooledCachedRunnerConfig
```

The embedded Android config decodes to:

```text
model_path                  ./gocr_group_rpn_text_detection_model_2024_q4.tflite
interpreter_num_threads     4
multiple_inputs             true
cache_max_size              5
use_xnnpack_delegate        true

inputs:
  input_features
  input_features_1
  input_features_2
  input_features_3

outputs:
  Identity
  Identity_1
  Identity_2
  Identity_3
  Identity_4
  Identity_5
  Identity_6
  Identity_7
  Identity_8
  Identity_9
  Identity_10
```

No value is inferred from naming here: the field names/numbers come from the
recovered Google protobuf descriptor and the values come from the current
Android Lens binarypb.

## Recovered Google schema

Relevant part of
`ocr/google_ocr/training/runner/tensorflow_model_runner.proto`:

```text
TensorFlowModelRunnerConfig:
  1   saved_model_runner_config
  3   tflite_model_pooled_runner_config
  4   cloudai_servomatic_runner_config
  5   any_model_runner_config
  6   model_runner_pool_selector
  7   tflite_model_pooled_cached_runner_config
  8   darwinn_multi_signature_runner_config
  9   tflite_model_gpu_runner_config
  100 mock_model_runner_config
```

Relevant fields of `TfliteModelPooledCachedRunnerConfig`:

```text
1   model_path
10  model_bytes
2   num_inference_threads
3   interpreter_num_threads
6   multiple_inputs
7   add_custom_ops
8   output_name repeated
12  input_name repeated
13  needs_custom_delegate
14  num_channels
15  batch_size
16  cache_max_size
17  use_xnnpack_delegate
18  warm_up_shapes repeated
19  use_darwinn_delegate
20  darwinn_inference_priority
```

Therefore the Android raw values previously seen as:

```text
field 3  = 4
field 6  = 1
field 16 = 5
field 17 = 1
```

mean exactly:

```text
interpreter_num_threads = 4
multiple_inputs         = true
cache_max_size          = 5
use_xnnpack_delegate    = true
```

## Native binary evidence

`liblens_ondevice_engine_play_ml.so` contains the matching Google OCR
execution implementation, including:

```text
google_ocr::TfliteModelPooledRunner::InterpreterFactoryCallback
TfliteModelPooledCachedRunner::Init
TfliteModelPooledCachedRunner::RunWithContext
TfliteModelPooledXNNPackCached::AllocateModelTensors
TfliteModelPooledXNNPackCached::InsertInterpreter
InterpreterFactoryCallbackXNNPack
ModifyGraphWithDelegate
Failed to modify graph with XNNPack delegate.
```

The same binary also contains GroupRPN implementation/source-path evidence:

```text
ocr/google_ocr/detection/group_rpn_detector_v2.cc
ocr/google_ocr/detection/group_rpn_detector_utils.cc
ocr/google_ocr/detection/group_rpn_detector_inference_utils.cc
GocrGroupRpnTextDetectionMutator
ProcessPackedImagePyramid
```

The targeted ARM64 xref evidence is stored in:

```text
docs/evidence/google-lens-runtime-latest/runner-xrefs.txt
docs/evidence/google-lens-runtime-latest/runner-neighborhood.txt
```

## Important correction to our earlier terminology

The existing LG profiles should now be interpreted as:

### STRICT

```text
system webOS TFLite
XNNPACK off
2 detector threads
```

This is the clean-room deterministic/reference profile used to preserve our
previous outputs. It is **not** the original Android Google execution contract.

### FAST_XNNPACK

```text
system webOS TFLite 2.17
XNNPACK on
2 detector threads
```

This is closer to Google's backend choice, but it is also **not** the original
Google execution environment:

- LG is ARM32; Google App tested here is ARM64.
- The TFLite/XNNPACK build is different.
- Google config requests four interpreter threads.
- Google uses its pooled cached runner.
- Runtime/kernel revisions and build flags may differ.

Therefore a disagreement between STRICT and FAST does not by itself establish
that FAST is lower quality than Google Lens. It only proves that the two LG
execution paths are numerically different.

The observed examples such as `Wildwoods -> Wildmoops` and `Demo -> Demd`
remain blockers for production because the project requires no quality loss,
but they must not be described as deviations from Google until compared with a
Google-native oracle or ground truth.

## Required next experiment

Do not switch production.

Create an experimental profile matching the Google runner contract as closely
as webOS permits:

```text
XNNPACK                 on
detector interpreter    4 threads
same four inputs
same 11 outputs
same model/config
same postprocess
same recognizer
```

Call it something explicit such as `google_runner_experimental`, not STRICT.

Compare on the existing corpus:

1. `STRICT`
2. existing `FAST_XNNPACK` (2 threads)
3. `google_runner_experimental` (XNNPACK + 4 detector threads)

Record raw detector tensors, proposals, final geometry/crops/text and latency.

This experiment still cannot prove Google parity because the webOS XNNPACK
binary differs from the Android one.

The stronger quality gate is an Android/Google-native oracle: the same stored
frames must be passed through the actual Google/Lens GroupRPN runner, then its
raw/final output compared with the LG candidate. Until that exists, no
XNNPACK-based mode becomes production default.

## Reproducible decoder

Run:

```bash
python3 scripts/decode-gocr-runner-config.py \
  /path/to/gocr_group_rpn_text_detection_config_2024_q4.binarypb \
  --assert-current-android-contract
```

The command fails if the current Android contract stops matching the values
documented above.
