(function () {
  'use strict';
  var endpoint = 'http://192.168.1.11:8765/api/settings';
  var inputs = Array.prototype.slice.call(document.querySelectorAll('.inputs input[type="checkbox"]'));
  var idle = document.getElementById('russian-idle');
  var languageCheck = document.getElementById('language-check');
  var provider = document.getElementById('provider');
  var server = document.getElementById('server');
  var save = document.getElementById('save');
  var status = document.getElementById('status');
  function request(method, value, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, endpoint);
    xhr.timeout = 5000;
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
      try {
        var result = JSON.parse(xhr.responseText);
        if (xhr.status !== 200) throw new Error(result.error || 'Ошибка сервера');
        callback(null, result);
      } catch (error) { callback(error); }
    };
    xhr.onerror = xhr.ontimeout = function () { callback(new Error('Нет связи с Orange Pi')); };
    xhr.send(value ? JSON.stringify(value) : null);
  }
  function enabled(value) {
    save.disabled = !value;
    inputs.forEach(function (input) { input.disabled = !value; });
    provider.disabled = server.disabled = !value;
    idle.disabled = languageCheck.disabled = !value;
    window.AppPicker.enable(value);
  }
  function load() {
    request('GET', null, function (error, settings) {
      if (error) { status.textContent = error.message + '. Нажмите OK для повтора.'; return; }
      inputs.forEach(function (input) { input.checked = settings.hdmi_inputs.indexOf(input.value) >= 0; });
      window.AppPicker.set(settings.applications || []);
      provider.value = settings.provider;
      server.value = settings.translation_server;
      idle.checked = settings.russian_idle !== false;
      languageCheck.value = String(settings.language_check_seconds || 60);
      enabled(true);
      status.textContent = 'Настройки загружены';
      inputs[0].focus();
    });
  }
  document.getElementById('settings').addEventListener('submit', function (event) {
    event.preventDefault();
    var selected = inputs.filter(function (input) { return input.checked; })
      .map(function (input) { return input.value; });
    enabled(false);
    status.textContent = 'Сохранение…';
    window.GoogleSettings.select(provider.value, function (providerError) {
      if (providerError) { enabled(true); status.textContent = providerError.message; return; }
      request('POST', {hdmi_inputs: selected, applications: window.AppPicker.get(), provider: provider.value,
        translation_server: server.value.trim(), russian_idle: idle.checked,
        language_check_seconds: Number(languageCheck.value)}, function (error) {
        enabled(true);
        status.textContent = error ? error.message + '. Настройки не сохранены.' : 'Сохранено';
        save.focus();
      });
    });
  });
  document.getElementById('back').addEventListener('click', function () { window.close(); });
  document.addEventListener('keydown', function (event) {
    if (event.keyCode === 461 || event.key === 'Escape') { window.close(); return; }
    if (save.disabled && event.keyCode === 13 && inputs[0].disabled) { load(); return; }
    var controls = inputs.concat(window.AppPicker.controls(), [document.getElementById('refresh-apps'),
      provider, server, document.getElementById('google-key'), document.getElementById('google-key-save'),
      idle, languageCheck, save, document.getElementById('back')]);
    var index = controls.indexOf(document.activeElement);
    if (event.keyCode >= 37 && event.keyCode <= 40) {
      if ((document.activeElement === server || document.activeElement === document.getElementById('google-key')) && (event.keyCode === 37 || event.keyCode === 39)) return;
      if ((document.activeElement === provider || document.activeElement === languageCheck)
          && (event.keyCode === 37 || event.keyCode === 39)) {
        event.preventDefault();
        var selector = document.activeElement;
        selector.selectedIndex = Math.max(0, Math.min(selector.options.length - 1,
          selector.selectedIndex + (event.keyCode === 37 ? -1 : 1)));
        status.textContent = 'Изменения ещё не сохранены';
        return;
      }
      event.preventDefault();
      var direction = event.keyCode === 37 || event.keyCode === 38 ? -1 : 1;
      var target = Math.max(0, Math.min(controls.length - 1, index + direction));
      if (!controls[target].disabled) {
        controls[target].focus();
        controls[target].scrollIntoView({block: 'nearest'});
      }
    }
    if (event.keyCode === 13 && document.activeElement.type === 'checkbox') {
      event.preventDefault();
      document.activeElement.checked = !document.activeElement.checked;
      if (window.AppPicker.controls().indexOf(document.activeElement) >= 0) window.AppPicker.get();
      status.textContent = 'Изменения ещё не сохранены';
    }
  });
  load();
  window.AppPicker.load();
}());
