(function (root) {
  'use strict';
  function apply(pixels, width, height, radius) {
    radius=radius===undefined ? 2 : Math.max(0,Math.min(16,Math.round(radius)));
    var output=new Uint8ClampedArray(pixels);
    function active(x,y) {
      return x>=0 && y>=0 && x<width && y<height && pixels[(y*width+x)*4+3]>0;
    }
    for(var y=0;y<height;y++) for(var x=0;x<width;x++) {
      if(!active(x,y) || (active(x-1,y) && active(x+1,y) && active(x,y-1) && active(x,y+1))) continue;
      for(var dy=-radius;dy<=radius;dy++) for(var dx=-radius;dx<=radius;dx++) {
        var xx=x+dx, yy=y+dy;
        if(dx*dx+dy*dy>radius*radius || xx<0 || yy<0 || xx>=width || yy>=height || active(xx,yy)) continue;
        var from=(y*width+x)*4, to=(yy*width+xx)*4;
        for(var c=0;c<4;c++) output[to+c]=pixels[from+c];
      }
    }
    return output;
  }
  if(typeof module!=='undefined') module.exports={apply:apply};
  else root.MaskGrow={apply:apply};
}(this));
