'use strict';
var assert=require('assert'),fs=require('fs'),state=require('./orange-state');
var originals={read:fs.readFileSync,write:fs.writeFileSync,rename:fs.renameSync,chmod:fs.chmodSync};
var files={},modes=[];
fs.readFileSync=function(file){if(file.indexOf('/media/developer/')!==0)return originals.read.apply(fs,arguments);
  if(!Object.prototype.hasOwnProperty.call(files,file))throw new Error('Missing fixture');return files[file];};
fs.writeFileSync=function(file,body,options){files[file]=body;assert.strictEqual(options.mode,384);};
fs.renameSync=function(source,target){files[target]=files[source];delete files[source];};
fs.chmodSync=function(file,mode){modes.push(mode);};
try{
  assert.strictEqual(state.enabled(),false);assert.strictEqual(state.provider(),null);
  assert.strictEqual(state.view(null,false).budget,null,'Unknown usage must not become zero');
  files['/media/developer/game-translator-layers.json']='{"translationEnabled":true}';
  assert.strictEqual(state.enabled(),true);
  state.saveSettings({provider:'madlad',translation_server:'http://192.168.1.11:8765',secret:'must-not-persist'});
  state.saveProvider({provider:'google',key_configured:true,public_key:'public',budget:{monthly_characters:125},secret:'must-not-persist'});
  assert.strictEqual(state.settings().value.provider,'google','Explicit provider change updates cached settings');
  files['/media/developer/game-translator-layers.json']='{"translationEnabled":false}';
  var value=state.view(state.provider(),false);
  assert(value.stale);assert.strictEqual(value.translation_enabled,false);
  assert.strictEqual(value.budget.monthly_characters,125);assert(value.snapshot_at>0);
  assert(!JSON.stringify(files).includes('must-not-persist'));assert(modes.every(function(mode){return mode===384;}));
  console.log('Persistent local budget/settings snapshot, unknown usage, timestamps and owner-only writes: PASS');
}finally{
  fs.readFileSync=originals.read;fs.writeFileSync=originals.write;
  fs.renameSync=originals.rename;fs.chmodSync=originals.chmod;
}
