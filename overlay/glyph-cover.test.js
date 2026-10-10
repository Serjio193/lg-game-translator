'use strict';
var assert = require('assert'), cover = require('./glyph-cover');
global.window = {atob:function (value) {return Buffer.from(value,'base64').toString('binary');}};
var mask = {width:4,height:2,bits:'21'};
var solid = cover.decode(mask,null,[100,80,60]);
assert.deepStrictEqual(Array.from(solid.slice(0,8)),[100,80,60,255,0,0,0,0]);
assert.strictEqual(solid[5*4+3],255);
assert.strictEqual(solid[7*4+3],0,'Background outside original ink stays transparent');
assert.strictEqual(cover.decode({width:4,height:2,bits:'zz'},null,[1,2,3]),null);
assert.strictEqual(cover.decode({width:4,height:2,bits:'2100'},null,[1,2,3]),null);
assert.strictEqual(cover.decode(mask,null,null),null);
var patch={width:2,height:1,rgb:Buffer.from([10,20,30,40,50,60]).toString('base64')};
var local=cover.decode({width:4,height:2,bits:'09'},patch,null);
assert.deepStrictEqual(Array.from(local.slice(0,4)),[10,20,30,255]);
assert.deepStrictEqual(Array.from(local.slice(12,16)),[40,50,60,255]);
var blended=cover.decode({width:4,height:2,bits:'02'},patch,null);
assert.deepStrictEqual(Array.from(blended.slice(4,8)),[20,30,40,255],
  'Local background samples interpolate instead of making colour blocks');
var softColor=cover.decode(mask,patch,[100,100,100],true);
assert.notStrictEqual(softColor[0],100,'Boundary uses blurred local colour instead of mean fill');
for (var i=3;i<solid.length;i+=4) assert.strictEqual(softColor[i],solid[i],
  'Colour blur must not change any mask alpha');
var canvasSize,lastPainted;
global.document={createElement:function () {return {getContext:function () {return {
  createImageData:function (w,h) {return {data:new Uint8ClampedArray(w*h*4)};},putImageData:function (image) {lastPainted=image.data;}
};},toDataURL:function () {canvasSize=[this.width,this.height];return 'data:image/png;base64,test';}};}};
var element={style:{}};
assert(cover.render(element,{erase_mask:mask,background_reliable:true,background:[1,2,3],
  box:{x:100,y:0,width:4,height:2}},{sourceWidth:6,height:3,x:140,y:0}));
assert.strictEqual(element.style.background,'transparent');
assert.strictEqual(element.style.backgroundPosition,'10px 0px');
assert.strictEqual(element.style.backgroundSize,'6px 3px','Mask keeps original crop width after drawing-area expansion');
assert.deepStrictEqual(canvasSize,[6,3],'PNG is created in OSD pixels, not source crop pixels');
assert.strictEqual(element.style.imageRendering,'pixelated');
assert.strictEqual(element.style.left,'140px');
var layers=require('./layer-settings');
layers.set({fillMode:'mask',opacity:50,offsetX:3,offsetY:-2,pixelated:false});
assert(cover.render(element,{erase_mask:mask,background_reliable:true,background:[1,2,3],
  box:{x:100,y:0,width:4,height:2}},{sourceWidth:6,height:3,x:140,y:0}));
assert.strictEqual(element.style.backgroundPosition,'13px -2px');
assert.strictEqual(element.style.imageRendering,'auto');
assert.deepStrictEqual(Array.from(lastPainted.slice(0,4)),[255,0,255,128]);
layers.set({});
console.log('Original ink only, transparent holes, local background and expanded-area anchoring: PASS');
