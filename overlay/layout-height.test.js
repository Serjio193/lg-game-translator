'use strict';
var assert=require('assert'), update=require('./layout-height').update, state={};
function appearance(height,lines) {
  return {frame_height:720,lines:lines || 1,box:{x:270,y:78,width:516,height:height}};
}
[46,40,46,48,46,48,46].forEach(function(h) {
  var input=appearance(h), output=update(state,input);
  assert.strictEqual(output.layout_height,46,'Transient detector jitter does not resize font');
  assert.strictEqual(output.box,input.box,'Mask retains current detector geometry');
  assert.strictEqual(input.layout_height,undefined,'Input observations are not modified');
});
[60,60,60,60,60].forEach(function(h){update(state,appearance(h));});
assert.strictEqual(state.height,60,'Sustained real size change is admitted');
assert.strictEqual(update(state,appearance(80,2)).layout_height,80,'Line-count changes reset estimator');
assert.strictEqual(update({},null),null);
var dedup={};update(dedup,appearance(46),1);
for(var i=0;i<10;i++) update(dedup,appearance(40),2);
assert.strictEqual(dedup.samples.length,2,'Polling the same OCR observation cannot fill the history');
assert.strictEqual(dedup.height,46);
console.log('Median font height rejects live jitter and admits sustained geometry changes: PASS');
