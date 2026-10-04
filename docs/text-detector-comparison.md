# G5 text-detector pilot, 2026-10-04

Further tests with multiline dialogue, smaller headings and another game are
recorded in [the follow-up](text-detector-followup.md). They show why 320 alone
and confidence-only filtering are insufficient for all scenes.
Additional PP-OCR versions, EAST, CRAFT and DBNet18 are covered by the
[expanded comparison](text-detector-expanded-comparison.md).

## Scope and actual inputs

Two detectors were cross-compiled and run on this G5 while its existing PicCap
1280×720 RGB, `nogui:true`, OCR enabled and loopback HyperHDR pipeline operated.
HyperHDR Forwarder stayed disabled. No second screen capture was started.

The initial experiment reads the same saved real PicCap video frame: Norway road
scene with two embedded Cyrillic caption lines at the bottom left. A subsequent
comparison uses one real English game frame, documented below. These are small
pilots, not a game/film accuracy dataset. The detection models find geometry;
English-only Tesseract cannot correctly recognize the Cyrillic captions.

A newly requested grayscale snapshot of the current YouTube video contained
video but no bottom captions. The user identified these as YouTube captions
rendered over the video in the graphical layer. With `nogui:true`, these are
absent from the OCR input; changing the text detector cannot recover absent
pixels. TV GUI capture was not enabled in this investigation. Prior measurements
with GUI suggested about 30 FPS, but GUI performance was not remeasured here.

- [Real embedded text input](evidence/text-detectors/burned-text.png)
- [Current video-only OCR input](evidence/text-detectors/video-only-input.png)
- [Visual comparison of boxes](evidence/text-detectors/detector-comparison.png)

## Detector costs at one invocation per second

Eight timed iterations per case after model load and warmup, one thread,
niceness 15. Resize and postprocessing are included. Full-frame detector input
was downscaled to maximum edge 320/640/960; original capture remained 1280×720.

| Detector / max edge | CPU ms/invocation | Mean wall ms | CPU share across 4 cores | Peak RSS MiB | Observed caption boxes |
|---|---:|---:|---:|---:|---|
| Contrast / 320 | 8.6 | 16.4 | 0.22% | 6.4 | Missed both |
| Contrast / 640 | 31.4 | 67.8 | 0.79% | 6.4 | Fragments of both |
| Contrast / 960 | 80.7 | 141.5 | 2.02% | 8.9 | Both, fragmented first line; background candidates |
| PP-OCRv5 mobile / 320 | 66.4 | 138.3 | 1.66% | 39.0 | Fragment of first, missed second |
| PP-OCRv5 mobile / 640 | 282.8 | 568.5 | 7.07% | 120.3 | Both main lines, plus small roadside candidate |
| PP-OCRv5 mobile / 960 | — | — | — | — | Safety guard stopped run |

CPU percentage comes from the experiment's process CPU time divided by wall
time and four CPUs. It is not total TV CPU load and does not include existing
OCR/lighting work. Peak RSS is process memory, including model initialization.
The two detectors use different score meanings; their score values cannot be
compared directly. PP-OCR postprocessing is a local horizontal bounding-box
prototype, not official full DBNet polygon postprocessing.

PicCap baseline before these cases averaged 58.46 reported FPS (four samples).
During PP-OCR / 640 at 1 Hz it averaged 50.92 FPS, sampled range 44.44–58.28.
PP-OCR / 960 reached consecutive 45.42 and 43.50 FPS samples, below the 80%
baseline guard, so the benchmark process was terminated. HyperHDR remained
running with the same PID 32464. A single low 44.53 sample also occurred in the
contrast / 640 case; short sequential trials and changing live video are not a
controlled proof that every FPS change is caused by the detector.

## Lower-cost alternatives actually measured

| PP-OCR / 640 mode | CPU ms/invocation | Mean wall ms | CPU share across 4 cores | Peak RSS MiB | PicCap sampled mean FPS |
|---|---:|---:|---:|---:|---:|
| Full frame once / 5 seconds | 269.0 | 443.3 | 1.35% | 113.0 | 55.62 (own baseline 56.68) |
| Bottom 25% once / second | 64.9 | 97.1 | 1.62% | 36.8 | 55.34 (own baseline 55.74) |

The bottom crop was **1280×180**, detector input **640×90 padded to 640×96**.
It found both embedded lines. Its coordinates are local to the crop; add 540
to y to recover full-screen coordinates. Recognition crops must be taken from
the original 1280×720 frame. Crop is software on an already acquired frame,
not evidence of hardware capture ROI.

Raw [main comparison](evidence/text-detectors/comparison.json),
[main telemetry](evidence/text-detectors/comparison-telemetry.jsonl),
[rare full scan](evidence/text-detectors/rare-full.json),
[rare scan telemetry](evidence/text-detectors/rare-full-telemetry.jsonl),
[bottom ROI](evidence/text-detectors/bottom-roi.json),
[ROI telemetry](evidence/text-detectors/bottom-roi-telemetry.jsonl).

## Choice and next implementation boundary

### Actual English game frame, after switching away from YouTube

The video-only 1280×720 grayscale snapshot contains the game dialogue
**"That's much better. Thank you kindly!"**. The full-frame OCR correctly reads
these six words, but also produces false words from background objects.

Eight paced iterations per detector/size, same stored game frame, while live
PicCap/HyperHDR and the existing full-frame OCR continued:

| Full-frame detector | CPU ms/search | Mean wall ms | CPU share across 4 cores at 1 Hz | Candidate boxes | PicCap sampled mean FPS |
|---|---:|---:|---:|---:|---:|
| Contrast / 320 | 10.6 | 15.6 | 0.27% | 10 | 58.95 |
| Contrast / 640 | 38.8 | 61.8 | 0.98% | 14 | 58.86 |
| Contrast / 960 | 96.2 | 120.4 | 2.41% | 19 | 59.03 |
| PP-OCR / 320 | 65.0 | 100.0 | 1.63% | 1 | 58.90 |
| PP-OCR / 640 | 257.0 | 340.4 | 6.42% | 1 | 56.65 |
| PP-OCR / 960 | 551.7 | 663.6 | 13.79% | 1 | 54.73 |

Own initial baseline: 58.86 FPS, four samples. The 960 neural case completed on
this scene; the earlier YouTube case was stopped by the guard. This illustrates
why scene workload and FPS must be measured rather than presumed constant.
All cases retained HyperHDR PID 32464 and connected/running source status.

PP-OCR / 320 found one region at x=276, y=624, width=584, height=40, score=0.985.
The contrast detector at 640 also found the dialogue, but most other boxes are
background candidates, making recognition/filtering more expensive downstream.
The visual comparison is included below; this is not a labeled precision/recall
evaluation or evidence that 320 always suffices for small game fonts.

The **bottom 25%** crop, detected at maximum edge 320, cost **21.5 CPU ms/search**,
29.3 ms mean wall time, 0.54% CPU share across four cores at 1 Hz, peak RSS 19.7
MiB. It found the dialogue (crop-local x=276, y=80, width=588, height=44).
PicCap averaged **59.08 FPS**, sampled 57.56–59.70. No inference runs in parallel
with another detector; the current full-frame OCR is still part of the baseline.

One OCR of the original-resolution region plus eight pixels padding yielded
exactly the six dialogue words, confidence 84.3–92.7, without the full-screen
background words. Crop size was **600×56**. `--psm 7`, English, one OpenMP thread,
niceness 15: elapsed 1.18 s, process CPU 0.98 s, peak RSS about 287.6 MiB, including
CLI model initialization. This was a single recognition, not a throughput
benchmark. It shows that OCR/model loading can remain expensive even after the
detector becomes cheap; detector CPU percentages do not include this OCR cost.
No same-frame repeated full-vs-crop OCR timing comparison was made.

- [Game input](evidence/text-detectors/game/input.png)
- [Game detector boxes](evidence/text-detectors/game/boxes.png)
- [Game full-frame OCR TSV](evidence/text-detectors/game/full-frame.tsv)
- [Game detector measurements](evidence/text-detectors/game/comparison.json)
- [Game runtime telemetry](evidence/text-detectors/game/comparison-telemetry.jsonl)
- [Game bottom ROI measurements](evidence/text-detectors/game/bottom-roi.json)
- [Game bottom ROI telemetry](evidence/text-detectors/game/bottom-roi-telemetry.jsonl)
- [OCR crop](evidence/text-detectors/game/ocr-crop.png)
- [Crop OCR TSV](evidence/text-detectors/game/ocr-crop.tsv)
- [Single OCR resource measurement](evidence/text-detectors/game/ocr-crop-time.txt)

For this dialogue, PP-OCR / 320 is the preferred full-frame detector candidate.
A known bottom ROI is even cheaper. A future adaptive mode can discover regions
at low cadence and track them, then use larger detector inputs only when small
text is missed. That combined mode and session learning are not implemented yet.

The simple contrast prototype is cheaper but does not reliably return complete
text regions on this frame. The neural detector is the better candidate for
region geometry, but a full-frame 1 Hz scan already has a noticeable cost.

Recommended next experiment: PP-OCR at low cadence for full-screen discovery,
then more frequent detection/changes in known ROIs, with OCR only on changed
full-resolution crops. The two scan modes have been measured **separately**;
their combined load, tracker/cache, OCR crop cost and recognition quality have
not yet been measured or implemented. Do not add the neural full scan on top of
permanent full-frame OCR and assume this improves CPU load.

No detector was added to PicCap's permanent runtime in this stage. All benchmark
processes ended; PicCap and HyperHDR remained running afterward (PicCap's final
status reported 59.65 FPS). Physical LED behavior was not visually inspected.

The TV exposes four CPUs. PicCap had nine threads allowed on CPUs 0–3. The
benchmark uses one thread with no forced CPU affinity; OpenMP was disabled in
ncnn. The scheduler distributes runnable threads, but one detector thread does
not compute in parallel on all four cores. Two-thread performance and affinity
have not been tested. Additional threads must be evaluated by total CPU cost
and capture FPS, not latency alone.

## Reproduction and deployed diagnostic change

[Experimental sources/build/run instructions](../experiments/text-detectors/README.md).
ARM build and host smoke tests passed; the test covers blank frames, synthetic
glyph grouping, resize, PGM decoding and truncated input rejection.
Source files are below 500 lines. The main capture probe's build is unchanged.

PicCap gained only an on-demand OCR snapshot diagnostic: create
`/tmp/piccap-ocr-snapshot-request`; after the next successful OCR, inspect
`/tmp/piccap-ocr-snapshot.pgm` and `.tsv`. This reads the worker's existing frame,
not another capture. The native binary was rebuilt/deployed and IPK rebuilt with
executable modes checked. The [PicCap patches](../patches/piccap-ocr/README.md)
include this addition. Root service and settings were retained; GUI is disabled.

Final native/IPK binary SHA256:
`7b0f9b9bc52f9218ce6a2e50fd1f66a4446d546dce0d2a5cb280b1e65deedd34`.
It was deployed after the detector comparisons, followed by successful native
root service activation and a fresh snapshot request. HyperHDR retained PID
32464. The final diagnostic change adds write-error guards, not another capture
or a detector in the production worker. Local IPK:
`E:\Github\piccap\build\org.webosbrew.piccap_0.5.4_all.ipk`.
