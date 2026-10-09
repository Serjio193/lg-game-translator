"""Original inputs/heads/proposals/quads/crops/text: Python vs native on one device."""
import argparse
import ctypes as C
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.detector import rectify_crop
from gocr_worker.detector_runtime import GoogleConfiguredGroupRpnDetector
from gocr_worker.image_contract import fingerprint
from gocr_worker.native_detector import NativeDetector, config_from_assets
from gocr_worker.native_postprocess import Proposal
from gocr_worker.recognizer import GocrLineRecognizer


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--assets",type=Path,required=True)
    ap.add_argument("--library",required=True)
    ap.add_argument("--runtime",default="/usr/lib/libtensorflow-lite.so")
    ap.add_argument("--threads",type=int,default=2)
    ap.add_argument("--xnnpack",type=int,choices=(0,1),default=0)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("frames",type=Path,nargs="+")
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    cfg=config_from_assets(args.assets)
    args.output.with_suffix(".config").write_bytes(b"GDNCFG1\0"+bytes(cfg))
    os.environ["GOCR_POSTPROCESS"]="native"
    os.environ["GOCR_TFLITE_C_LIBRARY"]="/usr/lib/libtensorflow-lite.so"
    reference=GoogleConfiguredGroupRpnDetector(args.assets,threads=args.threads)
    native=NativeDetector(args.assets,args.threads,args.library,args.runtime,args.xnnpack)
    recognizer=GocrLineRecognizer(args.assets,threads=args.threads)
    report={"reference":"Python + system TFLite + native postprocess",
            "scope":"current clean-room reference, not Google Lens",
            "runtime":args.runtime,"xnnpack":bool(args.xnnpack),"frames":[]}
    for path in args.frames:
        image=Image.open(path).convert("RGB")
        reference.detect(image)
        native.detect(image)
        tensors,_=reference._prepare(image)
        a=reference.detect(image)
        b=native.detect(image)
        inputs=[{"index":i,"python_sha256":sha(t.tobytes()),
                 "native_sha256":sha(native.tensor_bytes("input",i))} for i,t in enumerate(tensors)]
        outputs=[]
        heads={d["name"]:d for d in reference.interpreter.get_output_details()}
        for i in range(11):
            name="Identity" if i==0 else f"Identity_{i}"
            arr=reference.interpreter.get_tensor(heads[name]["index"])
            raw=native.tensor_bytes("output",i)
            candidate=np.frombuffer(raw,dtype=arr.dtype).reshape(arr.shape)
            outputs.append({"head":i,"python_sha256":sha(arr.tobytes()),"native_sha256":sha(raw),
                            "max_abs_error":float(np.max(np.abs(arr-candidate)))})
        # Decode the exact reference output tensors without another invocation.
        ref_proposals=[]
        for head,src,stride,anchor in [(i,cfg.sources[i],cfg.strides[i],cfg.anchors[i]) for i in range(11)]:
            name="Identity" if head==0 else f"Identity_{head}"
            raw=reference.interpreter.get_tensor(heads[name]["index"])
            sx=cfg.limits[src]/1280
            ref_proposals.extend(reference._decode_head(raw,stride,anchor,sx,sx,head))
        count=native.lib.gocr_detector_copy_proposals(native.context,None,0)
        proposals=(Proposal*count)()
        native.lib.gocr_detector_copy_proposals(native.context,proposals,count)
        proposal_errors=[]
        if len(ref_proposals)==count:
            for x,y in zip(ref_proposals,proposals):
                proposal_errors.append(max(float(np.max(np.abs(x["quad"].ravel()-list(y.quad)))),
                    abs(x["score"]-y.score),abs(x["angle"]-y.angle)))
        comparisons=[]
        for x,y in zip(a["lines"],b["lines"]):
            ca,cb=rectify_crop(image,x["quad"]),rectify_crop(image,y["quad"])
            ra,rb=recognizer.recognize(ca),recognizer.recognize(cb)
            comparisons.append({"line_id":x["line_id"],"python_quad":x["quad"],"native_quad":y["quad"],
                "quad_error":float(np.max(np.abs(np.asarray(x["quad"])-y["quad"]))),
                "angle_error":abs(x["angle"]-y["angle"]),"score_error":abs(x["score"]-y["score"]),
                "python_crop_sha256":fingerprint(ca),"native_crop_sha256":fingerprint(cb),
                "python_text":ra["text"],"native_text":rb["text"]})
        parity={"inputs_exact":all(x["python_sha256"]==x["native_sha256"] for x in inputs),
            "outputs_exact":all(x["python_sha256"]==x["native_sha256"] for x in outputs),
            "raw_count_equal":len(ref_proposals)==count,
            "proposal_error_within_1e_9":len(proposal_errors)==count and max(proposal_errors,default=0)<=1e-9,
            "counts_equal":a["counts"]==b["counts"],"line_count_equal":len(a["lines"])==len(b["lines"]),
            "geometry_within_1e_9":all(max(x["quad_error"],x["angle_error"],x["score_error"])<=1e-9 for x in comparisons),
            "crops_exact":all(x["python_crop_sha256"]==x["native_crop_sha256"] for x in comparisons),
            "text_exact":all(x["python_text"]==x["native_text"] for x in comparisons)}
        report["frames"].append({"frame":path.name,"frame_sha256":fingerprint(image),"parity":parity,
            "inputs":inputs,"outputs":outputs,"raw_proposal_count":count,
            "proposal_max_error":max(proposal_errors,default=None),"lines":comparisons,
            "python_detector":a,"native_detector":b})
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps({"frame":path.name,"parity":parity,"python_ms":a["total_ms"],
                          "native_ms":b["total_ms"]}),flush=True)
    if not all(all(f["parity"].values()) for f in report["frames"]):
        raise SystemExit("native detector strict equivalence failed")


if __name__=="__main__":
    main()
