// Manual translation admission. Source identity invalidates late work, never starts it.
'use strict';
var fs = require('fs');
var http = require('http');
var execFile = require('child_process').execFile;
var active = false;
var provider = 'madlad';
var host = '192.168.1.11';
var port = 8765;
var busy = false;
var russianIdle = false;
var languageCheck = 300;
var foregroundId = '';
var sourceEpoch = Date.now();
var path = '/tmp/game-translator-control.state';
var catalog = require('./app-catalog');
var snapshots = require('./orange-state');
var powerModule = require('./tv-power');
var power = null, store = null, started = false;
var cancelRequest = null;
var EXCLUDED = ['com.serjio193.lggametranslator.settings', 'com.serjio193.lggametranslator.overlay'];

function manuallyEnabled() {
  try {return JSON.parse(fs.readFileSync('/media/developer/game-translator-layers.json','utf8')).translationEnabled===true;}
  catch(error) {return false;}
}

function publish(value) {
  if (value === true && !active) sourceEpoch = Math.max(sourceEpoch + 1, Date.now());
  active = value === true;
  fs.writeFileSync(path + '.tmp', String(Date.now()) + ' ' + (active ? '1' : '0')
    + ' ' + provider + ' ' + host + ' ' + port + ' ' + (russianIdle ? 1 : 0)
    + ' ' + languageCheck + ' ' + foregroundId + ' ' + sourceEpoch + '\n');
  fs.renameSync(path + '.tmp', path);
}

function forceOff(invalidateCommands) {
  active = false;
  try { publish(false); } catch (error) { console.error('Control state write failed'); }
  if (cancelRequest) cancelRequest();
  if (!store) return;
  try {
    var value = store.read();
    if (value.settings.translationEnabled)
      store.update({revision:value.revision,patch:{translationEnabled:false}});
    if (invalidateCommands && store.invalidate) store.invalidate();
  } catch (error) { console.error('Cannot persist translation OFF'); }
}

function poll() {
  if (!power || !power.awake()) { forceOff(); return; }
  if (!manuallyEnabled()) {
    if (cancelRequest) cancelRequest();
    publish(false); return;
  }
  if (busy) return;
  busy = true;
  var finished = false;
  function finish(value) {
    if (finished) return;
    finished = true;
    busy = false;
    cancelRequest = null;
    try { publish(value); } catch (error) { active = false; console.error('Control state write failed'); }
  }
  var request = http.get('http://192.168.1.11:8765/api/settings', function (response) {
    var body = '';
    response.on('data', function (chunk) {
      body += chunk;
      if (body.length > 65536) { response.destroy(); finish(false); }
    });
    response.on('error', function () { finish(false); });
    response.on('end', function () {
      var settings, changed = false;
      try {
        settings = JSON.parse(body);
        if (response.statusCode !== 200) throw new Error();
        var address = /^http:\/\/([a-zA-Z0-9.-]+):(\d+)$/.exec(settings.translation_server);
        if (!address || ['madlad', 'google'].indexOf(settings.provider) < 0) throw new Error();
        changed = provider !== settings.provider || host !== address[1] || port !== Number(address[2]);
        provider = settings.provider;
        host = address[1]; port = Number(address[2]);
        snapshots.saveSettings(settings);
      } catch (error) { finish(false); return; }
      execFile('/usr/bin/luna-send', ['-n', '1', '-f',
        'luna://com.webos.applicationManager/getForegroundAppInfo', '{}'], {timeout: 1500},
        function (error, stdout) {
          try {
            var foreground = JSON.parse(stdout);
            var id = foreground.appId;
            var valid = typeof id === 'string' && /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(id);
            var selected = manuallyEnabled() && valid && EXCLUDED.indexOf(id) < 0;
            var sourceChanged = foregroundId !== '' && foregroundId !== (valid ? id : 'none');
            foregroundId = valid ? id : 'none';
            finish(!changed && !sourceChanged && !error && foreground.returnValue === true && selected);
          } catch (parseError) { finish(false); }
        });
    });
  });
  request.setTimeout(1500, function () { request.destroy(); finish(false); });
  request.on('error', function () { finish(false); });
  cancelRequest = function () { request.destroy(); finish(false); };
}

exports.start = function () {
  if (started) return;
  started = true;
  var mobile = require('./mobile-server').start({policyChanged:function () {
    publish(false);
    if (!manuallyEnabled() && cancelRequest) cancelRequest();
  },canTranslate:function () { return power !== null && power.awake(); }});
  store = mobile.store;
  forceOff(true);
  power = powerModule.create({changed:function () { forceOff(true); }});
  power.start();
  if (typeof process !== 'undefined') {
    process.once('exit', function () { power.stop(); });
    ['SIGTERM','SIGINT'].forEach(function (signal) {
      process.once(signal, function () { power.stop(); process.exit(0); });
    });
  }
  catalog.start(mobile); publish(false); poll(); setInterval(poll, 2000);
};
exports.allowed = function () { return active; };
exports.provider = function () { return provider; };
