(function(){
  'use strict';
  var button=document.getElementById('translation-toggle'),status=document.getElementById('translation-status');
  var enabled=false,revision=0;
  function request(method,value){return fetch('http://127.0.0.1:18779/translation-toggle',{
    method:method,headers:{'X-OSD-Menu-Key':window.OSD_MENU_KEY||'','Content-Type':'application/json'},
    body:value?JSON.stringify(value):undefined}).then(function(response){return response.json().then(function(data){
      if(!response.ok)throw new Error(data.error||'Ошибка переключателя');return data;
    });});}
  function render(value){revision=value.revision;enabled=value.settings.translationEnabled===true;
    button.textContent=enabled?'Перевод включён · OK выключить':'Перевод выключен · OK включить';
    button.disabled=false;}
  button.addEventListener('click',function(){button.disabled=true;
    request('POST',{revision:revision,enabled:!enabled}).then(function(value){render(value);
      status.textContent=enabled?'Включено. Вернитесь к игре кнопкой «Назад».':'Выключено. Новые OCR-задания запрещены.';
    }).catch(function(error){status.textContent=error.message;load();});
  });
  function load(){request('GET').then(function(value){render(value);button.focus();}).catch(function(error){status.textContent=error.message;button.disabled=true;});}
  load();button.focus();
}());
