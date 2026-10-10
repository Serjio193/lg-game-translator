(function (root) {
  'use strict';
  function render(container, blocks, layout) {
    var prior=container.translationNodes || Object.create(null), next=Object.create(null);
    var visible = (Array.isArray(blocks) ? blocks : []).slice(0,20);
    var neighbours = visible.filter(function (block) { return block && block.appearance; })
      .map(function (block) { return block.appearance.box; });
    visible.forEach(function (block,index) {
      if (!block || typeof block.text !== 'string' || !block.text.trim() || !block.appearance) return;
      var id=typeof block.id==='string' ? block.id : 'slot:'+index;
      var element = prior[id] || document.createElement('div');
      next[id]=element;
      element.className = 'translation-block';
      element.setAttribute('role','status');
      var position=Object.keys(next).length-1;
      if(container.children && container.children[position]!==element)
        container.insertBefore(element,container.children[position] || null);
      else if(element.parentNode!==container) container.appendChild(element);
      layout.render(element,block.text,block.appearance,neighbours);
    });
    Object.keys(prior).forEach(function(id) {
      if(!next[id] && prior[id].parentNode===container) container.removeChild(prior[id]);
    });
    container.translationNodes=next;
  }
  if (typeof module !== 'undefined') module.exports = {render:render};
  else root.MultiSubtitles = {render:render};
}(this));
