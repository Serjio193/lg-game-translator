import base64
import http.client
import io
import json
import math
import statistics
import time
from pathlib import Path
from PIL import Image


def summary(samples):
    return {"median_ms": statistics.median(samples), "min_ms": min(samples),
            "max_ms": max(samples), "p95_ms": sorted(samples)[math.ceil(.95*len(samples))-1]}


connection = http.client.HTTPConnection("192.168.1.11", 18773, timeout=15)
report = {"scope": "TV encode and HTTP upload+small response; no OCR", "frames": []}
try:
    for name in ("11-gocr-native-postprocess-20261009-emergency-guard.ppm",
                 "12-gocr-native-postprocess-20261009-luigi.ppm"):
        image = Image.open(Path("/media/developer/gocr-runtime/fast-corpus")/name).convert("RGB")
        variants = [("raw_rgb", image.tobytes(), None),
                    ("raw_gray", image.convert("L").tobytes(), None)]
        row = {"frame": name, "size": image.size, "encoding": {}, "transfers": []}
        for label, fmt, options in (("png", "PNG", {}), ("jpeg_q90", "JPEG", {"quality": 90})):
            durations = []
            for iteration in range(6):
                start = time.perf_counter()
                stream = io.BytesIO()
                image.save(stream, format=fmt, **options)
                payload = stream.getvalue()
                duration = (time.perf_counter()-start)*1000
                if iteration:
                    durations.append(duration)
            row["encoding"][label] = summary(durations)
            variants.append((label, payload, label))
            if fmt == "JPEG":
                start = time.perf_counter()
                packed = json.dumps({"image_b64": base64.b64encode(payload).decode("ascii")}).encode()
                row["jpeg_json_pack_ms"] = (time.perf_counter()-start)*1000
                variants.append(("jpeg_q90_base64_json", packed, label))
        for label, payload, encoder in variants:
            durations = []
            for iteration in range(13):
                start = time.perf_counter()
                connection.request("POST", "/measure", body=payload,
                                   headers={"Content-Type": "application/octet-stream"})
                response = connection.getresponse()
                reply = json.loads(response.read())
                elapsed = (time.perf_counter()-start)*1000
                if response.status != 200 or reply["received"] != len(payload):
                    raise RuntimeError("incomplete transfer")
                if iteration >= 3:
                    durations.append(elapsed)
            item = {"format": label, "bytes": len(payload), "warmups": 3, "repeats": 10,
                    "http_upload_and_response": summary(durations)}
            if encoder:
                item["encode_plus_http_median_ms"] = (
                    row["encoding"][encoder]["median_ms"]+statistics.median(durations)
                    +(row["jpeg_json_pack_ms"] if label.endswith("json") else 0))
            row["transfers"].append(item)
        report["frames"].append(row)
        print(json.dumps(row), flush=True)
    Path("/tmp/gocr-network-20261009.json").write_text(json.dumps(report, indent=2))
finally:
    connection.request("POST", "/stop", body=b"")
    connection.getresponse().read()
    connection.close()
