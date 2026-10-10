'use strict';
var assert = require('assert');
var vm = require('vm');
var fs = require('fs');
var handlers, fail, poll, state;
var manualEnabled=false;
var requests=0,destroyed=0,policyChanged;
var foreground = 'com.webos.app.hdmi4';
var settings = {hdmi_inputs: [foreground], provider: 'madlad', translation_server: 'http://192.168.1.11:8765'};
var context = {exports: {}, Date: {now: function () { return 10000; }}, console: console,
  setInterval: function (callback) { poll = callback; },
  require: function (name) {
    if (name === 'fs') return {readFileSync:function(){return JSON.stringify({translationEnabled:manualEnabled});},writeFileSync: function (path, value) { state = value; }, renameSync: function () {}};
    if (name === './app-catalog') return {start: function () {}};
    if (name === './orange-state') return {saveSettings:function(){}};
    if (name === './mobile-server') return {start: function (options) {policyChanged=options.policyChanged;return {};}};
    if (name === 'child_process') return {execFile: function (path, args, options, callback) {
      callback(null, JSON.stringify({returnValue: true, appId: foreground}));
    }};
    if (name === 'http') return {get: function (url, callback) {
      requests++;
      handlers = {};
      callback({statusCode: 200, on: function (name, handler) { handlers[name] = handler; }});
      return {setTimeout: function () {}, on: function (name, callback) { fail = callback; },destroy:function(){destroyed++;fail();}};
    }};
    throw new Error(name);
  }};
vm.runInNewContext(fs.readFileSync(__dirname + '/runtime-control.js', 'utf8'), context);
function deliver() { handlers.data(JSON.stringify(settings)); handlers.end(); }
context.exports.start();
assert(!context.exports.allowed());
assert.strictEqual(requests,0,'OFF bootstrap does not contact Orange');
assert(!context.exports.allowed(), 'Default manual OFF never starts OCR');
manualEnabled=true;poll();deliver();
assert(context.exports.allowed(), 'Manual ON permits the current source');
assert.strictEqual(state.trim().split(' ').slice(0,8).join(' '),'10000 1 madlad 192.168.1.11 8765 0 300 com.webos.app.hdmi4');
settings.russian_idle=true;settings.hdmi_inputs=[];settings.applications=[];poll();deliver();
assert(context.exports.allowed(), 'HDMI lists and language settings no longer gate manual ON');
foreground='youtube.leanback.v4';poll();deliver();
assert(!context.exports.allowed(), 'Source transition invalidates old work');
poll();deliver();assert(context.exports.allowed(), 'No application allowlist is required');
manualEnabled=false;var count=requests;poll();assert(!context.exports.allowed(), 'Manual OFF stops admission');
foreground='com.webos.app.hdmi1';poll();poll();
assert.strictEqual(requests,count,'Repeated OFF ticks do not contact Orange');
assert(!context.exports.allowed(), 'Changing HDMI never turns manual OFF into ON');
manualEnabled=true;poll();deliver();assert(!context.exports.allowed(),'Resume discovers the changed source before admitting work');
poll();deliver();assert(context.exports.allowed());
settings.provider='google';poll();deliver();assert(!context.exports.allowed(), 'Provider change invalidates old work');
poll();deliver();assert(context.exports.allowed());
foreground='com.serjio193.lggametranslator.settings';poll();deliver();
assert(!context.exports.allowed(), 'Our settings page is never translated');
foreground='com.webos.app.hdmi1';poll();deliver();poll();deliver();assert(context.exports.allowed());
poll();fail();assert(!context.exports.allowed(), 'Network failure fails closed');
poll();manualEnabled=false;count=requests;policyChanged();
assert(destroyed>0,'OFF aborts the already pending settings read');
deliver();assert(!context.exports.allowed(),'Late settings reply cannot reactivate OFF');
poll();assert.strictEqual(requests,count,'Late completion does not restart polling');
console.log('Manual OFF/ON, no HDMI/app/language autostart, source invalidation and failure admission: PASS');
