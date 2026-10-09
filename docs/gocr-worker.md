# GOCR worker

Цель модуля: дать ему изображение или уже вырезанную Google-строку и получать стабильный структурированный результат с текстом и координатами исходной строки.

## Два режима проекта

### 1. TV_FULL

```text
LG 1280x720 frame
  -> GroupRPN detector
  -> Google grouping
  -> rectified Google crop
  -> GOCR line recognizer
  -> UTF-8 text + original-frame geometry
  -> Orange Pi translation
```

### 2. TV_CROP

```text
LG 1280x720 frame
  -> GroupRPN detector
  -> Google grouping
  -> rectified Google crop + original-frame geometry
  -> Orange Pi
       -> GOCR line recognizer
       -> UTF-8 text
       -> translation
```

Обе ветки обязаны использовать одни и те же оригинальные Google assets/configs. Разрешено менять только место исполнения recognizer.

## Что уже работает

Есть два рабочих entrypoint:

- `gocr_worker.worker` — Google crop -> UTF-8 text + сохранённая geometry;
- `gocr_worker.worker_full` — полный кадр/photo -> GroupRPN -> line quads -> Google crops -> recognizer -> text + geometry.

Full worker использует:
- оригинальный Google GroupRPN `.tflite`;
- оригинальный Android Lens `gocr_group_rpn_text_detection_config_2024_q4.binarypb`;
- параметры threshold/anchors/grouping/profile читаются из binarypb во время запуска;
- оригинальную Google Latin/Cyrillic recognizer модель и label map.

GroupRPN postprocess является clean-room реализацией по восстановленной protobuf-схеме и production-параметрам Google. Он не является копированием исходного C++ Google.

Контрольная parity-проверка 1280x720 против оригинального `libchromescreenai.so`, которому был подан тот же Android Lens detector config:

```text
native lines:   3
portable lines: 3
exact text:     3 / 3
mean bbox IoU:  0.9331705

THE DOOR IS LOCKED  IoU 0.9699
Привет мир          IoU 0.9563
Press E to open     IoU 0.8733
```

Это подтверждает рабочий полный pipeline, но пока не доказывает 100% parity на всех наклонах, curved text и плотных UI.

## Оригинальные Google assets

Модели в git не коммитятся. Из APK извлекаются исходные файлы:

```text
gocr_group_rpn_text_detection_model_2024_q4.tflite
gocr_group_rpn_text_detection_config_2024_q4.binarypb
recognizer_latn_vi_cyrl_lm_retrained.tflite
recognizer_latn_vi_cyrl_label_map.pb
recognizer_cyrl_config.pb
recognizer_cyrl_lm.compact_fst.gz
recognizer_cyrl_lm.syms
recognizer_latn_vi_cyrl_prior.pb
```

Извлечение:

```bash
python3 scripts/extract-gocr-assets.py Google.apk /opt/gocr/assets
```

Скрипт сохраняет `manifest.json` с путём внутри APK, размером и SHA-256 каждого файла.

## Orange Pi: установка

```bash
python3 -m venv /opt/gocr/venv
/opt/gocr/venv/bin/pip install -r gocr_worker/requirements.txt
```

Проверка одного Google crop:

```bash
PYTHONPATH=. /opt/gocr/venv/bin/python -m gocr_worker.worker \\
  --assets /opt/gocr/assets \\
  --threads 4 \\
  crop test-line.png \\
  --meta-json '{"line_id":"17","source_quad":[[120,640],[780,640],[780,690],[120,690]],"angle":0.0,"detector_confidence":0.97}'
```

## HTTP server на Orange Pi

```bash
PYTHONPATH=. /opt/gocr/venv/bin/python -m gocr_worker.worker \\
  --assets /opt/gocr/assets --threads 4 \\
  serve --bind 0.0.0.0 --port 8770
```

Проверка:

```text
GET /v1/health
GET /v1/assets
POST /v1/recognize-crop
POST /v1/ocr
```


## Формат запроса crop

`image_b64` — PNG/JPEG/WEBP/PGM crop в base64. `source_quad` всегда относится к исходному TV frame, а не к координатам crop.

```json
{
  "image_b64": "...",
  "meta": {
    "line_id": "17",
    "source_quad": [[120,640],[780,640],[780,690],[120,690]],
    "angle": 0.0,
    "detector_confidence": 0.97
  }
}
```

## Что ждать на выходе

```json
{
  "schema": "gocr.worker.v1",
  "width": 660,
  "height": 50,
  "mode": "crop",
  "lines": [
    {
      "line_id": "17",
      "text": "THE DOOR IS LOCKED",
      "source_quad": {
        "p0": {"x":120,"y":640},
        "p1": {"x":780,"y":640},
        "p2": {"x":780,"y":690},
        "p3": {"x":120,"y":690}
      },
      "angle": 0.0,
      "detector_confidence": 0.97,
      "recognizer_confidence": null,
      "words": [],
      "symbols": [],
      "timings_ms": {
        "recognizer": 0.0,
        "tflite_invoke": 0.0
      }
    }
  ],
  "parity": {
    "detector": "external_google_crop",
    "recognizer_model": "google_original",
    "recognizer_decoder": "greedy_ctc",
    "production_lm_fst_applied": false,
    "window_contract": "google_config_16_136_16"
  }
}
```

Важный момент: сейчас текстовый decoder — greedy CTC. Оригинальные Google FST/LM/prior файлы переносятся в bundle и не меняются, но production FST decoder ещё не подключён. Поэтому поле `production_lm_fst_applied` честно равно `false`.

## Полный кадр -> текст + координаты

CLI:

```bash
PYTHONPATH=. /opt/gocr/venv/bin/python -m gocr_worker.worker_full \
  --assets /opt/gocr/assets \
  --threads 4 \
  image frame.png
```

HTTP:

```bash
PYTHONPATH=. /opt/gocr/venv/bin/python -m gocr_worker.worker_full \
  --assets /opt/gocr/assets \
  --threads 4 \
  serve --bind 0.0.0.0 --port 8771
```

Endpoint:

```text
POST /v1/ocr
```

Body:

```json
{"image_b64":"..."}
```

Response содержит массив строк. Для каждой строки возвращаются:
- `text`;
- `source_quad` — 4 точки в координатах исходного кадра;
- `angle`;
- `detector_confidence`;
- timings.

## Как подключить к текущему pipeline

Для режима TV_CROP TV после detector отправляет каждый rectified crop на `POST /v1/recognize-crop`, сохраняя `line_id/source_quad/angle`. Полученный `lines[0].text` передаётся существующему `translator/server.py /api/translate`.

Для режима TV_FULL тот же recognizer переносится на LG; по сети передаётся уже `text + geometry`. Формат `gocr.worker.v1` остаётся тем же.

## Правило конфигурации

Не переносить найденные Google параметры в UI и не давать пользователю их крутить. Original `.binarypb/.pb/.fst/.syms` — часть модели. Наши deployment-настройки отвечают только за:

- TV или Orange Pi;
- число CPU threads;
- адрес/порт транспорта;
- включение telemetry.

Это позволяет честно сравнить скорость двух размещений, не меняя сам OCR.
