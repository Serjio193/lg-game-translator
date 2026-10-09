# Quality-first PP-OCR RKNN experiment

Run started 2026-10-09; corpus filenames preserve that session date. Frozen saved crops, original installed PP-OCRv6 small FP16 RKNN models, existing CPU preprocessing/CTC decoder. No production switching. Quality baseline ran BEFORE experiments for each corpus subset.

## Frozen quality baseline

12 historical hard crops (decorative font, contractions, mixed punctuation, long wide input, Wildwoods, deliberately trimmed volunteer variant) plus six formerly problematic crops (Demo, Attack Combos, B, clipped guard, decorative Snoutlet School, button-ended Luigi description). Expected strings in corpus manifests are independent of current OCR output. Known negative/geometry cases remain present, not removed to make the score pass.

Primary 12: exact 12/12, five warmed repetitions each. Additional six: exact 3/6. Total 15/18. Three original errors:
- expected `Hold R while an enemy attacks to guard`, original `Hold R while an enemy attacks to guaro`: rightmost glyph cut by this saved crop;
- expected `Snoutlet School`, original `SnoutletSchool`: missing space;
- expected `goes. Make Luigi jump by pressing B.`, original ends after `pressing `: button/punctuation omitted by raw recognizer. Existing Tesseract-assisted button preservation is not included in this recognizer-only quality gate.

Corpus archive stores manifests + original pixel files for reproduction; no models/credentials. Baseline reports preserve normalized input SHA256, expected/actual UTF-8, confidence, raw output SHA256 and per-sample timings. Original crop bytes are grayscale, despite the initial report field's legacy name crop_rgb_sha256; harness now calls it crop_gray_sha256 and also stores source-file/model/vocabulary hashes for future runs.

Verified original assets:
- narrow model 01f30e42f331d73a3b474dd7d504303d90080059746781c0aa163759fcbfc192
- wide model 36178cd208adf27bf7781e4f28b9c877788c9082e315dd1f74d7ce12415ae08e
- vocabulary e6948b0b16c8d2c1255403b884fb9b3ecc3e5dea0ddafdfebe7276ef41520a08
- installed bridge e50590509771f141d6f9c47b795076178c3084ff5173f6475dc03a6054979747
- original bridge source 4d3e61e3e0b73a881234df3d897446fb83f47147b6e2ecb9d23d12188ba00a73, same source at E:/Github/lg-game-translator/experiments/madlad-npu/npu_bridge.c and Orange translator-test/ocr-bench/npu_bridge.c.

## Single controlled change

Native/rknn_bridge_experiment includes the ORIGINAL bridge C source by compile definition, avoiding a rewritten recognition/runtime mechanism. Two diagnostic libraries: timed unchanged reference and output-prealloc candidate. Thread-local timing data is solely for isolated sequential benchmark calls. No RKNN per-op profiling flags, model graph changes, core mask changes, FP/math changes or input conversion changes.

Candidate uses the existing SDK-documented rknn_output is_prealloc=1, buf=model->results[i], original float output size. want_float remains 1. The same original output validation runs; self-copy is omitted when RKNN has already written into the result buffer. Existing memcpy otherwise remains. This changes output allocation/copy ownership, not inference parameters.

## Exact gate and timings

For every case: models persistent per width/backend, one warmup per backend, five samples each, alternating backend order. Installed reference, instrumented reference and candidate all compared on SAME preprocessed NumPy inputs. All 18 cases × 3 backends × 5 samples: raw float32 output SHA256 exact, therefore texts/confidence also match. No new recognition errors; original three errors remain. Harness rejects future raw mismatch with nonzero exit, retaining evidence.

Aggregate is median of 18 per-case medians, not pooled latency or full-screen throughput:

| Backend | Recognition call median-of-medians |
|---|---:|
| Installed | 88.684 ms |
| Timed reference | 86.680 ms |
| Preallocated outputs | 85.032 ms |

Candidate faster than installed on 11/18 cases, slower on seven. Production service remained active, so competing NPU work/context switching affects absolute timings; original baseline-only series was faster than the subsequent three-backend A/B. These are not controlled thermal/hardware-isolation measurements. Do NOT promote ~4% aggregate difference as a durable speedup.

Inside the timed native bridges (median of per-case medians):

| Native stage | Reference | Prealloc |
|---|---:|---:|
| rknn_inputs_set | 0.831 ms | 0.829 ms |
| rknn_run | 77.516 ms | 78.572 ms |
| rknn_outputs_get | 3.596 ms | 3.600 ms |
| memcpy output | 0.651 ms | 0 ms |
| outputs release | 0.002 ms | ~0 ms |
| native bridge total | 85.014 ms | 83.419 ms |

Stage medians need not sum to total median. rknn_run includes runtime scheduling/execution; not a pure operator/NPU hardware event trace. Exact eliminated copy cost is modest. Output allocation elimination may affect overhead/cache, but this run does not prove its independently isolated cost.

## Decision / verification

Quality gate PASSES with complete raw-output equality on this corpus. Speed benefit small/inconsistent; candidate NOT installed/default. Original bridge hash rechecked, full-frame service active and translator healthy. Native libraries built with -Wall -Wextra -Werror -fno-fast-math, Python syntax/diff checks passed. All test processes exited, no model changes.

Next experiments should reuse this frozen corpus and numerical gate. Larger reserves: exact pixel OCR cache, native equivalent class-major CTC reduction (~284 ms/frame from prior live profile), or narrower model buckets with a separately stricter quality evaluation. This task did not implement those additional changes.

Files: baseline.json/comparison.json, extra-baseline.json/extra-comparison.json, corpus.tar.gz. Reproducer: scripts/benchmark-ppocr-quality-gate.py, native/rknn_bridge_experiment/CMakeLists.txt. Build requires existing bridge source + matching rknn_api.h + installed librknnrt.so; source/model provenance is mandatory.
