from pathlib import Path
from google.protobuf import descriptor_pb2, text_format
import sys

data=Path(sys.argv[1]).read_bytes()
out=Path(sys.argv[2])
needle=b"gocr_detector.proto"

def vi(buf,p):
    v=0;sh=0
    for _ in range(10):
        if p>=len(buf): raise ValueError
        b=buf[p];p+=1;v|=(b&127)<<sh
        if b<128:return v,p
        sh+=7
    raise ValueError

hits=[]; pos=0
while True:
    i=data.find(needle,pos)
    if i<0: break
    hits.append(i); pos=i+1

for hit in hits:
    for st in range(max(0,hit-500),hit):
        try:
            tag,p=vi(data,st)
            if tag!=10: continue
            n,p2=vi(data,p); e=p2+n
            if not (p2<=hit<e): continue
            payload=data[p2:e]
            if needle not in payload or not payload.endswith(b".proto"): continue
        except Exception:
            continue
        p=st; ends=[]
        for _ in range(20000):
            try:
                tag,q=vi(data,p); w=tag&7; fn=tag>>3
                if tag==0 or w in (3,4) or fn==0 or fn>1000: break
                p=q
                if w==0: _,p=vi(data,p)
                elif w==1: p+=8
                elif w==2:
                    n,p=vi(data,p); p+=n
                elif w==5: p+=4
                else: break
                if p>len(data): break
                ends.append(p)
            except Exception:
                break
        for end in reversed(ends):
            fd=descriptor_pb2.FileDescriptorProto()
            try: fd.ParseFromString(data[st:end])
            except Exception: continue
            if fd.name.endswith("gocr_detector.proto") and any(m.name.startswith("GocrDetector") or m.name=="DetectorInputImageConfig" for m in fd.message_type):
                out.with_suffix(".pb").write_bytes(data[st:end])
                txt=text_format.MessageToString(fd)
                out.with_suffix(".txt").write_text(txt)
                print(txt)
                raise SystemExit(0)
raise SystemExit("gocr_detector FileDescriptorProto not recovered")
