"""Explicit warmed STRICT/FAST_XNNPACK comparison on identical saved RGB frames."""
import argparse
import hashlib
import json
import os
import statistics
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker
from gocr_worker.profile_comparison import compare_lines


def identity(result):
    return [(r["text"],r["source_quad"]) for r in result["lines"]]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--repeats",type=int,default=5)
    p.add_argument("frames",type=Path,nargs="+")
    a=p.parse_args()
    if a.repeats<1:
        p.error("repeats must be positive")
    report={"scope":"selected saved frame to text, no capture/translation/OSD",
            "reference":"current clean-room STRICT, not Google Lens or ground truth",
            "threads":{"detector":2,"recognizer":2},"matching_iou":0.5,"runs":[]}
    workers={}
    try:
        for profile in ("strict","fast_xnnpack"):
            os.environ.update(GOCR_PROFILE=profile,GOCR_DETECTOR="native",GOCR_RECOGNIZER="native")
            workers[profile]=FullGocrWorker(a.assets,2)
            if workers[profile].native_full is None:
                raise RuntimeError("benchmark requires native full hot path")
        report["asset_status"]=workers["strict"].asset_status
        for path in a.frames:
            image=Image.open(path).convert("RGB")
            if image.size!=(1280,720):
                raise ValueError(f"not selected 1280x720: {path}")
            for worker in workers.values():
                worker.ocr(image)
            samples={profile:[] for profile in workers}
            for i in range(a.repeats):
                order=list(workers.items())
                for profile,worker in order if i%2==0 else reversed(order):
                    samples[profile].append(worker.ocr(image))
            summary={profile:{key:statistics.median(r["timings_ms"][key] for r in runs)
                              for key in runs[0]["timings_ms"]} for profile,runs in samples.items()}
            row={"frame":str(path),"rgb_sha256":hashlib.sha256(image.tobytes()).hexdigest(),
                 "samples":samples,"median_ms":summary,
                 "speedup":summary["strict"]["total"]/summary["fast_xnnpack"]["total"],
                 "repeat_stable":{k:all(identity(r)==identity(v[0]) for r in v) for k,v in samples.items()},
                 "comparison":compare_lines(samples["strict"][0]["lines"],samples["fast_xnnpack"][0]["lines"])}
            report["runs"].append(row)
            a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps({k:v for k,v in row.items() if k not in ("samples","comparison")}),flush=True)
    finally:
        for worker in workers.values():
            worker.close()


if __name__=="__main__":
    main()
