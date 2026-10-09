#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, zipfile
from dataclasses import dataclass
from pathlib import Path

TARGET_LIBS = [
    "liblens_ondevice_engine_base.so",
    "liblens_ondevice_engine_play_ml.so",
    "liblens_vision.so",
    "libtensorflowlite_jni_gms_client.so",
]
ASSET_NAMES = [
    "gocr_group_rpn_text_detection_config_2024_q4.binarypb",
    "gocr_group_rpn_text_detection_model_2024_q4.tflite",
    "recognizer_latn_vi_cyrl_lm_retrained.tflite",
]
KEYWORD_GROUPS = {
    "tflite_core": ["TfLiteInterpreter","InterpreterBuilder","FlatBufferModel","ModifyGraphWithDelegate","SetNumThreads","num_threads"],
    "xnnpack": ["XNNPACK","Xnnpack","TfLiteXNNPackDelegateCreate","TfLiteXNNPackDelegateOptions","xnnpack"],
    "nnapi": ["NNAPI","NnApi","NnApiDelegate","ANeuralNetworks","StatefulNnApiDelegate","nnapi"],
    "gpu": ["GpuDelegate","TfLiteGpuDelegate","OpenCL","OpenGL","EGL","glCompute","gpu_delegate","GPU delegate"],
    "ahwb": ["AHardwareBuffer","AHWB","use_ahwb_input","use_ahwb_output"],
    "gms": ["GMS","Google Play services","play_ml","tflite_jni_gms","com.google.android.gms","TfLiteGpuClient"],
    "group_rpn": ["GroupRpn","group_rpn","GocrDetector","TensorFlowModelRunnerConfig","ProcessPackedImagePyramid","GroupRpnTextDetectionMutator"],
    "recognizer": ["line_recognition","LineRecognizer","recognizer","CtcDecoder"],
}
DELEGATE_SYMBOL_PATTERNS = [re.compile(x,re.I) for x in [
    r"TfLite.*Delegate",r"ModifyGraphWithDelegate",r"XNNPACK",r"NnApi",r"ANeuralNetworks",
    r"GpuDelegate",r"AHardwareBuffer",r"SetNumThreads",r"InterpreterBuilder",r"FlatBufferModel"
]]
PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")

@dataclass
class LibEvidence:
    name: str
    sha256: str
    size: int
    needed: list[str]
    matched_imports: list[str]
    matched_symbols: list[str]
    keyword_hits: dict[str,list[dict]]
    disasm_hits: list[str]
    proto_clues: list[str]

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""): h.update(chunk)
    return h.hexdigest()

def run(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
    return p.stdout

def extract_apk(apk,root):
    libs_dir=root/"libs"; assets_dir=root/"assets"
    libs_dir.mkdir(parents=True,exist_ok=True); assets_dir.mkdir(parents=True,exist_ok=True)
    manifest={"apk":str(apk),"apk_sha256":sha256(apk),"libs":{},"assets":{}}
    with zipfile.ZipFile(apk) as z:
        names=z.namelist()
        for base in TARGET_LIBS:
            choices=[n for n in names if n.endswith("/"+base)]
            arm64=[n for n in choices if "arm64-v8a" in n]
            chosen=arm64[0] if arm64 else (choices[0] if choices else None)
            if not chosen: continue
            dst=libs_dir/base
            with z.open(chosen) as src,dst.open("wb") as out: shutil.copyfileobj(src,out)
            manifest["libs"][base]={"source":chosen,"bytes":dst.stat().st_size,"sha256":sha256(dst)}
        for base in ASSET_NAMES:
            choices=[n for n in names if Path(n).name==base]
            if not choices: continue
            chosen=choices[0]; dst=assets_dir/base
            with z.open(chosen) as src,dst.open("wb") as out: shutil.copyfileobj(src,out)
            manifest["assets"][base]={"source":chosen,"bytes":dst.stat().st_size,"sha256":sha256(dst)}
    return manifest

def readelf_needed(path):
    return re.findall(r"Shared library: \[(.*?)\]",run(["readelf","-d",str(path)]))

def readelf_symbols(path):
    txt=run(["readelf","-Ws",str(path)])
    imports=[]; symbols=[]
    for line in txt.splitlines():
        if not any(p.search(line) for p in DELEGATE_SYMBOL_PATTERNS): continue
        symbols.append(line.strip())
        if " UND " in (" "+line+" "): imports.append(line.strip())
    return imports[:500],symbols[:1000]

def strings_with_offsets(path):
    data=path.read_bytes()
    return [(m.start(),m.group().decode("ascii","replace")) for m in PRINTABLE.finditer(data)]

def keyword_hits(strings):
    result={}
    for group,keys in KEYWORD_GROUPS.items():
        hits=[]
        for off,s in strings:
            low=s.lower()
            for k in keys:
                if k.lower() in low:
                    hits.append({"offset":off,"text":s[:500],"keyword":k}); break
        result[group]=hits[:300]
    return result

def proto_clues(strings):
    out=[]; needles=("tensorflowmodelrunnerconfig","gocrdetectorgpuconfig","group_rpn","delegate","gpu_config","model_runner")
    for off,s in strings:
        low=s.lower()
        if any(n in low for n in needles) or ("gocr" in low and ".proto" in low):
            out.append("0x%x: %s"%(off,s[:700]))
    return out[:500]

def disasm_hits(path,out_file):
    tool=shutil.which("aarch64-linux-gnu-objdump") or shutil.which("llvm-objdump") or shutil.which("objdump")
    if not tool: return []
    txt=run([tool,"-d","-C",str(path)])
    out_file.write_text(txt,errors="replace")
    lines=txt.splitlines(); hits=[]
    for i,line in enumerate(lines):
        if any(p.search(line) for p in DELEGATE_SYMBOL_PATTERNS):
            hits.append("\n".join(lines[max(0,i-5):min(len(lines),i+7)]))
    return hits[:150]

def vi(buf,p):
    v=0; s=0
    for _ in range(10):
        if p>=len(buf): raise ValueError
        b=buf[p]; p+=1; v|=(b&127)<<s
        if b<128:return v,p
        s+=7
    raise ValueError

def raw_proto_fields(data):
    out=[]; p=0
    while p<len(data):
        start=p
        try:
            tag,p=vi(data,p); fn,wt=tag>>3,tag&7
            if wt==0:
                v,p=vi(data,p); out.append({"field":fn,"wire":wt,"value":v,"start":start})
            elif wt==1:
                v=data[p:p+8]; p+=8; out.append({"field":fn,"wire":wt,"hex":v.hex(),"start":start})
            elif wt==2:
                n,p=vi(data,p); v=data[p:p+n]; p+=n
                asc="".join(chr(x) if 32<=x<127 else "." for x in v[:160])
                out.append({"field":fn,"wire":wt,"len":len(v),"hex":v[:96].hex(),"ascii":asc,"start":start,"bytes":v})
            elif wt==5:
                v=data[p:p+4]; p+=4; out.append({"field":fn,"wire":wt,"hex":v.hex(),"start":start})
            else: break
        except Exception: break
    return out

def inspect_detector_config(path):
    if not path.exists(): return {}
    outer=raw_proto_fields(path.read_bytes())
    any_value=next((x["bytes"] for x in outer if x["field"]==2 and x["wire"]==2),None)
    if not any_value:return {"error":"Any.value not found"}
    top=raw_proto_fields(any_value)
    runner=next((x["bytes"] for x in top if x["field"]==1 and x["wire"]==2),None)
    summary={"top_fields":[{k:v for k,v in x.items() if k!="bytes"} for x in top],"model_runner_config":None}
    if runner is not None:
        fields=raw_proto_fields(runner)
        summary["model_runner_config"]={"length":len(runner),"sha256":hashlib.sha256(runner).hexdigest(),"hex":runner.hex(),
            "fields":[{k:v for k,v in x.items() if k!="bytes"} for x in fields]}
    return summary

def classify(evidence):
    imports="\n".join(x for e in evidence for x in e.matched_imports)
    disasm="\n".join(x for e in evidence for x in e.disasm_hits)
    strings="\n".join(h["text"] for e in evidence for hs in e.keyword_hits.values() for h in hs)
    rules={"xnnpack":r"XNNPACK|Xnnpack|TfLiteXNNPackDelegate","nnapi":r"NNAPI|NnApi|ANeuralNetworks",
           "gpu":r"GpuDelegate|TfLiteGpuDelegate|OpenCL|OpenGL","ahwb":r"AHardwareBuffer|AHWB"}
    out={}
    for name,pat in rules.items():
        imp=bool(re.search(pat,imports,re.I)); call=bool(re.search(pat,disasm,re.I)); st=bool(re.search(pat,strings,re.I))
        if imp and call: level,reason="PROVEN","dynamic reference plus disassembly call context"
        elif imp: level,reason="STRONG","dynamic import exists; GOCR ownership still needs call-path confirmation"
        elif call: level,reason="STRONG","disassembly context exists; GOCR ownership still needs confirmation"
        elif st: level,reason="POSSIBLE","matching strings only; presence is not proof of use"
        else: level,reason="NO_EVIDENCE","no matching evidence in inspected libraries"
        out[name]={"level":level,"reason":reason}
    return out

def make_report(manifest,evidence,config,classification,out):
    L=["# Google Lens / GOCR Android runtime research","",
       "Generated automatically from the current Google App APK. Strings alone are never treated as proof of execution.","",
       "## Input","", "- APK SHA-256: "+manifest["apk_sha256"]]
    for name,m in manifest["libs"].items():
        L.append("- %s: %d bytes, SHA-256 %s"%(name,m["bytes"],m["sha256"]))
    L += ["","## Delegate/backend evidence","","| Candidate | Evidence level | Meaning |","|---|---|---|"]
    for name,r in classification.items(): L.append("| %s | **%s** | %s |"%(name,r["level"],r["reason"]))
    L += ["","## Detector TensorFlowModelRunnerConfig raw payload",""]
    runner=config.get("model_runner_config") if isinstance(config,dict) else None
    if runner:
        L += ["- payload length: %d bytes"%runner["length"],"- payload SHA-256: "+runner["sha256"],
              "- raw hex: "+runner["hex"],"","Raw protobuf fields:","","    "+json.dumps(runner["fields"])]
    else:L.append("No model_runner_config payload was recovered.")
    L += ["","## Per-library evidence",""]
    for e in evidence:
        L += ["### "+e.name,"","NEEDED: "+(", ".join(e.needed) if e.needed else "none/stripped"),""]
        if e.matched_imports:
            L += ["Relevant dynamic imports:",""]
            L += ["    "+x for x in e.matched_imports[:80]]
        for group,hits in e.keyword_hits.items():
            if hits:
                L += ["","**%s strings (%d shown):**"%(group,len(hits)),""]
                L += ["    0x%x %s"%(h["offset"],h["text"]) for h in hits[:50]]
        if e.disasm_hits:
            L += ["","Relevant disassembly contexts:",""]
            for h in e.disasm_hits[:20]:
                L += ["    "+x for x in h.splitlines()]; L.append("    ---")
        if e.proto_clues:
            L += ["","Protobuf/config clues:",""]
            L += ["    "+x for x in e.proto_clues[:80]]
        L.append("")
    L += ["## Next confirmation step","",
          "Trace the GroupRPN model-runner constructor to the actual interpreter/delegate creation site. Detector and recognizer must be traced separately.",
          "Raw readelf/strings/disassembly evidence is uploaded as the workflow artifact and is not committed in full.",""]
    out.write_text("\n".join(L))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("apk",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    manifest=extract_apk(a.apk,a.output)
    (a.output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    raw=a.output/"raw"; raw.mkdir(exist_ok=True); evidence=[]
    for base in TARGET_LIBS:
        path=a.output/"libs"/base
        if not path.exists(): continue
        strings=strings_with_offsets(path); hits=keyword_hits(strings); imports,symbols=readelf_symbols(path)
        ev=LibEvidence(base,sha256(path),path.stat().st_size,readelf_needed(path),imports,symbols,hits,
                       disasm_hits(path,raw/(base+".objdump.txt")),proto_clues(strings))
        evidence.append(ev)
        (raw/(base+".strings.json")).write_text(json.dumps([{"offset":o,"text":s} for o,s in strings],indent=2)+"\n")
        (raw/(base+".readelf-symbols.txt")).write_text(run(["readelf","-Ws",str(path)]))
        (raw/(base+".readelf-relocs.txt")).write_text(run(["readelf","-r",str(path)]))
        (raw/(base+".readelf-dynamic.txt")).write_text(run(["readelf","-d",str(path)]))
    config=inspect_detector_config(a.output/"assets"/"gocr_group_rpn_text_detection_config_2024_q4.binarypb")
    classification=classify(evidence)
    summary={"manifest":manifest,"classification":classification,"detector_config":config,
             "libraries":[{"name":e.name,"sha256":e.sha256,"bytes":e.size,"needed":e.needed,
                           "matched_imports":e.matched_imports,"matched_symbols":e.matched_symbols,
                           "keyword_counts":{k:len(v) for k,v in e.keyword_hits.items()},"proto_clues":e.proto_clues} for e in evidence]}
    (a.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    make_report(manifest,evidence,config,classification,a.output/"report.md")
    print((a.output/"report.md").read_text())

if __name__=="__main__": main()
