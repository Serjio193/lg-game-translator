# Full Google OCR on Orange Pi: isolated CPU experiment

Date: 2026-10-09. Production was not switched. No TV capture, API, OSD,
translator, service configuration, nice, governor, or affinity changes.

## Method

- Orange Pi 5 Max / RK3588, ARM64, eight online cores, existing LiteRT 2.3.0
  Python installation. CPU execution; no NPU conversion or delegate.
- Original Google assets reused read-only from `/home/orangepi/gocr-runtime/assets`;
  existing project validation checks their canonical hashes.
- Current configured Python detector orchestration / head decode, ARM64 native
  postprocess compiled from the existing source, Python rectification and
  project recognizer with its existing greedy CTC decoding.
- Models/interpreters persist throughout each profile; no reload per crop.
- All 13 PNGs in `docs/evidence/gocr-google-runner-20261009/corpus`.
- One unmeasured warmup per frame, five measured OCR calls per frame/profile.
  Three profiles ran sequentially, without concurrent benchmark workers.
  Earlier overlapping exploratory runs were overwritten and are not evidence.
- Measurement starts at an already decoded 1280×720 RGB frame and ends at text.
  Disk decoding, network transfer, translation and OSD are excluded.
- TV comparison uses the earlier system STRICT native D2/R2 reference from
  `docs/evidence/gocr-strict-conv-20261009/reference.json.gz`, not simultaneous
  measurements. Runtime, architecture, preprocessing and crop paths differ;
  these results are not an isolated hardware-only A/B or numerical parity test.

## Timings (milliseconds, warmed medians)

Corpus value is the median of 13 per-frame medians, not pooled calls.

| Profile | D/R threads | Corpus Invoke | Corpus full OCR | Emergency Invoke / OCR | Luigi Invoke / OCR |
|---|---:|---:|---:|---:|---:|
| TV system STRICT, previous reference | 2/2 | 1305.6 | 1464.4 | 1353.6 / 1871.9 | 1311.8 / 1748.6 |
| Orange LiteRT, default delegates disabled | 2/2 | 330.9 | 380.9 | 331.6 / 531.3 | 331.2 / 490.5 |
| Orange LiteRT, default delegates disabled | 4/2 | 273.0 | 328.1 | 273.0 / 474.1 | 273.0 / 433.1 |
| Orange LiteRT, default delegates enabled | 4/2 | 72.2 | 119.9 | 76.8 / 224.6 | 77.0 / 194.7 |

LiteRT explicitly logged creation of its XNNPACK CPU delegate in the last
profile. That profile enables default delegates for **both models**, not only
detector; no relaxed/fp16 flags were requested by the experiment.

Initialization measured 45.3, 44.9 and 51.2 ms respectively, with assets already
in OS cache. This is not reboot-cold loading. Full OCR median-of-frame-medians
is 4.46× shorter without default delegates at D4/R2, 12.22× shorter with defaults,
relative to the historical TV series; transfer costs are still unknown.

Orange temperature snapshots: 54.5°C before exploratory execution, about 60.1°C
during measured work and 59.2°C afterward. Governor remained `ondemand`.
No thermal-throttling or long-session conclusion follows from these snapshots.

## Output comparison to TV STRICT

Polygon IoU ≥0.5, one-to-one maximum assignment, unchanged comparison utility.
STRICT is a reference, **not Google-native ground truth**.

| Orange profile | Matched regions | Exact text among matches | Unicode edits | Unmatched TV / Orange |
|---|---:|---:|---:|---:|
| Delegates off, D2/R2 | 102 | 93 | 9 | 7 / 7 |
| Delegates off, D4/R2 | 102 | 93 | 9 | 7 / 7 |
| Defaults enabled, D4/R2 | 102 | 91 | 11 | 7 / 7 |

Within every frame/profile all five measured runs have identical text, quads,
crop SHA and recognizer-input SHA. This repeatability is not cross-runtime parity.

Concrete differences from TV STRICT:

- Both off profiles: `Chapter 1: Wildwoods` → `Chapter 1: Wildwoops`,
  `Saving Your Game` → `Saving Your Gamc`, `222` → `227`, one final period
  removed, Latin/Cyrillic `B` differences and `ls`/`Is` differences.
- Defaults: additionally Emergency `Demo` → `Demd`, `Attack ComboS` →
  `Attack Combos`, one checkmark removed. These are differences, not evidence
  establishing which implementation matches the original screen.
- Emergency off: 21/21 matched texts exact; Luigi off: 16/17 exact.
- Six unmatched regions per side occur in the dense game-example-2 frame;
  remaining unmatched regions vary by profile. All details are in comparison.json.

No tensor parity claim is made: this experiment retained final OCR results,
stage timings, source quads, crop/window hashes and frame-file hashes, but did
not capture all raw model tensors. It is **not eligible as an exact STRICT
replacement** under the project's current quality gate.

## Reproduction and evidence

Isolated staging directory on Orange:
`/home/orangepi/gocr-orange-experiment-20261009`. No server was started, and all
benchmark processes exited. Existing production/runtime directories unchanged.

```sh
cmake -S native/gocr_postprocess -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
export GOCR_POSTPROCESS_LIBRARY="$PWD/build/libgocr_postprocess.so"
/home/orangepi/gocr-runtime/.venv/bin/python scripts/benchmark-orange-gocr.py \
  --assets /home/orangepi/gocr-runtime/assets \
  --corpus docs/evidence/gocr-google-runner-20261009/corpus \
  --detector-threads 4 --recognizer-threads 2 --delegate off \
  --output off-d4-r2.json.gz
```

Use `--delegate default` for the separate delegated experiment.

Evidence: `docs/evidence/gocr-orange-cpu-20261009/` contains three compressed
raw reports and the full geometry/text comparison. Scripts added:
`scripts/benchmark-orange-gocr.py`, `scripts/compare-orange-gocr.py`.
Both compile with Python; all three complete runs executed on Orange.

Next safe investigation: separate runtime, preprocessing and recognizer effects
using identical saved model input tensors. Only after that, measure full-frame
transfer and end-to-end network overhead in a separate experiment. None of this
requires changing the current working TV pipeline.
