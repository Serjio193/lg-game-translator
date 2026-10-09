# Thread/runtime evidence

- `thread-matrix.json`: seven fresh-process configurations including 2/2 repeated
  at the end; all raw samples, per-task counters, identities and strict parity.
- `thread-current-cpp-2.json`, `thread-current-cpp-4.json`: standalone native
  detector Invoke, ten measured samples after three warmups; system runtime,
  XNNPACK disabled, same original config snapshot and saved frame.
- `thread-invoke-boundary.json`: same four-thread detector context, Invoke-only
  and prepare+Invoke, before and after recognizer construction, ten samples each;
  enhanced per-task affinity/priority and system CPU counters.
- `thread-split-cli.json`, `thread-default-cli.json`: actual TV_FULL CLI replay
  of Luigi with new 4/2 flags and default 2/2. Cold one-pass outputs validate
  wiring; they are not warmed performance comparisons.

Commands in isolated `/media/developer/gocr-runtime`:

```bash
python3 -B profile-gocr-threads.py --assets assets \
  --frame fixtures/emergency-guard.ppm --output thread-matrix.json --repeats 3
python3 -B profile-gocr-invoke-boundary.py --assets assets \
  --frame fixtures/emergency-guard.ppm --output thread-invoke-boundary.json --threads 4
native/gocr_detector_native/gocr_detector_bench \
  assets/gocr_group_rpn_text_detection_model_2024_q4.tflite \
  /usr/lib/libtensorflow-lite.so native-detector-final-parity.config \
  fixtures/emergency-guard.ppm 4 0 10
```

The first profiler invocation completed the initial measurement but failed when
printing its JSON summary (misplaced `flush` argument). That formatting bug was
corrected and the complete seven-configuration matrix rerun successfully.
`parity:false` is intentionally retained: detector threading changes small quad
coordinates and one crop hash. All texts and normalized window hashes still
match. The report explains this distinction; it is not Google Lens parity.

Original frames/models and current native library identities remain as documented
in the prior detector/recognizer evidence. New code only exposes separate thread
counts and records observations. No thresholds, anchors, windows, decoder logic,
capture, production service selection or XNNPACK default changed.
