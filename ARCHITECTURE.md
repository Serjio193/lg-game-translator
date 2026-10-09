# OCR architecture boundaries

Existing PicCap selects the RGB 1280×720 frame. Capture scheduler/settings/API
belong to the separate hyperion-webos repository and are not replaced by GOCR.

Experimental `ORANGE_FULL` relays that same RGB buffer via the existing GFR1
frame header in an authenticated HTTP body. Orange reconstructs the original
RGB pixels, runs the configured detector / native postprocess / rectification /
recognizer, and returns text + original source quads and the frame fingerprint.
The TV checks frame identity, then reuses the existing translation client and
result publication. Capture and OSD are unchanged; no TV OCR models are created
in this mode. It is not numerically equivalent to TV system STRICT and is never
selected automatically. Its Orange LiteRT default delegates are explicitly off.

TV_FULL's selected-frame detector path:

```text
existing RGB frame
  → detector_backend selection
  → native C ABI
      → grayscale + fixed original pyramid directly into TFLite inputs
      → reused TFLite interpreter / Invoke
      → direct output tensor decode
      → native clean-room postprocess
      → final quads / native rectification
      → Google recognizer windows / persistent TFLite / greedy CTC / NFC
  → text + original source_quad
  → existing translation service
```

The existing binarypb parser supplies original model launch values at startup.
Only execution/thread/runtime/debug selection changes; OCR parameters are not UI
settings. Native C ABI does not depend on Python, capture APIs or translators.

Python is orchestration, config parsing, incoming image transport/decompression
and serialization. Selected-frame OCR uses one native call from RGB buffer to
text/quads, without returning to Python between detector and recognizer.
Non-selected generic images retain the reference API path. Interpreter buffers
are protected by one request lock per worker. Python serializes native text
pointers before releasing the lock.

Backend selection preserves Python reference for debug/unavailable platforms.
Runtime/delegate experiments are separate from production defaults. Matching the
clean-room reference is distinct from Google Lens parity or original LM/FST decoding.

`GOCR_PROFILE=strict` is the default. Explicit `fast_xnnpack` applies the system
TFLite XNNPACK delegate only to the native detector, retaining the recognizer.
FAST requires the selected RGB1280x720 TV_FULL native path and fails on unavailable
native support instead of silently labeling a fallback as FAST. No capture, API
settings or production service is automatically switched. FAST comparisons use
one-to-one quad IoU matching and Unicode text differences, not tensor/crop hashes.

`google_runner_experimental` additionally validates the recovered original
Android cached-runner config, uses detector 4 / recognizer 2, and preserves all
OCR parameters. A persistent webOS interpreter/delegate repeats only the known
execution subset; Google cache capacity 5 is recorded without inventing a pool
policy. STRICT is a reference, never a Google-quality oracle. Production selection
is unchanged. Detailed evidence is in `docs/gocr-google-runner-experimental.md`.

Detector and recognizer thread counts can be selected independently at worker
startup and forwarded by the TV_FULL frame server. Legacy `--threads` supplies
both defaults; measured default remains 2/2. TV_CROP recognition threads belong
to the Orange worker, not the TV frame consumer.

Benchmarks exclude translation/display and keep the capture pipeline unchanged.
See `docs/gocr-native-detector.md` for actual boundary, parity and timing evidence.
See `docs/gocr-native-recognizer.md` for the complete selected-frame native path.
