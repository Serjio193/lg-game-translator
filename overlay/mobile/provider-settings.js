(function(){
  'use strict';
  var started=false,preview=false,state=null,busy=false;
  function element(id){return document.getElementById(id);}
  function number(value){return Number(value).toLocaleString('ru-RU');}
  async function request(method,value,path){
    var response=await fetch(path||'/api/translator',{method:method,credentials:'same-origin',
      headers:value?{'Content-Type':'application/json'}:{},body:value?JSON.stringify(value):undefined});
    var result=await response.json();if(!response.ok)throw new Error(result.error||'Нет связи с переводчиком');return result;
  }
  function render(value){
    state=value;var budget=value.budget;
    if(value.provider)element('translator-provider').value=value.provider;
    element('translator-current').textContent=value.provider?'Выбран: '+(value.provider==='google'?'Google Translate API':'локальный переводчик'):'Источник ещё не получен с Orange';
    element('google-key-state').textContent='API-ключ: '+(value.key_configured===null?'нет сохранённых сведений':value.key_configured?'сохранён и зашифрован':'не задан');
    element('translator-status').textContent=value.stale?'Перевод выключен. '+(value.snapshot_at?'Последние данные: '+new Date(value.snapshot_at).toLocaleString('ru-RU'):'Сохранённых данных нет; Orange не опрашивается.'):'Данные обновлены';
    if(!budget){element('google-used').textContent='— / 490 000';element('google-progress').value=0;
      element('google-remaining').textContent='Расход неизвестен. При OFF Orange не опрашивается.';return;}
    element('google-used').textContent=number(budget.monthly_characters)+' / '+number(budget.limit);
    element('google-progress').value=budget.monthly_characters;
    element('google-remaining').textContent='Осталось: '+number(budget.remaining)+' символов. Месяц '+budget.period+' (UTC). '+
      (budget.blocked?'Лимит исчерпан: доступны только переводы из кэша. ':'')+
      'Защитный лимит также действует за последние 32 дня: '+number(budget.safety_window_characters)+'.';
  }
  async function refresh(){if(preview||busy||element('controls').hidden)return;try{render(await request('GET'));}catch(error){element('translator-status').textContent=error.message;}}
  async function update(value){
    if(preview){state.provider=value.provider||state.provider;render(state);element('translator-status').textContent='Макет: сервер и ТВ не изменены';return;}
    busy=true;element('translator-provider').disabled=true;
    try{render(await request('POST',value));element('translator-status').textContent='Сохранено на сервере';}
    catch(error){element('translator-status').textContent=error.message;if(state)render(state);}
    finally{busy=false;element('translator-provider').disabled=false;}
  }
  window.TranslatorSettings={start:function(isPreview){
    if(started)return;started=true;preview=isPreview;
    element('translator-provider').addEventListener('change',function(){update({provider:this.value});});
    var secure=!preview&&window.isSecureContext&&window.crypto&&crypto.subtle;
    element('google-key').disabled=element('google-key-save').disabled=!secure;
    if(secure)element('google-key-help').textContent='Ключ шифруется в браузере перед передачей. После сохранения поле очищается.';
    element('google-key-save').addEventListener('click',async function(){
      var input=element('google-key'),key=input.value;input.value='';
      try{
        if(!/^[A-Za-z0-9_-]{20,200}$/.test(key))throw new Error('Неверный формат ключа');
        var fresh=await request('POST',{},'/api/translator-key');
        var bytes=Uint8Array.from(atob(fresh.public_key.replace(/-----[^-]+-----|\s/g,'')),function(c){return c.charCodeAt(0);});
        var publicKey=await crypto.subtle.importKey('spki',bytes,{name:'RSA-OAEP',hash:'SHA-256'},false,['encrypt']);
        var encrypted=new Uint8Array(await crypto.subtle.encrypt({name:'RSA-OAEP'},publicKey,new TextEncoder().encode(key)));
        await update({encrypted_key:btoa(Array.from(encrypted,function(c){return String.fromCharCode(c);}).join(''))});
      }catch(error){element('translator-status').textContent=error.message;}finally{key='';}
    });
    if(preview){render({provider:'madlad',key_configured:false,budget:{monthly_characters:0,limit:490000,remaining:490000,
      period:'пример',safety_window_characters:0,blocked:false}});element('translator-status').textContent='Макет: счётчик показывает пример, не реальные запросы';}
    else{refresh();setInterval(refresh,3000);}
  }};
}());
