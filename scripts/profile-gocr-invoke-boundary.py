"""Compare cached-input Invoke vs per-frame prepare, before/after recognizer load."""
import argparse
import ctypes as C
import json
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.native_detector import NativeDetector
from gocr_worker.native_recognizer import NativeRecognizer
from importlib.util import module_from_spec,spec_from_file_location


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--frame',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--threads',type=int,default=4)
    a=p.parse_args()
    spec=spec_from_file_location('thread_profile',Path(__file__).with_name('profile-gocr-threads.py'))
    profiler=module_from_spec(spec); spec.loader.exec_module(profiler)
    image=Image.open(a.frame).convert('RGB')
    detector=NativeDetector(a.assets,a.threads,xnnpack=0)
    detector.detect(image)
    def invoke():
        if detector.lib.gocr_detector_invoke(detector.context):
            raise RuntimeError('Invoke failed')
    def prepared():
        pixels=image.tobytes()
        if detector.lib.gocr_detector_prepare(detector.context,pixels,len(pixels)):
            raise RuntimeError('prepare failed')
        invoke()
    report={'threads':a.threads,'phases':[]}
    for loaded in (False,True):
        rec=NativeRecognizer(a.assets,2) if loaded else None
        row={'recognizer_loaded':loaded}
        for name,operation in (('invoke_only',invoke),('prepare_invoke',prepared)):
            for _ in range(3): operation()
            row[name],_=profiler.measure(operation,10)
        detector.lib.gocr_detector_finish(detector.context,detector.output,len(detector.output),C.byref(detector.stats))
        row['last_detector_stats']={'invoke_ms':detector.stats.invoke_ms,'prepare_ms':detector.stats.prepare_ms}
        report['phases'].append(row)
        a.output.write_text(json.dumps(report,indent=2))
        print(json.dumps({'loaded':loaded,'threads':a.threads,
            'invoke_only':row['invoke_only']['median_ms'],
            'prepare_invoke':row['prepare_invoke']['median_ms']}),flush=True)
        if rec: rec.close()
    detector.close()


if __name__=='__main__': main()
