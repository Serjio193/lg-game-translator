# Где тормозит GOCR на LG G5: 9 октября 2026

Измерение заканчивается на получении OCR-текста. Перевод, подтверждение для
показа, ожидание очереди OSD и вывод на экран **не включены**.

## Условия

Настоящий G5: 32-битный Python 3.12.6, NumPy 1.26.4, Pillow 10.3.0,
системный TensorFlow Lite C API. На Orange — отдельный LiteRT runtime.
Google модели/config/label map извлечены из APK; четыре основных SHA совпали
с handoff. LM/FST/prior сохранены и проверены; существующий greedy CTC пока
не применяет production FST.

Сохранены два RGB кадра 1280×720: Luigi и выбранный пользователем проблемный
Emergency Guard. Каждый путь получил одинаковые пиксели. Один прогрев, затем
повторные измерения. Новый detector использует исходный Android 1280 профиль,
ничего в его параметрах не менялось.

CURRENT — standalone replay существующего TV detector и настоящего Orange
PP-OCRv6 crop service. Это текущий **OCR core**, без классификатора/стабилизатора
и OSD. Работающий production OCR оставался активен в фоне; дополнительная
нагрузка и конкуренция делают числа диагностическими, а не изолированным
performance ceiling. Capture/API/settings не менялись.

## Общие результаты до текста

Повторный инструментированный прогон:

| Кадр | CURRENT | GOCR TV_CROP | GOCR TV_FULL |
|---|---:|---:|---:|
| Luigi | 3052 мс | 6621 мс | 6573 мс |
| Emergency Guard | 4331 мс | 9401 мс | 9558 мс |

Первый прогон на Emergency Guard: 4316 / 9294 / 9250 мс соответственно.
Между новыми режимами пока нет существенного выигрыша общей скорости.

## Проблемный кадр: куда ушло время

Средние по инструментированному replay:

| Этап | CURRENT | TV_CROP | TV_FULL |
|---|---:|---:|---:|
| Detector целиком | 271 мс | 8931 мс | 8909 мс |
| Rectification | Не используется | 30 мс | 32 мс |
| Recognizer | Вместе с сетью: 4058 мс | 158 мс на Orange | 606 мс на ТВ |
| Остаточная RPC/scheduling overhead | Включена выше | 213 мс | 0: recognizer локальный |
| Полный OCR core | 4331 мс | 9401 мс | 9558 мс |

CURRENT обработал 19 регионов, GOCR — 21 строку. Это разные detector outputs;
время на один и тот же raw frame сравнимо, но количество/состав работы различаются.
В TV_CROP отправлено 204996 байт JSON/base64 crop payload, без HTTP/TCP/IP
заголовков; полный кадр на Orange не передавался. TV_FULL не отправлял OCR
данные на Orange в этом OCR-only replay.

RPC overhead — остаток времени запроса после вычитания server recognition,
включающий передачу, соединение, декодирование и очередь. Это не отдельный
сетевой ping и не измерение физического wire time.

## Подробный профиль GOCR TV_FULL

Отдельный прогон того же Emergency Guard:

| Этап | Время | Доля полного OCR |
|---|---:|---:|
| Pyramid, resize, allocation | 34 мс | 0,4% |
| Копирование входных tensor | 3 мс | <0,1% |
| **TFLite inference detector** | **1331 мс** | **14,1%** |
| Копирование выходных tensor | 3 мс | <0,1% |
| Decode 11 heads | 92 мс | 1,0% |
| **Удаление дублирующихся proposals** | **2731 мс** | **28,9%** |
| **Попарные связи / clustering** | **4691 мс** | **49,6%** |
| Подгонка компонентов | 27 мс | 0,3% |
| Group-head refinement / финальный dedupe | 24 мс | 0,3% |
| Rectification всех строк | 27 мс | 0,3% |
| Recognizer всех строк | 484 мс | 5,1% |
| Полный OCR | **9457 мс** | 100% |

Detector дал 858 raw pieces и 77 group proposals. После dedupe осталось
326 pieces; проверены **52975 пар**, получен 21 компонент.

Главное узкое место — Python postprocess: dedupe и pairwise connections вместе
занимают **7422 мс, около 78,5%** полного OCR. Нейросеть recognizer и сеть
не являются основной причиной этих девяти секунд.

Поэтому перенос recognizer на Orange экономит сотни миллисекунд, но почти
не меняет итог: одинаковый TV detector/postprocess остаётся в обеих ветках.

## Почему это не скорость Google Lens

Исполняются оригинальные Google модели и config, но grouping — существующая
clean-room Python реализация проекта, не нативный C++ Google. Она делает
попарный перебор и много мелких NumPy/Python операций. Native Lens применяет
свой optimized pipeline; его latency этим тестом не измерена.

Существующий portable detector также обрабатывает четыре pyramid inputs:
два 1280×736, один 640×384 и один 160×96 — около 2,15 млн input pixels.
Это поведение существующего worker, а не вновь подобранный профиль.
У current PP detector иной preprocessing; прямое сравнение размеров моделей
не объясняет объём работы. Менять pyramid/threshold ради ускорения здесь
не разрешено и не выполнялось.

## Качество и эквивалентность

Между TV_CROP и TV_FULL совпали:

* количество строк и line_id;
* source_quad, angle, detector_confidence;
* исходные rectified crop pixels;
* **точные входные окна recognizer**.

Текст имеет небольшие отличия: B/В на Luigi, Attack Combos/Attack ComboS
и в/B на Emergency Guard. При одинаковых входах это оставляет различия
runtime/kernel/architecture/greedy decoding как область расследования;
точная внутренняя причина пока не установлена. Параметры не менялись,
homoglyph correction не применялась. Полная текстовая эквивалентность
и production Google parity не заявлены.

## Что ускорять в первую очередь

1. Dedupe и построение pairwise connections: vectorization или native port
   **того же алгоритма**, сохраняя все исходные условия и проверяя точные
   detector outputs/crop hashes до и после.
2. Повторно измерить всю сеть detector после устранения Python bottleneck.
3. Лишь затем выбирать местоположение recognizer по итоговой задержке.

Изменение confidence threshold, anchors, pyramid, grouping constants или
recognizer windows не является допустимым способом улучшения этих чисел.

Сырые результаты:
[evidence/gocr-integration-20261009](evidence/gocr-integration-20261009/).
