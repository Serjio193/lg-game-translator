(function(root) {
  'use strict';
  function text(element,layers) {
    if(layers.textColorMode==='custom') element.style.color=layers.textColor;
    if(!layers.text) {element.textContent='';return;}
    if(layers.fontWidth===100&&layers.fontHeight===100)return;
    var span=document.createElement('span');
    span.style.display='inline-block';span.style.whiteSpace='pre-wrap';
    span.style.transformOrigin='left top';
    span.style.transform='scale('+layers.fontWidth/100+','+layers.fontHeight/100+')';
    while(element.firstChild)span.appendChild(element.firstChild);
    element.appendChild(span);
  }
  function rectangle(element,layers,background) {
    var color=layers.fillMode==='solid'?layers.fillColor:background;
    if(!layers.cover||!color||color==='transparent')return;
    var cover=document.createElement('span');
    var style=cover.style;
    style.position='absolute';style.pointerEvents='none';
    style.left=-layers.coverGrow+'px';style.top=-layers.coverGrow+'px';
    style.right=-layers.coverGrow+'px';style.bottom=-layers.coverGrow+'px';
    style.background=color;style.opacity=String(layers.opacity/100);
    style.zIndex='-1';element.style.isolation='isolate';
    element.style.background='transparent';element.insertBefore(cover,element.firstChild);
  }
  var api={text:text,rectangle:rectangle};
  if(typeof module!=='undefined')module.exports=api;else root.OsdManualStyle=api;
}(this));
