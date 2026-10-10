// Fixed QR version 2-L, byte mode, mask 0; LAN IPv4 HTTP URLs fit in 32 bytes.
'use strict';
function multiply(x,y) {var z=0;for(var i=7;i>=0;i--){z=(z<<1)^((z>>>7)*0x11d);z^=((y>>>i)&1)*x;}return z;}
function matrix(text) {
  if(!/^http:\/\/[0-9.]+:[0-9]+\/$/.test(text)||Buffer.byteLength(text)>32) throw new Error('Unsupported QR URL');
  var bits=[];function append(value,count){for(var n=count-1;n>=0;n--) bits.push((value>>>n)&1);}
  append(4,4);append(text.length,8);for(var i=0;i<text.length;i++) append(text.charCodeAt(i),8);
  append(0,Math.min(4,272-bits.length));while(bits.length%8) bits.push(0);
  var data=[];for(i=0;i<bits.length;i+=8){var byte=0;for(var j=0;j<8;j++) byte=(byte<<1)|bits[i+j];data.push(byte);}
  for(i=0;data.length<34;i++) data.push(i%2?0x11:0xec);
  var divisor=new Array(10).fill(0);divisor[9]=1;var root=1;
  for(i=0;i<10;i++){for(j=0;j<10;j++){divisor[j]=multiply(divisor[j],root);if(j<9)divisor[j]^=divisor[j+1];}root=multiply(root,2);}
  var remainder=new Array(10).fill(0);
  data.forEach(function(value){var factor=value^remainder.shift();remainder.push(0);for(var k=0;k<10;k++)remainder[k]^=multiply(divisor[k],factor);});
  var words=data.concat(remainder),size=25,grid=[],reserved=[];
  for(i=0;i<size;i++){grid.push(new Array(size).fill(false));reserved.push(new Array(size).fill(false));}
  function put(x,y,value){if(x>=0&&y>=0&&x<size&&y<size){grid[y][x]=!!value;reserved[y][x]=true;}}
  for(i=0;i<size;i++){put(6,i,i%2===0);put(i,6,i%2===0);}
  function finder(cx,cy){for(var dy=-4;dy<=4;dy++)for(var dx=-4;dx<=4;dx++){var d=Math.max(Math.abs(dx),Math.abs(dy));put(cx+dx,cy+dy,d!==2&&d!==4);}}
  finder(3,3);finder(21,3);finder(3,21);
  for(var dy=-2;dy<=2;dy++)for(var dx=-2;dx<=2;dx++)put(18+dx,18+dy,Math.max(Math.abs(dx),Math.abs(dy))!==1);
  var format=8,rem=format;for(i=0;i<10;i++)rem=(rem<<1)^((rem>>>9)*0x537);format=((format<<10)|rem)^0x5412;
  function fbit(n){return(format>>>n)&1;}
  for(i=0;i<6;i++)put(8,i,fbit(i));put(8,7,fbit(6));put(8,8,fbit(7));put(7,8,fbit(8));
  for(i=9;i<15;i++)put(14-i,8,fbit(i));for(i=0;i<8;i++)put(size-1-i,8,fbit(i));
  for(i=8;i<15;i++)put(8,size-15+i,fbit(i));put(8,size-8,true);
  var position=0;
  for(var right=size-1;right>=1;right-=2){if(right===6)right=5;
    for(var vertical=0;vertical<size;vertical++){var y=((right+1)&2)===0?size-1-vertical:vertical;
      for(j=0;j<2;j++){var x=right-j;if(reserved[y][x])continue;
        var value=position<words.length*8?((words[position>>>3]>>>(7-(position&7)))&1):0;
        grid[y][x]=!!(value^((x+y)%2===0?1:0));position++;
      }
    }
  }
  return grid;
}
function svg(text) {
  var grid=matrix(text),paths=[];grid.forEach(function(row,y){row.forEach(function(on,x){if(on)paths.push('M'+(x+4)+','+(y+4)+'h1v1h-1z');});});
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 33 33" shape-rendering="crispEdges"><rect width="33" height="33" fill="white"/><path fill="black" d="'+paths.join('')+'"/></svg>';
}
exports.matrix=matrix;exports.svg=svg;
