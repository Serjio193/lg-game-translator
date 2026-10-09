"""Three persistent native OCR profiles; diagnostics excluded from latency."""
import argparse
import hashlib
import itertools
import json
import os
import statistics
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.worker_full import FullGocrWorker
from gocr_worker.runner_diagnostics import snapshot, tensor_hashes, tensor_differences
from gocr_worker.native_postprocess import NativePostprocess
from gocr_worker.profile_comparison import compare_lines

PROFILES=("strict","fast_xnnpack","google_runner_experimental")


def identity(result):
    keys=("text","source_quad","crop_sha256","recognizer_input_sha256")
    return [[line[k] for k in keys] for line in result["lines"]]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--assets",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--repeats",type=int,default=5)
    parser.add_argument("frames",nargs="+",type=Path)
    a=parser.parse_args()
    if a.repeats<5:
        parser.error("at least five timed runs required")
    report={"reference_is_ground_truth":False,"scope":"saved RGB frame to UTF-8, no translation/OSD",
            "warmups_per_frame_profile":1,"repeats":a.repeats,"runs":[]}
    workers={}
    orders=list(itertools.permutations(PROFILES))
    try:
        for name in PROFILES:
            os.environ.update(GOCR_PROFILE=name,GOCR_DETECTOR="native",GOCR_RECOGNIZER="native")
            workers[name]=FullGocrWorker(a.assets,detector_threads=4 if name==PROFILES[2] else 2,
                                         recognizer_threads=2)
            if workers[name].native_full is None:
                raise RuntimeError("all profiles must use native full OCR")
        post=NativePostprocess()
        report["asset_status"]=workers[PROFILES[0]].asset_status
        report["google_contract"]=workers[PROFILES[2]].runner_contract
        for frame_index,path in enumerate(a.frames):
            image=Image.open(path).convert("RGB")
            if image.size!=(1280,720):
                raise ValueError(f"not selected RGB1280x720: {path}")
            for name in orders[frame_index%6]:
                workers[name].ocr(image)
            samples={name:[] for name in PROFILES}
            measured_orders=[]
            for i in range(a.repeats):
                order=orders[(frame_index+i)%6]
                measured_orders.append(order)
                for name in order:
                    result=workers[name].ocr(image)
                    result["raw_tensor_hashes"]=tensor_hashes(workers[name].detector.native)
                    samples[name].append(result)
            diagnostics={name:snapshot(workers[name].detector.native,a.assets,post) for name in PROFILES}
            pairs={}
            for before in PROFILES[:2]:
                key=f"{before}_vs_google_runner_experimental"
                pairs[key]={"lines":compare_lines(samples[before][-1]["lines"],samples[PROFILES[2]][-1]["lines"]),
                            "outputs":tensor_differences(workers[before].detector.native,workers[PROFILES[2]].detector.native),
                            "inputs_equal":diagnostics[before]["tensors"]["input"]==diagnostics[PROFILES[2]]["tensors"]["input"]}
            medians={name:{key:statistics.median(r["timings_ms"][key] for r in runs)
                           for key in runs[0]["timings_ms"]} for name,runs in samples.items()}
            row={"frame":str(path),"rgb_sha256":hashlib.sha256(image.tobytes()).hexdigest(),
                 "orders":measured_orders,"median_ms":medians,"samples":samples,
                 "diagnostics":diagnostics,"comparisons":pairs,
                 "repeat_stable":{name:all(identity(r)==identity(runs[0]) and
                     r["raw_tensor_hashes"]==runs[0]["raw_tensor_hashes"] for r in runs)
                     for name,runs in samples.items()}}
            report["runs"].append(row)
            a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps({"frame":str(path),"median_ms":medians,"stable":row["repeat_stable"]}),flush=True)
    finally:
        for worker in workers.values():
            worker.close()


if __name__=="__main__":
    main()
