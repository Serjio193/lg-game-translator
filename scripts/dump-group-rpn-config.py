#!/usr/bin/env python3
"""Dump the private GroupRPN binarypb launch contract without needing its .proto schema."""
import argparse,struct
from pathlib import Path

def varint(b,i):
    v=s=0
    while i<len(b):
        x=b[i];i+=1;v|=(x&127)<<s
        if x<128:return v,i
        s+=7
    raise ValueError("truncated varint")

def parse(b):
    i=0; out=[]
    while i<len(b):
        key,i=varint(b,i); field,wt=key>>3,key&7
        if wt==0:
            v,i=varint(b,i); out.append((field,"varint",v))
        elif wt==1:
            out.append((field,"double",struct.unpack_from("<d",b,i)[0])); i+=8
        elif wt==2:
            n,i=varint(b,i); raw=b[i:i+n]; i+=n
            try:
                s=raw.decode()
                printable=sum(32<=ord(c)<127 for c in s)/max(1,len(s))
            except Exception: printable=0
            if printable>.9:
                out.append((field,"string",s))
            else:
                try: child=parse(raw)
                except Exception: child=[]
                if child:
                    out.append((field,"message",child))
                elif n%4==0:
                    out.append((field,"packed_float",[struct.unpack_from("<f",raw,j)[0] for j in range(0,n,4)]))
                else:
                    out.append((field,"bytes",raw.hex()))
        elif wt==5:
            out.append((field,"float",struct.unpack_from("<f",b,i)[0])); i+=4
        else:
            raise ValueError(f"unsupported wire type {wt}")
    return out

def dump(nodes,indent=""):
    counts={}
    for f,t,v in nodes:
        counts[f]=counts.get(f,0)+1
        label=f"{f}[{counts[f]-1}]"
        if t=="message":
            print(f"{indent}{label}:")
            dump(v,indent+"  ")
        else:
            print(f"{indent}{label}: {t} {v}")

ap=argparse.ArgumentParser()
ap.add_argument("config")
args=ap.parse_args()
dump(parse(Path(args.config).read_bytes()))
