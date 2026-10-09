# Exact native PP-OCR CTC token scan — 2026-10-10

## Scope

Native CPU decoding of ORIGINAL PP-OCRv6 class-major float32 output. RKNN models, dictionary, preprocessing, core mask, native RKNN bridge, detector, policy, transport and OSD renderer unchanged. This does not accelerate NPU computation.

Native function scans class-major arrays without NumPy's transposed argmax path. It validates all values by float32 exponent bits, keeps first class on ties using strict greater, preserves blank index 0, adjacent-repeat collapse and blank-separated repeats. No fast/approximate math or probability transformations. Remaining Python maps Unicode labels and uses the SAME statistics.mean and [0,1] clamp as reference; confidence arithmetic is not rewritten. Unsupported dtype/layout/shape rejected by bounded wrapper. Other recognizer layouts stay with the original decoder.

Build: cmake -S native/ppocr_ctc -B BUILD -DCMAKE_BUILD_TYPE=Release, cmake --build BUILD -j2. ARM64 library built on Orange with -O3 -Wall -Wextra -Werror -fno-fast-math -ffp-contract=off. Library SHA256 631b74e67edb3ffd6d9f9998959b9006aa344702b76b8ca5d8a417aa1c641eae.

## Quality gate

Same frozen 18-crop corpus from ../ppocr-quality-gate-20261009/corpus.tar.gz. Original installed RKNN scores obtained once per case; both decoders see the EXACT SAME output array. One warmup, ten alternating measured calls per decoder/case. All texts AND Python float confidences match exactly on every call. Expected-ground-truth accuracy remains 15/18: prior clipped guard, missing school space and button omissions remain; no new errors.

66 artificial exact cases plus six nonfinite-rejection checks on Orange: random shapes/time widths, repeats, blanks, ties, negatives, Unicode labels, confidence >1 clamp, NaN/Inf in a losing class. Models/raw output are not modified by decoder. Eight existing PP-OCR host tests pass; Python syntax/diff checks pass. Native original-call tests are performed via scripts/validate-ppocr-native-ctc.py, not approximated by mocks.

## Decode-only controlled speed

Median of per-case medians, grouped by original model width; not a full inference time:

| Width | Python decoder | Native decoder |
|---|---:|---:|
| 640 | 6.204 ms | 1.706 ms |
| 2560 | 90.564 ms | 7.987 ms |

Native faster in all 18 cases. These values exclude NPU call, detector, image/network and translator. Same scores/call order make this a decoder-only paired comparison. Production NPU activity can affect CPU scheduling but does not change tested data.

## Deployment / complete response check

Explicit PP_OCR_CTC_LIBRARY user-unit setting selects native only for class-major output; removing the setting and restarting restores original Python decode. Library/module left as persistent default dependencies at /home/orangepi/ppocr-native-ctc-experiment-20261010/build/libppocr_ctc.so and ppocr-full-experiment-20261009/ppocr_native_ctc.py. Historical directory names retained, not ephemeral cleanup targets.

Full-frame actual endpoint replay on the three original saved Emergency/Luigi inputs compared with archived pre-change ../lz4-transfer-20261009/ocr-parity.json: complete lines/regions (including confidence, policy, appearance) and frame SHA exact. Raw and LZ4 paths also still match. Native library appears in active service memory maps; full-frame unit active and translator health OK. Original RKNN bridge hash remains e50590509771f141d6f9c47b795076178c3084ff5173f6475dc03a6054979747; no prealloc candidate installed.

Ten fresh live frames, 16–20 regions: OCR median 1684.36 ms, frame-to-returned-text 1801.14 ms (range 1712.97–2045.69), cached end-to-end 1835.83 ms, selected-frame-to-detector upper estimate 268.52 ms. Frames differ from previous live series, so entire difference is NOT an isolated decoder-only speedup or physical panel-to-OSD measurement. No reboot/long thermal test performed.

Artifacts: comparison.json, full-parity.json, live.json. Model/corpus provenance continues in quality-gate report. Python reference retained for regression and rollback.
