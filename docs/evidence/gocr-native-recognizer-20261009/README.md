# Native recognizer evidence, real G5, 2026-10-09

All inputs are the previously saved lossless selected frames, not new capture
or retuned OCR inputs. Emergency Guard and Luigi PPMs in the isolated TV runtime
correspond to the committed frame evidence in the previous native postprocess
directory. No proprietary Google model is committed.

Artifacts:

- `native-recognizer-final-parity.json`: final library, per-line byte/crop hash,
  input-window hash, text, margin and combined native OCR comparison. Both
  frames pass; 21 + 18 lines.
- `native-recognizer-final-benchmark.json`: final two-thread warmed A/B, five
  samples per backend/frame and complete per-sample outputs/timings.
- `native-recognizer-benchmark.json`: initial 2/4-thread matrix. This predates
  the final build's equivalent inverse-scale arithmetic and shared TFLite API
  reuse; use the final benchmark for final two-thread timing.
- `xnnpack-divergence.json`: separate system runtime off/on experiment, same
  four input tensors, all eleven output heads, decoded proposals, postprocess
  counts/membership diagnostics and final crop hashes.

Final installed library size: 145,644 bytes. Host build file and TV file SHA-256:

```text
4c41c0577430ca85f51a68ffa69de9c43075b2739c2c8cbedf538c849065cf81
```

Commands run in `/media/developer/gocr-runtime` on G5:

```bash
python3 -B validate-native-recognizer.py --assets assets \
  --output native-recognizer-final-parity.json \
  fixtures/emergency-guard.ppm fixtures/luigi.ppm

python3 -B benchmark-native-full.py --assets assets \
  --output native-recognizer-final-benchmark.json --threads 2 -- \
  fixtures/emergency-guard.ppm fixtures/luigi.ppm

GOCR_POSTPROCESS_LIBRARY=/media/developer/gocr-runtime/native/gocr_postprocess/libgocr_postprocess.so \
GOCR_NATIVE_PROBE=/media/developer/gocr-runtime/gocr_recognizer_probe \
python3 -B -m unittest discover -s tests -v

python3 -B research-gocr-xnnpack-divergence.py --assets assets \
  --output xnnpack-divergence.json fixtures/emergency-guard.ppm fixtures/luigi.ppm
```

The initial test discovery was invoked without the required postprocess-library
test environment and failed; it also exposed an overly permissive recognizer
test mock. Correcting the test setup/spec retained all assertions. The subsequent
full discovery ran 24 tests and passed. Windows ran the 14 backend/integration
tests successfully. ARM32 and host CMake builds completed successfully.

These tests deploy the native library only into the isolated GOCR runtime.
The existing PicCap GOCR-mode configuration remains absent; no production OCR,
capture/settings/translator/OSD switch or reboot was performed.
