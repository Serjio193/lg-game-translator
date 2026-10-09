"""Replay one manifest through current production OCR core and both GOCR modes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shlex
import socket
import statistics
import struct
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.frame_transport import HEADER, MAX_REPLY, read_exact
from gocr_worker.image_contract import fingerprint


def replay(sock_path, image, sequence):
    started = time.perf_counter()
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(300)
        connection.connect(sock_path)
        pixels = image.tobytes()
        connection.sendall(HEADER.pack(b"GFR1", 1280, 720, sequence,
                                      int(time.monotonic()*1000), len(pixels))+pixels)
        size = struct.unpack("!I", read_exact(connection, 4))[0]
        if not 0 < size <= MAX_REPLY:
            raise ValueError("invalid selected-frame response length")
        result = json.loads(read_exact(connection, size))
    if result.get("schema") != "gocr.worker.v1" or result.get("frame_sha256") != fingerprint(image):
        raise ValueError("GOCR did not process the stored frame")
    result["selected_frame_rpc_ms"] = (time.perf_counter()-started)*1000
    return result


def compare(crop, full):
    if len(crop["lines"]) != len(full["lines"]):
        return {"equivalent": False, "reason": "line_count"}
    failures = []
    for a, b in zip(crop["lines"], full["lines"]):
        for key in ("line_id", "source_quad", "angle", "detector_confidence", "crop_sha256",
                    "recognizer_input_sha256", "text"):
            if a.get(key) != b.get(key):
                failures.append({"line_id": a["line_id"], "field": key})
    return {"equivalent": not failures, "differences": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--current-command",
                        help="TV baseline command; {frame} and {repeats} are substituted")
    parser.add_argument("--crop-socket", required=True)
    parser.add_argument("--full-socket", required=True)
    parser.add_argument("--crop-command", help="Start just this TV_CROP server for its measurements")
    parser.add_argument("--full-command", help="Start just this TV_FULL server for its measurements")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error("repeats must be 1..20")
    rows = json.loads(args.manifest.read_text())
    report = {"schema": "gocr.benchmark.v1", "execution_host": socket.gethostname(),
              "method": "Same RGB fixtures; one untimed warmup; no capture API/settings modified",
              "frames": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = args.manifest.parent / row["file"]
        with Image.open(path) as original:
            image = original.convert("RGB")
        if image.size != (1280, 720):
            raise ValueError("benchmark requires selected 1280x720 fixtures")
        raw = path.with_suffix(".ppm")
        image.save(raw)
        current = None
        if args.current_command:
            command = shlex.split(args.current_command.format(
                frame=shlex.quote(str(raw)), repeats=args.repeats))
            current = json.loads(subprocess.check_output(command, timeout=300))
            if not current.get("complete"):
                raise RuntimeError("current OCR replay failed")
        frame = {"id": row["id"], "frame_sha256": fingerprint(image),
                 "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if current is not None:
            frame["CURRENT"] = current
        sequence = 0
        for mode, sock in (("TV_CROP", args.crop_socket), ("TV_FULL", args.full_socket)):
            command = args.crop_command if mode == "TV_CROP" else args.full_command
            process = None
            log = None
            try:
                if command:
                    if Path(sock).exists():
                        raise ValueError("benchmark socket must be unused before starting its server")
                    log = args.output.with_name(f"{mode}-{row['id']}.log").open("wb")
                    process = subprocess.Popen(shlex.split(command), stdout=log, stderr=log)
                    deadline = time.monotonic()+30
                    while not Path(sock).exists():
                        if process.poll() is not None or time.monotonic()>deadline:
                            raise RuntimeError("GOCR benchmark server failed to start")
                        time.sleep(.1)
                replay(sock, image, sequence)
                samples = [replay(sock, image, index+1) for index in range(args.repeats)]
            finally:
                if process:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
                    Path(sock).unlink(missing_ok=True)
                if log:
                    log.close()
            if any(sample["mode"] != mode for sample in samples):
                raise ValueError("benchmark socket runs the wrong execution location")
            frame[mode] = samples
        frame["parity"] = compare(frame["TV_CROP"][-1], frame["TV_FULL"][-1])
        frame["mean_ms"] = {
            "TV_CROP": statistics.mean(s["timings_ms"]["end_to_end"] for s in frame["TV_CROP"]),
            "TV_FULL": statistics.mean(s["timings_ms"]["end_to_end"] for s in frame["TV_FULL"])}
        if current is not None:
            frame["mean_ms"]["CURRENT"] = statistics.mean(s["ocr_ms"] for s in current["samples"])
        report["frames"].append(frame)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps({"frame": row["id"], "mean_ms": frame["mean_ms"],
                          "parity": frame["parity"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
