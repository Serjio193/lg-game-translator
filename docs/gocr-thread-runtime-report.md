# G5 detector/recognizer thread investigation — 2026-10-09

Scope: unchanged Google assets/config, system TFLite 2.17.0, XNNPACK off,
isolated TV_FULL runtime. No capture, OSD, production service or default thread
selection was changed. New independent execution options preserve legacy
`--threads 2` behavior.

## Experiment

`scripts/profile-gocr-threads.py` launches a **fresh process for each pair**.
Emergency Guard is unchanged from the previous evidence. Each child measures:

1. Detector only, before constructing recognizer.
2. The same detector after constructing recognizer in the same process.
3. Recognition of every rectified line, sequentially.
4. Complete one-call native TV_FULL.

Each stage uses warmups, then three measured observations. `/proc/self/task`
snapshots bracket measurements and record thread CPU ticks, voluntary and
involuntary switches, migrations, processor, process memory, frequency and
affinity. No sampling thread competes with inference. A repeated 2/2 run at
the end bounds session drift. Benchmarks exclude translation/display.

## Median milliseconds

Detector column includes native preprocessing/decode/postprocess overhead;
recognizer column includes all lines/windows, not one crop.

| Detector / recognizer | Detector alone | Detector with recognizer loaded | Recognizer only | Full OCR |
|---|---:|---:|---:|---:|
| 2 / 2 | 1375 | 1402 | 563 | 1948 |
| 4 / 4 | 1469 | 1490 | 3360 | 4886 |
| 4 / 1 | 1475 | 1467 | 651 | 2166 |
| 4 / 2 | 1499 | 1485 | 461 | 1937 |
| 3 / 1 | 1369 | 1397 | 609 | 2002 |
| 2 / 1 | 1328 | 1350 | 597 | 2314 |
| 2 / 2, repeated | 1401 | 1397 | 439 | 1957 |

The best mixed pair, 4/2, differs from 2/2 by only ~11 ms (~0.6%). Three samples
and uncontrolled TV background activity do not establish that as a real gain.
The 2/1 full pass had a slow recognizer sample and detector variation; do not
predict its full total by summing independently measured stage medians.

## What the measurements establish

- Four-thread detector slowdown exists **before recognizer creation**. Loading
  recognizer does not create the former 700→1400 ms jump in this experiment.
- Same-session pure C++ executable, no Python or recognizer, ten warmed Invokes:
  **2 threads median 1312.83 ms; 4 threads median 1429.09 ms**. The earlier
  ~707 ms four-thread result is not reproduced in current operating conditions.
- `profile-gocr-invoke-boundary.py`, four-thread detector, ten warmed samples:
  cached-input Invoke median 1378.06 ms before recognizer, 1465.54 ms after;
  prepare+Invoke median 1496.90 / 1556.41 ms. Neither Python binding nor fresh
  input preparation explains a current 2× speed difference.
- The large 4/4 regression resides mainly in recognizer execution. All seven
  detector-created worker TIDs record **zero additional CPU ticks** while
  recognizer-only calls execute. Tick resolution is 10 ms; this bounds observed
  CPU activity rather than proving absolutely zero execution.
- Recognizer phase, three passes: 2/2 consumes about **2.50 CPU seconds** over
  1.58 wall seconds; 4/4 consumes **16.87 CPU seconds** over 10.08 wall seconds.
  4/4 also records 13,593 voluntary and 16,747 involuntary switches, 219 thread
  migrations. Same input-window hashes mean the increase is not extra OCR work.
- Thread counts after detector warmup: 4 tasks at detector=2, 6 at detector=3,
  8 at detector=4 (including main). After recognizer warmup: 5 tasks at 2/2,
  11 at 4/4. Requested thread count is not the process's total task count.
- Destruction returns the process to one task. These pools persist while
  interpreters exist and are released when destroyed; they do not leak through
  this lifecycle test.
- The dedicated Invoke probe shows all threads allowed CPUs 0–3, nice=0,
  ordinary scheduling policy, and 1.4 GHz CPU frequency at snapshot boundaries.
  Global CPU activity over the probe intervals was about 85.7–87.6%, including
  the benchmark. Boundary frequency snapshots cannot rule out subinterval
  frequency changes. No affinity restriction was observed.

The evidence supports excessive scheduling/synchronization cost **within the
four-thread recognizer path**, not detector workers busy-spinning during
recognition. Background contention can contribute; the exact responsible kernel
or synchronization primitive is **not identified**. `perf` is not installed on
this TV. No global tracing controls, scheduler tuning or background production
services were changed to make a benchmark favorable.

## Quality and parity

Every configuration preserved all 21 recognized texts and normalized input-window
hashes on Emergency Guard. Every repeated sample within each configuration had
identical output.

Cross-thread detector results are **not strictly byte-identical**: detector=4
changes two line quads by roughly 1e-6 px and changes one RGB crop hash, while its
recognizer-window hash remains equal. The saved matrix's strict `parity:false`
is retained honestly. Detector=3 also has tiny geometry differences; crop/window
hashes and texts match. This is not a change to thresholds, anchors or grouping.
No cross-thread strict-parity assertion was weakened or relabeled as passing.

## Independent execution controls

Added to `FullGocrWorker` and forwarded through `FramePipeline`, TV server and
OCR benchmark server:

```bash
python3 -m gocr_worker.worker_full --assets /opt/gocr/assets \
  --detector-threads 4 --recognizer-threads 2 image frame.ppm

python3 -m gocr_worker.tv_server --assets /opt/gocr/assets --mode TV_FULL \
  --detector-threads 4 --recognizer-threads 2 \
  --translator http://translation-server:8765 --socket /tmp/gocr-frame.sock
```

Legacy `--threads` is the fallback for each unspecified count. Overrides accept
1–4; invalid values fail before interpreter construction. `--recognizer-threads`
is TV_FULL-only; TV_CROP recognition is configured on the Orange worker.
These are execution controls, not Google OCR parameter tuning. Default remains
**detector 2 / recognizer 2**: there is no convincing speed gain or strict parity
proof supporting a change to four-thread detector today.

Verification: 28 tests passed on G5; 18 backend/integration tests passed on
Windows; modified Python modules compile. Unix-socket server `--help` was tested
on G5. Windows lacks `socketserver.UnixStreamServer`, so this platform-specific
server is not runnable there; no unrelated portability rewrite was performed.
No C++ code or native binary changed in this stage.

Evidence: [thread matrix and runtime probes](evidence/gocr-thread-matrix-20261009/README.md).
