# Expanded text-detector comparison on the rooted G5

Date: 2026-10-04. All on-TV runs used the existing PicCap frame path and the
same two saved 1280×720 grayscale frames: Mario & Luigi: Brothership, and the
chapter/dialogue frame in `docs/evidence/text-detectors/game-example-2/`. There
was no second screen capture. PicCap and HyperHDR were left running.

## Measurement method

The ARM32 ncnn executable ran one inference thread at niceness 15. Model load and
one warm-up were excluded. Timed rows are the mean of three iterations, paced at
one-second intervals. The sole CRAFT row is one timed iteration. `CPU/search`
includes resize, neural inference and local box extraction. `four-core share`
is the CPU time for one search per second divided over four TV cores. Peak RSS
is for the probe process; it excludes PicCap, HyperHDR, and the OCR worker.

Each inference used the selected detector model. An early expanded-backend
dispatch bug routed names other than `ppocr` to the contrast detector. Those
initial results were discarded. The dispatch was fixed and every result below
was captured again with the requested model; model-specific timings and boxes
are from the corrected binary.

## Actual G5 measurements

| Detector | Edge | CPU/search | Four-core share at 1 Hz | Probe peak RSS | Brothership regions | Chapter/dialogue regions |
|---|---:|---:|---:|---:|---:|---:|
| Contrast | 320 | 10–11 ms | 0.26% | prior baseline | fragmented/noisy | dialogue fragments; heading missed |
| PP-OCRv3 mobile | 320 | 52 ms | 1.30% | 35 MiB | speaker + both dialogue lines | dialogue split into six; heading missed |
| PP-OCRv3 mobile | 640 | 204–207 ms | 5.1–5.2% | 110 MiB | speaker + both lines | heading + both lines, two extra regions |
| PP-OCRv4 mobile | 320 | 65–67 ms | 1.6–1.7% | 38 MiB | both lines; speaker missed | no regions |
| PP-OCRv4 mobile | 640 | 274–284 ms | 6.9–7.1% | 113 MiB | both lines + speaker candidate + one extra | heading + both lines, six small bottom candidates |
| PP-OCRv5 mobile | 320 | 72–74 ms | 1.8–1.9% | 37–38 MiB | all three wanted areas + six extra candidates | both dialogue lines; heading missed |
| PP-OCRv5 mobile | 640 | 253–278 ms | 6.3–7.0% | 113 MiB | all three wanted areas; see [prior frame report](text-detector-followup.md) | all three readable areas |
| PP-OCRv6 tiny | 320 | 68–75 ms | 1.7–1.9% | 22 MiB | both dialogue lines; speaker missed | heading fragmented into two boxes, both lines, bottom extras |
| PP-OCRv6 tiny | 640 | 288–289 ms | 7.2% | 68 MiB | all three wanted areas | heading + both lines, two extra bottom candidates |
| EAST MobileNetV3 | 320 | 590–596 ms | 14.8–14.9% | 159 MiB | dialogue split across three boxes; speaker missed | dialogue fragmented; heading missed |
| EAST MobileNetV3 | 640 | 602–618 ms | 15.1–15.5% | 160 MiB | dialogue split across three boxes; speaker missed | dialogue fragmented; heading missed |
| CRAFT | 320 | 1,315 ms | 32.9% | 365 MiB | three unrelated regions; dialogue missed | not run |

Contrast measurements are from the earlier same-device benchmark and are shown
as a baseline, not rerun in this expanded pass. At 640, V3/V4/V5/V6 have similar
latency; V5 yields the cleanest boxes across these two samples and also has the
best small-text result. At 320, V5 and V6 are fast enough for frequent checks,
but neither reliably locates the small chapter heading. A 640 discovery pass
remains useful for new scenes.

PicCap stayed `connected:true` and `videoRunning:true` during the corrected
three-iteration tests. Post-run samples were generally 56–60 FPS. The EAST
dialogue run briefly sampled 53.37 FPS; CRAFT used substantial memory but the
capture was still active afterward at 58.93 FPS. These short status samples are
not a long-duration stability or isolated lighting test.

## DBNet18: PC check, ARM blocker

The OpenCV DB_IC15_resnet18 ONNX model was run on the same saved frames on the
PC using ONNX Runtime. It produced word-level boxes, fragmenting both dialogue
lines and the `Chapter 1: Wildwoods` heading. PC inference was 17.8–18.9 ms at
320×192; this is not a G5 performance measurement.

The model has dynamic height/width inputs and shape-driven resize operations.
`onnx2ncnn` reported unsupported `Shape`, `Cast`, `Unsqueeze`, `Resize`, and
`Squeeze` operations. Fixing the input shape with onnxsim did not complete its
validation within the bounded attempt, so there is no verified static ncnn
model. DBNet18 was **not run on the TV** and is not represented as an ARM
candidate yet.

## Sources and model identities

The additional PP-OCRv3/v4/v6 ncnn files came from
[Avafly/PaddleOCR-ncnn-CPP](https://github.com/Avafly/PaddleOCR-ncnn-CPP), source
revision `342448fd164592026e9765746c48ac165ef5b66d`. EAST MobileNetV3 came from
[ishinvin/east-mobilenet](https://github.com/ishinvin/east-mobilenet), revision
`675ba53518e414a5b9c63f7f1e1d6033572a67c2`. CRAFT weights use the
[official CRAFT implementation](https://github.com/clovaai/CRAFT-pytorch) and
its general English/MLT checkpoint. DB_IC15_resnet18 is listed in the
[OpenCV text detection model documentation](https://docs.opencv.org/4.x/d4/d43/tutorial_dnn_text_spotting.html).
Weights and converted models remain local build artifacts and are not committed.

Model code is an experiment under `experiments/text-detectors`; none of these
detectors is enabled permanently in PicCap. The probe uses a deliberately simple
component postprocessor for EAST and CRAFT, so the results are candidate region
boxes, not official polygon decoding or benchmark scores.

## Decision

- Keep PP-OCRv5 as the current quality reference and diagnostic baseline.
- For a frequent detector on G5, continue with PP-OCRv5 or compare v6 at 320;
  both add under 2% of four-core CPU time at 1 search/second in this short run.
- Use a less frequent 640 discovery pass when small text may appear outside
  learned regions. Expect roughly 6–7% of four-core CPU time for PP-OCR models.
- Do not select EAST or CRAFT for the current low-overhead pipeline.
- Revisit DBNet18 only after producing and validating a static ARM-compatible
  graph and measuring it on the G5.

No OCR, tracking, caching, translation, or permanent PicCap integration was
added by this comparison.
