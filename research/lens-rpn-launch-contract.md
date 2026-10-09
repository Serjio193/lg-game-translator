# Google Lens / GOCR GroupRPN detector launch contract

Source snapshot: Google App 17.64.14.ve.arm64 (2026-10-07) and Chromium ScreenAI CIPD package current on 2026-10-09.

## Exact model identity

Model:
`gocr_group_rpn_text_detection_model_2024_q4.tflite`

SHA-256:
`55ab1290b1b481d71c65636d93570f4e48ae0d2c0a748f773d93b9cd13126a51`

The Android Lens asset and Chromium ScreenAI asset are byte-identical.

Android config SHA-256:
`45033fc42999a90e9fae90ef8303ee76e013f575ca1caa811d315a1e0107481c`

Chrome config SHA-256:
`d176576a7f39e45bc08a1ab014e04b83f6610de34a2c0c434cdb2b791ec26cc0`

Config type URL:
`type.googleapis.com/google_ocr.GroupRpnTextDetectionMutatorConfig`

## Proven inference interface

Inputs:
- `input_features`
- `input_features_1`
- `input_features_2`
- `input_features_3`

All are grayscale UINT8 image tensors. The model supports dynamic resizing by the runtime.

Outputs:
- `Identity` through `Identity_10`
- every head has last dimension 7.

Experimentally verified 7-channel semantics:
1. score logit
2. center dx
3. center dy
4. log width relative to anchor
5. log height relative to anchor
6. orientation vector X
7. orientation vector Y

Angle is `atan2(ch6, ch5)`. The orientation vector is NOT unit-normalized; only its direction is meaningful.

Geometry decode:
```
score = sigmoid(v0)
cx = (grid_x + 0.5 + v1) * stride
cy = (grid_y + 0.5 + v2) * stride
w = anchor_w * exp(v3)
h = anchor_h * exp(v4)
angle = atan2(v6, v5)
```

Rotated synthetic-text validation produced approximately -30 degrees for a +30 degree Pillow rotation, confirming the orientation channels modulo image-coordinate sign convention.

## Exact detector config values

Inference/postprocess block:

- score threshold: `0.5`
- anchor widths: `[16, 64, 16, 64, 64, 64]`
- anchor heights: `[16, 64, 16, 64, 64, 64]`
- additional scalar fields: `0.5, 0.5, 0.0`
- stride-related config contains `32, 32, 32`
- reference widths: six copies of `1280`
- reference heights: six copies of `1280`

Grouping block A exact floats:
`[1.75, 0.8, 30.0, 0.25, 0.1, 0.4, 0.3]`

Grouping block B exact values:
`[4.0, -4.0, 0.5, 0.5, 0.75, 0.75, 0.1, 0.75]`
plus boolean field 19 = true.

Other exact group/postprocess values:
- transform-like block: `[0.5, 0.0, 0.0, 0.5]`
- scalar: `64.0`
- enum/bool fields retained in the original binarypb and must not be replaced by guessed values.

Do not rename the grouping floats yet. Their numerical values are proven; some semantic field names are still private and must be recovered from binary behavior before reimplementation.

## Platform-specific optimized launch profiles

This is critical: the model weights are identical between Android Lens and Chromium, while the launch configs differ.

Android Lens config contains one image-size profile:
- `1280 x 1280`

Chromium ScreenAI config contains:
- `1280 x 1280`
- `2048 x 2048`

The original Chromium runtime independently reports:
`GetMaxImageDimension() = 2048`

Therefore max input size is a runtime/profile optimization, NOT an intrinsic model constant.

For an LG/webOS port, do not blindly choose 2048. Start from the Android 1280 profile unless profiling of the TV SoC proves that the Chrome 2048 profile is affordable.

## Original Chromium runtime reference

Current Chromium ScreenAI package:
`chromium/third_party/screen-ai/linux`

Original Google C ABI exposes:
- `SetFileContentFunctions`
- `InitOCRUsingCallback`
- `SetOCRLightMode`
- `GetMaxImageDimension`
- `PerformOCR`
- `FreeLibraryAllocatedCharArray`

Reference test:
- input: 1280x720 RGBA, white background, black "HELLO WORLD"
- max dimension reported: 2048
- output line: `HELLO WORLD`
- box: x=127, y=256, width=696, height=78, angle ~= -0.1167 degrees

The runtime requested the same GroupRPN model/config plus GOCR recognizer/layout assets.

## Proven original postprocess implementation names

Extracted from Google native binary:
- `ocr/google_ocr/detection/group_rpn_detector_utils.cc`
- `ocr/google_ocr/detection/group_rpn_detector_inference_utils.cc`
- `ocr/google_ocr/detection/group_rpn_detector_tensor_utils.cc`
- `ocr/google_ocr/detection/group_rpn_detector_v2.cc`
- `ocr/google_ocr/detection/group_rpn_detector_hac.h`
- `GocrGroupRpnTextDetectionMutator`
- `ProcessPackedImagePyramid`
- `GetPairwiseConnections`
- `ClusterBoxes`

Log strings prove additional stages/criteria including:
- height ratio
- angle difference
- normalized distance rejection
- overlap tests
- pairwise connections
- HAC-style clustering
- piece-wise fitting / cluster splitting

## Current head interpretation

The first six outputs are piece/proposal heads:
- Identity
- Identity_1
- Identity_2
- Identity_3
- Identity_4
- Identity_5

The remaining five are group/line-support heads:
- Identity_6 ... Identity_10

This split is strongly supported by the model behavior and an independent implementation, but exact Google head-to-pyramid mapping should still be checked against original ScreenAI output before TV integration.

## Preprocessing facts that must be preserved

Proven:
- grayscale UINT8 detector input
- aspect ratio preserved
- dynamic model input resizing
- image pyramid
- dimensions are aligned for model stride (32 appears explicitly in config)
- runtime has platform-specific max-size profiles
- Chromium downsamples inputs above its max dimension before OCR.

Still to recover exactly:
- exact luminance coefficients
- exact interpolation kernel
- exact padding fill value and side placement
- exact first-level selection rule on Android
- exact rules for whether 1280 and/or smaller pyramid inputs are skipped for small images.

No TV implementation should hardcode guessed values for the unresolved items.

## Porting rule

The webOS detector should be implemented as:

```
TV frame / ROI
 -> exact Google-compatible preprocessing
 -> exact GroupRPN TFLite
 -> exact config-driven decode
 -> config-driven GroupRPN clustering
 -> rotated line boxes
```

All tunables must come from a parsed/captured launch profile, not scattered constants.

Recommended profiles:
- `lens_android_1280`: reproduce current Android Lens config exactly.
- `screenai_linux_2048`: reference/validation profile only until TV performance is measured.
