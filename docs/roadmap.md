# Product roadmap

This document records the agreed direction for the LG Game Translator project.

## Current capture baseline

- Target TV: LG OLED65G51LW (G5), rooted webOS 25.
- Capture path already verified through PicCap / hyperion-webos.
- Working format: NV12.
- Chosen baseline for the translation pipeline: **1280×720 at about 60 FPS**.
- 1920×1080 works but is currently much slower (~14.6 FPS), so 720p is the working target.
- Existing PicCap + HyperHDR lighting must keep working.

For access to frames there are two planned paths:
1. Reuse the existing PicCap/HyperHDR local stream in parallel if HyperHDR exposes the received frames safely.
2. If that is not practical, fork/modify PicCap so it sends a second local stream to the translator while continuing to feed HyperHDR.

## OCR

Initial OCR language priority:
1. English.
2. Other Latin-script languages later.
3. Chinese and Japanese are not a current priority.

The OCR pipeline should not process every 60 FPS frame. The intended design is:
- receive 1280×720 frames;
- detect text regions at a lower cadence;
- crop only changed text regions;
- upscale/preprocess each ROI as needed;
- run OCR only on those ROIs.

OCR must preserve geometry, not only recognized text. For every text region we want its bounding box/coordinates so the translated output can be rendered in the same place.

Candidate OCR engines for early tests:
- PaddleOCR mobile / ONNX;
- other lightweight English OCR models if they outperform it on real game captures.

Candidate compute hosts:
- Orange Pi running Arch Linux;
- NVIDIA Shield TV;
- Android phone;
- the LG TV itself only for lightweight work unless measurements show it is practical.

The TV should primarily remain responsible for capture. Orange Pi or Shield are the preferred places for heavier OCR/translation workloads.

## Translation

Initial direction:
- English → Russian;
- local translation preferred for low latency and offline use;
- start with MarianMT / Helsinki EN→RU;
- compare later with NLLB distilled or other models.

Translation should retain short dialogue context instead of treating every OCR line as a completely independent sentence. Keep a small rolling context of prior lines where useful.

Cloud translation can remain an optional fallback, not the main path.

## Output modes

Two independent output modes are planned.

### Text overlay

Primary visual goal:
- render Russian text directly over the TV picture;
- use the OCR bounding box so the translation appears where the original game text appeared;
- eventually cover/mask the English source text and replace it with Russian.

Long-term quality target is a Google-Lens-like replacement effect:
- same position;
- similar font size;
- similar text color;
- similar weight/italic style;
- similar outline/shadow;
- similar line spacing and alignment;
- approximate font family when the exact game font is unavailable.

The first practical version only needs:
- correct position;
- readable Russian;
- matched size;
- matched color;
- basic outline/shadow.

### Voice / TTS

Secondary output:
- Russian TTS from translated lines.

Initial easy path:
- play TTS through a separate Bluetooth speaker / Orange Pi / Shield.

Later path:
- investigate mixing Russian TTS directly into the TV audio path.

## Development order

1. Keep 1280×720 capture stable while HyperHDR lighting still works.
2. Expose the frame stream to the translator without duplicate capture if possible.
3. Add text-region detection.
4. Add English OCR on ROIs.
5. Add English→Russian local translation.
6. Add text overlay using OCR coordinates.
7. Improve overlay styling to match the source text.
8. Add Russian TTS.
9. Compare Orange Pi, NVIDIA Shield and phone for latency and power efficiency.
10. Only after the core English pipeline is solid, consider additional OCR languages.

Each conversation/work branch should focus on the next concrete step rather than trying to implement the whole pipeline at once.
