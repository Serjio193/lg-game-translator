# Experimental FAST_XNNPACK, 2026-10-09

STRICT remains the default and the reference. FAST_XNNPACK is explicitly selected
at worker startup and is not enabled in the working production pipeline.

```sh
GOCR_PROFILE=strict python3 -m gocr_worker.worker_full \
  --assets /media/developer/gocr-runtime/assets --threads 2 image frame.ppm
GOCR_PROFILE=fast_xnnpack python3 -m gocr_worker.worker_full \
  --assets /media/developer/gocr-runtime/assets --threads 2 image frame.ppm
```

Both run the complete native detector/postprocess/rectification/recognizer path.
FAST changes only the detector delegate: the existing system TFLite 2.17.0
XNNPACK implementation, with two threads. Recognizer retains the same runtime,
model, greedy CTC decoder and two threads, without XNNPACK. Original Google model,
binarypb, thresholds, anchors, pyramid, grouping and window settings are unchanged.
The original LM/FST is still not applied; this is not Google Lens parity.

An unknown profile is a configuration error. FAST requires native TV_FULL and
selected RGB1280×720; unavailable native/delegate support fails without implicit
fallback. TV_CROP currently rejects FAST. STRICT keeps reference fallback and
generic-image behavior. Legacy `GOCR_DETECTOR_XNNPACK` no longer selects the worker
delegate; explicit low-level research `NativeDetector(...,xnnpack=1)` still works.
Response telemetry and worker health expose the selected profile.

## Same-device measurement

LG G5 ARM32, saved RGB1280×720 inputs, warmed once per frame/profile, five timed
passes each, alternating STRICT/FAST order. Both persistent workers coexist in
one process. Latency ends at OCR text; no capture, translation, network or OSD.
Background capture stayed running; this is not an isolated CPU benchmark.

13 distinct pixel hashes: nine color game frames, three saved grayscale game
frames, one video-only negative control. Several frames are related scenes in
the same game, not 13 independent games. No new resize/upscale, annotated frames
or translated OSD composites were used. Sources/hashes are in `corpus.json`.
The replay corpus is in local `build/fast-corpus/` and the isolated TV runtime;
some original source captures remain in the primary checkout's local evidence.

| Saved frame | STRICT total ms | FAST total ms | Speedup | STRICT / FAST lines |
|---|---:|---:|---:|---:|
| Rumble Dish dialogue | 1566 | 522 | 3.00× | 3 / 3 |
| Saving Your Game menu | 1768 | 699 | 2.53× | 18 / 18 |
| Yoshi choice, first | 1466 | 427 | 3.44× | 3 / 3 |
| Yoshi choice, second | 1522 | 470 | 3.24× | 3 / 3 |
| Main Story description | 1889 | 829 | 2.28× | 16 / 16 |
| Shipshape dialogue | 1544 | 471 | 3.28× | 4 / 5 |
| Brave volunteer subtitle | 1469 | 421 | 3.49× | 3 / 3 |
| Video without text | 1349 | 306 | 4.41× | 0 / 0 |
| Subtitle, grayscale | 1450 | 375 | 3.87× | 2 / 2 |
| Dialogue, grayscale | 1550 | 435 | 3.56× | 4 / 4 |
| Wildwoods book, grayscale | 1853 | 667 | 2.78× | 14 / 14 |
| Emergency Guard | 1930 | 862 | 2.24× | 21 / 21 |
| Luigi menu | 1820 | 749 | 2.43× | 18 / 17 |

Median of the 13 frame medians: STRICT **1549.562 ms**, FAST **471.055 ms**.
Ratio of summed frame medians: **2.927×**; this is a different aggregation from
the ratio of the two overall medians. Detector Invoke medians: **1343.688 ms** /
**287.450 ms**, about 4.67×. The recognizer limits dense-frame total speedup.

## Detection and text comparison

Line correspondence uses convex quad polygon IoU, global one-to-one maximum
assignment, and evaluation IoU ≥0.5. This threshold is only a comparison rule,
not an OCR parameter. Line IDs/order are not compared as identities. No tensor
or crop byte-equality requirement is imposed on FAST.

- 109 STRICT regions and 109 FAST regions overall; equal totals hide changes.
- 102 matched regions, mean IoU **0.9541**, median **0.9799**, minimum **0.5150**.
- Seven unmatched STRICT and seven unmatched FAST regions at this matching rule.
  Six on each side occur in the noisy book illustration; those are not six
  proven missing real text lines. Luigi loses one empty recognition region.
  Shipshape gains a false-positive `700` region. Raw samples retain all regions.
- Exact text: **93/102 matched regions (91.18%)**. This includes empty/noisy
  regions, so it is not a real-world OCR accuracy score.
- Unicode Levenshtein distance: **12 edits / 1431 matched STRICT characters**.
  This measures disagreement with STRICT, not ground-truth CER; unmatched regions
  are accounted for separately, not included in this character denominator.
- Every profile returned identical text/quads across its five repetitions.

Examples: `Choose a different Yoshi.` loses its final point; `✓A Sudden Island
Arrival` loses the checkmark; Cyrillic `В` becomes Latin `B`; `Attack ComboS`
becomes `Attack Combos`; `Demo` becomes `Demd`; `Chapter 1: Wildwoods` becomes
`Chapter I: Wildmoops`. Some changes may improve recognition, but the latter
word corruption prevents treating FAST as a quality-equivalent replacement.

STRICT Emergency Guard and Luigi were also compared with the previous saved
STRICT native benchmark: all 39 lines retain identical text, quads, angle,
confidence, crop hash and recognizer-input hash.

## Reproduce and verification

```sh
python3 scripts/benchmark-gocr-profiles.py --assets assets \
  --repeats 5 --output fast-profiles.json fast-corpus/*.ppm
```

Original assets and native shared libraries must be present. Worker profile
startup, native fallback rules, delegate flag, rotated/reordered quad matching,
Unicode edit distance and integration tests passed: **26 on Windows**, **36
distinct checks on G5** (34-test batch including native image/postprocess tests,
followed by the eight profile cases including two newly added cases). Assignment was also
checked against exhaustive optimum on 250 small random matrices. No C++ changes
or new native build were required; the existing delegate implementation is reused.
PicCap after the experiment: capture running/connected/elevated, **57.27 FPS**.
No production GOCR mode config was installed; no production restart/switch occurred.

Evidence: `docs/evidence/gocr-fast-xnnpack-20261009/results.json`, `summary.json`,
`corpus.json`, `runtime.json`. Raw results contain all five samples per profile
and every matched/unmatched text/quad. The reference is our clean-room STRICT
implementation, not Google Lens. Recommendation: FAST is useful as an opt-in
experiment, **not as the automatic production default**; retain STRICT while
testing more games and ground-truth text, especially small headings and icons.
