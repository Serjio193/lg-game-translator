// TV-local bridge for up to twenty independently admitted translation pairs.
'use strict';
var fs = require('fs'), childProcess = require('child_process');
var control = require('./runtime-control');
var layerSettings = require('./layer-settings');
var pairs = require('./translation-pairs').create();
var files = Object.create(null), busy = false, lastShown = null, retryAt = 0;
var nextWindowCheck = 0;
var appId = 'com.serjio193.lggametranslator.overlay';
control.start();

function checkWindow() {
  busy = true;
  nextWindowCheck = Date.now() + 2000;
  childProcess.execFile('/usr/bin/luna-send',['-n','1','-f',
    'luna://com.webos.applicationManager/running','{}'],{timeout:1500},
    function (error,stdout) {
      busy = false;
      try {
        var result = JSON.parse(stdout);
        if (error || !result.returnValue || !Array.isArray(result.running)) return;
        if (!result.running.some(function (app) { return app.id === appId; })) {
          lastShown = null;
          console.log(Date.now() + ' restoring missing OSD window');
          tick();
        }
      } catch (failure) { console.error('OSD window check failed'); }
    });
}

function readResponses(gate) {
  var responses = {};
  // Read held/queued final answers too, after their source leaves the gate.
  for (var slot = 0; slot < 20; slot++) {
    var path = (ppocrFullFeed() ? '/tmp/ppocr-full-osd-slot-' : '/tmp/piccap-translation-slot-') + ('0' + slot).slice(-2) + '.json';
    try {
      var stat = fs.statSync(path), stamp = stat.mtime.getTime();
      if (!files[path] || files[path].stamp !== stamp)
        files[path] = {stamp:stamp,value:JSON.parse(fs.readFileSync(path,'utf8'))};
      responses[slot] = files[path].value;
    } catch (error) {}
  }
  return responses;
}

function tick() {
  var gate = null;
  try { gate = JSON.parse(fs.readFileSync((ppocrFullFeed() ? '/tmp/ppocr-full-osd-admission.json' : '/tmp/piccap-translation-admission.json'),'utf8')); }
  catch (error) {}
  var blocks = pairs.update(gate,readResponses(gate),Date.now(),control.provider(),control.allowed());
  var layers=layerSettings.normalize({});
  try { layers=layerSettings.normalize(JSON.parse(fs.readFileSync('/media/developer/game-translator-layers.json','utf8'))); }
  catch (error) {}
  var signature = JSON.stringify({blocks:blocks,layers:layers});
  if (busy || Date.now() < retryAt) return;
  if (signature === lastShown) {
    if ((blocks.length || (layers.probe!=='off' && control.allowed()))
        && Date.now() >= nextWindowCheck) checkWindow();
    return;
  }
  busy = true;
  var snapshot=JSON.parse(signature);
  blocks=snapshot.blocks;
  var payload = {id:appId,params:{blocks:blocks,layers:snapshot.layers}};
  childProcess.execFile('/usr/bin/luna-send',['-n','1','-f',
    'luna://com.webos.applicationManager/launch',JSON.stringify(payload)],{timeout:5000},
    function (error,stdout) {
      busy = false;
      try {
        if (error || !JSON.parse(stdout).returnValue) throw new Error();
        lastShown = signature;
        pairs.shown(blocks,Date.now());
        nextWindowCheck = Date.now() + 2000;
        var visible = {timestamp_ms:Date.now(),pairs:blocks.map(function (block) {
          return {id:block.id,english:block.source,russian:block.text,box:block.appearance.box};
        })};
        try {
          fs.writeFileSync('/tmp/game-translator-active-pairs.json.tmp',JSON.stringify(visible));
          fs.renameSync('/tmp/game-translator-active-pairs.json.tmp','/tmp/game-translator-active-pairs.json');
        } catch (error) { console.error('Could not publish active pair diagnostics'); }
        console.log(Date.now() + ' active translation pairs: ' + blocks.length);
      } catch (failure) { retryAt = Date.now() + 1000; console.error('overlay launch failed'); }
    });
}
setInterval(tick,250);

function ppocrFullFeed() {
  return fs.existsSync('/media/developer/ppocr-full-osd.enabled');
}
