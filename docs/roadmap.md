# Product roadmap

This document records the agreed direction for the LG Game Translator project.

## Current capture baseline

- Target TV: LG OLED65G51LW (G5), rooted webOS 25.
- Capture path already verified through PicCap / hyperion-webos.
- Working format: NV12.
- Chosen baseline for the translation pipeline: **1280×720 at about 60 FPS**.
- 1920×1080 works but is currently much slower (~14.6 FPS), so 720p is the working target.
- Existing PicCap + HyperHDR lighting must keep working.

The current implementation uses modified PicCap: a single video capture feeds
HyperHDR over its existing loopback TCP connection and an independent internal
OCR worker. HyperHDR Forwarder is disabled. On 2026-10-04, the measured RGB
1280×720 profile with OCR enabled averaged about 57 FPS; completed full-frame
English OCR was about 0.43 FPS. See [measured dual output report](ocr-dual-output.md)
for actual input formats, paired frame proof, limitations, and reproducible patches.

Two text detectors were compared on this G5: contrast/component grouping and
PP-OCRv5 mobile through ncnn. On one real English game dialogue, neural detection
at max edge 320 cost about 65 ms CPU for the full frame or 21.5 ms for a known
bottom ROI. See [detector pilot](text-detector-comparison.md) for scene-dependent
results, CPU/FPS limits, and OCR crop evidence. Adaptive region tracking remains
the next implementation stage; detectors are not enabled permanently yet.

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

Current prototype direction:
- English → Russian;
- MADLAD-400 3B INT8 through CTranslate2 on Orange Pi 5 is the local/offline option;
- Google Cloud Translation v2 is an optional second provider selected in the app UI;
- the Orange Pi hosts the translation API and keeps the Google API key server-side;
- the LG app currently accepts text manually; OCR is not connected yet.

On 2026-10-05, the exact benchmark sentence completed through the Orange Pi API
in 17.4 s after model load (4.42 s model load; 59 generated tokens). The process
used about 3.5 GiB RSS after loading, leaving about 6.2 GiB available. MADLAD
translated the ambiguous phrase “Hold the line” as “Сохраняйте веревку”, which
is a quality limitation. Google remains selectable but is unavailable until
`GOOGLE_API_KEY` is configured in the Orange Pi service environment. The local
service setup and measured result should not be treated as a real-time claim.

Translation should retain short dialogue context instead of treating every OCR line as a completely independent sentence. Keep a small rolling context of prior lines where useful.

Cloud translation is an optional quality fallback, not the default path. Keep
the API key off the TV and out of the app bundle.

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
