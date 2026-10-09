# Google Lens / GOCR line recognizer launch contract

Snapshot: Google App 17.64.14.ve.arm64, extracted 2026-10-09.

## Recommended mobile recognizer for Latin + Cyrillic

Model:
`recognizer_latn_vi_cyrl_lm_retrained.tflite`

Size:
`1,805,208 bytes`

SHA-256:
`23501a73630270f22ad7fc9b54a6daa566db4b492eb7addaa160b88afba6d002`

Label map:
`recognizer_latn_vi_cyrl_label_map.pb`

SHA-256:
`d41cea501ff409954bc29e7e83eb6992e475312cfa15040066cd222a98dc3192`

The label map has 1,292 labels. CTC blank ID is 1,292.
It directly contains Latin and Cyrillic symbols, including Russian `Я`, `я`, `ё`.

## Exact model input

Tensor:
`serving_default_image_tensor:0`

Shape:
`[1, 32, 168, 1]`

Shape signature:
`[-1, 32, 168, 1]`

Type:
`uint8`

Quantization:
- scale = `0.00392117677256465` (~1/255)
- zero point = `0`

The Google configs specify line height `32.0`.

## Exact text output

Logits tensor:
`StatefulPartitionedCall:0`

Shape:
`[1, 42, 1293]`

Type:
`uint8`

Quantization:
- scale = `0.0784313753247261`
- zero point = `128`

The last dimension is 1,292 labels + one CTC blank.

For greedy decode:
1. argmax over 1293 classes at each of 42 time steps;
2. collapse consecutive repeated token IDs;
3. remove blank ID 1292;
4. map remaining IDs through the label map;
5. Unicode-normalize the result.

Softmax is unnecessary for argmax because output quantization uses a scalar scale/zero point.

## Additional model outputs

The config explicitly requests:
- `decode_logits`
- `symbol_left_offset`
- `symbol_right_offset`
- `symbol_top`
- `symbol_height`
- `direction_activations`
- `direction_gates`

Observed tensor shapes include:
- `[1,42,1293]` logits
- `[1,42,5]` one auxiliary head
- `[1,42,1]` one auxiliary head
- four/five `[1,42]` auxiliary heads

This means the recognizer can provide per-time-step/symbol geometry and direction in addition to text. Exact mapping of all generic `StatefulPartitionedCall:N` tensors to config names still needs behavioral verification before using symbol geometry.

## Android script selection

Current Android Lens uses `MultiPassLineRecognitionMutatorConfig`.

Relevant mappings:
- `Latn` -> `gocr_tflite_recognizer_latn_config.pb`
- `Cyrl` -> `recognizer_cyrl_config.pb`
- other scripts have their own recognizers.

The selector config contains:
- default script: `Latn`
- selector threshold/value: `0.4`

There is also an `UnreadableLineRecognizer` fallback.

## Latin configuration

Latin recognizer model:
`gocr_tflite_recognizer_latn_vi.tflite`

Size:
`1,711,168 bytes`

SHA-256:
`aa9c690d39f60cd88c0ecd7ff206c7ef7a9baf6421349ec5f7aa14106d2c4128`

Config facts:
- recognizer name: `latn`
- script/lang identifier: `latin`
- line height: `32.0`
- scalar threshold: `0.87`
- uses `gocr_tflite_recognizer_latn_prior.pb`
- output names include logits + four symbol geometry outputs
- no external FST path appears in this config

## Cyrillic configuration

Cyrillic uses the combined Latin/Vietnamese/Cyrillic model:
`recognizer_latn_vi_cyrl_lm_retrained.tflite`

Config facts:
- recognizer name: `cyrl`
- script ID: `Cyrl`
- line height: `32.0`
- exact integer fields include `136`, `16`, `16`
- uses `recognizer_cyrl_lm.compact_fst.gz`
- uses `recognizer_cyrl_lm.syms`
- uses `recognizer_latn_vi_cyrl_prior.pb`
- confidence scorer: `CtcDecoderConfidenceScorer_AvgLogits`

Observed LM/decoder config values include:
- `5.0`
- `5.0`
- `0.6`
- `-1.0`
- `0.1`
- `0.3`
- `-0.6`

Do not rename these values without recovering the private proto field names or validating their effect in the native decoder.

## Recognition window contract

Model width is 168 pixels and produces 42 time steps, exactly 4 image pixels per time step.

The Google config contains:
- `136`
- `16`
- `16`

A highly consistent interpretation is:
- left context = 16 px = 4 time steps
- useful center = 136 px = 34 time steps
- right context = 16 px = 4 time steps
- total = 168 px = 42 time steps

This is stronger than the earlier experimental standalone scheme `32 + 104 + 32`, because the exact `136/16/16` values come from the production Google config.

However, a simple long-line reference test produced the same text for both schemes, so this interpretation is not yet marked as behaviorally proven. Boundary-stress tests are still required.

## Chrome reference recognizer

Chromium ScreenAI uses:
`gocr_mobile_und.tflite`

Input:
`[1,32,168,1] uint8`

Output:
`[1,42,1293]`

The universal Chrome label map also contains Latin and Cyrillic.

A standalone LiteRT implementation using the universal model has already been independently demonstrated to work on line crops. Native ScreenAI remains the reference/oracle for exact preprocessing, stitching and decoder behavior.

## Proposed product split

Minimal system:

```
LG TV:
  frame
  -> GroupRPN detector
  -> Google line quad / "Google crop"

TV or Orange Pi:
  Google crop
  -> height normalization / exact windowing
  -> Latin+Cyrillic GOCR recognizer
  -> CTC decode
  -> UTF-8 text
```

Optional quality layers:
- script/language selector
- FST language model
- recognizer prior
- per-symbol geometry
- confidence scorer

For the first end-to-end prototype, detector + raw CTC recognizer are sufficient.
For parity with Google, the optional layers must be ported/configured rather than tuned manually.
