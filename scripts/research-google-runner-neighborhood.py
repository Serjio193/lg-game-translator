#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, shutil, subprocess, zipfile
from pathlib import Path

KEYS = [
    "TensorFlowModelRunnerConfig",
    "TfliteModelPooledRunner",
    "TfliteModelPooledXNNPackCached",
    "InterpreterFactoryCallbackXNNPack",
    "InterpreterFactoryCallback",
    "ModifyGraphWithDelegate",
    "Failed to apply the default TensorFlow Lite delegate",
    "GocrDetectorGpuConfig",
    "use_ahwb_input",
    "use_ahwb_output",
    "GroupRpnTextDetectionMutator",
]

PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")

def run(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
    return p.stdout

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("library",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--radius",type=lambda x:int(x,0),default=0x6000)
    a=ap.parse_args()
    data=a.library.read_bytes()
    strings=[(m.start(),m.group().decode("ascii","replace")) for m in PRINTABLE.finditer(data)]
    out=[]
    for key in KEYS:
        hits=[(off,s) for off,s in strings if key.lower() in s.lower()]
        for n,(off,s) in enumerate(hits):
            lo=max(0,off-a.radius); hi=min(len(data),off+a.radius)
            near=[{"offset":o,"delta":o-off,"text":t} for o,t in strings if lo<=o<=hi]
            out.append({"key":key,"hit_index":n,"hit_offset":off,"hit_text":s,"nearby":near})
    a.output.write_text(json.dumps(out,indent=2)+"\n")
    for block in out:
        print("###",block["key"],hex(block["hit_offset"]),block["hit_text"])
        for x in block["nearby"]:
            if abs(x["delta"])<=0x1800:
                print("%+7d 0x%x %s"%(x["delta"],x["offset"],x["text"]))
        print()

if __name__=="__main__": main()
