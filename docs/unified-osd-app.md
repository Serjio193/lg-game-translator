# Одно приложение «Перевод игры» — 0.2.0

Единственный устанавливаемый app id: `com.serjio193.lggametranslator.overlay`.
Старое приложение `com.serjio193.lggametranslator.settings` удалено с ТВ после
установки объединённого OSD. Меню является набором HTML-ресурсов внутри OSD;
отдельный `menu/appinfo.json` удалён, чтобы не создавать вторую иконку повторно.

Открытие иконки (без translation payload) или `{menu:true}` показывает большой
тумблер по центру. OK меняет существующий локальный translationEnabled;
aria-checked/цвет/надпись отражают реальное состояние. «Настройки» открывает
внутренний раздел с переводчиком, сервером, бюджетом, ключом и QR/PIN телефона.
Back из настроек возвращает к тумблеру, Back из главного экрана или «Вернуться
к игре» удаляет iframe меню, сохраняя прозрачную поверхность субтитров.

`overlay/osd-shell.js` различает пользовательское открытие и фоновые команды
blocks/text/layers. Перевод не открывает и не закрывает меню. Сообщение закрытия
принимается только от текущего embedded frame; оно не меняет настройки и
не передаёт секретов. Пока меню открыто, idle timer не закрывает OSD.

Авторизация, включение с пульта/телефона, питание/OFF и серверный API прежние.
Device menu capability устанавливается в `overlay/menu/menu-key.js`; ключ не
попадает в Git/IPK. Runtime Node-controller и transport relay не являются
отдельными launcher applications. Detector, OCR, PicCap, модели и thresholds
этим обновлением не изменены.

## Сборка и установка

1. `python scripts/package-unified-osd.py`: собирает один IPK из OSD и menu assets.
2. `python scripts/package-mobile-osd.py`: комплект controller/relay 0.2.0.
3. Установить `com.serjio193.lggametranslator.overlay_0.2.0_all.ipk`, распаковать
   комплект и запустить существующий `install-mobile.sh`. Он создаёт capability
   для встроенного меню и перезапускает controller/relay.
4. После проверки встроенного меню удалить прежний settings app. На G5
   использован штатный `com.webos.appInstallService/dev/remove`.

Прежние отчёты 0.1.x описывают историческое состояние с двумя приложениями.
Обновление IPK меняет файлы overlay, поэтому сборка включает установленный
watcher с прежним PP-OCR feed, start-controller и surface-probe без новых тестовых
эффектов. Ранее рабочая frontend логика сохраняется в читаемых исходниках.

## Проверено 2026-10-10

- 21 Node test files прошли; routing и iframe message source, возврат меню,
  аутентификация, reading queue и layout покрыты существующими/new regressions.
- IPK/комплект собраны и установлены, appinfo 0.2.0 подтверждён.
- listApps показывает ровно один id семейства lg-game-translator, visible=true,
  title «Перевод игры». Старый settings directory отсутствует.
- Локальный authenticated toggle GET HTTP 200; controller/relay работают.
- Пользователь подтвердил: тумблер виден по центру и переключается кнопкой OK.
- Пользователь подтвердил: после «Вернуться к игре»/Back меню исчезает,
  перевод остаётся поверх игры.
- После пользовательского ON control.state active=1, HDMI4 остаётся foreground,
  watcher показывает 2 активные translation pairs. Это runtime proof, а не
  отдельное визуальное подтверждение всех переведённых строк.

Backup обеих прежних приложений (0600):
`/media/developer/gocr-runtime/backups/pre-unified-0.2.0-20261010.tar.gz`.
Installer backups: `mobile-osd-1791663566106`, `app-menu-20261010-231926`.
