"""One resident Bergamot process; preliminary results never enter SQLite."""
import atexit
import json
import os
from pathlib import Path
import selectors
import subprocess
import threading
import time

_lock = threading.Lock()
_process = None


def close():
    global _process
    if _process is not None:
        _process.terminate()
        try:
            _process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _process.kill()
            _process.wait()
        _process.stdin.close()
        _process.stdout.close()
        _process = None


def translate(text):
    global _process
    with _lock:
        started = time.perf_counter()
        if _process is None or _process.poll() is not None:
            close()
            executable = os.environ.get("BERGAMOT_WORKER", str(Path(__file__).with_name("bergamot-worker")))
            config = os.environ.get("BERGAMOT_CONFIG",
                "/home/orangepi/translator-test/bergamot-model/config.yml")
            _process = subprocess.Popen([executable, "--model-config-paths", config,
                "--cpu-threads", "1", "--cache-size", "0", "--log-level", "off"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                bufsize=0)
        try:
            _process.stdin.write((" ".join(text.split()) + "\n").encode("utf-8"))
            _process.stdin.flush()
            line = bytearray()
            deadline = time.monotonic() + 30
            with selectors.DefaultSelector() as selector:
                selector.register(_process.stdout, selectors.EVENT_READ)
                while not line.endswith(b"\n"):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(timeout=remaining):
                        raise TimeoutError("Bergamot response timeout")
                    chunk = os.read(_process.stdout.fileno(), 4096)
                    if not chunk or len(line) + len(chunk) > 65536:
                        raise RuntimeError("Invalid Bergamot response framing")
                    line.extend(chunk)
            result = json.loads(line)
            if result.get("provider") != "bergamot" or not result.get("translation", "").strip():
                raise RuntimeError("Invalid Bergamot result")
            result["request_ms"] = round((time.perf_counter() - started) * 1000, 1)
            return result
        except Exception:
            close()
            raise


atexit.register(close)
