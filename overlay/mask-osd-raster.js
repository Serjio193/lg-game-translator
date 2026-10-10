(function (root) {
  'use strict';
  function prepare(pixels, mask, box, fitted) {
    var sx = fitted.sourceWidth / mask.width;
    var sy = fitted.scaleY===undefined ? fitted.height / mask.height : fitted.scaleY;
    if (!(sx > 0 && sy > 0 && Number.isFinite(sx) && Number.isFinite(sy)
        && Number.isFinite(box.x) && Number.isFinite(box.y)
        && Number.isFinite(fitted.x) && Number.isFinite(fitted.y))) return null;
    var left = Math.round(box.x*sx), top = Math.round(box.y*sy);
    var width = Math.round((box.x+mask.width)*sx)-left;
    var height = Math.round((box.y+mask.height)*sy)-top;
    if (!(width > 0 && height > 0) || width > 3840 || height > 2160 || width*height > 1048576
        || pixels.length !== mask.width*mask.height*4) return null;
    var output = new Uint8ClampedArray(width*height*4);
    // Explicit nearest-neighbour lookup preserves binary alpha at fractional ratios.
    for (var y=0;y<height;y++) for (var x=0;x<width;x++) {
      var sourceX = Math.max(0,Math.min(mask.width-1,Math.floor((left+x+.5)/sx-box.x)));
      var sourceY = Math.max(0,Math.min(mask.height-1,Math.floor((top+y+.5)/sy-box.y)));
      var from = (sourceY*mask.width+sourceX)*4, to=(y*width+x)*4;
      for (var c=0;c<4;c++) output[to+c]=pixels[from+c];
    }
    var containerX=Math.round(fitted.x), containerY=Math.round(fitted.y);
    return {pixels:output,width:width,height:height,x:left-containerX,y:top-containerY,
      containerX:containerX,containerY:containerY};
  }
  if (typeof module !== 'undefined') module.exports={prepare:prepare};
  else root.MaskOsdRaster={prepare:prepare};
}(this));
