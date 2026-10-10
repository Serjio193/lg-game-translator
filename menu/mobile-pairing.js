(function () {
  'use strict';
  var button=document.getElementById('pair-phone'),panel=document.getElementById('phone-pairing');
  var expiry=null;
  button.addEventListener('click',function () {
    panel.hidden=false;panel.textContent='Готовим подключение…';
    clearTimeout(expiry);
    if(!window.OSD_MENU_KEY) {panel.textContent='Сначала установите контроллер мобильных настроек на ТВ';return;}
    fetch('http://127.0.0.1:18779/pairing',{method:'POST',headers:{'X-OSD-Menu-Key':window.OSD_MENU_KEY}})
      .then(function(response){if(!response.ok)throw new Error('Не удалось создать PIN');return response.json();})
      .then(function(value){
        panel.textContent='';
        var image=document.createElement('img');image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(value.qrSvg);
        image.alt='QR-код для телефона';image.width=264;image.height=264;panel.appendChild(image);
        var description=document.createElement('p');description.textContent='В одной сети с ТВ откройте '+value.url+' и введите PIN '+value.pin+'. PIN действует 5 минут и используется один раз.';
        panel.appendChild(description);
        expiry=setTimeout(function(){panel.textContent='PIN истёк. Нажмите «Подключить телефон» ещё раз';},Math.max(0,value.expiresAt-Date.now()));
      }).catch(function(error){panel.textContent=error.message;});
  });
}());
