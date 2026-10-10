(function (root) {
  'use strict';
  var defaults={cover:true,text:true,edgeBlur:true,pixelated:true,opacity:100,
    offsetX:0,offsetY:0,fillMode:'auto',fillColor:'#ffffff',redBackground:false,probe:'off',
    coverGrow:2,textColorMode:'auto',textColor:'#ffffff',fontHeight:100,fontWidth:100,
    translationScope:'normal',speechEnabled:false};
  var current=normalize({});
  function normalize(input) {
    input=input || {};
    var result={};
    ['cover','text','edgeBlur','pixelated','redBackground'].forEach(function (key) {
      result[key]=typeof input[key]==='boolean' ? input[key] : defaults[key];
    });
    ['opacity','offsetX','offsetY','coverGrow','fontHeight','fontWidth'].forEach(function (key) {
      var limit=key==='opacity' ? [0,100] : key==='coverGrow' ? [0,16] :
        key==='fontHeight'||key==='fontWidth' ? [50,200] : [-20,20];
      result[key]=typeof input[key]==='number' && isFinite(input[key])
        ? Math.max(limit[0],Math.min(limit[1],input[key])) : defaults[key];
    });
    result.fillMode=['auto','solid','mask'].indexOf(input.fillMode)>=0 ? input.fillMode : 'auto';
    result.fillColor=/^#[0-9a-f]{6}$/i.test(input.fillColor || '') ? input.fillColor.toLowerCase() : '#ffffff';
    result.probe=['off','transparent','red','text','large'].indexOf(input.probe)>=0 ? input.probe : 'off';
    result.textColorMode=input.textColorMode==='custom' ? 'custom' : 'auto';
    result.textColor=/^#[0-9a-f]{6}$/i.test(input.textColor || '') ? input.textColor.toLowerCase() : '#ffffff';
    result.translationScope=input.translationScope==='all' ? 'all' : 'normal';
    result.speechEnabled=false;
    return result;
  }
  function get() { return normalize(current); }
  var api={normalize:normalize,get:get,set:function (input) {current=normalize(input);return get();}};
  if (typeof module!=='undefined') module.exports=api;
  else root.OsdLayerSettings=api;
}(this));
