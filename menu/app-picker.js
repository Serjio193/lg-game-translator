(function (root) {
  'use strict';
  var list = document.getElementById('app-list');
  var status = document.getElementById('app-status');
  var selected = [], catalogue = [], ready = false, disabled = true;

  function render() {
    list.textContent = '';
    var rows = catalogue.slice(), known = Object.create(null);
    rows.forEach(function (app) { known[app.id] = true; });
    selected.forEach(function (id) {
      if (!known[id]) rows.push({id: id, name: id + ' — недоступно в текущем списке'});
    });
    rows.forEach(function (app) {
      var row = document.createElement('label'); row.className = 'app-row';
      var icon = document.createElement('span'); icon.className = 'app-icon';
      if (app.icon && /^data:image\/(png|jpeg|webp);base64,/.test(app.icon)) {
        var image = document.createElement('img'); image.src = app.icon; image.alt = '';
        image.onerror = function () { icon.textContent = app.name.charAt(0); };
        icon.appendChild(image);
      } else { icon.textContent = app.name.charAt(0); }
      var name = document.createElement('span'); name.className = 'app-name'; name.textContent = app.name;
      var input = document.createElement('input'); input.type = 'checkbox'; input.value = app.id;
      input.checked = selected.indexOf(app.id) >= 0; input.disabled = disabled;
      input.addEventListener('change', function () {
        sync(); document.getElementById('status').textContent = 'Изменения ещё не сохранены';
      });
      row.appendChild(icon); row.appendChild(name); row.appendChild(input); list.appendChild(row);
    });
    if (ready && !rows.length) status.textContent = 'Доступных приложений нет';
  }

  function controls() { return Array.prototype.slice.call(list.querySelectorAll('input')); }
  function sync() {
    // Retain saved selections if the live catalogue is temporarily unavailable.
    selected = controls().filter(function (input) { return input.checked; }).map(function (input) { return input.value; });
  }
  function load(refresh) {
    status.textContent = 'Загрузка приложений ТВ…';
    var xhr = new XMLHttpRequest(); xhr.open('GET', 'http://127.0.0.1:18779/apps' + (refresh ? '?refresh=1' : '')); xhr.timeout = 5000;
    xhr.onload = function () {
      try {
        var value = JSON.parse(xhr.responseText);
        if (xhr.status !== 200 || !Array.isArray(value.applications)) throw new Error();
        catalogue = value.applications.filter(function (app) {
          return app && typeof app.id === 'string' && typeof app.name === 'string';
        });
        ready = true; status.textContent = 'Выберите приложения для перевода'; render();
      } catch (_) { status.textContent = 'Список недоступен. Нажмите «Обновить приложения».'; }
    };
    xhr.onerror = xhr.ontimeout = function () { status.textContent = 'Нет связи с каталогом ТВ. Сохранённый выбор сохранён.'; };
    xhr.send();
  }
  root.AppPicker = {
    load: load, controls: controls,
    set: function (ids) { selected = (ids || []).slice(); render(); },
    get: function () { sync(); return selected.slice(); },
    enable: function (value) { disabled = !value; controls().forEach(function (input) { input.disabled = disabled; }); }
  };
  document.getElementById('refresh-apps').addEventListener('click', function () { load(true); });
}(window));
