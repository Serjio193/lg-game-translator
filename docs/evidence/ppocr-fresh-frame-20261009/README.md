# Fresh-frame demand sampling — 2026-10-09

Explicitly authorized live fix. PicCap frame producer previously refreshed the OCR slot at most once per second while OCR/translation consumed an older local snapshot. When the consumer became free, it could immediately process an already-aged pending frame. New demand-only scheduling applies only to the selected-frame socket chain. Consumer requests its next frame after completion; producer copies only when requested and one-second cadence permits. It retains trylock/nonblocking capture, bounded buffers and no more than one selected frame per second. Old local PP-OCR path retains periodic producer behavior.

Changed existing PicCap source files:
- unicapture/ocr_frame_schedule.h: mutex-owned request/due/submitted helpers.
- unicapture/ocr_worker.h and ocr_worker.c: request the next fresh frame; reject unrequested samples before gray/RGB copy; cadence decision now under frame mutex.
- src/utils.c: cast timespec seconds to uint64 before multiply, fixing deployed ARM32 signed overflow in monotonic microseconds.
- tests/ocr_frame_schedule_test.c and tests/utils_time_test.c: demand/cadence/legacy regression and 5000-second timestamp overflow.

All existing working-tree changes preserved. Worker is 416 lines; no source over 500 lines introduced. No Google/PP-OCR model, inference arithmetic, thresholds, grouping, recognition, translation policy, resolution or OSD renderer modifications in this step. Selected frame changes intentionally; no byte-parity claim between different live frames.

## Tests / build / deployment

Both standalone tests built with -Wall -Wextra -Werror, passed on host and on real ARM32 TV. Existing complete ARM32 hyperion-webos build succeeded. Staged/installed SHA256 0d48ddf6ad0935d361421b536e6078a7f73bea8583b07404ea13ae4e0920c985 matched. Previous executable preserved as hyperion-webos.before-fresh-frame-20261009, SHA256 2605f977403540bee1e7c59c313ebf3f3bcf4b3436490125acadaff92d2dab6d. Atomic installed replacement followed by SIGTERM and service activation; capture recovered connected/videoRunning and 59.64 FPS. Startup/default routing unchanged. A transport BrokenPipe during service restart is historical; subsequent ten live responses updated successfully. Existing active OSD pairs remain.

## Ten-frame live before/after

Same active Command Blocks game screen, dynamic illustration. Not identical saved input frames, not randomized long thermal A/B. Frame counts 16–17 regions in both series. Before has source-backed legacy timestamp recovery; after uses normal monotonic_ms directly. Values are medians; detector endpoint is upper estimate including return overhead, as described in ../ppocr-detector-latency-20261009/README.md. Physical panel onset/sampling-before-selection remain unmeasured.

| Measurement | Before | After |
|---|---:|---:|
| Selected frame to TV relay receipt | 669.40 ms | 27.66 ms |
| Relay to detector upper estimate | 306.40 ms | 301.44 ms |
| Selected frame to detector upper estimate | 1077.76 ms | 329.06 ms |
| Detector alone | 125.08 ms | 138.66 ms |

After selected-frame-to-detector range: 298.14–513.18 ms; frame-to-relay 24.81–29.88 ms. Median detector alone did not accelerate. Main improvement is age/queue elimination, about 642 ms median at the relay; whole endpoint median reduction ~749 ms (69%). These differences are live observed series, not a general 3.3× speedup of OCR inference.

Current relay-start-to-OCR-text median 1868.39 ms, cached whole response 1893.23 ms. These exclude age at the native producer and are not a new physical panel-to-OSD benchmark. Full recognition/translation latency optimization remains separate. No capture CPU/RAM load or long-session thermal conclusion beyond preserved cadence and observed FPS.
