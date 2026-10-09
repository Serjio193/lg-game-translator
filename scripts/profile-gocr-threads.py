"""Fresh-process thread matrix; same system TFLite and unchanged OCR parameters."""
import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def snapshot():
    tasks={}
    for path in Path('/proc/self/task').iterdir():
        try:
            raw=(path/'stat').read_text()
            fields=raw[raw.rfind(')')+2:].split()
            status=dict(line.split(':',1) for line in (path/'status').read_text().splitlines() if ':' in line)
            sched=(path/'sched').read_text()
            migrations=next((int(line.split(':')[1]) for line in sched.splitlines()
                             if line.strip().startswith('se.nr_migrations')),None)
            tasks[path.name]={"name":status['Name'].strip(),"state":fields[0],
                "cpu_ticks":int(fields[11])+int(fields[12]),"processor":int(fields[36]),
                "allowed_cpus":status.get('Cpus_allowed_list','').strip(),
                "priority":int(fields[15]),"nice":int(fields[16]),"policy":int(fields[38]),
                "voluntary":int(status.get('voluntary_ctxt_switches','0')),
                "involuntary":int(status.get('nonvoluntary_ctxt_switches','0')),
                "migrations":migrations}
        except (OSError,ValueError):
            continue
    frequencies={str(p):p.read_text().strip() for p in Path('/sys/devices/system/cpu').glob(
        'cpu*/cpufreq/scaling_cur_freq')}
    status=Path('/proc/self/status').read_text()
    return {"tasks":tasks,"thread_count":len(tasks),"frequencies_khz":frequencies,
            "loadavg":Path('/proc/loadavg').read_text().strip(),
            "affinity":sorted(os.sched_getaffinity(0)),
            "system_cpu_ticks":[int(n) for n in Path('/proc/stat').read_text().splitlines()[0].split()[1:]],
            "memory":{line.split(':')[0]:line.split(':')[1].strip() for line in status.splitlines()
                      if line.startswith(('VmRSS:','VmHWM:'))}}


def measure(operation,repeats):
    before=snapshot()
    samples=[]
    last=None
    for _ in range(repeats):
        started=time.perf_counter()
        last=operation()
        samples.append((time.perf_counter()-started)*1000)
    after=snapshot()
    changes={}
    for tid,value in after['tasks'].items():
        original=before['tasks'].get(tid,{})
        changes[tid]={k:value[k]-original.get(k,0) for k in ('cpu_ticks','voluntary','involuntary')}
        changes[tid]['migrations']=None if value['migrations'] is None else value['migrations']-original.get('migrations',0)
    return {"wall_ms":samples,"median_ms":statistics.median(samples),
            "before":before,"after":after,"task_deltas":changes},last


def single(args):
    from PIL import Image
    from gocr_worker.native_detector import NativeDetector
    from gocr_worker.native_recognizer import NativeRecognizer,NativeFull
    from gocr_worker.detector import rectify_crop
    image=Image.open(args.frame).convert('RGB')
    row={"detector_threads":args.detector,"recognizer_threads":args.recognizer,
         "pid":os.getpid(),"startup":snapshot()}
    detector=NativeDetector(args.assets,args.detector,xnnpack=0)
    row['after_detector_create']=snapshot()
    for _ in range(3): detector.detect(image)
    row['detector_alone'],detections=measure(lambda:detector.detect(image),args.repeats)
    row['detector_alone']['last_invoke_ms']=detections['invoke_ms']
    recognizer=NativeRecognizer(args.assets,args.recognizer)
    row['after_recognizer_create']=snapshot()
    for _ in range(2): detector.detect(image)
    row['detector_with_recognizer'],detections=measure(lambda:detector.detect(image),args.repeats)
    row['detector_with_recognizer']['last_invoke_ms']=detections['invoke_ms']
    crops=[rectify_crop(image,item['quad']) for item in detections['lines']]
    def recognize_all():
        return [recognizer.recognize(crop) for crop in crops]
    recognize_all()
    row['recognizer_only'],recognized=measure(recognize_all,args.repeats)
    row['recognizer_only']['last_invoke_ms']=sum(r['invoke_ms'] for r in recognized)
    full=NativeFull(detector,recognizer)
    full.run(image)
    times=[]; signatures=[]
    def run_full():
        lines,stats=full.run(image)
        times.append({"detector_invoke":stats.detector.invoke_ms,"recognizer":stats.recognizer_ms,
                      "rectify":stats.rectify_ms,"total":stats.total_ms})
        signatures.append([(r['line_id'],r['quad'],r['text'],r['crop_sha256'],
                            r['recognizer']['input_windows_sha256']) for r in lines])
        return lines
    row['full'],_=measure(run_full,args.repeats)
    row['full']['stages']=times
    row['identity']=signatures[0]
    row['repeated_identity_equal']=all(s==signatures[0] for s in signatures)
    full.close(); recognizer.close(); detector.close()
    row['after_close']=snapshot()
    args.output.write_text(json.dumps(row,ensure_ascii=False,indent=2))
    print(json.dumps({"pair":[args.detector,args.recognizer],
        "detector_alone_ms":row['detector_alone']['median_ms'],
        "detector_with_recognizer_ms":row['detector_with_recognizer']['median_ms'],
        "recognizer_ms":row['recognizer_only']['median_ms'],"full_ms":row['full']['median_ms'],
        "threads":{k:row[k]['thread_count'] for k in ('startup','after_detector_create','after_recognizer_create','after_close')}}),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--frame',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=5)
    p.add_argument('--detector',type=int)
    p.add_argument('--recognizer',type=int)
    a=p.parse_args()
    if a.detector is not None:
        single(a); return
    a.output.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    for d,r in ((2,2),(4,4),(4,1),(4,2),(3,1),(2,1),(2,2)):
        child=a.output.with_name(a.output.stem+f'-{len(rows)}-{d}-{r}.json')
        subprocess.run([sys.executable,'-B',__file__,'--assets',str(a.assets),'--frame',str(a.frame),
            '--output',str(child),'--repeats',str(a.repeats),'--detector',str(d),'--recognizer',str(r)],check=True)
        rows.append(json.loads(child.read_text()))
        identity=rows[0]['identity']
        report={"scope":"fresh process per pair; XNNPACK off; current clean-room parity",
            "clock_ticks_per_second":os.sysconf('SC_CLK_TCK'),"runs":rows,
            "parity":all(row['identity']==identity and row['repeated_identity_equal'] for row in rows)}
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
