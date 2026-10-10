'use strict';
var assert=require('assert'),fs=require('fs'),os=require('os'),path=require('path'),EventEmitter=require('events');
var route=require('./manual-menu-route'),stores=require('./mobile-store');
var directory=fs.mkdtempSync(path.join(os.tmpdir(),'manual-menu-')),file=path.join(directory,'layers.json');
var changed=0,store=stores.create(file,function(){changed++;}),read=fs.readFileSync,key='a'.repeat(64);
fs.readFileSync=function(name){if(name==='/media/developer/game-translator-mobile-menu.key')return key;return read.apply(fs,arguments);};
function call(method,value,credential){
  var request=new EventEmitter();request.method=method;
  request.headers={'x-osd-menu-key':credential===undefined?key:credential,'content-type':'application/json'};
  var response={statusCode:200,setHeader:function(){},end:function(body){this.value=JSON.parse(body||'{}');}};
  route.handle(request,response,store);
  if(method==='POST'){request.emit('data',JSON.stringify(value));request.emit('end');}
  return response;
}
try{
  assert.strictEqual(call('GET',null,'invalid').statusCode,403);
  var first=call('GET');assert.strictEqual(first.value.settings.translationEnabled,false);
  assert.strictEqual(call('POST',{revision:first.value.revision,enabled:'yes'}).statusCode,400);
  var on=call('POST',{revision:first.value.revision,enabled:true});assert.strictEqual(on.statusCode,200);
  assert.strictEqual(on.value.settings.translationEnabled,true);assert.strictEqual(changed,1);
  assert.strictEqual(call('POST',{revision:first.value.revision,enabled:false}).statusCode,409);
  var off=call('POST',{revision:on.value.revision,enabled:false});assert.strictEqual(off.value.settings.translationEnabled,false);
  assert.strictEqual(changed,2);assert.strictEqual(stores.create(file).read().settings.translationEnabled,false);
  console.log('TV menu authentication, manual ON/OFF, revisions and persistence: PASS');
}finally{fs.readFileSync=read;if(fs.existsSync(file))fs.unlinkSync(file);fs.rmdirSync(directory);}
