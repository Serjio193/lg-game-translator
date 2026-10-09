from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import sys
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker

screen_root=Path(sys.argv[1])
android_assets=Path(sys.argv[2])
proto_path=Path(sys.argv[3])
out=Path(sys.argv[4])

resources=screen_root/"resources"
lib=resources/"libchromescreenai.so"
android_cfg=android_assets/"gocr_group_rpn_text_detection_config_2024_q4.binarypb"

spec=importlib.util.spec_from_file_location("csai",proto_path)
pb=importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)

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
ann=pb.VisualAnnotation(); ann.ParseFromString(blob)

native=[]
for line in ann.lines:
    if not line.utf8_string.strip(): continue
    b=line.bounding_box
    native.append({"text":line.utf8_string,"bbox":[float(b.x),float(b.y),float(b.x+b.width),float(b.y+b.height)],"angle":float(b.angle)})

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
