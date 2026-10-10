// Power URI and response fields follow AmbiSun (MIT, AmbiSun-LICENSE.txt).
// Unknown/cancelled power state never authorizes a translation session.
'use strict';
var spawn = require('child_process').spawn;
var stream = require('./luna-json-stream');
var URI = 'luna://com.webos.service.tvpower/power/getPowerState';

function classify(payload) {
  if (!payload || payload.returnValue === false) return 'unknown';
  var value = payload.state || payload.powerState;
  if (typeof value !== 'string') return 'unknown';
  value = value.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]/g, ' ').trim();
  if (/^(on|active)$/i.test(value)) return 'awake';
  if (/screen\s*(saver|off)|standby|suspend|power\s*off|^(off|sleep)$/i.test(value)) return 'asleep';
  return 'unknown';
}

exports.create = function (options) {
  options = options || {};
  var launch = options.spawn || spawn;
  var schedule = options.setTimeout || setTimeout;
  var clear = options.clearTimeout || clearTimeout;
  var state = 'unknown', child = null, retry = null, initial = null, stopped = true;

  function transition(next) {
    if (state === next) return;
    var previous = state;
    state = next;
    if (options.changed) options.changed(previous, next);
  }
  function connect() {
    if (stopped) return;
    var process, finished = false;
    function lost() {
      if (finished) return;
      finished = true;
      if (initial !== null) { clear(initial); initial = null; }
      if (process && child === process) child = null;
      transition('unknown');
      if (!stopped) retry = schedule(connect, 5000);
    }
    function abort() {
      lost();
      if (process) process.kill('SIGTERM');
    }
    try {
      process = launch('/usr/bin/luna-send', ['-i', '-f', URI, '{"subscribe":true}'],
        {stdio:['pipe','pipe','pipe']});
      child = process;
      process.on('error', lost);
      process.on('close', lost);
      var acknowledged = false;
      var decode = stream.create(function (payload) {
        if (finished || stopped) return;
        if (payload.returnValue === false || payload.subscribed === false) { abort(); return; }
        if (!acknowledged) {
          if (payload.subscribed !== true) { abort(); return; }
          acknowledged = true;
        }
        if (!payload.state && !payload.powerState) return;
        var next = classify(payload);
        if (next === 'unknown') { abort(); return; }
        if (initial !== null) { clear(initial); initial = null; }
        transition(next);
      });
      process.stdout.setEncoding('utf8');
      process.stdout.on('data', function (chunk) {
        if (finished || stopped) return;
        try { decode(chunk); } catch (error) { abort(); }
      });
      process.stdout.on('error', abort);
      process.stdin.on('error', abort);
      process.stderr.on('error', abort);
      process.stderr.resume();
      initial = schedule(abort, 3000);
    } catch (error) { abort(); }
  }
  return {
    start:function () { if (!stopped) return; stopped = false; connect(); },
    awake:function () { return state === 'awake' && !stopped; },
    state:function () { return state; },
    stop:function () {
      stopped = true;
      if (retry !== null) { clear(retry); retry = null; }
      if (initial !== null) { clear(initial); initial = null; }
      var process = child; child = null;
      transition('unknown');
      if (process) process.kill('SIGTERM');
    }
  };
};
exports.classify = classify;
exports.URI = URI;
