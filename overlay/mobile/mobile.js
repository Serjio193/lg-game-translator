(function () {
  'use strict';
  var preview = /(?:\?|&)preview=1(?:&|$)/.test(location.search);
  var state = {cover:true,text:true,coverGrow:2,fillMode:'auto',fillColor:'#f1d68a',opacity:100,
    textColorMode:'auto',textColor:'#15251f',fontHeight:100,fontWidth:100,translationScope:'normal'};
  var revision = 0, dirty = {}, timer = null, saving = false, section = 'cover';
  var controls = Array.prototype.slice.call(document.querySelectorAll('[data-key]'));
  var status = document.getElementById('save-status');
  function mode(value) {
    document.body.dataset.view = value;
    document.querySelectorAll('[data-view]').forEach(function (button) {
      if (button.tagName === 'BUTTON') button.classList.toggle('selected',button.dataset.view===value);
    });
    localStorage.setItem('osd-menu-view',value);
  }
  function tab(value) {
    section=value;
    document.querySelectorAll('.setting-section').forEach(function (card) {card.classList.toggle('active',card.dataset.section===value);});
    document.querySelectorAll('.section-tabs button').forEach(function (button) {button.classList.toggle('selected',button.dataset.section===value);});
  }
  function render() {
    controls.forEach(function (input) {
      var value=state[input.dataset.key];
      if (input.type==='checkbox') input.checked=value;
      else if (input.type==='radio') input.checked=input.value===value;
      else input.value=value;
    });
    document.querySelectorAll('[data-output]').forEach(function (output) {
      var key=output.dataset.output; output.textContent=state[key]+(key==='coverGrow'?' px':'%');
    });
    document.querySelectorAll('[data-color-value]').forEach(function (output) {output.textContent=state[output.dataset.colorValue];});
    document.getElementById('height-value').textContent='Высота '+state.fontHeight+'%';
    document.getElementById('width-value').textContent='Ширина '+state.fontWidth+'%';
    document.getElementById('grow-value').textContent='Заливка +'+state.coverGrow+' px';
    var cover=document.getElementById('sample-cover'), text=document.getElementById('sample-text');
    var color=state.fillMode==='solid'?state.fillColor:'#f1d68a';
    cover.style.background=color; cover.style.opacity=state.cover?state.opacity/100:0;
    cover.style.boxShadow='0 0 0 '+state.coverGrow+'px '+color;
    text.style.color=state.textColorMode==='custom'?state.textColor:'#15251f';
    text.style.visibility=state.text?'visible':'hidden';
    text.style.transform='scale('+state.fontWidth/100+','+state.fontHeight/100+')';
  }
  function show() {
    document.getElementById('login').hidden=true; document.getElementById('controls').hidden=false;
    document.getElementById('connection').textContent=preview?'Макет':'Телефон подключён';
    document.getElementById('logout').hidden=preview; render();
  }
  async function request(path, method, value) {
    var response=await fetch(path,{method:method||'GET',credentials:'same-origin',
      headers:value?{'Content-Type':'application/json'}:{},body:value?JSON.stringify(value):undefined});
    var data=await response.json();
    if (!response.ok) {var error=new Error(data.error||'Нет связи с OSD');error.status=response.status;throw error;}
    return data;
  }
  async function save() {
    if (preview) {status.textContent='Изменено в макете';return;}
    if (saving || !Object.keys(dirty).length) return;
    saving=true; var patch=dirty; dirty={};status.textContent='Применяем…';
    try {
      var result=await request('/api/settings','PATCH',{revision:revision,patch:patch});
      revision=result.revision;state=Object.assign(state,result.settings,dirty);render();status.textContent='Применено на ТВ';
    } catch (error) {
      if (!error.status || error.status===409) dirty=Object.assign(patch,dirty);
      status.textContent=error.message;
      if (error.status===401) {document.getElementById('login').hidden=false;document.getElementById('controls').hidden=true;}
      if (error.status===409) {
        try {
          var fresh=await request('/api/settings');revision=fresh.revision;state=Object.assign(state,fresh.settings,dirty);render();
        } catch (refreshError) {dirty={};status.textContent=refreshError.message;}
      }
    } finally {saving=false;}
    if (Object.keys(dirty).length) timer=setTimeout(save,400);
  }
  controls.forEach(function (input) {input.addEventListener('input',function () {
    if (input.type==='radio'&&!input.checked) return;
    var value=input.type==='checkbox'?input.checked:input.type==='range'?Number(input.value):input.value;
    state[input.dataset.key]=value;dirty[input.dataset.key]=value;render();
    clearTimeout(timer);timer=setTimeout(save,150);
  });});
  document.querySelectorAll('.designs button').forEach(function (button) {button.addEventListener('click',function () {mode(button.dataset.view);});});
  document.querySelectorAll('.section-tabs button').forEach(function (button) {button.addEventListener('click',function () {tab(button.dataset.section);});});
  document.getElementById('pair-form').addEventListener('submit',async function (event) {
    event.preventDefault();var message=document.getElementById('login-status');message.textContent='Подключение…';
    try {await request('/api/pair','POST',{pin:document.getElementById('pin').value});
      document.getElementById('pin').value='';var result=await request('/api/settings');
      state=Object.assign(state,result.settings);revision=result.revision;show();message.textContent='';
    } catch (error) {message.textContent=error.message;}
  });
  document.getElementById('logout').addEventListener('click',async function () {await request('/api/logout','POST',{});location.reload();});
  document.getElementById('reset').addEventListener('click',function () {
    var values={cover:true,text:true,coverGrow:2,fillMode:'auto',textColorMode:'auto',fontHeight:100,fontWidth:100,opacity:100};
    state=Object.assign(state,values);dirty=Object.assign(dirty,values);render();save();
  });
  mode(preview?(localStorage.getItem('osd-menu-view')||'pult'):'pult');tab(section);
  if (preview) {document.getElementById('design-bar').hidden=false;show();}
  else request('/api/settings').then(function (result) {state=Object.assign(state,result.settings);revision=result.revision;show();})
    .catch(function () {document.getElementById('connection').textContent='Нужен PIN';});
}());
