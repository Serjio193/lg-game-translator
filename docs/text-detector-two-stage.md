# Full-frame discovery and local ROI monitoring on the G5

Date: 2026-10-04. The comparison uses the existing PicCap OCR worker's
1280×720 grayscale snapshots. It does not start another capture, change PicCap
settings, or affect the HyperHDR forwarding path.

## What the two stages do

1. A full-frame detector periodically discovers text anywhere on screen and
   returns candidate rectangles.
2. A cheap monitor compares only each active text rectangle with its previous
   pixels. Unchanged regions do not need another OCR call. A changed region is
   sent to OCR; OCR can update or remove its cached text. The periodic full
   search remains responsible for finding text elsewhere or after a scene
   change.

The second stage is a change gate, not another text detector. A local text
detector is only needed to refine/replace a rectangle after its contents
change. The experiment compares both options below.

## Full-frame candidate results across the detector sweep

The earlier detector sweep tested contrast/C++, PP-OCRv3/v4/v5/v6, EAST,
CRAFT, and DBNet18 on real G5 game frames. The first six were run on the TV;
DBNet18 only ran on the PC because its dynamic ONNX graph did not convert to a
verified ARM model. EAST and CRAFT were too expensive for a frequent scan. See
the [expanded detector comparison](text-detector-expanded-comparison.md) for
their measured latencies, memory, and per-frame candidates.

For a frame from *Mario & Luigi: Brothership*, the on-TV full-frame scan at
320 reported:

| Detector | CPU per scan | Candidate regions | Observation |
|---|---:|---:|---|
| C++ contrast | 12.1 ms (0.30% of 4 cores at 1 Hz) | 12 | Dialogue split/noisy candidates |
| PP-OCRv5 mobile | 63.5 ms (1.59% of 4 cores at 1 Hz) | 5 | Both dialogue lines covered; speaker and top-of-frame extras |

The current frame is a distinct Brothership dialogue. On a prior Brothership
frame, contrast at 640 took about 39 ms and produced 16 regions, while PP-OCRv5
at 320 took about 63 ms and produced 9; PP-OCRv5 / 640 cost about 253 ms and
produced 4. PP-OCRv5 has fewer candidate regions on those samples, but this is
not a labeled precision/recall score. Other PP-OCR variants also found the
dialogue, with v3/v5/v6 generally more useful than v4 on the two scenes in the
[expanded report](text-detector-expanded-comparison.md). The full-screen
winner is therefore provisional; OCR confirmation and a larger annotated set
are needed to compare accuracy fairly.

## Same-frame regional rerun

The current image contains a speaker label and two dialogue lines in a region
at x=180, y=30, width=795, height=235 of the 1280×720 input. The crop was made
from that already captured frame; it is not a capture API ROI.

| Operation on that region | CPU per check | Result |
|---|---:|---|
| C++ contrast / 320 | 6.3 ms | Two dialogue lines, one box per line, no extra boxes inside the crop |
| PP-OCRv5 / 320 | 31.8 ms | Speaker and both dialogue lines |
| Pixel diff, text rows only (590×100) | 0.15 ms | Change signal only; it does not identify text |
| Pixel diff, full frame (1280×720) | 2.1–2.5 ms | Change signal only; scans all pixels |

So PP-OCRv5 should not be rerun on every active region check. A pixel-change
gate is over 200× cheaper than regional PP-OCRv5 in this measurement. If a
changed region needs fresh geometry, the small C++ contrast detector is also
cheaper than regional PP-OCRv5, though its boxes are less reliable on the full
screen. Checking one 590×100 ROI on each of 60 frames/second would cost about
9 ms of CPU per second by simple multiplication of the measured per-check cost;
that rate is an estimate, not a live 60 Hz test.

## Temporal evidence from the live PicCap path

Twelve snapshots were requested about once per second through the existing OCR
worker while the Brothership dialogue was on screen. The accepted high-
confidence TSV words continued to contain both dialogue lines. The game scene
animated, but from snapshots 7–12 the tight text rectangle had **0%** pixels
whose grayscale difference exceeded 8. In the same five frame-to-frame pairs,
the full screen changed by **0–10.23%** of pixels, averaging **5.53%**; the
larger dialogue bubble changed by **0–2.19%**, averaging **1.18%**. Comparing
the whole bubble would therefore cause unnecessary checks for background/UI
animation. In this short stable interval, comparing the tight text rectangles
did not.

The six frame/TSV pairs are preserved in
[the sample archive](evidence/text-detectors/two-stage/piccap-frame-series.tar.gz).

The ARM32 `lg-frame-diff-bench` utility made 50 comparisons per measurement on
the TV. At threshold 8, one full-frame comparison took 2.1–2.5 ms CPU, one
whole-bubble comparison about 0.5 ms, and one 590×100 text-region comparison
about 0.15 ms. A real transition where the dialogue text changed was not
captured in this series, so change-detection sensitivity across transitions
still needs a direct test. The tool takes PGM snapshots and arbitrary ROI
coordinates; build it with the existing ARM CMake configuration and run it as
documented in the experiment README.

After the on-TV timing run, PicCap remained connected with video capture active;
five later samples were 58.19–59.59 FPS. HyperHDR remained running. These are
short observations, not a long-term load test.

## Current choice

- **Full-frame discovery:** continue with PP-OCRv5 / 320 as the quality-oriented
  candidate. It spends about 64 ms CPU per second at one search per second in
  these runs. Keep the occasional larger discovery pass under consideration
  because small headings can be missed at 320.
- **Active-region checks:** use a tight grayscale pixel-difference gate first,
  then OCR only when that region changes. It cost about 0.15 ms per comparison
  for a 590×100 text rectangle in this test. Use C++ contrast / 320 only when
  local re-detection is needed; it cost 6.3 ms on the larger dialogue crop.
- **Do not use a bottom-only search as the global detector.** Brothership text
  is near the top. Full-frame discovery once per second is what catches text
  appearing in an unfamiliar location.

This is a candidate architecture, not production PicCap integration. A larger
test must include actual text appearing, changing, moving, and disappearing,
plus stable text over animated backgrounds. The live 12-frame sequence had no
text transition and cannot prove those cases.
