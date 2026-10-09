# PP-OCR stage profile — 2026-10-09

Optional timing wrappers around unchanged installed PP-OCRv6 small NPU runtime. Native PicCap detector/line geometry, crop extraction, exact preprocessing, original Model.__call__, original C lib npu_run, original decode/preserve calls and TSV parsing retain their inputs/results. No new arithmetic, shape changes, model or thresholds. `PP_OCR_PROFILE_STAGES=1` is opt-in. Profiler requires sequential pipeline; wrappers are scoped to one test process/worker and restored at close.

## Saved frame validation

Separate test process, three saved inputs, warm all model buckets first, five repeats each. Every profiled output region/text/coordinates/confidence matched uninstrumented reference exactly. Saved timings were elevated by concurrent production NPU work, therefore not used as normal operating latency. `saved-contention.json` preserves that evidence; it must not be mixed into live totals.

## Live operating measurement

Temporarily enabled profiler inside the existing persistent full-frame unit using stage-profile.conf user-service drop-in. No second active benchmark recognizer. Excluded initial cold-model frames (model_load calls). Five fresh frames: 17–19 regions, 18–20 line crops, one Tesseract-assisted control-icon check per frame. See live.json for per-frame sums/call counts. Times below are medians of whole-frame stage totals, not per-crop latencies.

| Stage | Median |
|---|---:|
| RGB-to-gray | 9.659 ms |
| Existing detector, includes native preprocessing/postprocess | 123.263 ms |
| Line/crop geometry extraction | 0.587 ms |
| Copy/cut all grayscale crop pixels | 0.581 ms |
| All recognizer resize/normalization/padding | 10.713 ms |
| Native RKNN npu_run bridge | 1424.979 ms |
| Python binding/input-output copy/nonfinite checks around bridge | 39.744 ms |
| Original CTC decoding, vocabulary/argmax/confidence/text | 284.325 ms |
| Control-icon preservation, inclusive | 155.083 ms |
| TSV text/confidence assembly | 0.557 ms |
| Full OCR | 2092.434 ms |
| Frame transport start to returned OCR text (LZ4) | 2204.439 ms |

NPU bridge time includes native runtime input/output handling, NPU execution and any runtime waits; it is not pure isolated hardware operator time. Inclusive Python NPU call median 1462.313 ms contains the bridge and must not be added to it. Icon preservation contains Tesseract geometry, subset median 154.546 ms, also not additive. Stage medians do not sum exactly to median total; other engine orchestration and Image.frombytes work remain in unallocated overhead.

Current live profile confirms cutting/preparing crops is small (<12 ms total) compared with NPU and CTC. Pipelining only this preparation cannot save hundreds of milliseconds on these frames. Main candidates for subsequent independent tests: avoid unchanged crop recognition via exact pixel cache, reduce decoding/binding memory overhead without changing argmax/text. No optimization or timing improvement claimed by this profiling step.

## Cleanup / verification

Temporary user-service stage-profile.conf removed, manager reloaded, full-frame service restarted active, translator health OK. Profiling defaults off; regular runtime remains active. Optional code and original arithmetic preserved. Three frame-contract tests and Python syntax/diff checks passed. Exact saved-frame validation ran on Orange for all fifteen measured passes. Tesseract ObjectCache shutdown warnings belong to the exited standalone test; no claim of active-service memory leak is made.
