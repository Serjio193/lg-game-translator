# Live selected-frame to Orange detector latency

2026-10-09. Ten updating live frames, 16–17 regions. Existing full-frame PP-OCR pipeline, native PicCap detector on Orange, PP-OCRv6 small NPU, policy and OSD remain selected. No model/threshold/capture-resolution change. Timing instrumentation only; workers restarted and transport tests passed.

## Measurement definition

Start is PicCap OCR producer's `last_submit_us`, recorded at the selected frame's submission before grayscale/RGB copying. It is NOT a timestamp of physical light emitted by the TV panel, nor first appearance of a newly changed sentence. The producer currently samples at OCR_INTERVAL_US; time before selection is not included. Waiting while a previous OCR/translation completes can affect the age of the queued frame.

TV relay records its own monotonic time immediately after receive_frame. The native detector's completion is recorded on Orange using local perf_counter. At reply construction, Orange computes duration from detector completion to response preparation. TV subtracts that server duration from the entire frame request duration (including materialization/hash). The remaining relay_to_detector_upper_ms includes outbound delivery, Orange preprocessing/queue/detection, response network transfer, response serialization and client processing. Therefore it is a conservative upper-bound estimate, not an exact synchronized one-way measurement. No TV/Orange absolute clocks are subtracted.

Deployed ARM32 PicCap utils.c computes `tp.tv_sec * 1000000 + tp.tv_nsec / 1000` before conversion to uint64; saved timestamp can be sign-extended/wrapped. Existing header value was enormous, e.g. 18446744073023026 ms. capture_timing.py restores its modulo-2^32 microsecond value to the nearest TV monotonic epoch and accepts only ages within 60 seconds. Truncation loses less than 1 ms. Two tests cover signed/multiple wraps and normal/missing timestamps. Native capture code was not patched in this task. Telemetry explicitly labels legacy recovery; this is a source-backed compatibility reconstruction, not a repair of all former time arithmetic.

## Observed results

| Stage | Median | Range |
|---|---:|---:|
| Selected capture to TV relay receipt | 669.4 ms | 49.5–954.6 ms |
| TV relay to detector completion upper estimate | 306.4 ms | 287.2–460.9 ms |
| Selected capture to detector upper estimate | 1077.8 ms | 437.5–1252.2 ms |
| Orange detector alone | 125.1 ms | 110.2–260.7 ms |
| TV materialization/hash | 21.4 ms | 19.8–25.7 ms |
| Frame network overhead estimate | 128.4 ms | 120.4–142.6 ms |
| Orange RGB to gray | 18.7 ms | 9.4–20.6 ms |
| Orange frame decode | 6.4 ms | 3.7–6.6 ms |

Stage medians do not add to median whole transaction. RPC network overhead includes response handling and is not measured one-way latency. First collection had no new frames; after user opened game text, ten fresh sequences 598–615 were retained. These are live observations, not a thermal/large-corpus benchmark. No before/after speedup claimed.

## Next optimization candidate

Investigate the existing one-slot producer/consumer sampling cadence. Preserve source frame identity and avoid sending a stale selected frame when worker becomes free. Do not solve this by blindly converting/copying full frames at panel FPS: that could increase capture CPU load. Queue/sampling change should be evaluated independently with the same new timing fields. Native detector speed is a secondary reserve here.

Verification: six lossless frame relay tests, six integration tests, two timestamp tests passed. JSON raw series contains all timing fields. OCR/translation arithmetic and filtering were not changed. Actual panel-to-detector latency or response to first appearance remains unmeasured.
