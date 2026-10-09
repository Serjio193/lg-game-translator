"""Warmed same-device TV_FULL A/B, excludes translation and display."""
import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--repeats",type=int,default=5)
    p.add_argument("--threads",type=int,nargs="+",default=[2,4])
    p.add_argument("frames",type=Path,nargs="+")
    a=p.parse_args()
    report={"scope":"frame to OCR text; no translation/OSD", "runs":[]}
    for threads in a.threads:
        os.environ["GOCR_RECOGNIZER"]="python"
        reference=FullGocrWorker(a.assets,threads)
        os.environ["GOCR_RECOGNIZER"]="native"
        native=FullGocrWorker(a.assets,threads)
        if native.native_full is None:
            raise RuntimeError("benchmark requires native full hot path")
        for path in a.frames:
            image=Image.open(path).convert("RGB")
            reference.ocr(image); native.ocr(image)
            samples={"reference":[],"native":[]}
            for i in range(a.repeats):
                # Alternate order to bound warm/load/order effects.
                order=[("reference",reference),("native",native)]
                for name,worker in order if i%2==0 else reversed(order):
                    samples[name].append(worker.ocr(image))
            summary={}
            for name,runs in samples.items():
                summary[name]={key:{"mean":statistics.mean(r["timings_ms"][key] for r in runs),
                                    "median":statistics.median(r["timings_ms"][key] for r in runs),
                                    "min":min(r["timings_ms"][key] for r in runs)}
                               for key in runs[0]["timings_ms"]}
            def identity(result):
                return [(r["line_id"],r["text"],r["source_quad"],r["crop_sha256"],
                         r["recognizer_input_sha256"]) for r in result["lines"]]
            parity=all(identity(r)==identity(samples["reference"][0])
                       for values in samples.values() for r in values)
            row={"frame":str(path),"threads":threads,"samples":samples,"summary":summary,"parity":parity}
            report["runs"].append(row)
            a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps({"frame":str(path),"threads":threads,"parity":parity,
                              "summary":summary}),flush=True)
        reference.close(); native.close()
    return 0 if all(r["parity"] for r in report["runs"]) else 1


if __name__=="__main__":
    raise SystemExit(main())
