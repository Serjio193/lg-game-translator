// Owner-only local snapshots: OFF must never poll Orange to populate the menu.
'use strict';
var fs=require('fs');
var files={settings:'/media/developer/game-translator-server-settings.json',
  provider:'/media/developer/game-translator-provider-status.json'};
exports.enabled=function(){
  try{return JSON.parse(fs.readFileSync('/media/developer/game-translator-layers.json','utf8')).translationEnabled===true;}
  catch(error){return false;}
};
function read(name){try{return JSON.parse(fs.readFileSync(files[name],'utf8'));}catch(error){return null;}}
function write(name,value){
  var snapshot={value:value,timestamp_ms:Date.now()},temporary=files[name]+'.tmp';
  fs.writeFileSync(temporary,JSON.stringify(snapshot),{mode:384});
  fs.chmodSync(temporary,384);fs.renameSync(temporary,files[name]);return snapshot;
}
exports.saveSettings=function(value){
  var result={};
  ['hdmi_inputs','applications','provider','translation_server','russian_idle','language_check_seconds'].forEach(function(key){if(value[key]!==undefined)result[key]=value[key];});
  return write('settings',result);
};
exports.settings=function(){return read('settings');};
exports.saveProvider=function(value){
  var settings=read('settings');
  if(settings&&['madlad','google'].indexOf(value.provider)>=0&&settings.value.provider!==value.provider)
    exports.saveSettings(Object.assign({},settings.value,{provider:value.provider}));
  return write('provider',{provider:value.provider,key_configured:value.key_configured,
    public_key:value.public_key,budget:value.budget});
};
exports.provider=function(){return read('provider');};
exports.view=function(snapshot,live){
  var settings=read('settings');
  return Object.assign({},snapshot?snapshot.value:{provider:null,key_configured:null,budget:null},
    {snapshot_at:snapshot?snapshot.timestamp_ms:null,stale:!live,
      translation_enabled:exports.enabled(),server_settings:settings?settings.value:null});
};
