# OCR отдельно от двух этапов перевода

Версия 0.1.8, 2026-10-10. Код подготовлен, TV install pending. Orange translation
API обновлён с backup/restart/health; provider `madlad` не переключался.

## Исполнение

При `PP_OCR_FULL_OSD=1` и `ORANGE_FULL` TV handler вызывает
`FramePipeline.process(..., ocr_only=True)`. Существующий FrameClient получает
полный OCR-ответ, проверяет frame identity, policy и геометрию как прежде.
У него не вызывается inline переводчик. Handler передаёт OCR координатору и
возвращает ответ PicCap без ожидания HTTP-переводов. Generic/benchmark пути
сохраняют прежнее синхронное поведение; модели/параметры/capture не изменены.

`LiveTranslations` использует только проверенный `source_session`: foreground,
provider, host, port, epoch. Поэтому выбранный Google/локальный переводчик и
адрес теперь применяются к этому пути, вместо фиксированного MADLAD из CLI.
Смена session уничтожает pending state старого источника. Перед API-вызовом и
публикацией снова проверяется действующая session. После OFF принятая работа
может завершиться/записать final cache, но её ответ в OSD не отправляется.

`OsdPublisher.observe()` увеличивает счётчики по свежим OCR-кадрам ещё до перевода:
тот же текст, прежняя IoU-проверка, уникальный возрастающий sequence. Сравнение
NFC/пробелов сохраняет регистр и пунктуацию. Сброс sequence при более свежем
capture timestamp распознаётся как restart producer и сбрасывает треки, а не
замораживает наблюдения. Дублирующий пакет не добавляет подтверждение.
Отсутствие/смена текста сбрасывают
трек; перевод/callback/cache не добавляют наблюдений. Координаты стабильной
версии сохраняются по существующему правилу.

## Предварительный и окончательный этапы

1. Для нового разрешённого текста `/api/translate-preview` сначала проверяет
   cache выбранного final provider. HIT возвращает final; модели не запускаются.
2. MISS вызывает прежний `_preview()` / Bergamot. Этот результат не записывается
   в SQLite. `provider` обозначает выбранную цепочку, `engine=bergamot` — настоящий
   предварительный двигатель; `stage=preliminary`.
3. После завершения предварительного этапа и **трёх** OCR-подтверждений текущего
   исходного текста координатор вызывает обычный `/api/translate` выбранного
   final provider. В Google-режиме это Google, в локальном — MADLAD.
4. Final caching/coalescing, encrypted key и atomic Google character budget
   остаются существующими. Пустой/ошибочный ответ не становится переводом.
5. `admission.js` разрешает ранний Bergamot только для текущей track/version/text,
   complete/fresh gate и явного `confirmation_policy=three-final-v1`, выставленного
   доверенным coordinator. Final всегда требует 3. Старые профили без marker
   сохраняют свой gate 3. Translation-pairs/font/layout/reading queue не заменяются.
6. Одинаковые переводы предварительного и final этапов не меняют видимые блоки:
   существующий watcher сравнивает их подпись. Отличающийся final обновляет ту
   же актуальную версию, а не создаёт новую реплику в reading queue.

Идентичные source text/type в текущей session делят один запрос, сохраняя разные
трек/позицию/счётчики. Final общей фразы не публикуется в другом кропе, пока тот
сам не набрал 3. Cache HIT также остаётся final и показывается после gate 3.
Ошибка preview допускает final после 3; ошибка final не вызывает автоматических
платных retries для той же версии. При новом manual session можно пробовать вновь.

Два preview и два final HTTP slots независимы. Нет очереди истории всех версий:
pending состоит только из максимум 20 text/type groups последнего полного кадра;
уже запущено максимум 4 jobs. Истёкшие версии удаляются до запуска. Timeout
HTTP-клиента — прежние 30 секунд. Это не четыре копии моделей на TV: там только
HTTP-задания, NPU/переводные модели остаются на Orange с прежними настройками.

## Проверки

- 11 новых coordinator тестов: 3 разных кадра, preview-before-final,
  nonblocking OCR, blocked final не мешает новому preview, case reset, cache HIT,
  source/region sharing, independent counts, OFF/late replies и bounded pending.
- 50 translator тестов, включая реальный preview HTTP handler с временным
  SQLite: Google никогда не вызывается preview endpoint, Bergamot не сохраняется,
  Google final HIT не вызывает модели, bad/CJK preview отклоняются.
- Handler regression подтверждает `ocr_only=True` и независимую публикацию;
  прежние publisher/transport/early/legacy integration тесты проверяются отдельно.
- Изолированный live preview на Orange: `We should check the map before we leave.`
  → «Мы должны проверить карту, прежде чем уйти.»; engine Bergamot,
  reported inference `latency_ms=378.197`, cache MISS. Это не end-to-end latency
  ТВ и не warmed-series benchmark. Google usage 0→0, key absent, selected madlad.
- ТВ недоступен: install, physical OSD и latency от появления текста ещё не проверены.
  Реальный Google final/его качество не проверены без пользовательского ключа.

## Оставшиеся этапы

В 0.1.9 предварительный путь разделён на завершённые предложения с
переиспользованием частей и добавлением в OSD слева; детали и ограничения:
[sentence-preview-osd.md](sentence-preview-osd.md). Финальная проверка целого
блока не заменена проверкой отдельных предложений.

Текущий native sender всё ещё выбирает/отправляет кадры сам. Pull request от Orange,
новый empty-screen scheduler, idle supervisor и выгрузка моделей после 5 минут
не реализованы этим изменением. В live deferred path сначала принимается полный
авторитетный OCR-кадр; early region events пока не запускают предварительный
перевод до окончания остальных кропов. Legacy early path оставлен для сравнения.

Полный TYPEWRITER по росту области/времени/тексту также ещё не подключён. Сейчас
есть точный счётчик исходного текста и существующая translation policy. Три
быстрых равных кадра не доказывают конец печати: эту границу нужно проверить
на сложных сохранённых/живых репликах перед включением Google в production.
