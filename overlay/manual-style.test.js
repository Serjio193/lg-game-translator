'use strict';
var assert=require('assert'),manual=require('./manual-style');
function node() {
  return {style:{},children:[],get firstChild(){return this.children[0];},
    appendChild:function(child){if(child.parent)child.parent.children.shift();child.parent=this;this.children.push(child);},
    insertBefore:function(child){this.children.unshift(child);}};
}
global.document={createElement:node};
var element=node();element.appendChild(node());
manual.text(element,{text:true,textColorMode:'custom',textColor:'#abcdef',fontWidth:130,fontHeight:80});
assert.strictEqual(element.style.color,'#abcdef');
assert.strictEqual(element.firstChild.style.transform,'scale(1.3,0.8)');
assert.strictEqual(element.firstChild.children.length,1);
assert.strictEqual(element.style.transform,undefined,'Background/container geometry must not scale with text');
manual.rectangle(element,{cover:true,coverGrow:6,fillMode:'solid',fillColor:'#123456',opacity:40},'transparent');
assert.strictEqual(element.firstChild.style.left,'-6px');
assert.strictEqual(element.firstChild.style.background,'#123456');
assert.strictEqual(element.firstChild.style.opacity,'0.4');
assert.strictEqual(element.children[1].style.transform,'scale(1.3,0.8)');
console.log('Text-only width/height scaling and independent expanded background: PASS');
