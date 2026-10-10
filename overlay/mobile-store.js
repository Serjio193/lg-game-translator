'use strict';
var fs=require('fs'),path=require('path'),crypto=require('crypto');
var layers=require('./layer-settings');
var KEYS=['cover','text','coverGrow','fillMode','fillColor','opacity','textColorMode','textColor',
  'fontHeight','fontWidth','translationScope','speechEnabled'];
function validate(patch) {
  if(!patch||typeof patch!=='object'||Array.isArray(patch)||Object.keys(patch).some(function(k){return KEYS.indexOf(k)<0;})) throw new Error('Неизвестная настройка');
  Object.keys(patch).forEach(function(key) {
    var value=patch[key];
    if(['cover','text','speechEnabled'].indexOf(key)>=0&&typeof value!=='boolean') throw new Error('Нужен переключатель');
    if(['coverGrow','opacity','fontHeight','fontWidth'].indexOf(key)>=0) {
      var limits=key==='coverGrow'?[0,16]:key==='opacity'?[0,100]:[50,200];
      if(typeof value!=='number'||!isFinite(value)||Math.floor(value)!==value||value<limits[0]||value>limits[1]) throw new Error('Размер вне диапазона');
    }
    if(['fillColor','textColor'].indexOf(key)>=0&&!/^#[0-9a-f]{6}$/i.test(value)) throw new Error('Нужен цвет #RRGGBB');
    if(key==='fillMode'&&['auto','solid'].indexOf(value)<0) throw new Error('Неверная заливка');
    if(key==='textColorMode'&&['auto','custom'].indexOf(value)<0) throw new Error('Неверный цвет текста');
    if(key==='translationScope'&&['normal','all'].indexOf(value)<0) throw new Error('Неверное правило перевода');
    if(key==='speechEnabled'&&value) throw new Error('Озвучка пока не подключена');
  });
  return patch;
}
function create(file,changed) {
  var revision=0,last='';
  function read() {
    var raw='{}';try {raw=fs.readFileSync(file,'utf8');}catch(error){if(error.code!=='ENOENT') throw error;}
    if(raw!==last){revision++;last=raw;}
    return {settings:layers.normalize(JSON.parse(raw)),revision:revision,capabilities:{speech:false}};
  }
  return {read:read,update:function (value) {
    var current=read();
    if(!value||!Number.isInteger(value.revision)||value.revision!==current.revision) {
      var conflict=new Error('Настройки изменились. Обновляем значения');conflict.status=409;throw conflict;
    }
    var patch=validate(value.patch),next=layers.normalize(Object.assign({},current.settings,patch));
    var temporary=file+'.tmp.'+crypto.randomBytes(6).toString('hex');
    fs.mkdirSync(path.dirname(file),{recursive:true});
    try {fs.writeFileSync(temporary,JSON.stringify(next),{mode:384});fs.renameSync(temporary,file);}
    finally {if(fs.existsSync(temporary)) fs.unlinkSync(temporary);}
    if(changed&&current.settings.translationScope!==next.translationScope) changed();
    return read();
  }};
}
exports.create=create;exports.validate=validate;
