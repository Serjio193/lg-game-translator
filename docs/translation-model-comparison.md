# Local translation model comparison on the G5

Last updated: 2026-10-04. Device: rooted LG OLED65G51LW, webOS 25, 32-bit
ARM userspace. These are point-in-time measurements, not a claim that all
models are production-ready.

## Fixed comparison sentence

All quality comparisons must use this exact English input, including its curly
quotes, curly apostrophes and em dashes:

> When the captain said, “Hold the line, watch the bank, and don’t touch the key,” Mira spotted a duck by the river—not the bank’s vault—and knew he meant the shore.

Reference rendering for judging meaning (alternate natural Russian wording is
acceptable):

> Когда капитан сказал: «Держите строй, следите за берегом и не трогайте ключ», Мира заметила утку у реки — не банковское хранилище — и поняла, что он имел в виду берег.

The phrase deliberately tests the idiom “hold the line” and the multiple
meanings of “bank”, “duck” and “key”, along with negation, quoted dialogue and
punctuation. Do not compare translation quality across different source text.

## Results on the fixed sentence

| Model / runtime | Quality | Method | Latency | Peak RSS | CPU | Translation result / observation |
|---|---:|---|---:|---:|---:|---|
| Bergamot tiny EN→RU | 4/10 | Correct model config; one warm-up, then five runs; median | 704 ms warmed | 131 MiB | Not measured | Fastest, but grammar and word choice were weak. Reported errors included “Мира заметил”, “ключа” and a faulty rendering of “Hold the line”. |
| Bergamot base EN→RU | 6/10 | Correct model config; one warm-up, then five runs; median | 1,490 ms warmed | 308 MiB | Not measured | Better grammar than tiny, but still mistranslated “Hold the line”. |
| Bergamot base-memory EN→RU | 6/10 | Correct model config; one warm-up, then five runs; median | 1,564 ms warmed | 225 MiB | Not measured | Similar quality to base with lower measured peak RSS. It was the best compromise among the three tested Bergamot variants. |
| OPUS-MT tiny TFLite EN→RU | — | ARM32 TFLite C API, one thread; exact fixed sentence tokenized with its SentencePiece model; decoder returned EOS | 522 ms total; encoder 449 ms; prefill 39 ms | 38.4 MiB by process `VmHWM` | 93% of one core (about 31% of the TV's three cores) | No output tokens. The first generated token was EOS. This is a valid same-input runtime/performance result, but not a translation-quality result. A separate 100-invoke graph warm-up averaged 4.79 ms/invoke; that is not full translation latency. |
| Argos EN→RU / CTranslate2 ARM32 | — | Guarded model-load attempts | No completed translation | One attempt stopped near 332 MiB RSS with about 102 MiB available; another failed allocation | Not measured | No output to compare. The tested package/configuration did not pass the safe-load check; this does not prove every smaller or differently built Argos setup impossible. |
| OPUS-MT mobile INT8 / ONNX Runtime 1.15.0 | 4/10 | CPU, one intra/inter-op thread, greedy decode with KV cache; exact fixed sentence, first inference after loading sessions | Load 1,754 ms; encoder 286 ms; decoder 1,192 ms; about 3,234 ms total | 271 MiB observed process RSS; minimum `MemAvailable` 156 MiB | Not measured | Output: “Когда капитан сказал: «Остановите линию, смотрите на берег и не трогайте ключ», Мира заметила утку у реки, а не утку в хранилище банка», и знала, что он имел в виду берег.” It mishandled the idiom and “bank’s vault”, and produced mismatched quotation punctuation. |
| OPUS-MT INT4 / MNN 3.6.0 ARM32 | — | CPU-only, one thread; official tokenizer IDs; stopped by memory guard during startup/inference attempt | No completed inference | 498.5 MiB sampled process RSS; minimum `MemAvailable` 164 MiB; model files total 284.5 MiB | Not measured | No translation was produced and no quality score is assigned. The process crossed the safe memory threshold with both graphs staged. |

The Bergamot rows are the only warmed five-run medians and can be compared
directly with one another. ONNX is a single cold-session run and must not be
ranked against those warmed medians as if the protocols matched. The TFLite
and Argos rows have no valid translation output. The MNN attempt was stopped
before inference completed. Quality scores are approximate human ratings of
the saved translation against the reference meaning; rows without a translation
are intentionally unscored.

## Repeatable test procedure

1. Send the exact fixed English sentence above, unchanged. Never reuse token IDs
   generated for a different sentence. Use the model's matching tokenizer and
   confirm its vocabulary size and special-token IDs.
2. Run on the actual G5 with the target ARM32 runtime, CPU backend and one
   inference thread. Record model files and hashes, model/interpreter load time,
   and the tokenizer/runtime version.
3. If loading succeeds, run the exact sentence once as warm-up, then five times
   in the same process. Record per-run and median end-to-end translation time.
   Keep load time separate from warmed inference time. If warm-up or decoding
   fails, record the partial stage timings and do not invent a quality score.
4. Record process `VmHWM` from `/proc/<pid>/status`, device `MemAvailable` and
   `SwapFree` before and during inference, plus process CPU time divided by wall
   time (percent of one core). Report CPU both per core and normalized by the
   TV's three online cores when useful.
5. Stop the process if available RAM falls below 200 MiB or free swap below
   180 MiB. Preserve the reason for stopping and the minimum observed values.
6. Score completed translations from 1–10 for meaning, grammar and handling of
   the deliberate ambiguities; use the overall score in the table. A human may
   accept different natural Russian wording from the reference.

On webOS, `/usr/bin/time -v` reported a peak RSS four times higher than the
same TFLite process's in-process `/proc/self/status` `VmHWM` (157,024 versus
39,312 KiB). The table uses the direct process `VmHWM`; future memory readings
should use `/proc/<pid>/status` consistently and retain the raw readings.

## Follow-up runs on the fixed sentence

### OPUS-MT tiny TFLite

The earlier run used a different short sentence, so it is excluded from this
comparison. The exact fixed sentence encoded to 49 input SentencePiece IDs
(plus EOS). The first decoder output was EOS (ID 0), producing zero text tokens.
The C API process reported 522.499 ms total, including interpreter setup,
448.934 ms encoder, 38.937 ms decoder prefill, 39,312 KiB `VmHWM`, and 93.3%
of one CPU core. This confirms the runtime can execute the model, but not
translate this input successfully. During the run `MemAvailable` changed from
588,660 to 567,708 KiB and `SwapFree` remained 301,804 KiB.

### OPUS-MT INT4 MNN

The encoder and decoder weights from
[Hosstia/opus-mt-en-ru-mnn](https://huggingface.co/Hosstia/opus-mt-en-ru-mnn)
total 298,284,664 bytes. MNN 3.6.0 was cross-compiled as a CPU-only ARM32
runtime. The 51 Marian-tokenizer IDs (including EOS) were checked against the
model's 62,518-entry vocabulary; the vocabulary mapping matched exactly.
Before running, the TV had 570,252 KiB `MemAvailable` and 307,356 KiB free
swap. The monitored process reached 510,492 KiB RSS and the guard stopped it
at 167,900 KiB `MemAvailable`; minimum free swap was 215,452 KiB. The output
was not flushed, so the test did not establish whether the guard fired during
startup or the warm-up inference.
After the process exited, available memory was 687,152 KiB and free swap was
212,672 KiB. No output translation was obtained. The attempted model and
runtime were staged on the developer data partition, not in RAM-backed `/tmp`.
I removed the temporary MNN and TFLite test files from the TV afterward; no
translation test process remains. After cleanup, `MemAvailable` was 700,260 KiB
and `SwapFree` was 219,608 KiB. A later read-only check found `MemAvailable`
704,784 KiB and `SwapFree` 220,076 KiB, with no test process or staging path
left on the TV. The guard sampled every 0.5 seconds, so the
observed 167,900 KiB minimum reflects a brief overshoot below its 200 MiB
trigger before the process exited.

## ONNX rerun notes

The first ONNX experiment used straight ASCII quotes/apostrophes. That encoded
to 50 token IDs and was not byte-for-byte the fixed sentence above; exclude
that earlier output from quality comparison. The rerun used the exact fixed
source string. Its host-side Marian tokenizer produced 51 IDs, including four
unknown-token IDs for curly punctuation. The ARM32 probe ran the installed
`/usr/lib/libonnxruntime.so.1.15.0` and the model's encoder, decoder and
decoder-with-past graphs; it did not load `tokenizer.bin` on the TV. Thus this
proves graph/runtime compatibility and translation generation, not a finished
on-device tokenizer integration.

During the exact ONNX rerun, `MemAvailable` reached about 156 MiB and free swap
fell by about 25 MiB. The process completed and was stopped afterward; no
model service was installed. This memory margin is tight enough that repeated
or concurrent inference should wait for a separately guarded test.

Model: [mobile INT8 OPUS-MT en→ru](https://huggingface.co/AndrPixel/opus-mt-mobile-onnx/tree/main/opus-mt-en-ru).
Runtime: [ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

## G5 shortlist closed; alternate Orange Pi 5 Max path

The current G5 shortlist is closed for the candidates recorded above: Bergamot
tiny/base/base-memory and OPUS-MT INT8 ONNX produced translations; TFLite ran
but emitted EOS without text; Argos/CTranslate2 ARM32 did not complete a safe
load; and MNN INT4 exceeded the available-memory guard before producing text.
This closes the tested shortlist, not every model that could theoretically be
ported to webOS. No further G5 model is currently queued for testing.

The next local/offline path is translation on the user's Orange Pi 5 Max, with
the G5 handling capture and OCR only. The first run used the Argos EN→RU 1.9
model directly through CTranslate2 and its matching SentencePiece tokenizer.
This deliberately avoids installing the Argos Python wrapper and its large
optional dependency chain on the board. ARM64 wheels for CTranslate2 and
SentencePiece were used inside a Python 3.13 virtual environment; no system
packages were installed. Board reports 8 CPU cores and 16 GiB RAM.

| Orange Pi 5 Max test | Quality | Warm-up / repeats | Median latency | Peak RSS | CPU time / wall time | Result |
|---|---:|---|---:|---:|---:|---|
| Argos EN→RU 1.9, CTranslate2 4.8.2, 1 intra-thread | 4/10 | One warm-up + five measured runs | 3,208.92 ms | 306,784 KiB | 100% of one core | Translation completed; literal “держи линию”, masculine “заметил/понял”, and bank ambiguity remains wrong. |
| Argos EN→RU 1.9, CTranslate2 4.8.2, 4 intra-threads | 4/10 | Two independent batches, each one warm-up + five runs | 1,471.99 ms first; 1,441.58 ms repeat; 1,459.79 ms latest | 305,924–311,724 KiB | 629% of one core (~6.3 core equivalents) | Fast but weak; identical output in all runs. Latest run loaded in 471 ms. |
| Argos EN→RU 1.9, CTranslate2 4.8.2, 8 intra-threads | 4/10 | One warm-up + five measured runs | 8,343.98 ms | 305,272 KiB | 740% of one core (~7.4 core equivalents) | Slower than 1 or 4 threads despite high aggregate CPU use. |
| Meta NLLB-200 distilled 600M INT8, CTranslate2 4.8.2, 4 intra-threads | 5/10 | One warm-up + five measured runs; CPU | 5,350.94 ms median | 1,037,880 KiB | 515% of one core (~5.2 core equivalents) | Correct feminine “заметила” and shore sense, but pluralized “duck”, translated “Hold the line” literally, and rendered bank vault as “хранилище берега”. |
| Bergamot base-memory EN→RU, ARM64 Orange Pi build | 6/10 | Model loaded once, one warm-up + five measured requests | 680.07 ms warmed median | 429,720 KiB | 100% of one core | Best speed among valid Orange Pi translations so far; retains the known “Дергите линию” idiom error and masculine agreement. |
| Meta M2M100 418M INT8, CTranslate2 4.8.2, 4 intra-threads | 5/10 | One warm-up + five measured runs; CPU | 4,482.53 ms median; load 2,145 ms | 803,144 KiB | 561% of one core (~5.6 core equivalents) | Translation completed consistently, but “duck” became “дук”, “Hold the line” became “Дайте линию”, and bank/vault distinction was lost. Slower and larger than NLLB-600M for similar quality. |
| Meta NLLB-200 distilled 1.3B INT8, CTranslate2 4.8.2, 4 intra-threads | 6/10 | One warm-up + five measured runs; CPU | 10,520.22 ms median; load 1,330 ms | 1,884,752 KiB | 531% of one core (~5.3 core equivalents) | Better grammatical agreement and shore sense, but “Hold the line” remained literal and “duck” pluralized. About twice the NLLB-600M latency and 1.8 GiB RSS. |
| OPUS-MT EN→RU CT2 INT8 (`ordois` conversion) | — | One warm-up + five measured runs; CPU, 4 intra-threads | 4,983 ms median | 211,512 KiB | Not retained in the first raw report | Output repeated clauses and malformed wording, including on the conversion card's short validation sentence. No model-family quality score assigned. |
| OPUS-MT EN→RU CT2 INT8 (`manancode` Android conversion) | — | One warm-up + five measured runs; CPU, 4 intra-threads | 4,870.70 ms median; load 297 ms | 211,584 KiB | 571% of one core (~5.7 core equivalents) | Invalid output: repeated clauses and words, inconsistent gender, and no useful full-sentence translation. No model-family quality score assigned; treat this conversion as unusable. |

Translation output in all runs:

> Когда капитан сказал: «Держи линию, следи за банком и не трогай ключ», Мира заметил утку у реки, а не в хранилище банка, и понял, что он имеет в виду берег.

Meta NLLB-200 distilled 600M output:

> Когда капитан сказал: «Подержите линию, следите за берегом и не трогайте ключ», Мира заметила уток у реки, а не в хранилище берега, и поняла, что он имел в виду берег.

All tests used the fixed sentence above. The 4-thread result repeated within
about 2% in median latency. Peak RSS stayed near 299 MiB, with about 9.3 GiB
`MemAvailable` after inference. The CPU number is process CPU time divided by
wall time and may exceed 100% because it sums work across threads. These are
model/runtime tests, not yet a live OCR-frame integration; the Orange Pi path
is viable for further evaluation, but this Argos result does not yet beat the
best Bergamot G5 translation for quality. NLLB used a third-party CTranslate2
INT8 conversion of Meta's [`facebook/nllb-200-distilled-600M`](https://huggingface.co/facebook/nllb-200-distilled-600M)
from [mijuanlo/nllb-200-distilled-600M-ct2-int8](https://huggingface.co/mijuanlo/nllb-200-distilled-600M-ct2-int8).
The model binary measured 593 MiB with SHA-256
`398726640cc2a02cc6a35277fa3cf2159ce8a1a66b48aa1b6c8837a47e3dd00c`. Peak RSS
was about 1,013 MiB, and `MemAvailable` after the run was 8.60 GiB. NLLB's
CC-BY-NC-4.0 license is non-commercial; keep that restriction in mind for any
future product use.

### Orange Pi follow-up: Bergamot, M2M100, larger NLLB and OPUS-MT

The Bergamot base-memory candidate was rebuilt natively for ARM64 on the Orange
Pi from the same source revision already used for the G5 experiment. The added
`scripts/bench-bergamot.cpp` harness loads the model once and measures a warm-up
plus five serial translations. It measured 136.6 ms model load, 680.07 ms warm
median, 429,720 KiB process peak RSS, and 100% of one core. Its translation was
the same previously scored 6/10; this is a new Orange Pi performance result,
not a new quality sample.

Meta's M2M100 418M INT8 CTranslate2 conversion was tested with the matching
official tokenizer, English source language and Russian target prefix. It
returned a stable but weak translation on all six invocations. The exported
model is about 467 MiB and distributed as MIT; this specific third-party
conversion is [gn64/M2M100_418M_CTranslate2](https://huggingface.co/gn64/M2M100_418M_CTranslate2)
of [facebook/m2m100_418M](https://huggingface.co/facebook/m2m100_418M). CTranslate2
documents M2M100 support and the required language-token prefix in its
[Transformers guide](https://opennmt.net/CTranslate2/guides/transformers.html).

NLLB-200 distilled 1.3B INT8 was tested from the
[OpenNMT conversion](https://huggingface.co/OpenNMT/nllb-200-distilled-1.3B-ct2-int8).
Its CPU backend warned that saved `int8_float16` weights are unsupported for
efficient CPU execution and converted them to `int8_float32` in memory. The
translation was somewhat more grammatical than the 600M output, but took
10.52 seconds warmed and 1.80 GiB peak RSS. This model is also CC-BY-NC-4.0, so
it is restricted to non-commercial use.

Two separately packaged OPUS-MT INT8 conversions were checked using the same
source sentence and CTranslate2 runtime. The
[ordois conversion](https://huggingface.co/ordois/opus-mt-en-ru-ctranslate2-int8)
and [manancode Android conversion](https://huggingface.co/manancode/opus-mt-en-ru-ctranslate2-android)
both emitted long, repetitive, malformed Russian instead of a valid
translation; the latter used about 207 MiB RSS and a 4.87 second median. These
are failed conversion/artifact tests, not evidence that all OPUS-MT checkpoints
are poor. No quality score is assigned. An alternate OPUS model exported and
validated directly from the original Helsinki-NLP checkpoint remains a useful
next candidate.

Reproduce the direct CTranslate2 model benchmarks with
[`bench-ctranslate2.py`](../scripts/bench-ctranslate2.py), choosing `--family`
`argos`, `nllb`, `opusmt` or `m2m100` and setting the matching tokenizer/model
paths and `--threads`. M2M100 additionally needs Transformers tokenizer files
and `--tokenizer`, plus `--source-language en --target-language ru`.
Fetch the NLLB INT8 conversion by running `sh` on
[`fetch-nllb-ct2.sh`](../scripts/fetch-nllb-ct2.sh).
