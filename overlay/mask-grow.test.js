'use strict';
var assert=require('assert'), grow=require('./mask-grow').apply;
var pixels=new Uint8ClampedArray(11*7*4), center=(3*11+5)*4;
pixels.set([140,80,40,255],center);
var output=grow(pixels,11,7);
function alpha(x,y) {return output[(y*11+x)*4+3];}
assert.strictEqual(alpha(3,3),255);assert.strictEqual(alpha(7,3),255);
assert.strictEqual(alpha(5,1),255);assert.strictEqual(alpha(5,5),255);
assert.strictEqual(alpha(2,3),0);assert.strictEqual(alpha(3,1),0);
assert.deepStrictEqual(Array.from(output.slice((3*11+3)*4,(3*11+3)*4+4)),[140,80,40,255]);
assert.strictEqual(pixels[(3*11+3)*4+3],0,'Input mask stays unchanged');
assert.deepStrictEqual(Array.from(grow(new Uint8ClampedArray(4),1,1)),[0,0,0,0]);
console.log('Cover grows exactly two OSD pixels, retains colour and preserves transparent exterior: PASS');
