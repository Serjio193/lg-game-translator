'use strict';
var assert = require('assert');
var layout = require('./subtitle-layout');
var appearance = {frame_width:1280, frame_height:720,
  box:{x:200,y:400,width:500,height:80}, lines:2, background_reliable:true,
  background:[128,80,40], foreground:[250,240,220], outline:[0,0,0]};
var measure = function (word, size) { return word.length * size * .5; };
var text = 'Проверь своё снаряжение в меню и обязательно используй найденные предметы.';
var fitted = layout.fit(text, appearance, {width:1920,height:1080}, measure);
assert(fitted);
assert.strictEqual(fitted.text.split('\n').length, 2);
assert.strictEqual(fitted.text.replace(/\s+/g, ' '), text);
assert.strictEqual(fitted.x + fitted.width / 2, 675);
assert(fitted.width >= 750 && fitted.width <= 1012.5);
assert.strictEqual(fitted.y, 600);
assert.strictEqual(fitted.background, 'rgb(128,80,40)');
assert(fitted.size >= 18);
assert(fitted.spacing >= 0 && fitted.spacing <= fitted.size * .04);
fitted.text.split('\n').forEach(function (line) {
  assert(measure(line, fitted.size) + Array.from(line).length * fitted.spacing <= fitted.width - 8 + .001);
});
var short = layout.fit('Короткая фраза', Object.assign({}, appearance, {lines:1}),
  {width:1920,height:1080}, measure);
assert(short.size > fitted.size && short.spacing > 0);
assert(Math.abs(short.paddingTop + short.size * 1.08 / 2 - short.height / 2) < .001,
  'A width-constrained line must stay vertically centered');
assert(Math.abs(fitted.paddingTop + fitted.size * 1.08 - fitted.height / 2) < .001,
  'Two fitted lines must be centered as one block');
var dynamic = layout.fit('Короткая фраза', Object.assign({}, appearance,
  {background_reliable:false,backdrop:{width:2,height:1,rgb:'AAAAAAAA'}}),
  {width:1920,height:1080}, measure);
assert.strictEqual(dynamic.background, 'transparent');
assert.strictEqual(dynamic.stroke, 0);
assert.strictEqual(dynamic.outline, 'transparent');
assert(dynamic.patch);
var outlined = layout.fit('Кнопка', Object.assign({}, appearance,
  {outline_reliable:true,outline:[0,0,0]}), {width:1920,height:1080}, measure);
assert.strictEqual(outlined.stroke,0,'Even measured source outlines must not be drawn by OSD');
assert.strictEqual(outlined.outline,'transparent');
var gradient = layout.fit('Кнопка', Object.assign({}, appearance,
  {background_reliable:false,background_gradient:true,foreground_reliable:true,
    foreground:[12,12,12],backdrop:{width:2,height:1,rgb:'AAAAAAAA'}}),
  {width:1920,height:1080}, measure);
assert.strictEqual(gradient.foreground, 'rgb(12,12,12)');
assert.strictEqual(gradient.stroke, 0, 'A smooth panel must not add a white outline');
assert(gradient.patch && gradient.background === 'transparent');
assert.strictEqual(layout.fit('word'.repeat(400), appearance, {width:1920,height:1080}, measure), null);
appearance.box.x = -1;
assert.strictEqual(layout.fit(text, appearance, {width:1920,height:1080}, measure), null);
var cleared = {style: {}, textContent: 'old'};
layout.render(cleared, '', null);
assert.strictEqual(cleared.textContent, '');
assert.strictEqual(cleared.style.background, 'transparent', 'Clearing must remove the cover rectangle too');
assert.strictEqual(cleared.style.letterSpacing, '0px');
assert.strictEqual(cleared.style.webkitTextStroke, '0px transparent');
assert.strictEqual(cleared.style.textShadow, 'none');
console.log('Original ROI scaling, two-line fitting, color and readable fallback: PASS');
