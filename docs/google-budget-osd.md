# Google Translate: лимит, ключ и меню OSD

Реализовано 2026-10-10. Рабочий provider остаётся `madlad`; Google включается
только выбором пользователя, после сохранения API-ключа. Capture/OCR/OSD renderer
не меняются. Меню ТВ 0.1.4 и телефонная вкладка «Перевод» показывают источник,
символы за месяц, остаток и заполнение лимита; опрос каждые 3 секунды.

## Учёт запросов

`translator/google_budget.py` хранит SQLite WAL в приватной директории Orange.
`BEGIN IMMEDIATE` атомарно резервирует `len(q)` Unicode code points непосредственно
перед каждым сетевым вызовом существующего Google Basic v2 NMT клиента.
Каждая попытка, включая повтор, учитывается отдельно; таймаут, HTTP-ошибка,
пустой/невалидный ответ и остановка процесса не возвращают бюджет автоматически.
Успех меняет состояние `reserved` на `completed`, не уменьшает расход.
Пустые запросы запрещены. Пробелы, CJK, emoji и передаваемые маркеры учитываются.
Существующая дедупликация одинаковых запросов и namespace кэша сохранены.
Cache HIT не вызывает Google; доступен и при исчерпанном бюджете.
Нет автоматического платного превышения или перехода на другой provider.

Предел — 490 000. UI показывает календарный месяц UTC и дополнительно защитное
скользящее окно 32 дня. Остаток равен `490000-max(monthly, rolling32days)`.
Это консервативная защита, пока граница расчётного месяца Google не доказана:
первого числа остаток может **не** восстановиться полностью. Она намеренно
не использует время суточного reset квот как время месячного кредита.
Смена provider/ключа, перезапуск и очистка translation cache журнал не сбрасывают.
Предполагается корректное системное время; удаления журнала/искусственные прыжки
часов, внешние запросы и расход других клиентов локальный счётчик не покрывает.

Google описывает первые 500 000 NMT символов в месяц как кредит $10, общий для
Basic/Advanced; пробелы и непереводимые символы также тарифицируются.
[Официальная тарификация](https://cloud.google.com/products/translate/pricing).
До реального включения нужен проект с доступным кредитом и без неучтённого
расхода. Наш UI не считывает Google Billing и не гарантирует отсутствие иных
платных сервисов/внешнего использования того же проекта.

## Шифрование и доступ

`google_vault.py`: AES-256-GCM, случайный nonce, authenticated context.
Директория `~/.local/share/lg-game-translator/private` — 0700,
`master.key`, `transport.pem`, `control.key`, `google-key.enc` — 0600.
Секрет сохраняется атомарной заменой; мастер-ключ остаётся только на Orange.
Это шифрование хранения, не защита от root/захвата самого серверного аккаунта.
`GOOGLE_API_KEY` environment больше не является источником ключа.
Старый env-key, если существовал, нужно перенести через защищённый provisioning;
на проверенном Orange ключ отсутствовал, миграция не потребовалась.

`/api/google-control` требует отдельный `X-OSD-Control-Key`; отдаёт только
provider, key_configured, открытый RSA ключ и budget. POST принимает provider
и/или encrypted_key. Plaintext key запрещён. RSA-OAEP SHA-256 расшифровывается
на Orange, после чего сохраняется AES-GCM. Google получает API-key только в
HTTPS header; URL, журнал, исходники и браузерные ответы ключ не содержат.

Меню ТВ отправляет key только loopback 127.0.0.1:18779 с установленной menu
capability; Node RSA-шифрует до передачи Orange. Телефонный endpoint требует
PIN-session + Origin/Host. На обычном LAN HTTP ввод ключа заблокирован;
secure-context браузер использует WebCrypto и отправляет только ciphertext.
LAN control transport пока HTTP: RSA не заменяет TLS/аутентификацию публичного
ключа против активного MITM. Не открывать endpoint в Интернет.

## Установка на ТВ

Собраны `settings_0.1.4_all.ipk` и `mobile-osd-controller-0.1.4.tar.gz`.
Owner-only provisioning файл создан на Orange:
`~/.local/share/lg-game-translator/private/tv-provider-config.json`.
Он содержит **не Google API-key**, а адрес сервера и приватную capability.
Передать его на ТВ по SSH в директорию распаковки как `provider-config.json`,
затем запустить `install-mobile.sh`. Не помещать его в Git/общий archive.
Установщик пишет `/media/developer/game-translator-provider.json` с mode 0600.
Повторный IPK install требует повторного controller install для menu capability.

## Проверено и границы

- Python: атомарность 20 конкурентных резервов, точный предел, persistence,
  Unicode, timeout accounting, boundary 32 дня, cache HIT после лимита,
  RSA/AES restart/tamper и авторизация/status без secret.
- Node: phone session/CSRF, anonymous denial, запрет plaintext key, TV RSA proxy.
- IPK/controller archive собраны; browser preview показывает переключатель
  и счётчик и явно сообщает, что это макет без сетевых переводов.
- Orange: backup, обновление translation service, restart, health ok,
  control без auth 401, authenticated status: madlad, key_configured=false,
  0 из 490 000. Provider не переключался; реальных Google API вызовов не было.
- ТВ недоступен: установка 0.1.4, loopback key encryption на его Node runtime,
  live provider switching и физическое отображение ещё не проверены.
