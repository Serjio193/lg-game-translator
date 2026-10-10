'use strict';
var assert = require('assert');
var vm = require('vm');
var fs = require('fs');
var handlers, fail, poll, state;
var foreground = 'com.webos.app.hdmi4';
var settings = {hdmi_inputs: [foreground], provider: 'madlad', translation_server: 'http://192.168.1.11:8765'};
var context = {exports: {}, Date: {now: function () { return 10000; }}, console: console,
  setInterval: function (callback) { poll = callback; },
  require: function (name) {
    if (name === 'fs') return {writeFileSync: function (path, value) { state = value; }, renameSync: function () {}};
    if (name === './app-catalog') return {start: function () {}};
    if (name === './mobile-server') return {start: function () {return {};}};
    if (name === 'child_process') return {execFile: function (path, args, options, callback) {
      callback(null, JSON.stringify({returnValue: true, appId: foreground}));
    }};
    if (name === 'http') return {get: function (url, callback) {
      handlers = {};
      callback({statusCode: 200, on: function (name, handler) { handlers[name] = handler; }});
      return {setTimeout: function () {}, on: function (name, callback) { fail = callback; }};
    }};
    throw new Error(name);
  }};
vm.runInNewContext(fs.readFileSync(__dirname + '/runtime-control.js', 'utf8'), context);
function deliver() { handlers.data(JSON.stringify(settings)); handlers.end(); }
context.exports.start();
assert(!context.exports.allowed());
deliver();
assert(context.exports.allowed());
assert.strictEqual(state.trim().split(' ').slice(0, 8).join(' '), '10000 1 madlad 192.168.1.11 8765 1 60 com.webos.app.hdmi4');
settings.russian_idle = false; settings.language_check_seconds = 300;
poll(); deliver();
assert.strictEqual(state.trim().split(' ').slice(0, 8).join(' '), '10000 1 madlad 192.168.1.11 8765 0 300 com.webos.app.hdmi4');
settings.hdmi_inputs = ['com.webos.app.hdmi2']; poll(); deliver();
assert(!context.exports.allowed(), 'Disabled HDMI stops translation');
settings.hdmi_inputs.push(foreground); settings.provider = 'google';
settings.translation_server = 'http://192.168.1.20:9000'; poll(); deliver();
assert(!context.exports.allowed(), 'Endpoint change first invalidates old admission');
poll(); deliver();
assert(context.exports.allowed());
assert.strictEqual(state.trim().split(' ').slice(0, 8).join(' '), '10000 1 google 192.168.1.20 9000 0 300 com.webos.app.hdmi4');
assert(Number(state.trim().split(' ')[8]) > 10001, 'Reactivation changes the session epoch');
foreground = 'com.serjio193.lggametranslator.settings'; poll(); deliver();
assert(!context.exports.allowed(), 'Non-HDMI apps cannot activate OCR');
foreground = 'youtube.leanback.v4'; settings.applications = [foreground]; poll(); deliver();
assert(!context.exports.allowed(), 'Source change invalidates previous session');
poll(); deliver();
assert(context.exports.allowed(), 'Explicitly selected application activates OCR');
assert(state.indexOf('youtube.leanback.v4') >= 0);
settings.applications = []; poll(); deliver();
assert(!context.exports.allowed(), 'Unselected application stops OCR');
settings.applications = ['com.serjio193.lggametranslator.overlay'];
foreground = settings.applications[0]; poll(); deliver(); poll(); deliver();
assert(!context.exports.allowed(), 'Own overlay never activates OCR');
poll(); fail();
assert(!context.exports.allowed(), 'Network failure denies admission');
console.log('HDMI/app selection, source invalidation and failure admission: PASS');
