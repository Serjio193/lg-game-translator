(function (root) {
  'use strict';
  function valid(icon) {
    return icon && Number.isInteger(icon.width) && Number.isInteger(icon.height)
      && icon.width > 0 && icon.width <= 48 && icon.height > 0 && icon.height <= 48
      && typeof icon.rgb === 'string' && icon.rgb.length === 4 * Math.ceil(icon.width * icon.height * 3 / 3)
      && /^[A-Za-z0-9+/]+={0,2}$/.test(icon.rgb);
  }
  function measure(word, size, icons, measureText) {
    var width = 0, parts = word.split(/(\[button\])/);
    parts.forEach(function (part) {
      if (part !== '[button]' || !icons.length) width += measureText(part, size);
      else width += Math.max.apply(null, icons.map(function (icon) {
        return size * 1.1 * icon.width / icon.height;
      }));
    });
    return width;
  }
  function render(element, text, icons, size) {
    var index = 0;
    element.textContent = '';
    text.split(/(\[button\])/).forEach(function (part) {
      var icon = part === '[button]' ? icons[index++] : null;
      if (!valid(icon)) { element.appendChild(document.createTextNode(part)); return; }
      var bytes = window.atob(icon.rgb);
      if (bytes.length !== icon.width * icon.height * 3) {
        element.appendChild(document.createTextNode('[кнопка]')); return;
      }
      var canvas = document.createElement('canvas');
      canvas.width = icon.width; canvas.height = icon.height;
      var context = canvas.getContext('2d'), pixels = context.createImageData(icon.width, icon.height);
      for (var pixel = 0; pixel < icon.width * icon.height; pixel++) {
        for (var channel = 0; channel < 3; channel++)
          pixels.data[pixel * 4 + channel] = bytes.charCodeAt(pixel * 3 + channel);
        pixels.data[pixel * 4 + 3] = 255;
      }
      context.putImageData(pixels, 0, 0);
      canvas.style.height = size * 1.1 + 'px';
      canvas.style.width = size * 1.1 * icon.width / icon.height + 'px';
      canvas.style.verticalAlign = 'middle';
      canvas.setAttribute('aria-label', 'значок кнопки');
      element.appendChild(canvas);
    });
  }
  var api = {valid: valid, measure: measure, render: render};
  if (typeof module !== 'undefined') module.exports = api;
  else root.ControlIcons = api;
}(this));
