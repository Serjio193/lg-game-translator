# STRICT detector runtime profiling — G5, 2026-10-09

Ускорение с полной strict parity **не найдено**. System TFLite остаётся
reference/default. Ни один custom runtime не подключён к production или
экспериментальному worker backend. На этом этапе XNNPACK не запускался.

## Границы и методика

Исходный corpus — 13 RGB 1280×720 кадров из
`docs/evidence/gocr-google-runner-20261009/corpus/`, на ТВ — соответствующие PPM
в `fast-corpus/`. Полный native TV_FULL путь до UTF-8; перевод и OSD не измеряются.
Detector threads=2, recognizer threads=2. Recognizer всегда использует неизменённый
system runtime, даже когда detector использует custom library.

Для каждой пары и кадра: один прогрев, пять замеров, порядок system/custom
чередуется между проходами и кадрами. Persistent interpreter и исходные buffers
переиспользуются. Snapshot proposals/components/tensor hashes выполняется вне
timed path. Median по corpus — медиана пятипроходных медиан отдельных кадров.
ARMv7 baseline проверен на двух обязательных кадрах; каждый из двух NEON вариантов
проверен на всех 13. Успешные latency-серии выполнялись поочерёдно.

Системная библиотека: `/usr/lib/libtensorflow-lite.so`, TFLite 2.17.0,
5,899,324 bytes, SHA256
`cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138`.
G5 имеет ARM32 userspace, четыре CPU; наблюдаемая частота до/после — 1.4 GHz.
PicCap продолжал работать: capture, модели, Google config, thresholds, anchors,
pyramid, grouping и recognizer windows не изменялись. Системная библиотека и
recognizer binary не заменялись. Всё исполнялось в отдельном developer runtime.

## Node profiling

`GOCR_DETECTOR_PROFILE` включает native telemetry C API TFLite 2.17.
ABI проверен по исходному `profiling/telemetry/c/profiler.h`: callbacks передают
operator name, node index, subgraph index. Профиль теперь разделяет одинаковые
типы ops по узлам, сохраняет execution count, total/median duration и долю
измеренного Invoke. Прогрев удаляется через `gocr_detector_reset_profile()`.

Shapes читаются **после allocation** через public `TfLiteInterpreterGetTensor`
и TensorDim. Неизменённая модель задаёт соответствие node → tensor indices;
минимальный schema-v3 reader работает только в диагностике. В inference он не участвует.
Kernel implementation public telemetry не раскрывает; поле `kernel_backend`
в node JSON явно сообщает об этом ограничении.

Emergency Guard и Luigi: один прогрев, 10 Invoke-only измерений. Все 329 узлов
наблюдались по 10 раз. Emergency: total Invoke 13,709.5 ms; Luigi: 13,852.4 ms.
Эти суммы включают profiler overhead и не заменяют unprofiled benchmark ниже.
Повторные 4 input / 11 output tensor hashes совпали на обоих кадрах.

На Emergency Guard `CONV_2D` занимает **82.45%** Invoke,
`DEPTHWISE_CONV_2D` **11.22%**, ADD 3.10%, QUANTIZE 1.74%.
Top-20 узлов занимают 39.55%. Главный резерв находится в convolution kernels,
а не в Python, декодировании или количестве proposals.

| Node | Op | Input / filter → output | Count | Total ms | Median ms | % Invoke |
|---:|---|---|---:|---:|---:|---:|
| 83 | CONV_2D | 1×92×160×64 / 7×5×5×64 → 1×92×160×7 | 10 | 560.11 | 53.18 | 4.09 |
| 167 | CONV_2D | 1×92×160×64 / 7×5×5×64 → 1×92×160×7 | 10 | 541.50 | 53.67 | 3.95 |
| 84 | CONV_2D | 1×92×160×64 / 7×5×5×64 → 1×92×160×7 | 10 | 475.07 | 44.90 | 3.47 |
| 168 | CONV_2D | 1×92×160×64 / 7×5×5×64 → 1×92×160×7 | 10 | 473.53 | 45.86 | 3.45 |
| 96 | CONV_2D | 1×184×320×16 / 64×1×1×16 → 1×184×320×64 | 10 | 354.65 | 35.26 | 2.59 |
| 12 | CONV_2D | 1×184×320×16 / 64×1×1×16 → 1×184×320×64 | 10 | 349.13 | 33.66 | 2.55 |
| 100 | CONV_2D | 1×184×320×16 / 64×1×1×16 → 1×184×320×64 | 10 | 341.19 | 33.57 | 2.49 |
| 16 | CONV_2D | 1×184×320×16 / 64×1×1×16 → 1×184×320×64 | 10 | 325.61 | 32.71 | 2.38 |
| 25 | CONV_2D | 1×92×160×32 / 128×1×1×32 → 1×92×160×128 | 10 | 208.94 | 18.49 | 1.52 |
| 105 | CONV_2D | 1×92×160×32 / 128×1×1×32 → 1×92×160×128 | 10 | 204.64 | 18.95 | 1.49 |
| 21 | CONV_2D | 1×92×160×32 / 128×1×1×32 → 1×92×160×128 | 10 | 203.24 | 19.14 | 1.48 |
| 78 | CONV_2D | 1×23×40×128 / 1024×1×1×128 → 1×23×40×1024 | 10 | 201.05 | 14.91 | 1.47 |
| 109 | CONV_2D | 1×92×160×32 / 128×1×1×32 → 1×92×160×128 | 10 | 191.79 | 18.46 | 1.40 |
| 80 | DEPTHWISE_CONV_2D | 1×92×160×64 / 1×5×5×64 → 1×92×160×64 | 10 | 155.44 | 12.11 | 1.13 |
| 162 | CONV_2D | 1×23×40×128 / 1024×1×1×128 → 1×23×40×1024 | 10 | 150.69 | 13.61 | 1.10 |
| 94 | CONV_2D | 1×736×1280×1 / 16×4×4×1 → 1×184×320×16 | 10 | 148.76 | 14.42 | 1.09 |
| 81 | CONV_2D | 1×92×160×64 / 64×1×1×64 → 1×92×160×64 | 10 | 138.90 | 11.00 | 1.01 |
| 50 | CONV_2D | 1×46×80×64 / 256×1×1×64 → 1×46×80×256 | 10 | 138.25 | 14.00 | 1.01 |
| 101 | CONV_2D | 1×184×320×64 / 16×1×1×64 → 1×184×320×16 | 10 | 130.25 | 12.15 | 0.95 |
| 13 | CONV_2D | 1×184×320×64 / 16×1×1×64 → 1×184×320×16 | 10 | 129.31 | 11.58 | 0.94 |

Все input/output shapes, включая bias, сохранены в `emergency-ops.json` и
`luigi-ops.json`; таблица показывает основные input/filter/output.

## Какие system kernels доказаны

- ARM32 disassembly default `Register_CONV_2D()` непосредственно переходит в
  `Register_CONVOLUTION_MULTITHREADED_OPT()`. Это доказательство default
  registration family, а не утверждение, что каждый CONV проходит один kernel.
- Default `Register_DEPTHWISE_CONV_2D()` переходит в
  `Register_DEPTHWISE_CONVOLUTION_NEON_OPT()`. Сохранён соответствующий disassembly.
- Диагностический LD_PRELOAD probe на standalone detector, 3 warmups + 5 Invoke,
  зарегистрировал **88 реальных вызовов Eigen GetThreadPoolDevice**, 3 pthread_create.
  Это подтверждает фактическое использование Eigen threadpool.
- Exported ruy float32/int8 NEON kernels и ruy ThreadPool присутствуют в бинарнике.
  В probe их перехваченные вызовы равны нулю. Ноль не доказывает отсутствие
  непрехватываемых внутренних вызовов. gemmlowp templates также присутствуют;
  их фактический per-node dispatch в этом исследовании не установлен.
- Возможность reference fallback внутри registration family, точное распределение
  Eigen/gemmlowp/ruy по всем 167 CONV узлам и полные compiler flags LG **не доказаны**.
  `.comment` отсутствует. Нельзя достоверно назвать каждый node reference/optimized
  только по его типу или наличию символов в `.so`.

Probe только считает и передаёт исходные аргументы неизменёнными. Он не входит
в production library и не используется в latency сравнениях. Исходники Google
Android runner и его XNNPACK contract не подменяют evidence системного LG runtime.

## Custom builds и результат

TensorFlow v2.17.0 commit
`ad6d8cc177d0c868982e39e0823d0efbfb95f04c`, GCC 12.2 webOS SDK, ARM32 softfp.
Все варианты: XNNPACK/GPU/NNAPI OFF, `-O2`, `-fno-fast-math`,
`-fno-unsafe-math-optimizations`, `-fno-associative-math`,
`-fno-reciprocal-math`, `-fno-finite-math-only`, `-ffp-contract=off`,
`EIGEN_FAST_MATH=0`. FP16/relaxed/approximate forcing не включалось.
Модель и её типы данных не менялись; поддержка FLOAT16 других моделей библиотекой
не означает использование FP16 для этого detector.

- baseline: `-march=armv7-a -mfpu=vfpv3-d16`, RUY ON.
- neon: `-march=armv7-a -mfpu=neon-vfpv4`, RUY ON.
- neon_eigen: те же NEON CPU flags, RUY OFF, чтобы повторить системную
  multithreaded Eigen registration family. Это дополнительный kernel-family
  experiment, не заявление об идентичной сборке LG.

Baseline означает compiler target, а не гарантию отсутствия всех NEON assembly
в dependency runtime dispatch. Отдельного CPU-tuned build не делалось: сначала
проверены базовые kernel families. Аудит всех 760 compile commands каждого
варианта: unsafe flags не обнаружены, XNNPACK sources — 0. Полные convolution
flags, CMake controls, размеры и SHA библиотек находятся в `build-audit.json`.

| Runtime / corpus | System Invoke ms | Custom Invoke ms | System full OCR ms | Custom full OCR ms | Invoke speedup | Полная parity |
|---|---:|---:|---:|---:|---:|---|
| ARMv7 baseline / 2 | 1317.94 | 32700.81 | 1829.45 | 33227.54 | 0.040× | нет, 0/2 |
| NEON/RUY / 13 | 1331.43 | 938.06 | 1523.79 | 1145.91 | 1.419× | нет, 0/13 |
| NEON/Eigen / 13 | 1312.43 | 1318.76 | 1473.82 | 1477.56 | 0.995× | нет, 0/13 |

Это три отдельные alternating серии, поэтому значения system немного различаются.
У custom baseline recognizer не замедлялся до 32 s: почти всё это время находится
в detector Invoke. Tensor equality и скорость — отдельные gates.

| Кадр / candidate | System Invoke / full ms | Custom Invoke / full ms |
|---|---:|---:|
| Emergency Guard / baseline | 1295.37 / 1825.74 | 32414.86 / 32954.05 |
| Luigi / baseline | 1340.52 / 1833.15 | 32986.77 / 33501.03 |
| Emergency Guard / neon | 1334.72 / 1901.67 | 916.81 / 1440.46 |
| Luigi / neon | 1338.99 / 1813.22 | 985.88 / 1444.15 |
| Emergency Guard / neon_eigen | 1313.65 / 1842.83 | 1329.41 / 1822.94 |
| Luigi / neon_eigen | 1342.00 / 1772.52 | 1320.58 / 1757.90 |

## Strict parity

В каждом кадре сохранены все 11 raw detector hashes и element-wise diff,
decoded proposals, deduped pieces/indices, membership/components, source quads,
crop SHA, recognizer input-window SHA и UTF-8. Также проверены повторяемость
внутри серии, scores, words/symbols и остальные line fields без timing clocks.
Google config заполняется прежним parser; никакого numerical tuning не было.

| Candidate | Input tensors | Отличающихся output heads | Полностью совпавших кадров | Совпавший UTF-8 по строкам |
|---|---|---:|---:|---:|
| baseline | 4/4 на 2 кадрах | 22/22 | 0/2 | 0/2 |
| neon | 4/4 на 13 кадрах | 143/143 | 0/13 | 5/13 |
| neon_eigen | 4/4 на 13 кадрах | 143/143 | 0/13 | 13/13 |

Пример отличия baseline/NEON от STRICT: `Attack ComboS` → `Attack Combos`.
Это отличие, не оценка качества Google. Для Eigen текст совпал, но численные
отличия выходов, proposals/geometry/crops всё равно нарушают требование.
На пустом кадре proposals/components и строки совпали у обоих NEON вариантов;
raw tensors при этом отличаются, поэтому полный gate всё равно не проходит.
Стадии сравниваются независимо: hashes не используются как доказательство
различия membership. Эти флаги отдельно пересчитаны по сохранённым observations;
исходные результаты и timings не изменялись.
**Лучшего exact custom runtime нет; допустимый speedup пока 1.0× — прежний system.**

Новый диагностический detector на system runtime дополнительно сравнен с
сохранённой предыдущей STRICT серией: 13/13 кадров, 143/143 raw heads,
proposals/components и все semantic line fields exact. Финальная сборка
диагностического модуля прошла такую же отдельную regression серию:
13/13 exact, включая scores, words и symbols, повторяемость всех пяти проходов.
Её SHA256 — `67927906730e9e366bc76d6a1d62f2933e099dc29f42a00efc4e24d9ed9d7ead`.

## Воспроизведение и проверки

```sh
bash scripts/build-gocr-strict-runtime.sh "$SDK" "$TF_SOURCE" "$BUILD" neon_eigen
cmake -S native/gocr_detector_native -B "$NATIVE_BUILD" \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/buildroot/toolchainfile.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DGOCR_BUILD_KERNEL_PROBE=ON
cmake --build "$NATIVE_BUILD" -j4
```

На ТВ используется isolated `strict-runtime-experiment/`, system `.so` не заменяется:

```sh
GOCR_DETECTOR_LIBRARY="$EXPERIMENT/libgocr_detector_native.so" \
LD_LIBRARY_PATH="$EXPERIMENT:$POSTPROCESS_DIR" \
python3 scripts/benchmark-gocr-strict-runtimes.py --assets assets \
  --output results.json --runtime system=/usr/lib/libtensorflow-lite.so \
  --runtime neon_eigen="$EXPERIMENT/tflite-strict-neon-eigen.so" fast-corpus/*.ppm
python3 scripts/profile-gocr-strict-ops.py --assets assets --output ops.json FRAME.ppm
```

Profiler script также требует новой diagnostic library в `GOCR_DETECTOR_LIBRARY`.
Recognizer library/runtime остаются прежними. `GOCR_PROFILE=strict` и delegate OFF
устанавливаются benchmark/profiler явно. `kernel_probe.cpp` собирается только при
отдельном `GOCR_BUILD_KERNEL_PROBE=ON`; загрузка — только через diagnostic LD_PRELOAD.

Native ARM SDK build прошёл. Детерминированный native profiler regression test
проверяет reset/warmup exclusion, отдельные node/subgraph keys, count, median и %.
33 host regression tests и 43 tests на G5 прошли. Evidence и итоговые проверки сохранены рядом
с [summary.json](evidence/gocr-strict-runtime-20261009/summary.json).

## Что ещё исследовать без изменения результата

1. Восстановить точные compiler flags/зависимости LG и конкретный per-node kernel
   dispatch: одного совпадения имени family недостаточно для exact recreation.
2. На прежнем system runtime измерить affinity и scheduling при неизменных
   thread counts. Частота/нагрузка/миграция могут быть резервом без смены kernels;
   каждое изменение всё равно должно пройти полный hash gate.
3. Изучить ожидания и idle поведение уже существующих pools. Три созданных pthread
   при requested threads=2 — повод измерить их active time, не доказательство contention.
4. Memory packing/preallocation/CPU tuning рассматривать только с сохранением
   порядка операций и всех промежуточных hashes. Перестановка float reductions,
   другой GEMM, FMA/FP16/relaxed math в допустимое ускорение не входят.

Python, postprocess, recognizer, capture/API/settings/OSD в этом этапе не оптимизировались.
