# Native detector evidence

Device: LG G5, 2026-10-09. Models/config from the existing original Google bundle.
Frames: stored Emergency Guard and Luigi from the earlier integration benchmark;
lossless exports are in `../gocr-native-postprocess-20261009/`.

- `native-detector-final-parity.json`: final ARM32 library, system runtime,
  explicit XNNPACK OFF, threads=2. Four inputs and eleven outputs exact; all raw
  proposals exact; all 39 crops and texts exact against current Python reference.
- `native-detector-parity.json`: first native implementation checkpoint.
- `native-detector-threads4-parity.json`: separate four-thread checkpoint; strict PASS.
- `native-detector-xnnpack-parity.json`, `native-detector-custom-parity.json`:
  explicit runtime experiments, strict equivalence FAIL (expected non-admission).
  Their validation command exits nonzero; tests were not weakened or skipped.
- `detector-system-benchmark/`: three warm-up + twenty Invoke samples for each
  thread/delegate combination, standalone C++, same stored Emergency Guard.
- `custom-tflite-benchmark.json`, `custom-tflite-no-xnnpack-benchmark.json`:
  isolated ARMv7/NEON TensorFlow 2.17 build comparison, twenty Invoke samples.
- `affinity-01-benchmark.json`, `affinity-23-benchmark.json`: taskset affected only
  the benchmark subprocess, not TV/capture global settings.
- `system-op-profile.json`, `xnnpack-op-profile.json`: separate instrumented
  passes with actual builtin/delegate operations, excluded from timing matrix.
- `full-native-benchmark.json`: TV_FULL, one warm-up + five calls per frame/thread
  configuration; includes rectification/recognizer and excludes translator/OSD.
- `native-full-final.json`: final TV_FULL CLI proof with native detector telemetry.
  This is a first OCR call after construction, not the warmed timing summary.

Verification: webOS ARM32 and Linux x86_64 CMake builds PASS; optional original
TensorFlow 2.17 ARMv7/NEON/XNNPACK build and actual G5 load/run PASS. Fifteen
backend/integration/reference regression cases passed on Orange Pi; nine
backend/integration cases passed on Windows. Python compile and diff whitespace
checks passed. All human-maintained source files in this phase are under 500 lines.

Normal capture continued during measurements. At completion PicCap status was
returnValue=true, videoRunning=true, connected=true, isRunning=true, ~58.58 fps.
No capture/API/settings changes or production mode switch were made in this phase.

Library SHA256 (final ARM32 detector):
`1ccdeb3bf94561d9310360bc19423956727ccae2003dca1761ed869212d4a73e`.
Model/runtime binaries, tokens and downloaded third-party sources are not committed.
Parity scope is the project's Python clean-room reference, not Google Lens.
