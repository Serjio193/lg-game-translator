import ctypes,sys,os,json,importlib.util
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

root=Path(sys.argv[1]); proto_path=Path(sys.argv[2]); out=Path(sys.argv[3])
lib=root/'libchromescreenai.so'
requested=[]

GETSZ=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_char_p)
GET=ctypes.CFUNCTYPE(None,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p)
@GETSZ
def get_sz(p):
    s=p.decode(); requested.append(s)
    f=root/s
    return f.stat().st_size if f.exists() else 0
@GET
def get_file(p,n,ptr):
    s=p.decode(); requested.append(s)
    f=root/s
    if f.exists(): ctypes.memmove(ptr,f.read_bytes()[:n],n)

class SkColorInfo(ctypes.Structure): _fields_=[('fColorSpace',ctypes.c_void_p),('fColorType',ctypes.c_int32),('fAlphaType',ctypes.c_int32)]
class SkISize(ctypes.Structure): _fields_=[('fWidth',ctypes.c_int32),('fHeight',ctypes.c_int32)]
class SkImageInfo(ctypes.Structure): _fields_=[('fColorInfo',SkColorInfo),('fDimensions',SkISize)]
class SkPixmap(ctypes.Structure): _fields_=[('fPixels',ctypes.c_void_p),('fRowBytes',ctypes.c_size_t),('fInfo',SkImageInfo)]
class SkBitmap(ctypes.Structure): _fields_=[('fPixelRef',ctypes.c_void_p),('fPixmap',SkPixmap),('fFlags',ctypes.c_uint32)]

so=ctypes.CDLL(str(lib),mode=os.RTLD_LAZY)
so.SetFileContentFunctions.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
so.InitOCRUsingCallback.restype=ctypes.c_bool
so.GetMaxImageDimension.restype=ctypes.c_uint32
so.SetOCRLightMode.argtypes=[ctypes.c_bool]
so.PerformOCR.argtypes=[ctypes.POINTER(SkBitmap),ctypes.POINTER(ctypes.c_uint32)]
so.PerformOCR.restype=ctypes.c_void_p
so.FreeLibraryAllocatedCharArray.argtypes=[ctypes.c_void_p]
so.SetFileContentFunctions(get_sz,get_file)
init=bool(so.InitOCRUsingCallback())
so.SetOCRLightMode(False)
maxdim=int(so.GetMaxImageDimension())

im=Image.new('RGBA',(1280,720),'white')
d=ImageDraw.Draw(im)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',96)
d.text((120,240),'HELLO WORLD',font=font,fill='black')
raw=im.tobytes(); buf=ctypes.create_string_buffer(raw)
bm=SkBitmap(); bm.fPixmap.fPixels=ctypes.cast(buf,ctypes.c_void_p); bm.fPixmap.fRowBytes=im.width*4
bm.fPixmap.fInfo.fColorInfo.fColorType=4; bm.fPixmap.fInfo.fColorInfo.fAlphaType=1
bm.fPixmap.fInfo.fDimensions.fWidth=im.width; bm.fPixmap.fInfo.fDimensions.fHeight=im.height
n=ctypes.c_uint32(0); ptr=so.PerformOCR(ctypes.byref(bm),ctypes.byref(n))
proto=ctypes.string_at(ptr,n.value) if ptr else b''
if ptr: so.FreeLibraryAllocatedCharArray(ptr)

spec=importlib.util.spec_from_file_location('csai',proto_path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ann=m.VisualAnnotation(); ann.ParseFromString(proto)
lines=[]
for l in ann.lines:
    b=l.bounding_box
    lines.append({'text':l.utf8_string,'bbox':{'x':b.x,'y':b.y,'width':b.width,'height':b.height,'angle':b.angle},'block_id':getattr(l,'block_id',0)})
report={'init':init,'max_image_dimension':maxdim,'response_bytes':len(proto),'requested_files':sorted(set(requested)),'lines':lines,'lib_size':lib.stat().st_size}
out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,indent=2,ensure_ascii=False))
