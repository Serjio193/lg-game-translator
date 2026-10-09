from __future__ import annotations

import ctypes
import json
import struct
import os
import sys
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker

screen_root=Path(sys.argv[1])
android_assets=Path(sys.argv[2])
out=Path(sys.argv[3])

resources=screen_root/"resources"
lib=resources/"libchromescreenai.so"
android_cfg=android_assets/"gocr_group_rpn_text_detection_config_2024_q4.binarypb"

# Build a 1280x720 game-like frame with separated lines.
im=Image.new("RGBA",(1280,720),"white")
d=ImageDraw.Draw(im)
font1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",54)
font2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",40)
d.text((95,150),"THE DOOR IS LOCKED",font=font1,fill="black")
d.text((560,350),"Press E to open",font=font2,fill="black")
d.text((180,545),"Привет мир",font=font1,fill="black")
frame=out.parent/"frame.png"; im.save(frame)

requested=[]
GETSZ=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_char_p)
GET=ctypes.CFUNCTYPE(None,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p)

def content_for(name):
    # Native ScreenAI asks for its chrome config; use the original Android Lens config.
    if name.endswith("gocr_group_rpn_text_detection_config_2024_q4_chrome.binarypb"):
        return android_cfg.read_bytes()
    p=resources/name.lstrip("/")
    if p.exists() and p.is_file():
        return p.read_bytes()
    return None

@GETSZ
def getsz(p):
    name=p.decode(); requested.append(name)
    b=content_for(name)
    return len(b) if b is not None else 0

@GET
def getf(p,n,ptr):
    name=p.decode(); b=content_for(name)
    if b is not None:
        ctypes.memmove(ptr,b[:n],n)

class CI(ctypes.Structure):
    _fields_=[("fColorSpace",ctypes.c_void_p),("fColorType",ctypes.c_int32),("fAlphaType",ctypes.c_int32)]
class SZ(ctypes.Structure):
    _fields_=[("fWidth",ctypes.c_int32),("fHeight",ctypes.c_int32)]
class II(ctypes.Structure):
    _fields_=[("fColorInfo",CI),("fDimensions",SZ)]
class PM(ctypes.Structure):
    _fields_=[("fPixels",ctypes.c_void_p),("fRowBytes",ctypes.c_size_t),("fInfo",II)]
class BM(ctypes.Structure):
    _fields_=[("fPixelRef",ctypes.c_void_p),("fPixmap",PM),("fFlags",ctypes.c_uint32)]

so=ctypes.CDLL(str(lib),mode=os.RTLD_LAZY)
so.SetFileContentFunctions.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
so.InitOCRUsingCallback.restype=ctypes.c_bool
so.PerformOCR.argtypes=[ctypes.POINTER(BM),ctypes.POINTER(ctypes.c_uint32)]
so.PerformOCR.restype=ctypes.c_void_p
so.FreeLibraryAllocatedCharArray.argtypes=[ctypes.c_void_p]
so.SetFileContentFunctions(getsz,getf)
assert so.InitOCRUsingCallback()

raw=im.tobytes(); buf=ctypes.create_string_buffer(raw)
bm=BM(); bm.fPixmap.fPixels=ctypes.cast(buf,ctypes.c_void_p); bm.fPixmap.fRowBytes=1280*4
bm.fPixmap.fInfo.fColorInfo.fColorType=4; bm.fPixmap.fInfo.fColorInfo.fAlphaType=1
bm.fPixmap.fInfo.fDimensions.fWidth=1280; bm.fPixmap.fInfo.fDimensions.fHeight=720
n=ctypes.c_uint32(0)
ptr=so.PerformOCR(ctypes.byref(bm),ctypes.byref(n))
blob=ctypes.string_at(ptr,n.value); so.FreeLibraryAllocatedCharArray(ptr)
def vi(data,pos):
    v=0; sh=0
    while True:
        b=data[pos]; pos+=1; v|=(b&127)<<sh
        if b<128: return v,pos
        sh+=7

def fields(data):
    p=0
    while p<len(data):
        tag,p=vi(data,p); f,w=tag>>3,tag&7
        if w==0:
            v,p=vi(data,p)
        elif w==2:
            n,p=vi(data,p); v=data[p:p+n]; p+=n
        elif w==5:
            v=data[p:p+4]; p+=4
        elif w==1:
            v=data[p:p+8]; p+=8
        else:
            raise ValueError("unsupported wire")
        yield f,w,v

def rect(raw):
    vals={"x":0,"y":0,"width":0,"height":0,"angle":0.0}
    for f,w,v in fields(raw):
        if f in (1,2,3,4) and w==0:
            vals[{1:"x",2:"y",3:"width",4:"height"}[f]]=int(v)
        elif f==5 and w==5:
            vals["angle"]=struct.unpack("<f",v)[0]
    return vals

native=[]
for f,w,line_raw in fields(blob):
    if f!=2 or w!=2: continue
    txt=""; box=None
    for lf,lw,lv in fields(line_raw):
        if lf==2 and lw==2: box=rect(lv)
        elif lf==3 and lw==2: txt=lv.decode("utf-8")
    if txt.strip() and box:
        native.append({"text":txt,"bbox":[float(box["x"]),float(box["y"]),float(box["x"]+box["width"]),float(box["y"]+box["height"])],"angle":float(box["angle"])})

worker=FullGocrWorker(android_assets,threads=2)
portable=worker.ocr(im.convert("RGB"))
pred=[]
for line in portable["lines"]:
    q=line["source_quad"]
    pts=[q["p0"],q["p1"],q["p2"],q["p3"]]
    xs=[p["x"] for p in pts]; ys=[p["y"] for p in pts]
    pred.append({"text":line["text"],"bbox":[min(xs),min(ys),max(xs),max(ys)],"angle":line["angle"]})

def iou(a,b):
    x1=max(a[0],b[0]); y1=max(a[1],b[1]); x2=min(a[2],b[2]); y2=min(a[3],b[3])
    inter=max(0,x2-x1)*max(0,y2-y1)
    aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]); bb=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    return inter/max(aa+bb-inter,1e-9)

pairs=[]
used=set()
for ni,nl in enumerate(native):
    choices=sorted(((iou(nl["bbox"],pl["bbox"]),pi) for pi,pl in enumerate(pred) if pi not in used),reverse=True)
    if choices and choices[0][0]>0:
        score,pi=choices[0]; used.add(pi)
        pairs.append({"native":ni,"portable":pi,"iou":score,"native_text":nl["text"],"portable_text":pred[pi]["text"]})

report={
    "native":native,
    "portable":pred,
    "matches":pairs,
    "mean_iou":sum(x["iou"] for x in pairs)/max(1,len(pairs)),
    "native_count":len(native),
    "portable_count":len(pred),
    "requested_detector_config_override":any("gocr_group_rpn_text_detection_config_2024_q4_chrome.binarypb" in x for x in requested),
    "worker_timings":portable["timings_ms"],
}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
