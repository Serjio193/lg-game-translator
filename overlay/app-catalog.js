// Installed webOS catalogue approach from AmbiSun (MIT); no application launch.
'use strict';
var http = require('http');
var execFile = require('child_process').execFile;
var icons = require('./app-icon');
var fs = require('fs');
var auth = require('./mobile-auth');
var EXCLUDED = ['com.serjio193.lggametranslator.settings', 'com.serjio193.lggametranslator.overlay',
  'com.webos.app.home', 'com.webos.app.inputcommon', 'com.webos.app.screensaver',
  'com.webos.app.tvhotkey', 'com.webos.app.voice', 'com.webos.app.welcomewizard'];
var server = null, cached = null, cachedAt = 0, waiters = [];

function catalogue(payload) {
  if (!payload || payload.returnValue !== true || !Array.isArray(payload.apps)) throw new Error('Catalogue unavailable');
  var seen = Object.create(null), budget = 6 * 1024 * 1024;
  return payload.apps.filter(function (app) {
    if (!app || !app.visible || typeof app.id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(app.id)
        || typeof app.title !== 'string' || !app.title || (app.class || {}).hidden
        || /^com\.webos\.app\.hdmi[1-4]$/.test(app.id) || EXCLUDED.indexOf(app.id) >= 0 || seen[app.id]) return false;
    seen[app.id] = true;
    return true;
  }).slice(0, 256).map(function (app) {
    var icon = icons.toDataUri(app);
    if (icon && icon.length > budget) icon = null;
    if (icon) budget -= icon.length;
    return {id: app.id, name: app.title.slice(0, 240), icon: icon};
  }).sort(function (a, b) { return a.name.localeCompare(b.name); });
}

function load(callback, refresh) {
  if (!refresh && cached && Date.now() - cachedAt < 60000) return callback(null, cached);
  waiters.push(callback);
  if (waiters.length > 1) return;
  execFile('/usr/bin/luna-send', ['-n', '1', '-f', 'luna://com.webos.applicationManager/listApps', '{}'],
    {timeout: 3000, maxBuffer: 4 * 1024 * 1024}, function (error, stdout) {
      var result;
      try {
        if (error) throw error;
        result = catalogue(JSON.parse(stdout));
        cached = result; cachedAt = Date.now();
      } catch (failed) { error = failed; }
      var listeners = waiters; waiters = [];
      listeners.forEach(function (listener) { listener(error, result); });
    });
}

exports.start = function (mobile) {
  if (server) return;
  server = http.createServer(function (request, response) {
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('Content-Type', 'application/json; charset=utf-8');
    if (request.url === '/pairing' && mobile) {
      response.setHeader('Access-Control-Allow-Headers', 'X-OSD-Menu-Key');
      response.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
      if (request.method === 'OPTIONS') { response.end(); return; }
      var key;
      try { key = fs.readFileSync('/media/developer/game-translator-mobile-menu.key', 'utf8').trim(); }
      catch (error) { key = ''; }
      if (request.method !== 'POST' || !auth.equal(key, request.headers['x-osd-menu-key'])) {
        response.statusCode = 403; response.end('{"error":"Подключение разрешено только из меню ТВ"}'); return;
      }
      try { response.end(JSON.stringify(mobile.pairing())); }
      catch (error) { response.statusCode = 503; response.end(JSON.stringify({error:error.message})); }
      return;
    }
    if (request.method !== 'GET' || ['/apps', '/apps?refresh=1'].indexOf(request.url) < 0) {
      response.statusCode = 404; response.end('{"error":"Not found"}'); return;
    }
    load(function (error, applications) {
      response.statusCode = error ? 503 : 200;
      response.end(JSON.stringify(error ? {error: 'Не удалось получить приложения ТВ'} : {applications: applications}));
    }, request.url === '/apps?refresh=1');
  });
  server.on('error', function () { console.error('Local app catalogue unavailable'); });
  server.listen(18779, '127.0.0.1');
};
exports.catalogue = catalogue;
