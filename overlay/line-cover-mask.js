(function (root) {
  'use strict';
  // Join the existing ink mask into row bands; retain every original covered pixel.
  function join(mask) {
    if (!mask || !Number.isInteger(mask.width) || !Number.isInteger(mask.height)
        || mask.width <= 0 || mask.height <= 0 || mask.width * mask.height > 65536
        || typeof mask.bits !== 'string' || !/^[0-9a-f]+$/i.test(mask.bits)
        || mask.bits.length !== Math.ceil(mask.width * mask.height / 8) * 2) return null;
    var w=mask.width, h=mask.height, bits=new Uint8Array(Math.ceil(w*h/8)), bands=[];
    for (var i=0;i<bits.length;i++) bits[i]=parseInt(mask.bits.slice(i*2,i*2+2),16);
    function active(x,y) {var p=y*w+x;return bits[p>>3] & (1<<(p%8));}
    for (var y=0;y<h;y++) {
      var left=w, right=-1;
      for (var x=0;x<w;x++) if (active(x,y)) {left=Math.min(left,x);right=x;}
      if (right<0) continue;
      var last=bands[bands.length-1];
      // Bridge one empty row for detached dots without joining separate text lines.
      if (last && y-last.bottom<=2) {
        last.bottom=y;last.left=Math.min(last.left,left);last.right=Math.max(last.right,right);
      } else bands.push({left:left,right:right,top:y,bottom:y});
    }
    bands.forEach(function (band) {
      var radius=Math.min(4,(band.bottom-band.top+1)/4,(band.right-band.left+1)/4);
      for (var yy=band.top;yy<=band.bottom;yy++) for (var xx=band.left;xx<=band.right;xx++) {
        var cx=Math.max(band.left+radius,Math.min(band.right+1-radius,xx+.5));
        var cy=Math.max(band.top+radius,Math.min(band.bottom+1-radius,yy+.5));
        if (Math.pow(xx+.5-cx,2)+Math.pow(yy+.5-cy,2)<=radius*radius) {
          var p=yy*w+xx;bits[p>>3]|=1<<(p%8);
        }
      }
    });
    return {width:w,height:h,bits:Array.from(bits).map(function (b) {
      return ('0'+b.toString(16)).slice(-2);
    }).join('')};
  }
  if (typeof module!=='undefined') module.exports={join:join};
  else root.LineCoverMask={join:join};
}(this));
