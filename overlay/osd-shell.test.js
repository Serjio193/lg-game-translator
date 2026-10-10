'use strict';
var assert=require('assert'),fs=require('fs'),vm=require('vm'),events={},children=[];
var body={appendChild:function(node){children.push(node);node.parentNode=this;},
  removeChild:function(node){children.splice(children.indexOf(node),1);}};
var root={addEventListener:function(name,fn){events[name]=fn;}};
vm.runInNewContext(fs.readFileSync(__dirname+'/osd-shell.js','utf8'),{
  window:root,document:{body:body,createElement:function(){return {contentWindow:{},focus:function(){}};}},
  JSON:JSON,Object:Object
});
assert.strictEqual(root.OsdShell.accept({blocks:[]}),false,'Background feed never opens the menu');
assert.strictEqual(root.OsdShell.accept('{}'),true);
assert(root.OsdShell.open());assert.strictEqual(children.length,1);
assert.strictEqual(children[0].src,'menu/index.html');
assert.strictEqual(root.OsdShell.accept({params:{blocks:[{text:'Translation'}]}}),false);
assert(root.OsdShell.open(),'Translation updates must not close the user menu');
root.OsdShell.accept({menu:true});assert.strictEqual(children.length,1);
events.message({source:{},data:{osdMenu:'close'}});assert(root.OsdShell.open());
events.message({source:children[0].contentWindow,data:{osdMenu:'close'}});
assert(!root.OsdShell.open());assert.strictEqual(children.length,0);
var manifest=JSON.parse(fs.readFileSync(__dirname+'/appinfo.json','utf8'));
assert.strictEqual(manifest.id,'com.serjio193.lggametranslator.overlay');
assert.strictEqual(manifest.transparent,true);
assert.strictEqual(manifest.defaultWindowType,'overlay');
console.log('Single OSD menu routing, trusted frame close and background updates: PASS');
