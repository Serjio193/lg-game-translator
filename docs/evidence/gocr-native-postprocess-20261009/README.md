# Evidence provenance

Date: 2026-10-09. Device: LG G5, ARM32 userland, original Google assets from
the previous integration runtime. No model/config/threshold/profile changes.

- `emergency-guard.png`, `luigi.png`: lossless RGB exports of the stored PPM
  frames used in the prior three-mode test. No new capture source or resizing.
- `*-proposals.json`: every decoded proposal from the one shared detector
  inference of the final A/B benchmark, including original quad/center/score/head.
  These are model outputs, not proprietary model files.
- `parity-benchmark.json`: three measured postprocess runs after one warm-up for
  each backend; two real full OCR passes per frame (one Python, one native).
  Full passes run inference anew; no translation/stabilization/display time.

Reference/native comparisons use the exact same proposals, same G5 recognizer,
same rectification implementation. Counts, membership, final count, geometry,
angle, score, piece_count, crop SHA and text pass on both frames.
Floating-point absolute tolerance: 1e-9. Max observed quad difference: 4.55e-13.
All 39 rectified crops are byte-identical; all 39 texts match.

The `benchmarks` summaries are medians calculated from the retained raw runs.
Full OCR fields are direct single warm measurements, not medians. Normal capture
remained running during the benchmark; CPU load can affect future timings.

Verification performed:

- ARM32 webOS SDK shared library build; Linux x86_64 CMake build.
- ARM64 Orange Pi build and 10 unittest cases: PASS.
- Actual G5 shared library load and six native regression cases: PASS.
- Host integration tests (4): PASS; Python compile checks: PASS.
- Source size check: all manually changed source files in this stage <=500 lines.
- Diff whitespace check: PASS.

Native ABI/backend proven with the current clean-room Python reference only.
No claim of general parity with Google Lens or original production FST decoding.
Capture/API/settings were not changed and production OCR mode was not switched.
