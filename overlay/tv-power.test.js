'use strict';
var assert = require('assert'), EventEmitter = require('events');
var power = require('./tv-power'), jsonStream = require('./luna-json-stream');

assert.strictEqual(power.classify({returnValue:true,state:'On'}), 'awake');
assert.strictEqual(power.classify({returnValue:true,powerState:'Active'}), 'awake');
['Standby','Active Standby','Screen Saver','Suspend','PowerOff','ScreenOff','Off'].forEach(function (state) {
  assert.strictEqual(power.classify({state:state}), 'asleep');
});
assert.strictEqual(power.classify({returnValue:false,state:'On'}), 'unknown');
assert.strictEqual(power.classify({state:'unrecognized'}), 'unknown');

var children = [], timers = new Map(), nextTimer = 1, changes = [];
function spawn(command, args) {
  assert.strictEqual(command, '/usr/bin/luna-send');
  assert.deepStrictEqual(args, ['-i','-f',power.URI,'{"subscribe":true}']);
  var child = new EventEmitter();
  child.stdout = new EventEmitter(); child.stdout.setEncoding = function () {};
  child.stdin = new EventEmitter(); child.stderr = new EventEmitter();child.stderr.resume=function () {};
  child.kill = function (signal) { assert.strictEqual(signal,'SIGTERM'); child.emit('close'); };
  children.push(child); return child;
}
var monitor = power.create({spawn:spawn,
  setTimeout:function (callback, delay) {var id=nextTimer++;timers.set(id,{callback:callback,delay:delay});return id;},
  clearTimeout:function (id) {timers.delete(id);},
  changed:function (before, after) {changes.push([before,after]);}
});
function send(child, value) {child.stdout.emit('data',JSON.stringify(value)+'\n');}
function runTimer(delay) {
  var entry=Array.from(timers.entries()).find(function (entry) {return entry[1].delay===delay;});
  assert(entry,'Expected scheduled timer '+delay);timers.delete(entry[0]);entry[1].callback();
}
monitor.start(); monitor.start(); assert.strictEqual(children.length,1);
assert(!monitor.awake());
var message=JSON.stringify({returnValue:true,subscribed:true,state:'On',extra:{note:'brace } quote "'}});
children[0].stdout.emit('data',message.slice(0,22));assert(!monitor.awake());
children[0].stdout.emit('data',message.slice(22));assert(monitor.awake());
children[0].stdout.emit('data',JSON.stringify({state:'Standby'})+'\n'+JSON.stringify({state:'On'}));
assert.deepStrictEqual(changes.slice(-2),[['awake','asleep'],['asleep','awake']]);
children[0].emit('close');assert(!monitor.awake());
send(children[0],{state:'On'});assert(!monitor.awake(),'Late disconnected child cannot authorize power');
runTimer(5000);assert.strictEqual(children.length,2);
send(children[1],{returnValue:true,state:'On'});
assert(!monitor.awake(),'An unconfirmed subscription cannot authorize translation');
runTimer(5000);send(children[2],{returnValue:true,subscribed:true});
assert(!monitor.awake(),'An acknowledgement without power still waits for a state');
runTimer(3000);assert(!monitor.awake());
runTimer(5000);send(children[3],{returnValue:true,subscribed:true,powerState:'Active'});
assert(monitor.awake());
children[3].emit('error',new Error('subscription lost'));assert(!monitor.awake());
runTimer(5000);send(children[4],{returnValue:true,subscribed:true,state:'On'});assert(monitor.awake());
send(children[4],{returnValue:false,errorText:'denied'});assert(!monitor.awake());
runTimer(5000);send(children[5],{returnValue:true,subscribed:true,state:'On'});assert(monitor.awake());
monitor.stop();assert(!monitor.awake());assert.strictEqual(timers.size,0);
send(children[5],{state:'On'});assert(!monitor.awake());

var received=[];var decode=jsonStream.create(function (value) {received.push(value);});
decode(' {"state":"On"}\n{"state":"Sleep"} ');assert.strictEqual(received.length,2);
assert.throws(function () {jsonStream.create(function () {})('not JSON');});
assert.throws(function () {jsonStream.create(function () {})(' '.repeat(65537));});
console.log('Power subscription acknowledgement, JSON streaming, sleep/wake, unknown/error/timeout and cleanup: PASS');
