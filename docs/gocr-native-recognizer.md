# Native recognizer and complete TV_FULL hot path

Implemented 2026-10-09. Equivalence means this project's current Python
clean-room reference, not Google Lens parity or original LM/FST decoding.

## Boundary and unchanged behavior

Selected RGB 1280×720 frames now use one `gocr_full_ocr` call:

```text
RGB buffer → native detector → native postprocess
  → native QUAD/BICUBIC rectification
  → native RGB-to-L / Pillow-compatible LANCZOS / 32×168 windows
  → persistent system TFLite recognizer Invoke
  → uint8 logits argmax / stitched greedy CTC / NFC / Unicode strip
  → UTF-8 text + original quad + crop/window SHA-256
```

Python does not execute between detector and recognizer. It still verifies
assets/parses config at startup, handles incoming transport/decompression,
passes the RGB buffer, serializes results and orchestrates translation. The
native function does not perform capture, transport, translation or display.
Generic non-selected images retain the reference path. Persistent buffers and
returned text pointers are protected by a per-worker request lock.

The original model/label map and blank 1292 remain unchanged. Existing reference
32/168 and 16/136/16 constants are passed through the ABI and checked. No decoder
logic was retuned: scalar positive affine dequantization leaves argmax unchanged,
so native reads uint8 logits directly, just like reference. No softmax, beam
search or LM/FST/prior decoding is added. The final short window preserves black
pixels beyond the white padded image's bounds.

Native NFC uses generated Unicode 15.0.0 tables from the actual TV reference's
Python database. `scripts/generate-gocr-unicode.py` reproduces the tables.
`unicode_tables.h` is generated data; all manually maintained source files stay
under 500 lines. No new runtime dependency is introduced. The existing detector
library supplies its TFLite C API implementation.

## Build / binding

```bash
cmake -S native/gocr_recognizer_native -B build/recognizer-tv \
  -DCMAKE_TOOLCHAIN_FILE=/path/to/webos-sdk/share/buildroot/toolchainfile.cmake
cmake --build build/recognizer-tv -j4
```

Builds include detector/postprocess dependencies, `libgocr_recognizer_native.so`
and model-free `gocr_recognizer_probe`. ARM32 webOS and x86-64 host builds passed
with `-O2 -Wall -Wextra -Werror -fno-fast-math -ffp-contract=off`. SDK psABI notes
and NTFS clock-skew warnings appeared; neither caused build failure.

Runtime layout:

```text
native/gocr_postprocess/libgocr_postprocess.so
native/gocr_detector_native/libgocr_detector_native.so
native/gocr_detector_native/libgocr_postprocess.so
native/gocr_recognizer_native/libgocr_recognizer_native.so
```

RPATH includes the sibling detector directory. `GocrFull` borrows detector and
recognizer contexts: destroy it first. Returned text pointers remain valid until
the next OCR call or destruction. Python copies/serializes them while locked.

The isolated GOCR worker defaults to native selection where libraries exist:

```bash
GOCR_DETECTOR=native GOCR_RECOGNIZER=native GOCR_DETECTOR_XNNPACK=0 \
python3 -m gocr_worker.worker_full --assets /opt/gocr/assets --threads 2 image frame.ppm
```

`GOCR_RECOGNIZER=python` selects the regression reference with native detector
still available. `GOCR_RECOGNIZER_LIBRARY` overrides the library path. Missing
native libraries warn and fall back at startup. Runtime inference errors surface
instead of silently substituting results. Capture/API/settings/translation/OSD
are unchanged. Live PicCap's GOCR mode was not enabled and production PP-OCR was
not replaced by these tests.

## Parity / regression

Real G5, Emergency Guard (21 lines) and Luigi (18 lines):

- All 39 native RGB crops match Pillow byte for byte.
- All 39 concatenated recognizer-window hashes match.
- All 39 UTF-8 texts and diagnostic logit margins match.
- Complete native output preserves IDs, quads and crop/window hashes.
- Warmed two/four-thread A/B samples preserve identity on both frames.

24 tests passed on G5. Probe tests cover SHA-256 empty/standard/multiblock
vectors; every canonical Unicode decomposition plus 1,000 randomized combining
sequences; Hangul/Cyrillic/whitespace; 24 RGB/L resize/window cases; nine rotated,
perspective, outside-fill and ties-to-even rectification cases. Other tests
cover native/reference selection, missing-library fallback, explicit debug mode,
concurrent request serialization, transport and native postprocess regressions.
14 backend/integration tests also passed on Windows.

## Warmed timing: frame to OCR text only

`benchmark-native-full.py`: one warmup per frame/backend, five measured samples
per backend, alternating call order. Same system runtime/assets/native detector;
translation and display excluded. Final two-thread comparison, mean milliseconds:

| Frame | Reference recognizer/rectification | All-native OCR |
|---|---:|---:|
| Emergency Guard | 2111.61 | 2069.64 |
| Luigi | 2020.89 | 1903.37 |

Final recognizer totals: 570.30→510.68 ms and 489.71→399.76 ms. Native scalar
rectification itself is slower than Pillow's compiled C transform:
28.54→43.52 ms and 26.74→39.75 ms. Its benefit is the single native hot-path
boundary, not an independently claimed rectification speedup.

The first matrix also tested four threads:

| Frame | Threads | Reference total | Native total |
|---|---:|---:|---:|
| Emergency Guard | 2 | 2268.12 | 2126.30 |
| Luigi | 2 | 2117.22 | 1976.34 |
| Emergency Guard | 4 | 4979.00 | 4929.87 |
| Luigi | 4 | 4831.85 | 4426.16 |

Four threads still degrade the complete path despite the earlier standalone
detector result. The exact cause remains unproven; default stays two threads.
Paired gains vary about 42–142 ms across runs. Do not compare absolute totals
against the older 1.71–1.78 s session as a controlled A/B: detector Invoke here
took ~1.42–1.47 s, versus ~1.21–1.24 s earlier. The 1.3–1.5 s target has not
been achieved. Model Invoke remains dominant; moving orchestration cannot
remove that work. No parity/quality gate was weakened to obtain faster numbers.

## XNNPACK research, separate from the strict profile

`research-gocr-xnnpack-divergence.py` compares two native detector contexts,
system runtime, two threads, XNNPACK explicitly off/on.

For both real frames, all four inputs match and **all eleven output heads
already differ before decode/grouping**. The earliest observed divergent
boundary is detector output tensors. It is not created by this rectification
or postprocess port. This does not identify the first internal operator.

Emergency Guard: proposals 935→941, deduped pieces 326→321, components 21→21.
Luigi: proposals 735→739, deduped pieces 267→266, components 18→17. Evidence
records changed-element counts, first changed flat index, max/mean error,
decoded-proposal/component-membership hashes and final quads/crop hashes.
Membership hashes across different proposal sets are diagnostics, not an
identity/quality score. XNNPACK remains disabled in the strict profile.

See [raw evidence and commands](evidence/gocr-native-recognizer-20261009/README.md).
