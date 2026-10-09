# Native postprocess: LG G5, 2026-10-09

Порт сохраняет текущую Python clean-room реализацию. Это **не parity с Google Lens**.
Параметры threshold, anchors, pyramid, recognizer windows не изменены.
Grouping-параметры поступают из существующего `detector_config.py`, читающего исходный
Google binarypb. Два литерала уже существующей reference-реализации (IoU 0.75 и
group-head across factor 0.75) передаются отдельными полями ABI. Они не заменены
другими похожими полями Google config. Неиспользованные Python reference поля
конфига остаются неиспользованными и в native.

## Изменения

- `native/gocr_postprocess/gocr_postprocess.h`: ABI v1, proposals, config, lines,
  timings и диагностический membership.
- `native/gocr_postprocess/gocr_postprocess.cpp`: bbox/basis/angle/overlap, стабильный
  dedupe, полный pairwise, union/find, merge/fitting, group refinement, final dedupe.
- `native/gocr_postprocess/CMakeLists.txt`: отдельная shared library.
- `gocr_worker/native_postprocess.py`: ctypes binding, один массив и один native вызов.
- `gocr_worker/detector.py`: выделена Python reference, выбор backend, fallback,
  одинаковая сортировка и clipping результатов после postprocess.
- `gocr_worker/detector_runtime.py`: выбор native после чтения Google config.
- `gocr_worker/worker_full.py`: backend в диагностике.
- `scripts/benchmark-gocr-postprocess.py`: A/B на одинаковых decoded proposals,
  затем отдельные полные OCR проходы.
- `tests/test_native_postprocess.py`: реальные proposals, random/rotated/group cases,
  одинаковые score, дубликаты, empty, ABI errors и fallback.

Существующие изменения интеграции TV_CROP/TV_FULL в worktree предшествуют этому
порту. Capture, API и settings в рамках этого этапа не менялись.

## Сборка .so

В Linux/WSL с webOS ARM32 SDK:

```bash
cmake -S native/gocr_postprocess -B build/postprocess-tv \
  -DCMAKE_TOOLCHAIN_FILE=/path/to/arm-webos-sdk/share/buildroot/toolchainfile.cmake
cmake --build build/postprocess-tv -j2
```

Проверенная сборка: webOS SDK GCC 12.2, ARM32; Linux host GCC 13.3 и Orange Pi
ARM64 g++ также собрали библиотеку. `-fno-fast-math -ffp-contract=off` сохраняют
обычную floating-point арифметику. ABI использует double, как Python float64;
decoded quads передаются без повторного пересчёта через sin/cos.

Результат: `libgocr_postprocess.so`, ARM32 файл 76 460 байт,
SHA256 `a61de7818f567b12ec2e7c0658691a8480d809431af2bc71b2e5dfc94bed39d8`.
SDK выводил informational psABI notes и предупреждение clock skew WSL/NTFS;
компиляция и линковка успешно завершились с `-Wall -Wextra -Werror`.

## Подключение Python

```bash
GOCR_POSTPROCESS=native \
GOCR_POSTPROCESS_LIBRARY=/absolute/path/libgocr_postprocess.so \
PYTHONPATH=. python3 -m gocr_worker.worker_full --assets /opt/gocr/assets image frame.png
```

`native` — предпочтительный backend по умолчанию. Библиотека ищется в
`native/gocr_postprocess/libgocr_postprocess.so` относительно корня runtime,
потом через системный loader. При отсутствии/неверном ABI или отрицательном
результате native вызова выдаётся warning и используется Python reference.
`GOCR_POSTPROCESS=python` принудительно оставляет reference. Неизвестное значение
переменной считается ошибкой конфигурации, а не тихим fallback.

На ТВ библиотека установлена только в изолированный GOCR runtime; текущий
production PP-OCR pipeline и его настройки не переключались.

## Parity на реальных кадрах

Источники — сохранённые кадры предыдущего замера 2026-10-09, а не новая сцена.
Frames/proposals/results: `docs/evidence/gocr-native-postprocess-20261009/`.
Raw tensors декодировались один раз на G5; оба backend получили одни и те же
decoded proposals. Это один из разрешённых reference-equivalence входов;
ускорения tensor decode в этой работе нет.

| Проверка | Emergency Guard | Luigi |
|---|---:|---:|
| Raw pieces / group proposals | 858 / 77 | 676 / 59 |
| После dedupe | 326 | 267 |
| Проверено пар | 52 975 | 35 511 |
| Компоненты / финальные строки | 21 / 21 | 18 / 18 |
| Membership | одинаковый | одинаковый |
| Максимальная ошибка quad, px | 2.27e-13 | 4.55e-13 |
| SHA rectified crops | 21/21 совпали | 18/18 совпали |
| Текст тем же TV recognizer | 21/21 совпал | 18/18 совпал |

Angle/score проверены с абсолютным допуском 1e-9; piece_count совпадает.
Это эквивалентность результата с допустимым float roundoff, не побитовое
равенство всех intermediate double. Поведение на всех возможных изображениях
не доказано. Production Google LM/FST decoder по-прежнему не подключён.

## Время до OCR-текста

Модели прогреты. Postprocess: один нетаймируемый проход и три измеренных на
одинаковых proposals, таблица показывает медиану. Полный OCR: отдельный
измеренный проход каждого backend с новым inference; загрузка модели исключена.
Перевод, стабилизация, OSD, показ на ТВ не входят. Обычный capture продолжал
работать, поэтому это замер при фоновой нагрузке, а не isolated CPU ceiling.

| Emergency Guard | Python, ms | Native, ms |
|---|---:|---:|
| Dedupe | 2761.82 | 8.18 |
| Pairwise + components bookkeeping | 4673.66 | 6.52 |
| Postprocess, включая binding | 7478.68 | 22.64 |
| Весь C++ postprocess | — | 14.83 |
| Full OCR | 9191.66 | 1880.00 |

Luigi: postprocess 4916.65 → 15.98 ms; full OCR 6723.43 → 1835.20 ms.
Emergency Guard full OCR ускорился примерно в 4.9 раза; postprocess с binding
примерно в 330 раз. Нет сокращения proposals и нет spatial indexing.

## Что осталось Python

Orchestration, binarypb parser, TFLite вызов, decode 11 heads, сборка contiguous
proposal buffer, final sorting/clipping, PIL rectification, recognizer windowing
и greedy CTC, transport/translation routing. Главный оставшийся расход на G5 —
TFLite detector inference (~1.26–1.30 s в новых native полных проходах).

## Повторение проверок

```bash
GOCR_POSTPROCESS_LIBRARY=/absolute/path/libgocr_postprocess.so \
PYTHONPATH=. python3 -m unittest discover -s tests -v

python3 scripts/benchmark-gocr-postprocess.py \
  --assets /opt/gocr/assets --library /absolute/path/libgocr_postprocess.so \
  --output build/parity-benchmark.json --repeats 3 \
  docs/evidence/gocr-native-postprocess-20261009/emergency-guard.png \
  docs/evidence/gocr-native-postprocess-20261009/luigi.png
```

`benchmarks` содержит python/native_dedupe_ms, python/native_pairwise_ms,
python/native_total_postprocess_ms и full_ocr_ms. Raw timings и per-line
quads/crop SHA/text сохранены рядом. Синтетические/реальные proposal regression
тесты не требуют запуска модели; benchmark требует оригинальные Google assets.

## Повторный замер TV_CROP / TV_FULL после native порта

Оригинальные сохранённые RGB кадры 1280×720; на G5 один warm-up и пять
измеренных проходов на режим. Режимы запускались последовательно. На всех
20 измеренных проходах telemetry подтверждает native backend, translation=0.
Измерялось только до OCR-текста. Capture продолжал работать.

| Кадр | TV_CROP, среднее | TV_FULL, среднее | TV_CROP диапазон | TV_FULL диапазон |
|---|---:|---:|---:|---:|
| Luigi | 1877.63 ms | 1894.91 ms | 1822–1953 ms | 1801–2036 ms |
| Emergency Guard | 2052.06 ms | 1955.11 ms | 2018–2159 ms | 1907–2004 ms |

Emergency Guard stages (средние):

| Stage | TV_CROP | TV_FULL |
|---|---:|---:|
| Detector | 1551.49 ms | 1332.74 ms |
| TFLite invoke (входит в detector) | 1409.63 ms | 1186.28 ms |
| Rectification | 28.56 ms | 29.43 ms |
| Recognizer | 194.03 ms | 580.28 ms |
| Network | 215.08 ms | 0 ms |

Разница detector между режимами отражает разные проходы под фоновой нагрузкой:
оба используют один native detector. Небольшой разрыв общего времени не
доказывает универсального преимущества одного режима.

TV_CROP отправил около 185.6 KB JSON на Luigi и 205.0 KB на Emergency Guard
(без HTTP/TCP overhead). TV_FULL OCR по LAN не передавал изображения.

Quads, score, crop SHA и recognizer-input SHA совпали между режимами.
Сохранились прежние различия разных recognizer runtimes: Luigi B / В;
Emergency Guard Attack Combos / Attack ComboS и в / B. Поэтому полная
межрежимная text parity остаётся false; native/Python postprocess parity это
не отменяет.

Raw samples: `evidence/gocr-native-postprocess-20261009/modes-benchmark.json`.
Benchmark servers завершены, временные sockets удалены; production mode не
переключался. После добавления optional CURRENT replay и backend telemetry
host integration tests (4), Python compile и whitespace checks прошли.
