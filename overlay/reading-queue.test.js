'use strict';
var assert = require('assert'), create = require('./translation-pairs').create;
function reading(version,text,now,stage) {
  var admission = {track_id:1,version_ms:version,text:text};
  return {gate:{complete:true,required:3,timestamp_ms:now,regions:[{
    slot:0,observations:3,admission:admission,source_text:text,
    appearance:{box:{x:100,y:600,width:600,height:80}}
  }]},responses:{0:{admission:admission,provider:'madlad',stage:stage || 'final',translation:text}}};
}
function update(pairs,f,now) { return pairs.update(f.gate,f.responses,now,'madlad',true); }
var pairs = create(), a = reading(1,'First',1000), b = reading(2,'Second',2000);
var blocks = update(pairs,a,1000);
// Nothing expires before the OSD actually acknowledges displaying it.
assert.strictEqual(update(pairs,b,20000)[0].text,'First');
pairs.shown(blocks,20000);
b.gate.timestamp_ms = 24999;
assert.strictEqual(update(pairs,b,24999)[0].text,'First');
b.gate.timestamp_ms = 25000;
blocks = update(pairs,b,25000);
assert.strictEqual(blocks.length,1);
assert.strictEqual(blocks[0].text,'Second');
pairs.shown(blocks,25000);
b.gate.regions = [];
assert.strictEqual(update(pairs,b,29999)[0].text,'Second');
assert.strictEqual(update(pairs,b,30000).length,0);

pairs = create(); a = reading(1,'First',1000,'preliminary');
blocks = update(pairs,a,1000); pairs.shown(blocks,1000);
b = reading(2,'Second',2000,'preliminary');
assert.strictEqual(update(pairs,b,2000)[0].text,'First');
b.responses[0] = Object.assign({},b.responses[0],{stage:'final',translation:'Second corrected'});
update(pairs,b,2100);
// Already admitted queued text remains readable even if its original leaves.
b.gate.regions = [];
blocks = update(pairs,b,6000);
assert.strictEqual(blocks[0].text,'Second corrected');
pairs.shown(blocks,6000);
assert.strictEqual(update(pairs,b,10999)[0].text,'Second corrected');
assert.strictEqual(update(pairs,b,11000).length,0);

pairs = create(); a = reading(1,'First',1000);
blocks = update(pairs,a,1000); pairs.shown(blocks,1000);
b = reading(2,'Second',2000); update(pairs,b,2000);
var c = reading(3,'Latest',3000); update(pairs,c,3000);
c.gate.timestamp_ms = 6000;
assert.strictEqual(update(pairs,c,6000)[0].text,'Latest','One pending position keeps latest ready reply');
assert.strictEqual(pairs.update(c.gate,c.responses,6100,'madlad',false).length,0);
assert.strictEqual(pairs.update({regions:[]},{},6200,'madlad',true).length,0,'HDMI off clears the queue');

pairs = create(); a = reading(1,'First',1000,'preliminary');
blocks = update(pairs,a,1000); pairs.shown(blocks,1000);
b = reading(2,'Second',2000); update(pairs,b,2000);
var heldFinal = Object.assign({},a.responses[0],{stage:'final',translation:'First corrected'});
b.responses[1] = heldFinal;
blocks = update(pairs,b,3000);
assert.strictEqual(blocks[0].text,'First corrected');
pairs.shown(blocks,3000);
b.gate.timestamp_ms = 7999;
assert.strictEqual(update(pairs,b,7999)[0].text,'First corrected');
b.gate.timestamp_ms = 8000;
assert.strictEqual(update(pairs,b,8000)[0].text,'Second');
console.log('Actual display hold, queued promotion, final upgrades, latest pending and clear: PASS');
