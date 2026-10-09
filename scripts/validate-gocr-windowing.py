import ctypes,sys,os,json,itertools,importlib.util,math,unicodedata
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from ai_edge_litert.interpreter import Interpreter

root=Path(sys.argv[1]); proto_path=Path(sys.argv[2]); out=Path(sys.argv[3])
lib=next(root.rglob('libchromescreenai.so'))
res=root/'resources'
base=res/'gocr/gocr_models/line_recognition_mobile_convnext320_omni'
model=base/'gocr_mobile_und.tflite'
labels_path=base/'gocr_mobile_und_label_map.pb'

# protobuf label map
def vi(b,i):
    v=s=0
    while True:
        x=b[i];i+=1;v|=(x&127)<<s
        if x<128:return v,i
        s+=7

def fields(b):
    i=0
    while i<len(b):
        k,i=vi(b,i);f,w=k>>3,k&7
        if w==0:v,i=vi(b,i);yield f,w,v
        elif w==2:
            n,i=vi(b,i);v=b[i:i+n];i+=n;yield f,w,v
        elif w==1:v=b[i:i+8];i+=8;yield f,w,v
        elif w==5:v=b[i:i+4];i+=4;yield f,w,v
        else:break
labels={}
for f,w,v in fields(labels_path.read_bytes()):
    if f==1 and w==2:
        d={f2:v2 for f2,w2,v2 in fields(v)}
        labels[int(d.get(2,0))]=d.get(1,b'').decode('utf-8','replace')
blank=len(labels)

# Native ScreenAI
requested=[]
GETSZ=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_char_p)
GET=ctypes.CFUNCTYPE(None,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p)
@GETSZ
def getsz(p):
    s=p.decode(); requested.append(s); f=res/s
    return f.stat().st_size if f.exists() else 0
@GET
def getf(p,n,ptr):
    s=p.decode(); requested.append(s); f=res/s
    if f.exists(): ctypes.memmove(ptr,f.read_bytes()[:n],n)
class CI(ctypes.Structure): _fields_=[('fColorSpace',ctypes.c_void_p),('fColorType',ctypes.c_int32),('fAlphaType',ctypes.c_int32)]
class SZ(ctypes.Structure): _fields_=[('fWidth',ctypes.c_int32),('fHeight',ctypes.c_int32)]
class II(ctypes.Structure): _fields_=[('fColorInfo',CI),('fDimensions',SZ)]
class PM(ctypes.Structure): _fields_=[('fPixels',ctypes.c_void_p),('fRowBytes',ctypes.c_size_t),('fInfo',II)]
class BM(ctypes.Structure): _fields_=[('fPixelRef',ctypes.c_void_p),('fPixmap',PM),('fFlags',ctypes.c_uint32)]
so=ctypes.CDLL(str(lib),mode=os.RTLD_LAZY)
so.SetFileContentFunctions.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
so.InitOCRUsingCallback.restype=ctypes.c_bool
so.PerformOCR.argtypes=[ctypes.POINTER(BM),ctypes.POINTER(ctypes.c_uint32)]
so.PerformOCR.restype=ctypes.c_void_p
so.FreeLibraryAllocatedCharArray.argtypes=[ctypes.c_void_p]
so.SetOCRLightMode.argtypes=[ctypes.c_bool]
so.SetFileContentFunctions(getsz,getf); assert so.InitOCRUsingCallback(); so.SetOCRLightMode(False)

text='THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG 0123456789 THE QUICK BROWN FOX'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42)
bbox=font.getbbox(text); W=max(1800,bbox[2]-bbox[0]+80); H=140
im=Image.new('RGBA',(W,H),'white'); d=ImageDraw.Draw(im); d.text((30,35),text,font=font,fill='black')
raw=im.tobytes(); buf=ctypes.create_string_buffer(raw)
bm=BM(); bm.fPixmap.fPixels=ctypes.cast(buf,ctypes.c_void_p); bm.fPixmap.fRowBytes=W*4
bm.fPixmap.fInfo.fColorInfo.fColorType=4; bm.fPixmap.fInfo.fColorInfo.fAlphaType=1
bm.fPixmap.fInfo.fDimensions.fWidth=W; bm.fPixmap.fInfo.fDimensions.fHeight=H
n=ctypes.c_uint32(0); ptr=so.PerformOCR(ctypes.byref(bm),ctypes.byref(n)); data=ctypes.string_at(ptr,n.value); so.FreeLibraryAllocatedCharArray(ptr)
spec=importlib.util.spec_from_file_location('csai',proto_path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ann=m.VisualAnnotation(); ann.ParseFromString(data)
lines=[x for x in ann.lines if x.utf8_string.strip()]
native=max(lines,key=lambda x:len(x.utf8_string))
b=native.bounding_box
crop=im.convert('L').crop((max(0,int(b.x)-2),max(0,int(b.y)-2),min(W,int(b.x+b.width)+2),min(H,int(b.y+b.height)+2)))

it=Interpreter(model_path=str(model),num_threads=2); it.allocate_tensors()
inp=it.get_input_details()[0]
outs=it.get_output_details()
logit_out=next(o for o in outs if list(o['shape'])[-1]==len(labels)+1)

def decode(ids):
    return unicodedata.normalize('NFC',''.join(labels[i] for i,_ in itertools.groupby(ids) if i!=blank)).strip()

def recognize(crop,left_ctx,useful,right_ctx):
    g=crop.convert('L')
    width=max(1,round(g.width*32/g.height))
    g=g.resize((width,32),Image.Resampling.LANCZOS)
    pad=Image.new('L',(width+left_ctx+right_ctx,32),255); pad.paste(g,(left_ctx,0))
    ids=[]
    ts_left=left_ctx//4; ts_useful=useful//4
    for x in range(0,width,useful):
        win=pad.crop((x,0,x+168,32))
        arr=np.asarray(win,dtype=np.uint8)[None,:,:,None]
        it.set_tensor(inp['index'],arr); it.invoke()
        logits=it.get_tensor(logit_out['index'])[0]
        seq=np.argmax(logits,axis=-1).tolist()
        remain=max(0,width-x)
        keep=min(ts_useful,math.ceil(remain/4))
        ids.extend(seq[ts_left:ts_left+keep])
    return decode(ids)

a=recognize(crop,16,136,16)
b2=recognize(crop,32,104,32)
report={
 'expected':text,
 'native':native.utf8_string,
 'native_box':{'x':b.x,'y':b.y,'w':b.width,'h':b.height,'angle':b.angle},
 'crop_size':crop.size,
 'google_16_136_16':a,
 'experimental_32_104_32':b2,
 'exact_google_vs_native':a==native.utf8_string.strip(),
 'exact_old_vs_native':b2==native.utf8_string.strip(),
}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
