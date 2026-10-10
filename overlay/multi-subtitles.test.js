'use strict';
var assert = require('assert'), render = require('./multi-subtitles').render;
var children = [], texts = [], removals=0;
var container = {get firstChild() { return children[0]; },get children(){return children;},
  removeChild:function (node) { children.splice(children.indexOf(node),1);node.parentNode=null;removals++; },
  appendChild:function (node) {this.insertBefore(node,null);},
  insertBefore:function(node,before) {
    var old=children.indexOf(node);if(old>=0)children.splice(old,1);
    var index=before?children.indexOf(before):children.length;
    children.splice(index,0,node);node.parentNode=this;
  }};
global.document = {createElement:function () { return {setAttribute:function () {}}; }};
var blocks = [];
for (var i = 0; i < 21; ++i) blocks.push({text:'перевод '+i,appearance:{box:{x:i,y:i,width:20,height:20}}});
render(container,blocks,{render:function (node,text) { texts.push(text); }});
assert.strictEqual(children.length,20);
assert.strictEqual(texts[19],'перевод 19');
var firstNode=children[0];
render(container,blocks,{render:function () {}});
assert.strictEqual(children[0],firstNode,'The same source retains its layout-carrying DOM node');
assert.strictEqual(children.length,20);
assert.strictEqual(removals,0,'Unchanged nodes stay attached, preserving CSS transitions');
render(container,[],{render:function () { throw new Error(); }});
assert.strictEqual(children.length,0);
assert.strictEqual(Object.keys(container.translationNodes).length,0,'Removed source releases its layout cache');
console.log('Twenty independent OSD nodes and complete clear: PASS');
