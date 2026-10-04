"""Bounded single-thread benchmarks on saved PicCap frames, with pipeline telemetry."""

import argparse
import datetime
import json
import pathlib
import shlex
import subprocess
import time


def ssh(host, command, **kwargs):
    return subprocess.run(["ssh", host, command], timeout=15, check=True,
                          capture_output=True, text=True, **kwargs).stdout


def telemetry(host):
    output = ssh(host, "luna-send-pub -n 1 luna://org.webosbrew.piccap.service/status '{}'\n"
                      "luna-send-pub -n 1 luna://org.webosbrew.hyperhdr.loader.service/status '{}'\n"
                      "head -n 1 /proc/stat")
    lines = output.splitlines()
    return {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "piccap": json.loads(lines[0]), "hyperhdr": json.loads(lines[1]),
            "cpu_ticks": [int(v) for v in lines[2].split()[1:]]}


def stop_owned_probe(host):
    ssh(host, "pid=$(cat /tmp/lg-text-detector-bench/benchmark.pid)\n"
              "if test -r /proc/$pid/cmdline && "
              "grep -q /tmp/lg-text-detector-bench/lg-text-detector-bench /proc/$pid/cmdline; "
              "then kill $pid; fi")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="root@192.168.1.3")
    parser.add_argument("--image", default="text.ppm")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--backends", nargs="+", choices=("contrast", "ppocr"), default=["contrast", "ppocr"])
    parser.add_argument("--edges", nargs="+", type=int, choices=(320, 640, 960), default=[320, 640, 960])
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--period-ms", type=int, default=1000)
    args = parser.parse_args()
    if pathlib.PurePosixPath(args.image).name != args.image:
        parser.error("Image must be a basename in the remote experiment directory")
    if not 1 <= args.iterations <= 100 or not 0 <= args.period_ms <= 10000:
        parser.error("Iterations/period out of bounds")
    args.output.mkdir(parents=True, exist_ok=True)
    samples = []
    baseline = []
    for _ in range(4):
        sample = telemetry(args.host)
        sample["case"] = "baseline"
        samples.append(sample)
        baseline.append(sample["piccap"]["framerate"])
        time.sleep(1)
    baseline_fps = sum(baseline) / len(baseline)
    initially_active = all(s["piccap"]["videoRunning"] and s["piccap"]["connected"] for s in samples)
    results = []
    for backend in args.backends:
        for edge in args.edges:
            name = f"{backend}-{edge}"
            directory = "/tmp/lg-text-detector-bench"
            command = (f"echo $$ > {directory}/benchmark.pid\n"
                       f"exec /usr/bin/nice -n 15 {directory}/lg-text-detector-bench "
                       f"{backend} {shlex.quote(directory + '/' + args.image)} {edge} "
                       f"{args.iterations} {args.period_ms} {directory}/model")
            # Inner exec writes the actual benchmark PID. Timeout bounds failures/hangs.
            limit = max(35, args.iterations * max(args.period_ms, 1000) // 1000 + 15)
            remote = f"/usr/bin/timeout {limit} /bin/sh -c " + shlex.quote(command)
            # ncnn warnings can exceed a pipe buffer; stream stderr to a file instead.
            with (args.output / f"{name}.stderr.log").open("w") as errors:
                process = subprocess.Popen(["ssh", args.host, remote], text=True,
                                           stdout=subprocess.PIPE, stderr=errors)
                below_limit = 0
                aborted = False
                while process.poll() is None:
                    sample = telemetry(args.host)
                    sample["case"] = name
                    samples.append(sample)
                    source = sample["piccap"]
                    lost = initially_active and not (source["videoRunning"] and source["connected"])
                    below_limit = below_limit + 1 if source["framerate"] < baseline_fps * 0.80 else 0
                    if lost or not sample["hyperhdr"]["running"] or (initially_active and below_limit >= 2):
                        stop_owned_probe(args.host)
                        aborted = True
                        break
                    time.sleep(1)
                stdout, _ = process.communicate(timeout=40)
            if process.returncode != 0 or aborted:
                result = {"backend": backend, "max_edge": edge, "aborted": aborted,
                          "exit_code": process.returncode}
            else:
                result = json.loads(stdout)
                result["four_core_cpu_percent"] = result["one_core_cpu_percent"] / 4
            selected = [s for s in samples if s["case"] == name]
            result["piccap_fps_samples"] = [s["piccap"]["framerate"] for s in selected]
            result["hyperhdr_pids"] = sorted({s["hyperhdr"]["pid"] for s in selected})
            results.append(result)
            (args.output / "results.json").write_text(json.dumps({
                "baseline_fps": baseline_fps, "initially_active": initially_active,
                "image": args.image, "results": results}, indent=2) + "\n")
            (args.output / "telemetry.jsonl").write_text("".join(json.dumps(s) + "\n" for s in samples))
            print(json.dumps(result), flush=True)
            if aborted:
                return


if __name__ == "__main__":
    main()
