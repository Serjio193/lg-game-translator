'use strict';
var assert = require('assert'), createPairs = require('./translation-pairs').create;
// Existing tests model an immediately acknowledged OSD launch.
function create() {
  var engine = createPairs();
  return {update:function (gate,responses,now,provider,allowed) {
    var blocks = engine.update(gate,responses,now,provider,allowed);
    engine.shown(blocks,now);
    return blocks;
  }};
}
function fixture(count, now) {
  var gate = {complete:true,required:3,timestamp_ms:now,regions:[]}, responses = {};
  for (var i = 0; i < count; i++) {
    var key = {track_id:i+1,version_ms:100,text:'original '+i};
    gate.regions.push({slot:i,observations:3,admission:key,appearance:{box:{x:i,y:1,width:10,height:10}}});
    responses[i] = {admission:key,provider:'madlad',translation:'перевод '+i};
  }
  return {gate:gate,responses:responses};
}
var f = fixture(20,1000), pairs = create();
assert.strictEqual(pairs.update(f.gate,f.responses,1000,'madlad',true).length,20);
f.gate.timestamp_ms = 20000;
assert.strictEqual(pairs.update(f.gate,f.responses,20000,'madlad',true).length,20,
  'Unchanged source must remain beyond five seconds');
assert.strictEqual(pairs.update(f.gate,f.responses,26000,'madlad',true).length,20,
  'Slow OCR refresh must keep already shown pairs');
f.gate.regions.splice(3,1);
assert.strictEqual(pairs.update(f.gate,f.responses,27000,'madlad',true).length,19,
  'Only the disappeared source must be removed');
f.gate.timestamp_ms = 28000;
f.gate.regions[0].admission = {track_id:1,version_ms:200,text:'new original'};
assert.strictEqual(pairs.update(f.gate,f.responses,28000,'madlad',true).length,18,
  'Late response for the prior version must not show');
f.responses[0] = {admission:f.gate.regions[0].admission,provider:'madlad',translation:'новый перевод'};
assert.strictEqual(pairs.update(f.gate,f.responses,28500,'madlad',true).length,19);
assert.strictEqual(pairs.update(f.gate,f.responses,29000,'madlad',false).length,0);
f = fixture(21,30000); pairs = create();
assert.strictEqual(pairs.update(f.gate,f.responses,30000,'madlad',true).length,20);
f = fixture(1,40000); pairs = create(); f.gate.regions[0].observations = 2;
assert.strictEqual(pairs.update(f.gate,f.responses,40000,'madlad',true).length,0);
f.gate.regions[0].observations = 3;
assert.strictEqual(pairs.update(f.gate,f.responses,40000,'madlad',true).length,1);
f.gate.regions = [];
var held = pairs.update(f.gate,f.responses,41000,'madlad',true);
assert.strictEqual(held.length,1);
assert.strictEqual(pairs.update(f.gate,f.responses,45000,'madlad',true).length,0);
f = fixture(1,50000); pairs = create();
f.gate.regions[0].appearance.background_reliable = false;
f.gate.regions[0].appearance.backdrop = {rgb:'old'};
pairs.update(f.gate,f.responses,50000,'madlad',true);
f.gate.regions[0].appearance = {background_reliable:false,backdrop:{rgb:'fresh'}};
assert.strictEqual(pairs.update(f.gate,f.responses,51000,'madlad',true)[0].appearance.backdrop.rgb,'fresh');
f.gate.regions[0].appearance = {background_reliable:false,background_gradient:true,
  foreground:[12,12,12],backdrop:{rgb:'gradient'}};
var restyled = pairs.update(f.gate,f.responses,51100,'madlad',true)[0].appearance;
assert.strictEqual(restyled.foreground[0],12);
assert.strictEqual(restyled.background_gradient,true);
f.gate.timestamp_ms = 30000;
f.gate.regions[0].appearance.backdrop = {rgb:'stale'};
assert.strictEqual(pairs.update(f.gate,f.responses,51000,'madlad',true).length,1);
console.log('Twenty independent pairs, source persistence, fresh backdrop and late-version rejection: PASS');
f = fixture(1,60000); pairs = create();
f.responses[0].stage = 'preliminary';
assert.strictEqual(pairs.update(f.gate,f.responses,60000,'madlad',true)[0].text,'перевод 0');
f.responses[0] = Object.assign({},f.responses[0],{stage:'final',translation:'Уточнённый'});
assert.strictEqual(pairs.update(f.gate,f.responses,60200,'madlad',true)[0].text,'Уточнённый');
f.responses[0] = Object.assign({},f.responses[0],{stage:'preliminary',translation:'Поздний быстрый'});
assert.strictEqual(pairs.update(f.gate,f.responses,60300,'madlad',true)[0].text,'Уточнённый');
f.gate.regions[0].admission = {track_id:1,version_ms:200,text:'new original'};
f.responses[0] = Object.assign({},f.responses[0],{stage:'final',translation:'Устаревший'});
assert.notStrictEqual(pairs.update(f.gate,f.responses,60400,'madlad',true)[0].text,'Устаревший');
console.log('Preview upgrades in place; late preview and stale final cannot replace: PASS');
f=fixture(1,70000);pairs=create();
f.gate.regions[0].appearance.sentence_flow=true;
f.gate.regions[0].admission.text='Follow me! Take';
f.responses[0]=Object.assign({},f.responses[0],{admission:f.gate.regions[0].admission,
  stage:'preliminary',engine:'bergamot',confirmation_policy:'three-final-v1',translation:'Иди за мной!'});
var first=pairs.update(f.gate,f.responses,70000,'madlad',true)[0];
f.responses[0]=Object.assign({},f.responses[0],{translation:'Иди за мной! Береги себя!'});
assert.strictEqual(pairs.update(f.gate,f.responses,70100,'madlad',true)[0].text,
  'Иди за мной! Береги себя!','A new sentence updates the same preliminary source');
f.gate.regions[0].admission={track_id:22,version_ms:70150,text:'Follow me! Take care!'};
f.gate.regions[0].source_text='Follow me! Take care!';
f.responses[0]=Object.assign({},f.responses[0],{admission:f.gate.regions[0].admission});
var extended=pairs.update(f.gate,f.responses,70200,'madlad',true);
assert.strictEqual(extended.length,1);
assert.strictEqual(extended[0].id,first.id,'Source extension preserves the DOM identity without a five-second wait');
assert.strictEqual(extended[0].source,'Follow me! Take care!');
f.responses[0]=Object.assign({},f.responses[0],{stage:'final',translation:'Полный финальный перевод'});
assert.strictEqual(pairs.update(f.gate,f.responses,70300,'madlad',true)[0].text,'Полный финальный перевод');
