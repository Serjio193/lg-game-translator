import sys, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ai_edge_litert.interpreter import Interpreter

model,out=sys.argv[1],sys.argv[2]
interp=Interpreter(model_path=model,num_threads=2)
inputs=interp.get_input_details()

def make(angle=0):
    im=Image.new('L',(1280,720),255)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',96)
    layer=Image.new('L',(900,180),255)
    d=ImageDraw.Draw(layer)
    d.text((30,20),'HELLO WORLD',font=font,fill=0)
    if angle:
        layer=layer.rotate(angle,expand=True,fillcolor=255,resample=Image.Resampling.BICUBIC)
    im.paste(layer,((1280-layer.width)//2,(720-layer.height)//2))
    return im

def run(im):
    scales=[]; tensors=[]
    for d,limit in zip(inputs,[1280,1280,640,160]):
        scale=min(1.0, limit/max(im.size)) if limit==1280 else limit/max(im.size)
        cw,ch=max(1,round(im.width*scale)),max(1,round(im.height*scale))
        w,h=math.ceil(cw/32)*32,math.ceil(ch/32)*32
        src=Image.new('L',(w,h),255)
        src.paste(im.resize((cw,ch),Image.Resampling.BILINEAR),(0,0))
        arr=np.asarray(src,dtype=np.uint8)[None,:,:,None]
        interp.resize_tensor_input(d['index'],arr.shape,strict=False)
        tensors.append(arr); scales.append((cw/im.width,ch/im.height))
    interp.allocate_tensors()
    for d,a in zip(inputs,tensors): interp.set_tensor(d['index'],a)
    interp.invoke()
    return {d['name']:interp.get_tensor(d['index']) for d in interp.get_output_details()},scales

def analyze(name,angle):
    im=make(angle)
    raw,scales=run(im)
    lines=[f'CASE {name} requested_angle={angle}']
    heads=[(0,0,8,16),(1,0,32,64),(2,1,8,16),(3,1,32,64),(4,2,32,64),(5,3,32,64),
           (6,0,8,16),(7,0,32,64),(8,1,8,16),(9,1,32,64),(10,2,32,64)]
    for idx,source,stride,anchor in heads:
        key='Identity' if idx==0 else f'Identity_{idx}'
        a=raw[key][0]
        flat=a[:,:,0]
        yi,xi=np.unravel_index(np.argmax(flat),flat.shape)
        v=a[yi,xi]
        score=1/(1+math.exp(-float(v[0])))
        ang=math.degrees(math.atan2(float(v[6]),float(v[5])))
        norm=math.hypot(float(v[5]),float(v[6]))
        cx=(xi+.5+float(v[1]))*stride/scales[source][0]
        cy=(yi+.5+float(v[2]))*stride/scales[source][1]
        w=anchor*math.exp(float(np.clip(v[3],-8,8)))/scales[source][0]
        h=anchor*math.exp(float(np.clip(v[4],-8,8)))/scales[source][1]
        lines.append(f'head={idx} shape={list(a.shape)} maxlogit={float(v[0]):.4f} score={score:.4f} xy=({cx:.1f},{cy:.1f}) wh=({w:.1f},{h:.1f}) angle={ang:.2f} anglevec_norm={norm:.4f} raw={v.tolist()}')
    return '\n'.join(lines)

text=analyze('horizontal',0)+'\n\n'+analyze('rotated30',30)+'\n'
Path(out).write_text(text)
print(text)
