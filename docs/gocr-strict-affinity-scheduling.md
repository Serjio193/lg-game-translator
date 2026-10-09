# STRICT affinity and scheduling on LG G5

## Scope

Only `/usr/lib/libtensorflow-lite.so` is used, detector 2 threads / recognizer
2 threads, XNNPACK off. The existing native detector, postprocess, rectification
and recognizer binaries are reused without rebuilding. No model, original Google
binarypb, kernels, FP flags, capture, API, OSD or production settings are changed.

Runtime SHA-256:
`cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138`.
The comparison is against this project's STRICT reference, not a Google-native
quality oracle.

## Measurement method

Evidence: `docs/evidence/gocr-strict-scheduling-20261009/`.

1. Read-only topology/system load snapshot, then unmodified scheduling baseline.
2. Fresh process per candidate; create original detector and recognizer with 2/2
   threads. Identify new TIDs before/after first detector/full invocation.
3. One warmup per condition per frame. Ten baseline and ten candidate full OCR
   observations per frame, alternating order. Detector Invoke comes from the
   existing native timer inside full OCR, not wall time around Python. Full OCR
   ends at recognized text, with translation and OSD excluded.
4. Initial audit also records ten isolated Invoke observations per frame.
5. A separate observer samples `/proc/PID/task/TID/{stat,status,sched,schedstat,wchan}`
   and sysfs frequencies every nominal 50 ms. Counter snapshots and hash checks
   are outside the timing interval. Trace polling is not an exact wakeup/CPU
   scheduling trace: core transitions are lower bounds and state samples can miss
   short sleeps. Exact kernel `se.nr_migrations` is reported separately.
6. All changes target only discovered TIDs under `/proc/self/task`. No system or
   production PID is modified. Original masks, scheduler policy and nice value
   are restored and checked before the test process exits. Realtime is prohibited.

Variants: all six two-core process masks, main 0 / all model workers 1,
main + three detector-owned TIDs on separate cores 0/1/2/3, nice -5/+5 and
SCHED_BATCH. The process mask variant applies to every discovered TID; Linux
`sched_setaffinity(pid, ...)` alone would only affect the main thread.

Commands (in isolated `/media/developer/gocr-runtime`):

```sh
python3 -B scripts/benchmark-gocr-strict-scheduling.py \
  --topology --output strict-scheduling-experiment/topology.json
python3 -B scripts/benchmark-gocr-strict-scheduling.py \
  --assets assets --output strict-scheduling-experiment/matrix \
  --variants pair_0_1,pair_0_2,pair_0_3,pair_1_2,pair_1_3,pair_2_3,main_worker_0_1,detector_spread,nice_-5,nice_5,batch \
  --modes full fast-corpus/11-gocr-native-postprocess-20261009-emergency-guard.ppm \
  fast-corpus/12-gocr-native-postprocess-20261009-luigi.ppm
```

## CPU and runtime thread evidence

Four online cores 0–3 have identical implementer 0x41, part 0xd41, variant 1,
revision 2. One shared policy exposes only 1400000 kHz; schedutil governor;
minimum/maximum are both 1400000 kHz. No thermal-zone, cooling-device or hwmon
sensor temperatures were exposed. Hardware throttling is therefore unknown.
No DVFS or governor changes were made.

The initial two-second read-only load snapshot had approximately 38–43% busy on
all cores. `hyperion-webos` (PicCap) and `hyperhdr` were the largest users, followed
by `pqcontroller` and `WebAppMgr`. Their sampled last CPU is not a permanent core
assignment. An apparently less busy core in a two-second sample is not an idle
reserved core.

Detector creation itself added no TID. First detector Invoke added three TIDs;
first recognizer/full Invoke added one more. Main thread PID is known exactly.
Detector-owned and recognizer-owned TIDs are determined by this lifecycle, not
by the `python3` comm name. Existing kernel profiling proves use of the Eigen
threadpool, but does not prove which of the three detector-owned TIDs belongs to
which internal Eigen/gemmlowp pool. This experiment does not interpose pthread
creation or change kernels to assign names. The exact pool-to-TID mapping remains
unknown.

Initial isolated Invoke audit: main ~0.993 s CPU, detector workers ~0.891,
0.175 and 0.173 s CPU per Invoke, recognizer-only worker idle. Model thread count
2 is not the number of all runtime pthreads: the existing runtime creates more
than one pool. Sleeping workers predominantly report `futex_wait_queue`.

The original audit parser retained padded `/proc/sched` keys, so its migration
counter was unavailable (null), not zero. The parser was corrected with a
regression test. Later traces/counter reports use stripped keys. Sampled CPU
histories from the original audit remain valid. A repeat audit supplies exact
migration counters; no absent counter is substituted with zero.

## Parity gate

Every measured observation saves four exact input hashes and all eleven output
hashes. Every full OCR observation compares quads, angles, scores, crop SHA,
recognizer input-window SHA and UTF-8 against the same frame's fresh STRICT
reference. Decoded proposals, deduped pieces and component membership are
exported and compared outside timing; reference arrays are included in evidence.
Timing fields alone are excluded from semantic comparison.

A candidate with any raw tensor difference is rejected regardless of its text.
This gate establishes parity with the project's existing numerical path, not
with Google Lens. Changing scheduling must not be used to excuse a tensor mismatch.

## Results

### Two-frame screening (with polling observer)

Times in milliseconds; each entry is median / p95. Each candidate has its own
alternating, unpinned SCHED_OTHER nice=0 baseline. Different rows were collected
at different times; compare within a row.

| Variant | EG Invoke baseline | EG Invoke candidate | Luigi Invoke baseline | Luigi Invoke candidate |
|---|---:|---:|---:|---:|

| pair_0_1 | 1427.73 / 1641.96 | 1457.91 / 1514.06 | 1424.35 / 1581.20 | 1400.14 / 1451.50 |
| pair_0_2 | 1407.45 / 1535.72 | 1392.30 / 1482.16 | 1420.85 / 1439.56 | 1414.69 / 1454.33 |
| pair_0_3 | 1385.11 / 1632.98 | 1382.86 / 1633.30 | 1487.13 / 1687.98 | 1456.17 / 1609.87 |
| pair_1_2 | 1468.29 / 1640.14 | 1393.87 / 1521.67 | 1427.68 / 1618.40 | 1388.53 / 1460.60 |
| pair_1_3 | 1389.08 / 1473.67 | 1376.97 / 1505.27 | 1524.55 / 1697.94 | 1458.68 / 1927.60 |
| pair_2_3 | 1423.04 / 1593.26 | 1437.44 / 1554.46 | 1413.98 / 1538.51 | 1391.47 / 1476.94 |
| main_worker_0_1 | 1420.79 / 1511.60 | 1479.03 / 1593.54 | 1411.46 / 1997.25 | 1570.24 / 1682.23 |
| detector_spread | 1386.61 / 1459.32 | 1488.63 / 1796.85 | 1458.37 / 1574.78 | 1471.94 / 1575.00 |
| nice_-5 | 1382.80 / 1548.64 | 1187.66 / 1245.81 | 1418.92 / 1528.29 | 1209.73 / 1263.16 |
| nice_5 | 1429.98 / 1492.53 | 1577.17 / 1631.63 | 1521.27 / 1795.29 | 1725.25 / 1924.94 |
| batch | 1519.28 / 1678.20 | 1468.23 / 1577.32 | 1470.86 / 1512.05 | 1474.63 / 1677.51 |

SCHED_BATCH has no consistent benefit across both frames; nice +5 is slower.
Affinity pairs give small/mixed effects. nice -5 is the screening winner.
All screening frames passed numerical/semantic gates and all restores succeeded.

Full OCR median / p95:

| Variant | EG baseline | EG candidate | Luigi baseline | Luigi candidate |
|---|---:|---:|---:|---:|
| pair_0_1 | 1963.32 / 2231.35 | 2030.97 / 2181.89 | 1938.70 / 2033.48 | 1916.70 / 1999.33 |
| pair_0_2 | 2006.65 / 2078.03 | 1980.23 / 2084.43 | 1877.68 / 1943.11 | 1894.99 / 1985.13 |
| pair_0_3 | 1998.63 / 2208.97 | 1977.97 / 2511.53 | 2010.68 / 2190.18 | 2060.41 / 2226.85 |
| pair_1_2 | 2073.53 / 2259.15 | 2054.39 / 2187.02 | 1903.31 / 2134.06 | 1875.20 / 1937.80 |
| pair_1_3 | 1962.09 / 2070.07 | 1937.03 / 2134.09 | 2043.51 / 2532.10 | 1956.79 / 2335.46 |
| pair_2_3 | 2121.02 / 2224.47 | 2093.32 / 2267.69 | 1933.42 / 2008.76 | 1904.71 / 2026.81 |
| main_worker_0_1 | 2019.90 / 2100.16 | 2051.88 / 2318.62 | 1920.69 / 2469.90 | 2042.61 / 2175.93 |
| detector_spread | 1973.15 / 2249.08 | 2110.46 / 2384.74 | 1937.33 / 2080.55 | 1978.01 / 2028.87 |
| nice_-5 | 1947.75 / 2095.77 | 1669.17 / 1721.26 | 1969.86 / 2080.39 | 1637.86 / 1710.22 |
| nice_5 | 2037.15 / 2177.47 | 2230.89 / 2326.41 | 2081.06 / 2413.86 | 2295.31 / 2482.90 |
| batch | 2159.91 / 2392.38 | 2105.41 / 2172.96 | 1947.71 / 2066.70 | 1943.01 / 2189.76 |

### Persistent placement diagnostic

`validation/persistent-detector-tids.json.gz`: one warmup then ten uninterrupted
Invoke and ten full OCR calls per frame, fixed masks throughout. Main and the
three detector-owned TIDs each have a unique core. Their kernel migration count
is **zero in all 40 observations**. TID set and masks persist; all parity gates
and restoration checks pass. This diagnostic is not an alternating latency A/B
and does not establish a speedup. In alternating A/B screening, spread placement
was slower. The isolated migration remaining there is a forced placement change
when a previously sleeping worker first wakes, not an automatic affinity reset.

### Priority telemetry from screening

Numbers below are mean sums across all test TIDs per full OCR call. CPU-time and
runqueue sums across concurrent threads are not wall-clock latency.

| Frame | Policy | Runqueue sum ms | Involuntary switches |
|---|---|---:|---:|
| Emergency | baseline | 532.52 | 4235.4 |
| Emergency | nice_-5 | 204.12 | 2329.3 |
| Luigi | baseline | 626.08 | 4005.9 |
| Luigi | nice_-5 | 318.04 | 2221.2 |

### Final 13-frame validation, observer disabled

`validation/corpus-nice_-5.json.gz`: 13 frames, one warmup per condition/frame,
10 baseline + 10 nice=-5 observations per frame in alternating order. No
polling process runs during this series. Per-call before/after snapshots and
exact parity checks remain outside the native timing interval.

| Metric | Baseline median / p95 ms | nice=-5 median / p95 ms | Median speedup |
|---|---:|---:|---:|
| Invoke | 1360.18 / 1536.77 | 1226.17 / 1322.13 | 1.109x |
| Full OCR | 1562.14 / 1955.60 | 1376.04 / 1743.57 | 1.135x |

Pooled values contain 130 observations per condition with equal frame weights.
Per-frame medians (detector Invoke / full OCR milliseconds):

| Frame | Baseline Invoke | nice=-5 Invoke | Baseline full | nice=-5 full | Exact parity |
|---|---:|---:|---:|---:|---|
| 00-description-screen-20261006-capture.ppm | 1370.46 | 1216.82 | 1560.97 | 1362.90 | True |
| 01-description-screen-20261006-current-full.ppm | 1339.88 | 1254.10 | 1771.30 | 1608.19 | True |
| 02-font-matching-20261007-source-frame.ppm | 1350.47 | 1234.61 | 1535.05 | 1377.29 | True |
| 03-ocr-candidates-20261007-live-frame.ppm | 1341.15 | 1216.61 | 1493.92 | 1337.76 | True |
| 04-ocr-fullscreen-discussion-20261005-screen.ppm | 1339.92 | 1219.82 | 1875.08 | 1723.59 | True |
| 05-ocr-policy-live-20261005-frame.ppm | 1359.01 | 1221.83 | 1503.75 | 1364.25 | True |
| 06-ppocr-only-live-20261007-frame.ppm | 1404.77 | 1234.90 | 1524.98 | 1347.10 | True |
| 07-text-detectors-video-only-input.ppm | 1336.68 | 1232.04 | 1356.29 | 1252.29 | True |
| 08-game-input.ppm | 1353.24 | 1215.45 | 1451.74 | 1301.34 | True |
| 09-game-brothership-input.ppm | 1348.10 | 1219.27 | 1487.77 | 1346.20 | True |
| 10-game-example-2-input.ppm | 1376.64 | 1211.98 | 1773.25 | 1546.85 | True |
| 11-gocr-native-postprocess-20261009-emergency-guard.ppm | 1378.87 | 1236.10 | 1908.23 | 1705.50 | True |
| 12-gocr-native-postprocess-20261009-luigi.ppm | 1484.47 | 1241.13 | 2068.97 | 1654.10 | True |

All 13 per-frame Invoke medians improve, by ratios 1.068x–1.196x.
The median of frame medians is 1353.24 → 1221.83 ms for Invoke.
This is a sustained observed gain under the measured background load, not a
guarantee of the same gain on an otherwise idle TV.

Final full OCR per-thread counter sums, mean over 130 observations per condition:

| Counter | Baseline | nice=-5 |
|---|---:|---:|
| migrations | 5.58 | 2.19 |
| voluntary | 141.25 | 93.88 |
| involuntary | 3266.67 | 1997.19 |
| runtime ms | 2635.24 | 2558.19 |
| runqueue ms | 467.78 | 256.75 |

The observed gain accompanies less runnable wait and fewer preemptions.
These are scheduling/cache-pressure observations; the model arithmetic is
unchanged. Priority is applied to main + three detector-owned + one
recognizer-owned TID, so the full OCR improvement is not detector-only priority.
Detector and recognizer interpreter thread counts remain 2/2.

## Final parity and environment limits

- 13/13 frames pass. Four input hashes and all 11 output hashes match in every
  one of 130 candidate full OCR calls (143 distinct frame/head references,
  1430 candidate output-hash comparisons).
- Decoded proposals, deduped pieces, components, source quads, crop hashes,
  recognizer input-window hashes and all UTF-8 strings match exactly. Every
  final validation call also repeats the full proposal/component comparison.
- Every experiment retains the same persistent worker set. Before/after masks
  and sampled masks show no automatic affinity reset by the runtime. All
  restoration checks succeed; every test process exits.
- Original system runtime and detector/recognizer binary hashes are unchanged.
  No native code, model or config is rebuilt or edited.
- Frequency samples remain 1400000 kHz on all cores. Thermal temperature and
  hidden hardware throttling are unknown: no usable thermal sensor is exposed.
- Baseline changed during the series. Initial isolated Invoke medians were
  1399.50/1394.02 ms; later repeat was approximately 1305 ms on Emergency.
  HyperHDR PID changed from 11279 to 29677 between the initial and final
  snapshots. The experiments did not restart it. A capture status observation
  during the audit showed connected=false / 53.25 FPS; after all tests it
  showed connected=true / 58.48 FPS, running/elevated=true. The cause of the
  external background change is not established. Alternating local baselines
  are essential; comparisons across different sessions are not causal evidence.
- `topology-final.json` additionally samples PicCap/HyperHDR/WebAppMgr TIDs:
  runnable PicCap threads were observed on cores 0,1,3, WebAppMgr on 2,3 and
  HyperHDR on 0 in this short observation. No core is permanently reserved;
  final per-core busy fractions span 53–65%. State R means runnable, not proof
  that the thread was executing at the precise sample instant.

## Conclusion and integration decision

Affinity alone is not a useful optimization on this workload. Persistent
unique-core placement removes detector migrations completely but does not
improve the alternating latency comparison.

An explicit experimental STRICT scheduling option for CFS nice=-5 is worth
a separate integration: final corpus Invoke is 1.360 → 1.226 s (1.109x;
9.9% lower latency), full OCR 1.562 → 1.376 s (1.135x; 11.9% lower latency).
No tensor or recognized result changes were found. Keep normal affinity; do
not combine the winning priority with an unvalidated core mask.

This change only adds isolated benchmark/controller tools; it does not integrate
priority into the production worker or enable it by default. Future opt-in
integration should verify live capture/UI responsiveness under representative
load and preserve restoration/lifecycle boundaries. No realtime policy was used.

Host and G5: 41 targeted unit/regression tests passed. Evidence is compressed
losslessly as `.json.gz`; the analysis script reads both plain and gzip JSON.
