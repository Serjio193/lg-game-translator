(function (root) {
  'use strict';
  function render(container, mode, width, height) {
    while (container.firstChild) container.removeChild(container.firstChild);
    container.style.display='none';
    if (['transparent','red','text','large'].indexOf(mode)<0) return false;
    container.style.display='block';
    var element=document.createElement('div'), style=element.style;
    element.className='surface-probe-shape';
    style.position='absolute'; style.left=Math.round(width/2-50)+'px';
    style.top=Math.round(height/2-50)+'px'; style.width='100px'; style.height='100px';
    style.background='transparent'; style.border='0'; style.outline='none';
    style.boxShadow='none'; style.textShadow='none'; style.filter='none';
    style.webkitTextStroke='0px transparent'; style.opacity='1';
    if (mode==='red') style.background='#ff0000';
    if (mode==='text') {
      element.textContent='Тест OSD'; style.color='white'; style.font='700 32px Arial';
      style.whiteSpace='nowrap'; style.width='auto'; style.height='auto';
    }
    if (mode==='large') {
      style.left='40px'; style.top='40px';
      style.width=Math.max(1,width-80)+'px'; style.height=Math.max(1,height-80)+'px';
      style.background='#ff0000';
    }
    container.appendChild(element);
    return true;
  }
  if (typeof module!=='undefined') module.exports={render:render};
  else root.SurfaceProbe={render:render};
}(this));
