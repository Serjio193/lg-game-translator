# OCR engines on detected text regions

Measured 2026-10-04 on the rooted LG OLED65G51LW, webOS 25. PicCap and
HyperHDR remained running. This experiment feeds saved, already-detected line
regions into recognition only; it does not run a second screen capture or the
full-frame text detector during the timed OCR calls.

## Corpus and method

Five grayscale PGM inputs are checked in under
[`docs/evidence/text-recognition/crops`](evidence/text-recognition/crops/): two
Brothership dialogue lines, the speaker label after the previously tested
white/threshold preprocessing, a `Chapter 1: Wildwoods` title, and the line
`That's much better. Thank you kindly!`. The two dialogue lines were separated
from the known PP-OCRv5 dialogue region so each recognizer received a single
text line, matching the detector's line-level output. These five examples are a
small diagnostic set, not a general accuracy estimate.

Tesseract uses `--psm 7`/`PSM_SINGLE_LINE`, English, and one thread
(`OMP_THREAD_LIMIT=1`). The ARM32 C API process loads its model once, warms each
crop once, then measures five recognitions per crop. Model initialization took
548 ms and is excluded from the per-crop measurements. The separate Tesseract
CLI measurements include process/model startup. PP-OCRv5 uses the mobile
multilingual ncnn recognizer only, one inference thread, one warm-up and three
timed inferences. Its timings include crop resize and input normalization;
network load is excluded. Both are nice 19 and ran serially while PicCap's own
OCR worker continued independently.

## G5 recognition results

| Detected region | Expected text | Tesseract 5.4.1 + `eng` fast, API mean | PP-OCRv5 mobile multilingual, ncnn mean | PP-OCRv5 output |
|---|---|---:|---:|---|
| Brothership line 1 (436×41) | `What's that? You want` | 56.2 ms, exact | 275.5 ms | `What'sthat?Youwant` |
| Brothership line 2 (436×44) | `to know where you are?` | 57.6 ms, exact | 301.7 ms | `toknowwhereyouare?` |
| Speaker (110×46, thresholded) | `Connie` | 16.2 ms, exact | 57.5 ms | `Connie,` |
| Chapter title (270×44) | `Chapter 1: Wildwoods` | 40.4 ms, exact | 146.7 ms | `ChapterI:Wildwoods` |
| Dialogue line (600×56) | `That's much better. Thank you kindly!` | 145.2 ms, exact | 310.5 ms | `That'smuchbetter.Thankyoukindly!` |

For these inputs the warmed Tesseract API averaged **63.1 ms/crop** (median
56.2 ms), versus **218.4 ms/crop** for the multilingual PP-OCRv5 recognizer
(median 275.5 ms). Tesseract fast returned the exact expected string in all
five cases. PP-OCRv5 preserved the letters in ordinary dialogue but emitted no
word separators, added punctuation to the speaker, and confused `1` with `I`
in the chapter title. PP-OCRv5's aggregate character error was 16/106 (15.1%)
with whitespace and punctuation counted, and 2/92 (2.2%) after removing
whitespace. Removing whitespace gives zero character errors for the three
dialogue lines but does not repair their unusable word boundaries. A
simple CTC blank-gap rule was also tested: thresholds 1–3 inserted spaces
inside words, while thresholds 4–8 still inserted none.

The speaker label needed the existing white-text/threshold-200 preprocessing:
all raw-crop models returned `What'`. The OCR engine is not expected to repair
a poor crop or contrast by itself.

## CPU, memory, and model variants

| Candidate on G5 | Model / mode | Measured result |
|---|---|---|
| Installed Tesseract 5.4.1 | system `eng.traineddata`, 22.4 MB (timestamp 2018) | PSM 7 recognized ordinary dialogue and the processed `Connie`; it read the chapter as `_Qhéplcr 1: Wildwoods`. CLI peak RSS was about 295 MiB. |
| Tesseract 5.4.1 | official `tessdata_fast` English model, 4.11 MB | Exact on all five examples through the persistent API; API max RSS 75,392 KiB. One API initialization served all crops. |
| Tesseract 5.4.1 | official `tessdata_best` English model, 15.40 MB | Exact on dialogue, chapter, and processed speaker examples; no observed accuracy improvement over fast here. CLI peak RSS was about 192,512 KiB. |
| PP-OCRv5 recognition only | multilingual mobile ncnn weights, 8.24 MB | One-thread inference was 57–302 ms/crop; process peak RSS reached 182,416 KiB. Text spacing and one title character were wrong. |

On the Tesseract fast API run, process CPU time was 2.23 s for model setup,
warm-ups, and 25 measured recognitions (five crops × five repeats); the
per-crop means above exclude initialization and warm-up. A same-model CLI run
with `OMP_THREAD_LIMIT=1` took 0.74 s for the chapter crop and 0.79 s for the
600×56 dialogue line because it creates a new process and reloads traineddata
for each invocation. With PicCap's one-thread setting, an ARM32 persistent API
is therefore the relevant Tesseract comparison, not spawning its CLI once per
crop.

After testing, PicCap remained `connected:true` and `videoRunning:true`. Three
later status samples reported 57.86, 59.40 and 58.79 FPS. These are PicCap's
status estimates, not independent counts of unique frames; they do not prove
zero capture impact or sustained 60 FPS. The test left PicCap and HyperHDR
configuration unchanged.

## Decision and next candidate

**Use Tesseract 5.4.1 with the `tessdata_fast` English model as the current OCR
reference for detected line regions.** The model gave exact word spacing on the
small G5 sample and the long-lived API was both fast and memory-light. Keep
recognition asynchronous to PicCap's frame path and retain only a replaceable
latest crop; the measured Tesseract call does not justify OCR on every 60 Hz
frame.

The multilingual PP-OCRv5 ncnn recognizer is not ready to feed translation
because it omits spaces on these lines. A sensible follow-up is the official
`en_PP-OCRv5_mobile_rec` model, whose documentation specifically describes
improved English spacing, converted to ARM32 ncnn and measured on the same
corpus. That English model was **not** run on this G5 in this experiment.

## Reproduction assets and sources

The isolated ARM32 utilities are in [`experiments/text-recognition`](../experiments/text-recognition/).
They accept P5 PGM line crops and do not connect to PicCap. The existing
buildroot ARM toolchain, a configured one-thread ncnn build, and Tesseract 5.4.1
headers/libraries are needed for their respective targets. Model files are
not checked in. The tested fast and best model SHA-256 values are:

- `tessdata_fast/eng.traineddata`: `7D4322BD2A7749724879683FC3912CB542F19906C83BCC1A52132556427170B2`
- `tessdata_best/eng.traineddata`: `8280AED0782FE27257A68EA10FE7EF324CA0F8D85BD2FD145D1C2B560BCB66BA`
- ncnn `PP_OCRv5_mobile_rec.bin`: `49D9907A55BA20FA6637F9F788F66AB00793BC8CE57A733A09DBE86B9A2E3DB0`

Sources: [Tesseract fast models](https://github.com/tesseract-ocr/tessdata_fast),
[Tesseract best models](https://github.com/tesseract-ocr/tessdata_best),
[Tencent ncnn PP-OCRv5 recognizer example](https://github.com/Tencent/ncnn/blob/master/examples/ppocrv5.cpp),
[converted multilingual ncnn model](https://github.com/nihui/ncnn-android-ppocrv5),
and [PaddleOCR English PP-OCRv5 model details](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md).
