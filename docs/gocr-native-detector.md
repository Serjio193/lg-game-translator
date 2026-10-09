# Native detector / runtime benchmark — LG G5, 2026-10-09

Первый этап detector выполнен: grayscale → pyramid → interpreter → Invoke →
decode 11 heads → existing native postprocess находятся в C++. Модель, binarypb,
threshold, anchors, grouping, head mapping и recognizer windows не изменены.
Это перенос текущей clean-room реализации, не доказательство parity с Google Lens.

## Файлы и границы

- `native/gocr_detector_native/gocr_detector.h`: C ABI, config snapshot, context,
  stage timings, debug exports inputs/outputs/proposals.
- `gocr_detector.cpp`: interpreter lifecycle, fixed-profile allocation один раз,
  прямое заполнение input tensors, прямое чтение output tensors, native grouping.
- `preprocess.cpp/.h`: точный Pillow grayscale и separable bilinear pyramid.
- `decode.cpp/.h`: все 11 head decoders в исходном порядке.
- `tflite_runtime.cpp/.h`: динамический stable C API; отдельное explicit XNNPACK
  подключение только для экспериментов. System library не заменяется.
- `profiler.cpp/.h`: optional telemetry profiler для отдельных диагностических
  проходов. Он выключен в timing benchmark.
- `benchmark.cpp`: executable `gocr_detector_bench`, три warm-up, Invoke x20,
  min/median/p95. В измеренном цикле нет Python, preprocessing или decode.
- `gocr_worker/native_detector.py`: startup config из existing binarypb parser,
  ctypes call и сериализация quads. В Python нет preprocessing или head decode.
- `gocr_worker/detector_backend.py`: native для selected RGB 1280×720; Python
  fallback при недоступной библиотеке, explicit debug mode и прочих image sizes/modes.
  Последний fallback сохраняет прежний generic image API.
- `gocr_worker/worker_full.py`: factory подключена к TV_FULL.
- `scripts/validate-native-detector.py`: same-device строгая проверка input/head
  tensors, proposals, geometry, crops и recognizer text.
- `scripts/benchmark-gocr-detector.sh`: standalone 1/2/4-thread × XNNPACK matrix.
- `scripts/build-gocr-tflite.sh`: воспроизводимая isolated ARM32 runtime сборка.
- `tests/test_detector_backend.py`: regression для selection/fallback/generic API.

В Python остаются orchestration/serialization, PIL rectification и recognizer
windowing/greedy CTC. Native recognizer — следующий отдельный этап. Capture,
его API/settings, classification/translation policy и production mode не менялись.
Native библиотека и TV_FULL entrypoint проверены в изолированном TV runtime.

## Config и preprocessing

Startup вызывает существующий `parse_detector_binarypb()` на исходном Google
config. Все Google numerical parameters передаются через ABI. Strides/head
mapping/profile и clamp exp сохраняют условия Python reference. Бенч получает
snapshot этих параметров (`GDNCFG1`), экспортированный validation script;
ручной подбор параметров не используется.

Для 1280×720 ветки имеют content sizes 1280×720, 1280×720, 640×360, 160×90;
tensor padding остаётся белым до кратности 32. Grayscale и resize воспроизводят
Pillow 10.3, включая 22-bit coefficients и промежуточное uint8 округление после
каждого separable pass. Простой generic bilinear дал бы другой tensor.

Источники контракта: [Pillow Convert.c](https://github.com/python-pillow/Pillow/blob/10.3.0/src/libImaging/Convert.c),
[Pillow Resample.c](https://github.com/python-pillow/Pillow/blob/10.3.0/src/libImaging/Resample.c),
[TFLite C API](https://github.com/tensorflow/tensorflow/blob/v2.17.0/tensorflow/lite/core/c/c_api.h),
[XNNPACK options](https://github.com/tensorflow/tensorflow/blob/v2.17.0/tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h).
Новый C++ код — реализация математического/ABI контракта; сторонний source в repo не vendored.

## Parity выбранного backend

Системный `/usr/lib/libtensorflow-lite.so`, explicit XNNPACK OFF, threads=2:

| Проверка | Emergency Guard | Luigi |
|---|---:|---:|
| Input tensor SHA | 4/4 exact | 4/4 exact |
| Output head SHA | 11/11 exact | 11/11 exact |
| Raw proposals | 935 = 858+77 | 735 = 676+59 |
| Proposal max error | 0 | 0 |
| Final lines | 21/21 | 18/18 |
| Geometry/angle/score tolerance 1e-9 | PASS | PASS |
| Rectified crop SHA | 21/21 exact | 18/18 exact |
| Text через тот же TV recognizer | 21/21 exact | 18/18 exact |

Threads=4 также прошёл строгую parity на двух кадрах. Это ограниченная проверка
reference-equivalence, а не гарантия на всех изображениях. Original LM/FST assets
не изменены; production FST decoder по-прежнему не подключён.

## Чистый C++ Invoke benchmark

Одинаковый Emergency Guard, original model/config, 3 warm-up + 20 измерений.
Обычный capture продолжал работать. Показаны milliseconds. Это **Invoke only**.

| System TFLite 2.17 | Min | Median | P95 |
|---|---:|---:|---:|
| 1 thread, explicit XNNPACK OFF | 2435.08 | 2469.48 | 2505.44 |
| 2 threads, OFF | 1247.68 | 1281.31 | 1299.86 |
| 4 threads, OFF | 639.06 | 706.69 | 806.06 |
| 1 thread, ON | 532.25 | 536.88 | 558.51 |
| 2 threads, ON | 247.16 | 258.51 | 313.97 |
| 4 threads, ON | 204.24 | 301.54 | 408.42 |

Native подготовка inputs обычно ~20–30 ms, decode ~0.5–0.9 ms, grouping ~13–15 ms.
Input/output buffers и resize coefficients переиспользуются; нет AllocateTensors
на каждом кадре и нет output tensor copies в основном detector пути.

## Affinity и реальная нагрузка

System, OFF, 2 threads, Invoke x20:

| Affinity | Min | Median | P95 |
|---|---:|---:|---:|
| default (фактическая mask в raw JSON) | 1247.68 | 1281.31 | 1299.86 |
| CPU 0,1 | 1135.64 | 1233.54 | 1440.20 |
| CPU 2,3 | 1133.53 | 1214.02 | 1340.27 |

Небольшой сдвиг median сопровождается разбросом и изменением фоновой нагрузки.
Affinity не включена в основной путь. `taskset` менял только benchmark процесс,
не capture или глобальные настройки ТВ.

## Своя ARMv7/NEON сборка

Исходники TensorFlow v2.17.0, commit
`ad6d8cc177d0c868982e39e0823d0efbfb95f04c`, webOS SDK GCC 12.2, Release,
ARMv7-A, NEON-VFPv4, softfp, XNNPACK/RUY ON, GPU OFF. Сборка и запуск на G5 прошли.
Системный ELF также уже ARMv7 + NEON; NEON здесь не был впервые «включён».
Точная assembly microkernel-функция системного builtin CONV не установлена.

| Runtime, 2 threads | Median Invoke | P95 | Raw pieces |
|---|---:|---:|---:|
| System, OFF | 1281.31 ms | 1299.86 ms | 858 |
| Custom, OFF | 878.15 ms | 1263.20 ms | 852 |
| System, ON | 258.51 ms | 313.97 ms | 864 |
| Custom, ON | 257.18 ms | 339.74 ms | 864 |

Custom binary: 4 632 412 bytes, SHA256
`31d44852aab934120547471e6b6d7a864991c5b496f48aba813967a8fd7d1028`.
System: 5 899 324 bytes, SHA256
`cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138`.

XNNPACK и custom runtime строгую equivalence не прошли: input tensors exact,
но output tensors/proposals/quads/crops меняются. На Luigi system XNNPACK выдаёт
17 строк вместо 18. Есть текстовые различия; часть связана с переупорядочиванием
regions, поэтому positional text mismatch не является самостоятельной оценкой
качества. Для утверждения улучшения/ухудшения нужны matched-region и ground-truth
проверки. Они **не включены по умолчанию**.

Собственная сборка с XNNPACK не дала заметного преимущества над системным XNNPACK.
Параметры модели не менялись; вычислительные kernels runtime дают другой результат.

## Какие операции исполняются

Отдельный telemetry pass (не timing matrix), четыре Invoke включая warm-up:

- OFF: `CONV_2D` 668 вызовов / ~4254 ms; `DEPTHWISE_CONV_2D` 296 / ~548 ms;
  также CAST, ADD, SUB, MUL, QUANTIZE, DEQUANTIZE, DEPTH_TO_SPACE.
- ON: XNNPACK `Convolution (NHWC, QC8) GEMM/IGEMM/DWConv`, F32 IGEMM;
  `Add (ND, QS8)`, преобразования F32↔QS8 и др.

Это доказательство реально вызванных builtin/delegate operations из profiler,
а не вывод только по наличию XNNPACK symbols в библиотеке.

## Полный TV_FULL до OCR-текста

Original stored frames, один warm-up + пять measured calls; translation/OSD отсутствуют.

| Frame | Native detector + system, 2 threads | Тот же full worker, 4 threads |
|---|---:|---:|
| Emergency Guard | 1782.87 ms | 4031.88 ms |
| Luigi | 1712.41 ms | 3592.34 ms |

На 2 потоках Emergency Guard: средний Invoke 1242.36 ms, recognizer 466.22 ms.
На 4: Invoke 1335.66 ms, recognizer 2608.90 ms. Standalone fast 4-thread Invoke
не переносится автоматически на Python-hosted full worker с recognizer и иной
нагрузкой. Точная причина этого расхождения здесь не установлена. Поэтому threads=2
сохранены в рабочем benchmark deployment; recognizer не оптимизировался в этой фазе.

Предыдущий TV_FULL замер с Python preprocessing/decode на тех же frames был
1955.11/1894.91 ms. Новый warm full benchmark показывает ~1.78/1.71 s, но runs
последовательные и фон меняется; это не синхронный причинный A/B процент.
Переписывание обвязки не устранило основную стоимость Invoke.

## Сборка и запуск

```bash
cmake -S native/gocr_detector_native -B build/detector-tv \
  -DCMAKE_TOOLCHAIN_FILE=/path/to/webos-sdk/share/buildroot/toolchainfile.cmake
cmake --build build/detector-tv -j4

# Copied together: executable, libgocr_detector_native.so, libgocr_postprocess.so.
gocr_detector_bench MODEL.tflite /usr/lib/libtensorflow-lite.so \
  ORIGINAL_CONFIG_SNAPSHOT FRAME.ppm 2 0 20
```

Одна validation команда экспортирует config snapshot и проверяет весь результат:

```bash
python3 scripts/validate-native-detector.py --assets /opt/gocr/assets \
  --library /path/libgocr_detector_native.so --output build/parity.json \
  emergency-guard.ppm luigi.ppm
```

TV_FULL selection:

```bash
GOCR_PROFILE=strict GOCR_DETECTOR=native \
GOCR_DETECTOR_LIBRARY=/path/libgocr_detector_native.so \
python3 -m gocr_worker.worker_full --assets /opt/gocr/assets --threads 2 image frame.png
```

`GOCR_DETECTOR=python` включает reference. `GOCR_DETECTOR_TFLITE_LIBRARY` выбирает
runtime только detector, не recognizer. XNNPACK/profile ABI ограничен проверенной
версией 2.17.0; default stable C API path не зависит от этих optional interfaces.
Другие dimensions/modes generic image API используют прежний Python path.

Experimental TV_FULL: `GOCR_PROFILE=fast_xnnpack` explicitly selects the detector
XNNPACK delegate; recognizer stays unchanged. Default `strict` forces delegate off,
including when the legacy `GOCR_DETECTOR_XNNPACK` variable is present. Low-level
research probes may still pass `NativeDetector(..., xnnpack=1)` directly.
FAST requires native full execution and RGB1280x720; it never silently falls back.
It is unsupported in TV_CROP and is not automatically enabled in production.
See `docs/gocr-fast-xnnpack.md` for quality/latency evidence and benchmark usage.

Raw evidence: `docs/evidence/gocr-native-detector-20261009/`.
Модели, runtime binaries и скачанные TensorFlow sources не включены в Git.
