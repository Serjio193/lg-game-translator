#!/usr/bin/env python3
from pathlib import Path
from google.protobuf import descriptor_pb2, text_format
import argparse

def vi(buf,p):
    v=0;sh=0
    for _ in range(10):
        if p>=len(buf): raise ValueError
        b=buf[p];p+=1;v|=(b&127)<<sh
        if b<128:return v,p
        sh+=7
    raise ValueError

def has_message(msgs,target):
    for m in msgs:
        if m.name==target: return True
        if has_message(m.nested_type,target): return True
    return False

def try_file(data,st,target):
    p=st; ends=[]
    for _ in range(50000):
        try:
            tag,q=vi(data,p); w=tag&7; fn=tag>>3
            if tag==0 or fn==0 or fn>2000 or w in (3,4): break
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
        if fd.name.endswith(".proto") and has_message(fd.message_type,target):
            return fd,data[st:end]
    return None,None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("binary",type=Path)
    ap.add_argument("message")
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    data=a.binary.read_bytes()
    target=a.message.encode()
    tpos=[]; p=0
    while True:
        i=data.find(target,p)
        if i<0: break
        tpos.append(i); p=i+1
    if not tpos: raise SystemExit("message string not found: "+a.message)
    proto=[]; p=0
    while True:
        i=data.find(b".proto",p)
        if i<0: break
        proto.append(i); p=i+6
    tried=set()
    for t in tpos:
        nearby=[x for x in proto if 0 < t-x < 300000]
        for hit in reversed(nearby):
            for st in range(max(0,hit-500),hit):
                if st in tried: continue
                tried.add(st)
                try:
                    tag,p1=vi(data,st)
                    if tag!=10: continue
                    n,p2=vi(data,p1); e=p2+n
                    if not (p2<=hit<e): continue
                    payload=data[p2:e]
                    if not payload.endswith(b".proto"): continue
                except Exception: continue
                fd,raw=try_file(data,st,a.message)
                if fd is None: continue
                a.output.with_suffix(".pb").write_bytes(raw)
                txt=text_format.MessageToString(fd)
                a.output.with_suffix(".txt").write_text(txt)
                print(txt)
                return
    raise SystemExit("descriptor containing message not recovered: "+a.message)

if __name__=="__main__": main()
