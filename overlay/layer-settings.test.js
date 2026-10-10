'use strict';
var assert=require('assert'), settings=require('./layer-settings');
var defaults=settings.get();
assert(defaults.cover && defaults.text && defaults.edgeBlur && defaults.pixelated);
assert.strictEqual(defaults.opacity,100);
settings.set({text:false,opacity:37,offsetX:4,fillMode:'solid',fillColor:'#AaBBcc'});
assert.strictEqual(settings.get().text,false);
assert.strictEqual(settings.get().fillColor,'#aabbcc');
var copy=settings.get();copy.text=true;assert.strictEqual(settings.get().text,false);
assert.strictEqual(settings.normalize({opacity:NaN}).opacity,100);
assert.strictEqual(settings.normalize({offsetX:999}).offsetX,20);
assert.strictEqual(settings.normalize({fillMode:'bad'}).fillMode,'auto');
assert.strictEqual(settings.normalize({probe:'large'}).probe,'large');
assert.strictEqual(settings.normalize({probe:'bad'}).probe,'off');
global.document={createElement:function () {return {getContext:function () {return {
  measureText:function (text) {return {width:text.length*10};}
};}};}};
global.window={innerWidth:1920,innerHeight:1080};
var layout=require('./subtitle-layout'), element={style:{}};
var appearance={frame_width:1280,frame_height:720,lines:1,box:{x:100,y:100,width:200,height:40}};
settings.set({cover:false,text:false});layout.render(element,'Text',appearance);
assert.strictEqual(element.textContent,'');
assert.strictEqual(element.style.backgroundImage,'none');
assert.strictEqual(element.style.background,'transparent');
settings.set({cover:false,text:true});layout.render(element,'Text',appearance);
assert.strictEqual(element.textContent,'Text');
settings.set({});
assert.deepStrictEqual(settings.get(),defaults);
console.log('Layer defaults, typed values, bounded geometry, custom colours and reset: PASS');
