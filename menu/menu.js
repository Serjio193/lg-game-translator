(function () {
  'use strict';
  var endpoint='http://192.168.1.11:8765/api/settings',base=null;
  var provider=document.getElementById('provider'),server=document.getElementById('server');
  var save=document.getElementById('save'),status=document.getElementById('status');
  function request(method,value,callback){
    var xhr=new XMLHttpRequest();xhr.open(method,endpoint);xhr.timeout=5000;
    xhr.setRequestHeader('Content-Type','application/json');
    xhr.onload=function(){try{var result=JSON.parse(xhr.responseText);if(xhr.status!==200)throw new Error(result.error||'Ошибка сервера');callback(null,result);}catch(error){callback(error);}};
    xhr.onerror=xhr.ontimeout=function(){callback(new Error('Нет связи с Orange Pi'));};
    xhr.send(value?JSON.stringify(value):null);
  }
  function enable(value){provider.disabled=server.disabled=save.disabled=!value;}
  function load(){request('GET',null,function(error,value){
    if(error){status.textContent=error.message;return;}base=value;provider.value=value.provider;
    server.value=value.translation_server;enable(true);status.textContent='Настройки загружены';
  });}
  document.getElementById('settings').addEventListener('submit',function(event){
    event.preventDefault();if(!base)return;enable(false);status.textContent='Сохранение…';
    function persist(error){
      if(error){enable(true);status.textContent=error.message;return;}
      var value=Object.assign({},base,{provider:provider.value,translation_server:server.value.trim(),russian_idle:false});
      request('POST',value,function(failed,result){enable(true);if(!failed)base=result;
        status.textContent=failed?failed.message:'Сохранено';save.focus();});
    }
    if(provider.value==='google')window.GoogleSettings.select('google',persist);else persist(null);
  });
  document.getElementById('back').addEventListener('click',function(){window.close();});
  document.addEventListener('keydown',function(event){
    if(event.keyCode===461||event.key==='Escape'){window.close();return;}
    var controls=[document.getElementById('translation-toggle'),document.getElementById('pair-phone'),
      provider,server,document.getElementById('google-key'),document.getElementById('google-key-save'),save,document.getElementById('back')];
    var index=controls.indexOf(document.activeElement);
    if(event.keyCode>=37&&event.keyCode<=40){
      if((document.activeElement===server||document.activeElement===document.getElementById('google-key'))&&(event.keyCode===37||event.keyCode===39))return;
      if(document.activeElement===provider&&(event.keyCode===37||event.keyCode===39)){
        event.preventDefault();provider.selectedIndex=Math.max(0,Math.min(provider.options.length-1,provider.selectedIndex+(event.keyCode===37?-1:1)));return;
      }
      event.preventDefault();var direction=event.keyCode===37||event.keyCode===38?-1:1;
      var target=Math.max(0,Math.min(controls.length-1,index+direction));
      while(controls[target].disabled&&target>0&&target<controls.length-1)target+=direction;
      if(!controls[target].disabled){controls[target].focus();controls[target].scrollIntoView({block:'nearest'});}
    }
  });
  load();
}());
