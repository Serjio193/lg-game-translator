#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG

TARGETS = [
    "TensorFlowModelRunnerConfig=",
    "Invalid TensorFlowModelRunnerConfig.",
    "TfliteModelPooledXNNPackCached::AllocateModelTensors",
    "TfliteModelPooledXNNPackCached::InsertInterpreter",
    "XNNPACK runtime is null.",
    "Failed to modify graph with XNNPack delegate.",
    "Failed to apply the default TensorFlow Lite delegate indexed at %zu.",
    "ocr/google_ocr/detection/group_rpn_detector_v2.cc",
    "ocr/google_ocr/detection/group_rpn_detector_utils.cc",
]

def load_symbols(elf):
    syms=[]
    for secname in [".symtab",".dynsym"]:
        sec=elf.get_section_by_name(secname)
        if not sec: continue
        for s in sec.iter_symbols():
            if s["st_value"] and s.name:
                syms.append((int(s["st_value"]),int(s["st_size"]),s.name))
    syms.sort()
    return syms

def owner(syms,addr):
    best=None
    for va,size,name in syms:
        if va>addr: break
        best=(va,size,name)
    if best is None:return None
    va,size,name=best
    if size and addr>=va+size:return {"name":name,"start":va,"delta":addr-va,"outside_size":True}
    return {"name":name,"start":va,"delta":addr-va,"outside_size":False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("library",type=Path); ap.add_argument("output",type=Path); a=ap.parse_args()
    with a.library.open("rb") as f:
        elf=ELFFile(f)
        text=elf.get_section_by_name(".text")
        if not text: raise SystemExit("no .text")
        text_addr=int(text["sh_addr"]); text_data=text.data()
        syms=load_symbols(elf)
        # Find target VAs by section-local byte search.
        target_addrs={}
        for sec in elf.iter_sections():
            try: data=sec.data()
            except Exception: continue
            base=int(sec["sh_addr"])
            for t in TARGETS:
                needle=t.encode()
                pos=0
                while True:
                    i=data.find(needle,pos)
                    if i<0: break
                    target_addrs.setdefault(t,[]).append(base+i)
                    pos=i+1
        md=Cs(CS_ARCH_ARM64,CS_MODE_ARM); md.detail=True
        ins=list(md.disasm(text_data,text_addr))
        by_addr={x.address:i for i,x in enumerate(ins)}
        xrefs=[]
        # ADR direct references.
        for i,x in enumerate(ins):
            if x.mnemonic=="adr" and len(x.operands)>=2 and x.operands[1].type==ARM64_OP_IMM:
                dest=int(x.operands[1].imm)
                for t,addrs in target_addrs.items():
                    for ta in addrs:
                        if ta<=dest<ta+len(t)+1:
                            xrefs.append((t,ta,i,"adr",dest))
            if x.mnemonic!="adrp" or len(x.operands)<2 or x.operands[0].type!=ARM64_OP_REG or x.operands[1].type!=ARM64_OP_IMM:
                continue
            reg=x.operands[0].reg; page=int(x.operands[1].imm)
            for j in range(i+1,min(len(ins),i+9)):
                y=ins[j]
                # Stop if destination register is overwritten by an unrelated instruction.
                if y.mnemonic=="add" and len(y.operands)>=3 and y.operands[0].type==ARM64_OP_REG and y.operands[1].type==ARM64_OP_REG and y.operands[0].reg==reg and y.operands[1].reg==reg and y.operands[2].type==ARM64_OP_IMM:
                    dest=page+int(y.operands[2].imm)
                    for t,addrs in target_addrs.items():
                        for ta in addrs:
                            if ta<=dest<ta+len(t)+1:
                                xrefs.append((t,ta,j,"adrp+add",dest))
                    break
                # LDR [reg,#imm] can also reference pointer tables, record near target table addresses.
                if y.mnemonic in ("adrp","mov") and y.operands and y.operands[0].type==ARM64_OP_REG and y.operands[0].reg==reg:
                    break
        rows=[]
        seen=set()
        for t,ta,i,kind,dest in xrefs:
            key=(t,ins[i].address,kind)
            if key in seen: continue
            seen.add(key)
            lo=max(0,i-16); hi=min(len(ins),i+22)
            ctx=[]
            for z in ins[lo:hi]:
                ctx.append("0x%x:\t%s\t%s"%(z.address,z.mnemonic,z.op_str))
            rows.append({"target":t,"target_va":ta,"xref_va":ins[i].address,"kind":kind,"resolved_va":dest,
                         "owner":owner(syms,ins[i].address),"context":ctx})
        out={"targets":{k:[hex(x) for x in v] for k,v in target_addrs.items()},"xrefs":rows}
        a.output.write_text(json.dumps(out,indent=2)+"\n")
        for r in rows:
            print("###",r["target"],"target",hex(r["target_va"]),"xref",hex(r["xref_va"]),r["kind"],r["owner"])
            print("\n".join(r["context"])); print()

if __name__=="__main__": main()
