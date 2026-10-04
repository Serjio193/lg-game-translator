# Additional real-game text examples, G5, 2026-10-04

All frames are from the existing video-only PicCap OCR snapshot mechanism,
1280×720 GRAY8, `nogui:true`, HyperHDR over loopback. No second capture or GUI
capture is enabled. Comparisons use the same saved frame per example; CPU cost
is per detector search, including resize and postprocessing, excluding model
load/warmup. Current PicCap full-frame OCR continues during short measurements.

## Example 2: two dialogue lines and a smaller chapter heading

Visible text:

- `Chapter 1: Wildwoods`
- `May I ask you to take a close look at my`
- `contents and see if anything is amiss?`

The decorative writing on the book is not included as readable reference text.

| Detector | CPU ms/search | Four-core CPU share at 1 Hz | Candidate regions | PicCap sampled mean FPS |
|---|---:|---:|---:|---:|
| Contrast / 320 | 10.6 | 0.27% | 12 | 58.86 |
| Contrast / 640 | 37.8 | 0.95% | 18 | 58.57 |
| PP-OCR / 320 | 64.8 | 1.62% | 2 | 58.72 |
| PP-OCR / 640 | 266.3 | 6.66% | 3 | 57.25 |

Five timed iterations each. PP-OCR / 320 finds both dialogue lines, but misses
the smaller chapter title. PP-OCR / 640 finds all three readable text regions.
Contrast produces fragmented regions and background candidates; its chapter
region at 640 does not cover the whole heading.

Recognition crops were taken from the original 1280×720 input, with 12 pixels
padding. Tesseract English, one thread, niceness 19:

- Combined dialogue crop / PSM 6: all 18 words returned, but standalone `I`
  becomes `|`, despite confidence about 92.9. Confidence is not proof of accuracy.
- Heading crop / PSM 7: `Wildwoods` and `1:` are recognized; `Chapter` is
  incorrectly returned as `_Qhéplcr` (confidence 45.7).
- Heading enlarged 2× using Lanczos / PSM 7: `Chapter` remains incorrect
  (`.Shépter`, confidence 41.9). Upscaling alone is not sufficient here.
- A manually chosen grayscale threshold of 100 (dark pixels to black, others
  white) also fails to recover `Chapter` (`.Chaptcy`, confidence 48.6).

This distinguishes three independent requirements: the text must exist in the
captured pixels, the detector must cover it, and recognition must correctly read
the crop. A higher detector input size repairs the missed heading location, not
the Tesseract recognition error. Full-frame 640 every second costs significantly
more CPU; rare higher-resolution discovery remains the candidate strategy.

[Input](evidence/text-detectors/game-example-2/input.png),
[detector boxes](evidence/text-detectors/game-example-2/boxes.png),
[measurements](evidence/text-detectors/game-example-2/comparison.json),
[telemetry](evidence/text-detectors/game-example-2/telemetry.jsonl),
[parsed OCR](evidence/text-detectors/game-example-2/analysis.json).

## Example 3: Mario & Luigi: Brothership, dialogue at the top

The user identified the second game as Mario & Luigi: Brothership. The inspected
frame contains:

- Speaker: `Connie`, white letters with black outline.
- `What's that? You want`
- `to know where you are?`

All three regions are near the **top**, so a bottom-only region from the previous
game would miss them completely. The current capture already contains these
game graphics; no TV GUI capture is needed.

| Detector | CPU ms/search | Four-core CPU share at 1 Hz | Candidate regions | PicCap sampled mean FPS |
|---|---:|---:|---:|---:|
| Contrast / 320 | 10.3 | 0.26% | 11 | 57.93 |
| Contrast / 640 | 39.0 | 0.98% | 16 | 59.12 |
| PP-OCR / 320 | 63.3 | 1.58% | 9 | 59.06 |
| PP-OCR / 640 | 253.3 | 6.33% | 4 | 57.20 |

Five timed iterations each; own baseline 58.89 FPS. These are short sequential
trials, not long-term unique-frame throughput or isolated TV-load measurements.
All retain active video/connection and HyperHDR PID 32464.

PP-OCR / 320 covers all three wanted regions, but also emits six other candidates
from the fence/background and the dialogue advance triangle. The triangle has
score **0.977**: high detection score alone cannot reject non-text.
PP-OCR / 640 covers the three wanted regions plus one tiny background candidate.
The contrast method fragments dialogue and produces more background regions.

Original-resolution crops, 12 pixels padding, same English Tesseract setup:

- Dialogue / PSM 6: **all nine words correct**, confidence 88.6–92.6, with none
  of the full-frame background words included.
- Speaker / PSM 7: `{Connie]`, confidence 14.2; the interior name is right, but
  extra boundary characters make the complete result incorrect.
- Manual preprocessing of that same speaker crop: pixels above grayscale 200
  become black; all other pixels become white. This isolates the white glyph
  interiors, dropping dark outline/background. OCR then returns **Connie**,
  confidence 78.4. This hand-picked threshold is a diagnostic example, not a
  generally validated preprocessing rule or a production setting.

[Input](evidence/text-detectors/game-brothership/input.png),
[detector boxes](evidence/text-detectors/game-brothership/boxes.png),
[measurements](evidence/text-detectors/game-brothership/comparison.json),
[telemetry](evidence/text-detectors/game-brothership/telemetry.jsonl),
[parsed OCR](evidence/text-detectors/game-brothership/analysis.json),
[prepared speaker crop](evidence/text-detectors/game-brothership/name-white-200.png).

## What the additional examples establish

1. 320 is cheap and useful for frequent searches, but can miss smaller text and
   hallucinate background regions. It is not a universal replacement for 640.
2. A larger 640 discovery scan materially improves these examples at about four
   times the CPU/search. At one scan per five seconds the measured per-search CPU
   implies about 1.3% of four-core CPU time, excluding recognition and startup;
   that cadence was measured separately on the previous road frame.
3. Learned regions must be per source/session with periodic whole-screen review;
   the relevant text moves from bottom to top between these games.
4. Detection score and OCR confidence are separate and neither proves accuracy.
   Temporal stability plus OCR confirmation is preferable to score-only gates.
5. Preparing an original-size crop can help outlined fonts, but some fonts remain
   problematic for the current Tesseract model. No automatic preprocessing
   selection, tracking, cache or second OCR engine is implemented in this stage.

The proposed next integration remains: rare whole-screen discovery, cheap checks
of known regions, changed-region OCR, cache. Both examples and the successful
name preprocessing are preserved; current permanent PicCap OCR is still the
full-frame prototype. No translation or overlay is introduced.

During all detector-case samples the source remained active/connected and
HyperHDR kept PID 32464. After the additional standalone OCR preprocessing
experiments, one status query reported inactive video/disconnected; a subsequent
query showed active video and 59.46 FPS. The worker uptime had reset. This
transient restart/pause was not isolated to a cause; filtered kernel logs showed
no OOM message. Final status was active/connected at 58.33 FPS, HDMI4 foreground,
with about 437 MiB MemAvailable. This is not proof of uninterrupted operation
through every auxiliary OCR invocation. Avoid adding simultaneous full OCR jobs
to production before measuring RAM as well as CPU.

## Reproducing the evidence export

`experiments/text-detectors/export_example.py` runs on the PC with its existing
Pillow dependency. It takes a case directory containing `input.pgm`,
`comparison/results.json`, `comparison/telemetry.jsonl` and optional OCR TSV/crop
files, and writes a lossless input PNG, box comparison, raw measurements, crops,
and parsed word/confidence/coordinate output. No image processing is performed
on the TV by that exporter.

The main benchmark remains `run_tv.py`; these examples used `--edges 320 640
--iterations 5`. Detectors are diagnostic tools and are not enabled permanently
in the installed PicCap worker yet.
