import sys,json,itertools,unicodedata
from pathlib import Path
import numpy as np
from ai_edge_litert.interpreter import Interpreter

model,labels,out=sys.argv[1:4]

def vi(b,i):
    v=s=0
    while True:
        x=b[i];i+=1;v|=(x&127)<<s
        if x<128:return v,i
        s+=7

def fields(b):
    i=0
    while i<len(b):
        k,i=vi(b,i); f,w=k>>3,k&7
        if w==0: v,i=vi(b,i); yield f,w,v
        elif w==2:
            n,i=vi(b,i);v=b[i:i+n];i+=n;yield f,w,v
        elif w==1: v=b[i:i+8];i+=8;yield f,w,v
        elif w==5: v=b[i:i+4];i+=4;yield f,w,v
        else: break

lab={}
for f,w,v in fields(Path(labels).read_bytes()):
    if f==1 and w==2:
        d={f2:v2 for f2,w2,v2 in fields(v)}
        lab[int(d.get(2,0))]=d.get(1,b'').decode('utf-8','replace')

it=Interpreter(model_path=model,num_threads=2)
it.allocate_tensors()

def clean(d):
    out={}
    for k in ('name','index','shape','shape_signature','dtype','quantization'):
        v=d[k]
        if k=='dtype':
            v=str(v)
        elif hasattr(v,'tolist'):
            v=v.tolist()
        out[k]=v
    return out

report={
 'inputs':[clean(x) for x in it.get_input_details()],
 'outputs':[clean(x) for x in it.get_output_details()],
 'label_count':len(lab),
 'blank_id':len(lab),
 'sample_label_ids':{c:[i for i,s in lab.items() if s==c] for c in ['A','a','Я','я','ё','é']},
}
Path(out).write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
