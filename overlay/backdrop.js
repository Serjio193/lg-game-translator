(function (root) {
  'use strict';
  var controls = typeof module !== 'undefined' ? require('./control-icons') : root.ControlIcons;
  function render(element, patch) {
    element.style.backgroundImage = 'none';
    element.style.backgroundSize = '100% 100%';
    element.style.backgroundRepeat = 'no-repeat';
    if (!controls.valid(patch)) return false;
    var bytes = window.atob(patch.rgb);
    if (bytes.length !== patch.width * patch.height * 3) return false;
    var canvas = document.createElement('canvas');
    canvas.width = patch.width; canvas.height = patch.height;
    var context = canvas.getContext('2d');
    var pixels = context.createImageData(patch.width, patch.height);
    for (var i = 0; i < patch.width * patch.height; i++) {
      for (var channel = 0; channel < 3; channel++)
        pixels.data[i * 4 + channel] = bytes.charCodeAt(i * 3 + channel);
      pixels.data[i * 4 + 3] = 255;
    }
    context.putImageData(pixels, 0, 0);
    element.style.backgroundImage = 'url("' + canvas.toDataURL('image/png') + '")';
    return true;
  }
  if (typeof module !== 'undefined') module.exports = {render:render};
  else root.SubtitleBackdrop = {render:render};
}(this));
