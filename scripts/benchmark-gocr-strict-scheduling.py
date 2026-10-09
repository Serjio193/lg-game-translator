"""Fresh child per candidate; system STRICT 2/2 only; no persistent setting changes."""
import argparse
import ctypes as C
import gzip
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.scheduler_observation import tasks, environment, topology, system_load, delta
from gocr_worker.scheduler_experiment import Placement, VARIANTS

SYSTEM = "/usr/lib/libtensorflow-lite.so"


def accepted(report, expected_frames):
    return (expected_frames > 0 and len(report["frames"]) == expected_frames
            and all(row["parity"] for row in report["frames"])
            and not report["restore_errors"] and report["persistent_tid_set"])


def semantic(rows):
    return [{**{k: v for k, v in row.items() if k != "recognizer"},
             "recognizer": {k: v for k, v in row["recognizer"].items()
                            if k not in ("invoke_ms", "total_ms", "stages_ms")}} for row in rows]


def summary(samples):
    ordered = sorted(samples)
    return {"samples_ms": samples, "median_ms": statistics.median(samples),
            "p95_ms": ordered[math.ceil(len(ordered) * .95) - 1]}


def observe(args):
    cpu_start = time.process_time()
    with gzip.open(args.output, "wt", encoding="utf-8") as file:
        while not args.stop.exists() and Path(f"/proc/{args.observe}").exists():
            row = {"monotonic": time.monotonic(), "tasks": tasks(args.observe), "environment": environment()}
            file.write(json.dumps(row) + "\n")
            file.flush()
            time.sleep(args.interval)
        file.write(json.dumps({"observer_cpu_seconds": time.process_time() - cpu_start}) + "\n")


def single(args):
    from PIL import Image
    from gocr_worker.native_detector import NativeDetector
    from gocr_worker.native_recognizer import NativeRecognizer, NativeFull
    from gocr_worker.native_postprocess import NativePostprocess
    from gocr_worker.runner_diagnostics import tensor_hashes, snapshot
    os.environ.update(GOCR_PROFILE="strict", GOCR_TFLITE_C_LIBRARY=SYSTEM,
                      GOCR_DETECTOR_TFLITE_LIBRARY=SYSTEM)
    os.environ.pop("GOCR_DETECTOR_PROFILE", None)
    report = {"pid": os.getpid(), "variant": args.variant, "runtime": SYSTEM,
              "runtime_sha256": hashlib.sha256(Path(SYSTEM).read_bytes()).hexdigest(),
              "detector_threads": 2, "recognizer_threads": 2, "xnnpack": False,
              "warmups_per_condition_mode_frame": 1, "repeats": args.repeats,
              "fixed_placement_diagnostic": args.fixed_placement, "observer_enabled": not args.no_observer,
              "phases": {"imports": tasks(os.getpid())}, "frames": []}
    images = [(path, Image.open(path).convert("RGB")) for path in args.frames]
    if any(image.size != (1280, 720) for _, image in images):
        raise ValueError("selected frame contract changed")
    detector = NativeDetector(args.assets, threads=2, runtime=SYSTEM, xnnpack=False)
    report["phases"]["detector_create"] = tasks(os.getpid())
    detector.detect(images[0][1])
    report["phases"]["detector_first_invoke"] = tasks(os.getpid())
    detector_tids = set(report["phases"]["detector_first_invoke"]) - set(report["phases"]["imports"])
    recognizer = NativeRecognizer(args.assets, threads=2)
    report["phases"]["recognizer_create"] = tasks(os.getpid())
    full = NativeFull(detector, recognizer)
    full.run(images[0][1])
    report["phases"]["full_first_invoke"] = tasks(os.getpid())
    worker_tids = set(report["phases"]["full_first_invoke"]) - set(report["phases"]["imports"])
    report["roles"] = {"main": os.getpid(), "detector_owned": sorted(detector_tids),
                       "recognizer_new": sorted(worker_tids - detector_tids),
                       "import_background": sorted(set(report["phases"]["imports"]) - {os.getpid()})}
    placement = Placement(detector_tids, worker_tids)
    trace = args.output.with_suffix(".trace.jsonl.gz")
    stop = args.output.with_suffix(".stop")
    stop.unlink(missing_ok=True)
    observer = None if args.no_observer else subprocess.Popen([sys.executable, "-B", __file__, "--observe", str(os.getpid()),
                                 "--stop", str(stop), "--output", str(trace), "--interval", str(args.interval)])
    post = NativePostprocess()
    def configure(name):
        if args.variant != "baseline":
            placement.apply(name)
    try:
        if args.duration_seconds:
            from gocr_worker.scheduler_series import run_series
            run_series(args, images, detector, full, post, placement, report, semantic, summary)
        else:
            for frame_index, (path, image) in enumerate(images):
                configure("baseline")
                reference_rows, _ = full.run(image)
                reference = tensor_hashes(detector)
                reference_diagnostics = snapshot(detector, args.assets, post)
                row = {"frame": str(path), "reference_tensors": reference,
                       "reference_lines": reference_rows, "reference_diagnostics": reference_diagnostics,
                       "modes": {}, "events": [], "parity": True}
                for mode in args.modes.split(","):
                    conditions = [args.variant] if args.fixed_placement else ["baseline", args.variant]
                    values = {name: [] for name in conditions}
                    telemetry = {name: [] for name in values}
                    for name in values:
                        configure(name)
                        full.run(image) if mode == "full" else detector.detect(image)
                    for repeat in range(args.repeats):
                        order = list(values)
                        if (frame_index + repeat) % 2:
                            order.reverse()
                        for name in order:
                            configure(name)
                            before = tasks(os.getpid())
                            started = time.monotonic()
                            if mode == "invoke":
                                if detector.lib.gocr_detector_invoke(detector.context):
                                    raise RuntimeError("strict Invoke failed")
                                ms = (time.monotonic() - started) * 1000
                                lines = None
                            else:
                                lines, stats = full.run(image)
                                ms = stats.total_ms
                            ended = time.monotonic()
                            after = tasks(os.getpid())
                            observed = tensor_hashes(detector)
                            tensor_equal = observed == reference
                            line_equal = lines is None or semantic(lines) == semantic(reference_rows)
                            row["parity"] &= tensor_equal and line_equal
                            values[name].append(ms)
                            telemetry[name].append({"before": before, "after": after, "delta": delta(before, after),
                                                    "environment": environment(), "tensors": observed,
                                                    "tensor_equal": tensor_equal, "semantic_lines_equal": line_equal,
                                                    "detector_invoke_ms": None if mode == "invoke" else stats.detector.invoke_ms,
                                                    "postprocess_exact": snapshot(detector, args.assets, post) == reference_diagnostics if mode == "full" else None})
                            if mode == "full":
                                row["parity"] &= telemetry[name][-1]["postprocess_exact"]
                            row["events"].append({"mode": mode, "variant": name, "repeat": repeat,
                                                  "start": started, "end": ended})
                    if mode == "invoke":
                        if detector.lib.gocr_detector_finish(detector.context, detector.output, len(detector.output), C.byref(detector.stats)) < 0:
                            raise RuntimeError("strict detector finish failed")
                    diagnostics = snapshot(detector, args.assets, post)
                    row["parity"] &= diagnostics == reference_diagnostics
                    row["modes"][mode] = {"timing": {name: summary(samples) for name, samples in values.items()},
                                          "telemetry": telemetry, "final_diagnostics_equal": diagnostics == reference_diagnostics}
                row["final_lines"] = lines
                row["final_diagnostics"] = diagnostics
                report["frames"].append(row)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({"variant": args.variant, "frame": str(path), "parity": row["parity"],
                                  "timings": {m: v["timing"] for m, v in row["modes"].items()}}), flush=True)
    except OSError as exc:
        report["unsupported"] = repr(exc)
        raise
    finally:
        report["restored_tasks"] = tasks(os.getpid()) if args.variant == "baseline" else placement.restore()
        report["restore_errors"] = placement.restore_errors
        report["persistent_tid_set"] = set(tasks(os.getpid())) == set(placement.original)
        stop.touch()
        if observer is not None:
            observer.wait(timeout=10)
        stop.unlink(missing_ok=True)
        report["trace"] = str(trace) if observer is not None else None
        full.close()
        recognizer.close()
        detector.close()
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return accepted(report, len(images))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS)
    parser.add_argument("--variants", help="comma-separated variants")
    parser.add_argument("--modes", default="invoke,full", choices=("invoke", "full", "invoke,full"))
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--duration-seconds", type=float, default=0)
    parser.add_argument("--observe", type=int)
    parser.add_argument("--stop", type=Path)
    parser.add_argument("--interval", type=float, default=.05)
    parser.add_argument("--topology", action="store_true")
    parser.add_argument("--fixed-placement", action="store_true", help="persistent-mask diagnostic; no latency A/B claim")
    parser.add_argument("--no-observer", action="store_true", help="validate latency without polling overhead")
    parser.add_argument("frames", nargs="*", type=Path)
    args = parser.parse_args()
    if not math.isfinite(args.duration_seconds) or args.duration_seconds < 0:
        parser.error("duration must be finite and nonnegative")
    if args.duration_seconds and not args.variant:
        parser.error("duration is supported only by a single persistent nice_-5 series")
    if args.observe:
        observe(args)
    elif args.topology:
        args.output.write_text(json.dumps({"topology": topology(), "system_load": system_load()}, indent=2))
    elif args.variant:
        if not args.assets or not args.frames or args.repeats < 10:
            parser.error("assets, frames and ten repeats required")
        if args.duration_seconds and (args.variant != "nice_-5" or args.modes != "full"
                                      or args.fixed_placement or not args.no_observer
                                      or args.duration_seconds < 0):
            parser.error("duration series requires nice_-5, full, no-observer and positive duration")
        if not single(args):
            raise SystemExit(2)
    else:
        if not args.variants:
            parser.error("variants required")
        if not args.assets or not args.frames or args.repeats < 10:
            parser.error("assets, frames and ten repeats required")
        if any(v not in VARIANTS for v in args.variants.split(",")):
            parser.error("unsupported matrix variant")
        args.output.mkdir(parents=True, exist_ok=True)
        failures = []
        for variant in args.variants.split(","):
            command = [sys.executable, "-B", __file__, "--assets", str(args.assets),
                            "--output", str(args.output / (variant + ".json")), "--variant", variant,
                            "--repeats", str(args.repeats), "--interval", str(args.interval), "--modes", args.modes,
                            *map(str, args.frames)]
            if args.no_observer:
                command.append("--no-observer")
            if args.fixed_placement:
                command.append("--fixed-placement")
            completed = subprocess.run(command, check=False)
            if completed.returncode:
                failures.append({"variant": variant, "returncode": completed.returncode})
        (args.output / "matrix-exit-status.json").write_text(json.dumps(failures, indent=2))
        if failures:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
