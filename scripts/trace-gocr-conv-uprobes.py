"""Bounded private tracefs probes, pinned system offsets; no global trace reset."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SYSTEM = Path("/usr/lib/libtensorflow-lite.so")
SHA = "cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138"
POINTS = {
    # ELF text virtual addresses equal file offsets in this exact library.
    "int8_eval": 0x3892FC,
    "float_eval": 0x38F80C,
    "gemmlowp_neon_run": 0x3233A4,
    "gemmlowp_dispatch": 0x382528,
    "ruy_trmul": 0x523A3C,
}


def definition(path, text):
    # O_APPEND is rejected by this tracefs control; O_TRUNC would clear unrelated
    # probes. Open only O_WRONLY and submit one complete definition.
    descriptor = os.open(path, os.O_WRONLY)
    try:
        encoded = text.encode()
        if os.write(descriptor, encoded) != len(encoded):
            raise OSError("partial uprobe definition")
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or hashlib.sha256(SYSTEM.read_bytes()).hexdigest() != SHA:
        parser.error("command and exact system runtime required")
    root = Path("/sys/kernel/tracing")
    group = f"gocr_conv_{os.getpid()}"
    instance = root / "instances" / group
    args.output.mkdir(parents=True, exist_ok=True)
    added, armed = [], []
    # LG exposes traceoff but not histogram triggers. Stop at the first actual
    # inner NEON entry, then promptly disarm all probes instead of tracing millions
    # of matrix tiles. This is call evidence, not a timing benchmark.
    trigger = "traceoff:1"
    report = {"runtime_sha256": SHA, "offsets": POINTS, "command": command,
              "cleanup_errors": []}
    try:
        instance.mkdir()
        for name, offset in POINTS.items():
            definition(root / "uprobe_events", f"p:{group}/{name} {SYSTEM}:0x{offset:x}\n")
            added.append(name)
            event = instance / "events" / group / name
            armed.append(event)
            if name == "gemmlowp_neon_run":
                definition(event / "trigger", trigger + "\n")
            definition(event / "enable", "1\n")
        completed = subprocess.Popen(command)
        while completed.poll() is None:
            if (instance / "tracing_on").read_text().strip() == "0":
                for event in armed:
                    definition(event / "enable", "0\n")
                report["disarmed_after_first_neon_entry"] = True
                break
            time.sleep(0.01)
        report["command_returncode"] = completed.wait()
        report["trace"] = (instance / "trace").read_text()
        for event in armed:
            definition(event / "enable", "0\n")
    except OSError as error:
        report["trace_error"] = str(error)
        raise
    finally:
        for event in reversed(armed):
            try:
                definition(event / "enable", "0\n")
                if event.name == "gemmlowp_neon_run":
                    definition(event / "trigger", "!traceoff\n")
            except OSError as error:
                report["cleanup_errors"].append(str(error))
        if instance.exists():
            try:
                instance.rmdir()
            except OSError as error:
                report["cleanup_errors"].append(str(error))
        for name in reversed(added):
            try:
                definition(root / "uprobe_events", f"-:{group}/{name}\n")
            except OSError as error:
                report["cleanup_errors"].append(str(error))
        (args.output / "uprobes.json").write_text(json.dumps(report, indent=2))
    if report["cleanup_errors"] or report["command_returncode"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
