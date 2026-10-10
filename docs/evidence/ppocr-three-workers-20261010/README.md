# Three persistent PP-OCR RKNN workers — 2026-10-10

## Contract

Three owner threads share one bounded FIFO job queue. Each owns its own existing
Engines instance, lazy narrow/wide model contexts, RKNN input/output buffers and
thread-local Tesseract control-icon helper. Core masks are 1, 2, 4 (NPU cores
0, 1, 2). The previous single engine selected mask 7 for each model, using all
three cores for one inference. Models, preprocessing, tensor IO, native CTC,
label mapping, confidence calculation and icon logic are unchanged.

All detected lines from ALL regions are queued before waiting. Results are
assembled in original region/line order. The entire frame drains even on crop
failure before another frame starts; the existing server request lock remains.
The queue permits at most the existing 24 regions x 24 lines. No stale-frame
backlog, new frame capture cadence, translation policy or OSD changes.

One shared exact-pixel RAM cache wraps the worker pool. In-flight identical
mode/model/shape/pixel requests share a Future; even noncacheable empty/error
results reach current waiters, and later requests can retry. SHA index AND full
pixel bytes distinguish both cached and in-flight results. No fuzzy matching.
Cache limits remain 16 MiB/256 entries; transient queued frame memory is separate.
`shared_waits` counts duplicate jobs awaiting an existing computation; these jobs
do not increment recognize_calls. Worker completed_jobs counts queue tasks,
including cache hits/waiters, not just hardware invokes.

## Native bridge/build

native/rknn_core_bridge includes the exact previously deployed original bridge
source and adds ONLY npu_set_core(model_t*, mask) calling rknn_set_core_mask. No
preallocation, fast-math or kernel/model modification.

```sh
cmake -S native -B build -DCMAKE_BUILD_TYPE=Release \
  -DBRIDGE_REFERENCE_SOURCE=/home/orangepi/translator-test/ocr-bench/npu_bridge.c \
  -DRKNN_HEADERS=/home/orangepi/translator-test/ocr-bench \
  -DRKNN_LIBRARY=/home/orangepi/lg-game-ocr-runtime/assets/librknnrt.so
cmake --build build -j2
```

Deployed directory: /home/orangepi/ppocr-parallel-experiment-20261010/.
Original C source SHA256: 4d3e61e3e0b73a881234df3d897446fb83f47147b6e2ecb9d23d12188ba00a73.
Original installed bridge remains intact: e50590509771f141d6f9c47b795076178c3084ff5173f6475dc03a6054979747.
New core-selection library: d1d6574d074205fc7503ad86fda6602020929cf810af9d928bc471102c44440b.
Python reuses existing Runtime/Model bindings; sets mask before first Invoke.
Private context buffers are never concurrently used by two threads.

## Quality gates

18 frozen difficult crops: original installed engine vs each of masks 1/2/4.
All raw float32 output SHA256 hashes, status and complete TSV exact. Another
18-crop batch runs concurrently through the actual queue: raw outputs and TSV
also exact. Known baseline OCR mistakes remain; this does not improve accuracy.

Three complete saved frames: one warmup per mode, five alternating sequential /
three-worker passes, without the crop cache. All regions, line order, text,
confidence and coordinates exact. Fresh-cache and repeated-cache parallel passes
also exact. Actual installed authenticated endpoint: six requests per fixture;
all regions AND lines (including appearance and pretranslation policy) match the
previous single-worker archived endpoint. comparison.json and endpoint.json.

The first diagnostic attempt had a benchmark hook lifecycle bug: raw capture
was removed before the concurrent gate. Corrected harness rerun passes. That
attempt is not treated as a numerical mismatch or a performance result.

## Full OCR timings to text, excluding network/translation/OSD

| Saved frame | Sequential median | Three-worker median | Speedup |
|---|---:|---:|---:|
| current.png (large text) | 2080.82 ms | 1181.64 ms | 1.76x |
| Emergency | 1925.93 ms | 952.09 ms | 2.02x |
| Luigi | 1349.84 ms | 666.35 ms | 2.03x |

Production service continued running during paired tests. These are alternating
same-frame measurements, not isolated NPU throughput or physical screen onset.
Warmed final endpoint repeats with cache: medians 111.11 / 109.69 / 109.02 ms; exact
cache-hit path still skips NPU. Extra workers benefit new/changed crops, not hits.
All three workers received jobs (benchmark final counts 142/159/149).

Observed process RSS before: 418960 KiB; after three workers and both bucket
models warm: 772868 KiB (~755 MiB). MemAvailable afterwards 5837604 KiB; no RAM
capacity shortage observed. Shared DRAM bandwidth remains a throughput constraint.

## Deployment/rollback

Default user unit explicitly selects PP_OCR_RECOGNIZER_WORKERS=3 and
PP_OCR_CORE_LIBRARY=%h/ppocr-parallel-experiment-20261010/build/librknn_core_bridge.so.
Scripts copied to the existing full-frame working directory, user unit reloaded
and restarted, service active, translation /api/health status OK. Actual endpoint
reports masks [1,2,4] and increasing job counts on all workers. Existing original
crop service/runtime bridge not modified. Backup scripts and unit in before/.

Rollback: remove the two new environment settings (or workers=1), reload user
unit and restart lg-game-ppocr-full.service. Native CTC and exact cache still work
in the sequential path. Original bridge remains available. Sequential diagnostic
StageProfiler explicitly rejects parallel operation rather than corrupting stage
attribution; ordinary frame timing remains available.

16 targeted host tests pass, covering actual simultaneous ownership, four
separate one-line regions, output order, job exceptions, startup/shutdown failure,
in-flight duplicate success/error propagation and previous cache/policy/OSD gates.
No reboot/long thermal endurance test or new physical OSD quality proof claimed.

## Live chain

After the Orange restart the prior TV relay/capture session did not publish fresh
frames. Relay and PicCap process were restarted, preserving getSettings:
1280x720, fps=60, ocr=true, nogui=true. Capture resumed; returnValue:false from
the subsequent start call was not treated as success proof, actual videoRunning
and fresh sequences were verified. No TV reboot performed.

Ten actual fresh frames (sequences 12–21, 17–19 regions): all report masks [1,2,4]
with jobs increasing on each worker. OCR median 256.22 ms (177.57–1537.87), frame
to returned text median 432.31 ms (288.29–1706.59). First frame had 19 misses;
later frames 0–7 misses and 10–19 hits. This mixes cold recognition and cache,
not a paired live speedup or MADLAD uncached generation estimate. Capture status
connected/videoRunning, 57.53 FPS. OSD admission/active-pair files updated.
live.json retains these measurements; saved-frame pairs above isolate the gain.

Final module has worker completion counters updated before its task Future is
resolved, avoiding diagnostic counter races. Final endpoint rerun and 16 host
tests pass after this refinement; tensor/inference code unchanged. Six existing
Orange server tests and one malformed LZ4 frame regression also pass (expected
negative-path error logging).
