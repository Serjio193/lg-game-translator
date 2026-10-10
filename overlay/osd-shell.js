(function(root){
  'use strict';
  var frame=null;
  function parse(value){
    try {value=typeof value==='string'?JSON.parse(value):value;
      return value && value.params ? parse(value.params) : value || {};
    }catch(error){return {};}
  }
  function close(){if(frame){frame.parentNode.removeChild(frame);frame=null;}}
  function accept(value){
    var params=parse(value);
    if(params.menu===true || !['blocks','text','layers','responseId'].some(function(key){
      return Object.prototype.hasOwnProperty.call(params,key);
    })){
      if(!frame){
        frame=document.createElement('iframe');frame.id='osd-menu';
        frame.title='Управление переводом';frame.src='menu/index.html';
        document.body.appendChild(frame);frame.onload=function(){frame.focus();};
      }
      return true;
    }
    return false;
  }
  root.addEventListener('message',function(event){
    if(frame && event.source===frame.contentWindow && event.data && event.data.osdMenu==='close')close();
  });
  root.OsdShell={accept:accept,open:function(){return !!frame;},close:close};
}(window));
