(function (root) {
  'use strict';
  function apply(pixels, width, height, colorAt) {
    var source = new Uint8ClampedArray(pixels), weights = [1,2,1];
    for (var y = 0; y < height; y++) for (var x = 0; x < width; x++) {
      var offset = (y * width + x) * 4;
      if (!source[offset+3]) continue;
      var edge = false;
      for (var dy = -2; dy <= 2 && !edge; dy++) for (var dx = -2; dx <= 2; dx++) {
        var xx = x+dx, yy = y+dy;
        if (xx < 0 || yy < 0 || xx >= width || yy >= height
            || !source[(yy*width+xx)*4+3]) {edge = true;break;}
      }
      if (!edge) continue;
      var sum = [0,0,0];
      // Blur surrounding background colours, never the mask's alpha or text.
      for (dy = -1; dy <= 1; dy++) for (dx = -1; dx <= 1; dx++) {
        var value = colorAt(Math.max(0,Math.min(width-1,x+dx)),
          Math.max(0,Math.min(height-1,y+dy)));
        var weight = weights[dx+1]*weights[dy+1];
        for (var c = 0; c < 3; c++) sum[c] += value[c]*weight;
      }
      for (c = 0; c < 3; c++) pixels[offset+c] = sum[c]/16;
    }
    return pixels;
  }
  if (typeof module !== 'undefined') module.exports = {apply:apply};
  else root.MaskEdgeBlur = {apply:apply};
}(this));
