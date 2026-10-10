(function (root) {
  'use strict';
  var controls = typeof module !== 'undefined' ? require('./control-icons') : root.ControlIcons;
  var edgeBlur = typeof module !== 'undefined' ? require('./mask-edge-blur') : root.MaskEdgeBlur;
  var osdRaster = typeof module !== 'undefined' ? require('./mask-osd-raster') : root.MaskOsdRaster;
  var layerSettings = typeof module !== 'undefined' ? require('./layer-settings') : root.OsdLayerSettings;
  var lineMask = typeof module !== 'undefined' ? require('./line-cover-mask') : root.LineCoverMask;
  var maskGrow = typeof module !== 'undefined' ? require('./mask-grow') : root.MaskGrow;
  function sample(bytes, patch, x, y, c) {
    var left = Math.floor(x), top = Math.floor(y), dx = x - left, dy = y - top;
    var right = Math.min(patch.width - 1,left + 1), bottom = Math.min(patch.height - 1,top + 1);
    function pixel(xx,yy) {return bytes.charCodeAt((yy * patch.width + xx) * 3 + c);}
    return (pixel(left,top)*(1-dx) + pixel(right,top)*dx)*(1-dy)
      + (pixel(left,bottom)*(1-dx) + pixel(right,bottom)*dx)*dy;
  }
  function decode(mask, patch, background, blurEdge) {
    if (!mask || !Number.isInteger(mask.width) || !Number.isInteger(mask.height)
        || mask.width <= 0 || mask.height <= 0 || mask.width * mask.height > 65536
        || typeof mask.bits !== 'string' || !/^[0-9a-f]+$/i.test(mask.bits)
        || mask.bits.length !== Math.ceil(mask.width * mask.height / 8) * 2) return null;
    var solid = Array.isArray(background) && background.length === 3
      && background.every(function (c) { return Number.isFinite(c) && c >= 0 && c <= 255; });
    var bytes = !solid && controls.valid(patch) ? window.atob(patch.rgb) : null;
    if (!solid && (!bytes || bytes.length !== patch.width * patch.height * 3)) return null;
    var pixels = new Uint8ClampedArray(mask.width * mask.height * 4);
    for (var i = 0; i < mask.width * mask.height; i++) {
      var active = parseInt(mask.bits.slice(Math.floor(i / 8) * 2, Math.floor(i / 8) * 2 + 2),16)
        & (1 << (i % 8));
      if (!active) continue;
      var x = i % mask.width, y = Math.floor(i / mask.width);
      var px = mask.width === 1 ? 0 : x * (patch ? patch.width - 1 : 0) / (mask.width - 1);
      var py = mask.height === 1 ? 0 : y * (patch ? patch.height - 1 : 0) / (mask.height - 1);
      for (var c = 0; c < 3; c++)
        pixels[i * 4 + c] = solid ? background[c] : sample(bytes,patch,px,py,c);
      pixels[i * 4 + 3] = 255;
    }
    if (blurEdge && controls.valid(patch)) {
      var local = window.atob(patch.rgb);
      if (local.length !== patch.width * patch.height * 3) return null;
      edgeBlur.apply(pixels,mask.width,mask.height,function (x,y) {
        var px = mask.width === 1 ? 0 : x*(patch.width-1)/(mask.width-1);
        var py = mask.height === 1 ? 0 : y*(patch.height-1)/(mask.height-1);
        return [sample(local,patch,px,py,0),sample(local,patch,px,py,1),sample(local,patch,px,py,2)];
      });
    }
    return pixels;
  }
  function render(element, appearance, fitted) {
    var layers=layerSettings.get();
    var mask = lineMask.join(appearance.erase_mask);
    var fill=appearance.background_reliable ? appearance.background : null;
    var patch=appearance.backdrop;
    if (layers.fillMode!=='auto') {
      var hex=layers.fillMode==='mask' ? '#ff00ff' : layers.fillColor;
      fill=[parseInt(hex.slice(1,3),16),parseInt(hex.slice(3,5),16),parseInt(hex.slice(5,7),16)];
      patch=null;
    }
    var pixels = decode(mask,patch,fill,layers.edgeBlur && layers.fillMode==='auto');
    if (!pixels || mask.width !== appearance.box.width || mask.height !== appearance.box.height) return false;
    var raster=osdRaster.prepare(pixels,mask,appearance.box,fitted);
    if (!raster) return false;
    raster.pixels=maskGrow.apply(raster.pixels,raster.width,raster.height,layers.coverGrow);
    if (layers.opacity!==100) for (var i=3;i<raster.pixels.length;i+=4)
      raster.pixels[i]=Math.round(raster.pixels[i]*layers.opacity/100);
    var canvas = document.createElement('canvas');
    canvas.width = raster.width; canvas.height = raster.height;
    var context = canvas.getContext('2d'), data = context.createImageData(raster.width,raster.height);
    context.imageSmoothingEnabled=false;
    data.data.set(raster.pixels); context.putImageData(data,0,0);
    element.style.left=raster.containerX+'px'; element.style.top=raster.containerY+'px';
    element.style.background = 'transparent';
    element.style.backgroundImage = 'url("' + canvas.toDataURL('image/png') + '")';
    element.style.backgroundOrigin = 'border-box';
    element.style.backgroundSize = raster.width + 'px ' + raster.height + 'px';
    element.style.backgroundPosition = (raster.x+layers.offsetX) + 'px ' + (raster.y+layers.offsetY) + 'px';
    element.style.imageRendering=layers.pixelated ? 'pixelated' : 'auto';
    element.style.backgroundRepeat = 'no-repeat';
    return true;
  }
  var api = {decode:decode,render:render};
  if (typeof module !== 'undefined') module.exports = api;
  else root.GlyphCover = api;
}(this));
