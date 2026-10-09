# Codex handoff: GOCR worker integration

This document is the integration entry point for the Google Lens / GOCR work in this repository.

## Goal

Integrate the portable GOCR worker into the existing LG game translator pipeline.

Target behavior:

```text
1280x720 frame
  -> Google GroupRPN detector
  -> Google line grouping
  -> rectified Google crops
  -> Google Latin/Cyrillic recognizer
  -> UTF-8 text + source-frame geometry
```

There are two deployment modes:

### MODE A: TV_FULL

```text
LG TV:
frame -> detector -> crop -> recognizer -> text + geometry

Orange Pi:
translation only
```

### MODE B: TV_CROP

```text
LG TV:
frame -> detector -> crop + geometry

Orange Pi:
recognizer -> text -> translation
```

The OCR behavior must remain the same in both modes. Only the recognizer execution location changes.

## Read these files first

1. `docs/gocr-worker.md`
   - current usage
   - API
   - expected JSON output
   - asset extraction
   - current parity status

2. `research/lens-rpn-launch-contract.md`
   - GroupRPN model contract
   - tensor inputs/outputs
   - detector channel semantics
   - Android 1280 profile

3. `research/gocr-recognizer-launch-contract.md`
   - recognizer tensor contract
   - Latin/Cyrillic model
   - label map / CTC
   - windowing values
   - LM/FST/prior assets

4. `research/gocr-two-mode-benchmark.md`
   - TV_FULL vs TV_CROP benchmark plan

5. `gocr_worker/worker_full.py`
   - full-frame entrypoint

6. `gocr_worker/worker.py`
   - crop-recognition entrypoint / HTTP server

7. `gocr_worker/detector.py`
   - portable GroupRPN network decode + clean-room grouping

8. `gocr_worker/detector_runtime.py`
   - detector execution driven by the original Google binarypb

9. `gocr_worker/detector_config.py`
   - runtime parser for the original Google detector config

10. `gocr_worker/recognizer.py`
    - Google Latin/Cyrillic recognizer + CTC decoding

11. `gocr_worker/protocol.py`
    - output structures

12. `scripts/extract-gocr-assets.py`
    - extracts original Google assets from the Google App APK

13. `scripts/validate-full-gocr-worker.py`
    - A/B validation against native ScreenAI

## Important rule

Do NOT retune Google OCR settings.

Google model/config assets are part of the runtime contract.

Detector settings must come from:

```text
gocr_group_rpn_text_detection_config_2024_q4.binarypb
```

Recognizer settings/assets must remain paired with the original Google model/config/label-map/LM files.

Do not expose detector thresholds, anchors, grouping constants, recognizer window sizes, LM weights, or similar values as project UI settings.

Our own configurable values may include:
- execution location: TV or Orange Pi
- thread count
- transport address/port
- telemetry/benchmark logging

## Original Google assets

Required:

```text
gocr_group_rpn_text_detection_model_2024_q4.tflite
gocr_group_rpn_text_detection_config_2024_q4.binarypb
recognizer_latn_vi_cyrl_lm_retrained.tflite
recognizer_latn_vi_cyrl_label_map.pb
```

Additional recognizer assets:

```text
recognizer_cyrl_config.pb
recognizer_cyrl_lm.compact_fst.gz
recognizer_cyrl_lm.syms
recognizer_latn_vi_cyrl_prior.pb
```

The proprietary model files are not committed to git. Use:

```bash
python3 scripts/extract-gocr-assets.py Google.apk /opt/gocr/assets
```

## Current full-frame CLI

```bash
PYTHONPATH=. python3 -m gocr_worker.worker_full \
  --assets /opt/gocr/assets \
  --threads 4 \
  image frame.png
```

## Current full-frame HTTP server

```bash
PYTHONPATH=. python3 -m gocr_worker.worker_full \
  --assets /opt/gocr/assets \
  --threads 4 \
  serve --bind 0.0.0.0 --port 8771
```

Endpoint:

```text
POST /v1/ocr
```

Input:

```json
{
  "image_b64": "..."
}
```

Output schema:

```json
{
  "schema": "gocr.worker.v1",
  "width": 1280,
  "height": 720,
  "mode": "full",
  "lines": [
    {
      "line_id": "0",
      "text": "THE DOOR IS LOCKED",
      "source_quad": {
        "p0": {"x": 94, "y": 160},
        "p1": {"x": 684, "y": 159},
        "p2": {"x": 684, "y": 202},
        "p3": {"x": 94, "y": 202}
      },
      "angle": 0.0,
      "detector_confidence": 0.99,
      "recognizer_confidence": null,
      "timings_ms": {}
    }
  ],
  "timings_ms": {},
  "parity": {}
}
```

The geometry is in original-frame coordinates.

## Current validation result

A controlled 1280x720 frame was passed through:

1. native `libchromescreenai.so` using the Android Lens detector config;
2. our portable full GOCR worker.

Result:

```text
native line count:   3
portable line count: 3
text match:          3/3

THE DOOR IS LOCKED   IoU 0.9699
Привет мир           IoU 0.9563
Press E to open      IoU 0.8733

mean bbox IoU:       0.93317
```

This proves the end-to-end pipeline works. It does NOT yet prove perfect parity for every rotated, curved, small, dense, or stylized UI case.

## What Codex should do next

### First integration target

Integrate `GoogleConfiguredGroupRpnDetector` into the existing LG-side frame path.

The existing project already captures/selects a 1280x720 frame. Do not replace the capture scheduler.

Expected insertion point:

```text
existing selected 1280x720 frame
    -> GoogleConfiguredGroupRpnDetector
    -> line quads / crops
```

### MODE B first

Implement TV_CROP first because it is the easier benchmark split:

```text
LG:
frame -> detector -> rectified crop + source_quad

Orange Pi:
crop -> GocrLineRecognizer -> text -> existing translation server
```

Preserve:
- line_id
- source_quad
- angle
- detector_confidence

Do not recompute source coordinates on Orange Pi.

### MODE A second

Once detector is stable on LG, move `GocrLineRecognizer` to TV:

```text
LG:
frame -> detector -> crop -> recognizer -> text + source_quad

Orange Pi:
translation only
```

The network payload should change, but OCR output semantics must not.

## Benchmark requirements

For the same stored 1280x720 frames, record:

```text
detector_ms
crop_rectify_ms
recognizer_ms
network_ms
bytes_sent
translation_ms
end_to_end_ms
```

Compare both modes using the same frames and the same Google assets/config.

## Do not silently change these

- GroupRPN model
- detector binarypb
- detector threshold
- anchors
- grouping constants
- input profile
- recognizer model
- label map
- CTC blank
- recognizer window contract
- LM/FST/prior parameters

If an experiment changes OCR settings, create a separate experimental profile and do not overwrite the production-compatible profile.

## Practical integration success condition

Codex can consider the first LG integration successful when:

```text
same 1280x720 test frame
-> LG detector output
-> same line count / close quads as desktop worker
-> crops recognized by Orange Pi worker
-> translated text can be mapped back to source_quad
```

After that, benchmark MODE A vs MODE B.
