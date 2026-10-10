(function(){
  'use strict';
  function element(id){return document.getElementById(id);}
  function number(value){return Number(value).toLocaleString('ru-RU');}
  function request(method,value,callback){
    var xhr=new XMLHttpRequest();xhr.open(method,'http://127.0.0.1:18779/translator-settings');xhr.timeout=6000;
    xhr.setRequestHeader('X-OSD-Menu-Key',window.OSD_MENU_KEY||'');
    xhr.setRequestHeader('Content-Type','application/json');
    xhr.onload=function(){try{var result=JSON.parse(xhr.responseText);if(xhr.status!==200)throw new Error(result.error||'Ошибка сервера');callback(null,result);}catch(error){callback(error);}};
    xhr.onerror=xhr.ontimeout=function(){callback(new Error('Нет связи с управлением переводчиком'));};
    xhr.send(value?JSON.stringify(value):null);
  }
  function render(state){
    var b=state.budget;
    element('google-status').textContent=state.stale?'Перевод выключен. '+(state.snapshot_at?'Последние данные: '+new Date(state.snapshot_at).toLocaleString('ru-RU'):'Сохранённых данных нет; Orange не опрашивается.'):'Данные обновлены';
    element('google-key-state').textContent='Ключ: '+(state.key_configured===null?'нет сохранённых сведений':state.key_configured?'сохранён зашифрованным':'не задан');
    if(!b){element('google-usage').textContent='Расход неизвестен — при OFF Orange не опрашивается.';element('google-progress').value=0;return;}
    element('google-usage').textContent='Отправлено: '+number(b.monthly_characters)+' / '+number(b.limit)+
      ' символов · '+b.period+' UTC. Осталось: '+number(b.remaining)+'. За 32 дня: '+number(b.safety_window_characters)+
      (b.blocked?'. Лимит исчерпан — только кэш.':'.');
    element('google-progress').value=b.monthly_characters;
  }
  function refresh(){request('GET',null,function(error,state){if(error)element('google-status').textContent=error.message;else render(state);});}
  window.GoogleSettings={select:function(provider,callback){
    request('POST',{provider:provider},function(error,state){if(!error)render(state);callback(error);});
  }};
  element('google-key-save').addEventListener('click',function(){
    var key=element('google-key').value;element('google-key').value='';
    if(!/^[A-Za-z0-9_-]{20,200}$/.test(key)){element('google-status').textContent='Неверный формат API-ключа';return;}
    element('google-key-save').disabled=true;
    request('POST',{key:key},function(error,state){element('google-key-save').disabled=false;
      element('google-status').textContent=error?error.message:'Ключ сохранён зашифрованным';if(!error)render(state);});key='';
  });
  refresh();setInterval(refresh,3000);
}());
