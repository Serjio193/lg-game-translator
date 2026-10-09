"""Same decoded proposals, two backends, same rectifier and recognizer."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import statistics
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.detector import rectify_crop
from gocr_worker.detector_runtime import GoogleConfiguredGroupRpnDetector
from gocr_worker.native_postprocess import NativePostprocess
from gocr_worker.recognizer import GocrLineRecognizer
from gocr_worker.image_contract import fingerprint


def ordered(lines, image):
    result=[]
    for b in sorted(lines,key=lambda x:(x["bbox"][1],x["bbox"][0])):
        x1,y1,x2,y2=b["bbox"]
        if x2<=0 or y2<=0 or x1>=image.width or y1>=image.height:
            continue
        result.append(b)
    return result


def evaluate(detector,native,pieces,groups,image,recognizer,repeats):
    runs={"python":[],"native":[]}
    results={}
    for name in runs:
        for repeat in range(repeats+1):
            start=time.perf_counter()
            lines=(native.run(detector,pieces,groups) if name=="native" else
                   detector._postprocess_python(pieces,groups))
            elapsed=(time.perf_counter()-start)*1000
            if repeat:
                runs[name].append({"total_postprocess_ms":elapsed,**detector.cluster_timings})
        results[name]={"lines":ordered(lines,image),"counts":dict(detector.cluster_counts),
                       "membership":list(detector.component_membership)}
    a,b=results["python"],results["native"]
    parity={"counts_equal":a["counts"]==b["counts"],
            "membership_equal":a["membership"]==b["membership"],
            "line_count_equal":len(a["lines"])==len(b["lines"])}
    comparisons=[]
    for x,y in zip(a["lines"],b["lines"]):
        ca,cb=rectify_crop(image,x["quad"]),rectify_crop(image,y["quad"])
        ra,rb=recognizer.recognize(ca),recognizer.recognize(cb)
        comparisons.append({"python_quad":x["quad"].tolist(),"native_quad":y["quad"].tolist(),
            "quad_max_error":float(np.max(np.abs(x["quad"]-y["quad"]))),
            "angle_error":abs(x["angle"]-y["angle"]),"score_error":abs(x["score"]-y["score"]),
            "pieces_equal":x["pieces"]==y["pieces"],
            "python_crop_sha256":fingerprint(ca),"native_crop_sha256":fingerprint(cb),
            "python_text":ra["text"],"native_text":rb["text"]})
    parity["crops_equal"]=all(x["python_crop_sha256"]==x["native_crop_sha256"] for x in comparisons)
    parity["text_equal"]=all(x["python_text"]==x["native_text"] for x in comparisons)
    parity["coordinates_within_1e_9"]=all(max(x["quad_max_error"],x["angle_error"],x["score_error"])<=1e-9 for x in comparisons)
    parity["pieces_equal"]=all(x["pieces_equal"] for x in comparisons)
    return {"runs":runs,"parity":parity,"counts":a["counts"],
            "membership":a["membership"],"lines":comparisons}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--assets",type=Path,required=True)
    ap.add_argument("--library",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--repeats",type=int,default=3)
    ap.add_argument("frames",type=Path,nargs="+")
    args=ap.parse_args()
    os.environ["GOCR_POSTPROCESS"]="python"
    detector=GoogleConfiguredGroupRpnDetector(args.assets,threads=2)
    recognizer=GocrLineRecognizer(args.assets,threads=2)
    native=NativePostprocess(args.library)
    report={"parity_scope":"current Python clean-room reference, not Google Lens","frames":[]}
    for frame in args.frames:
        image=Image.open(frame).convert("RGB")
        detector._run_network(image)  # model warm-up, not timed
        started=time.perf_counter()
        decoded,invoke_ms=detector._run_network(image)
        network_ms=(time.perf_counter()-started)*1000
        pieces=[b for i in range(6) for b in decoded[i]]
        groups=[b for i in range(6,11) for b in decoded[i]]
        raw=[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in b.items()}
             for b in pieces+groups]
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.with_name(frame.stem+"-proposals.json").write_text(json.dumps(raw))
        result=evaluate(detector,native,pieces,groups,image,recognizer,args.repeats)
        # Separate real full passes; inference is timed again, not added as an estimate.
        for name in ("python","native"):
            detector.native_postprocess=native if name=="native" else None
            start=time.perf_counter()
            detected=detector.detect(image)
            for line in detected["lines"]:
                recognizer.recognize(rectify_crop(image,line["quad"]))
            result[name+"_full_ocr_ms"]=(time.perf_counter()-start)*1000
            result[name+"_full_detector"]=detected
        result["benchmarks"]={}
        for name in ("python","native"):
            for label,key in (("dedupe","piece_dedupe"),("pairwise","pairwise_connections"),
                              ("total_postprocess","total_postprocess_ms")):
                result["benchmarks"][name+"_"+label+"_ms"]=statistics.median(
                    run[key] for run in result["runs"][name])
        result["benchmarks"]["full_ocr_ms"]={name:result[name+"_full_ocr_ms"]
                                              for name in ("python","native")}
        report["frames"].append({"frame":frame.name,"frame_sha256":fingerprint(image),
            "raw_piece_count":len(pieces),"raw_group_count":len(groups),
            "network_ms":network_ms,"invoke_ms":invoke_ms,**result})
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps({"frame":frame.name,"parity":result["parity"],"runs":result["runs"]}),flush=True)
    if not all(all(x["parity"].values()) for x in report["frames"]):
        raise SystemExit("reference equivalence failed")


if __name__=="__main__":
    main()
