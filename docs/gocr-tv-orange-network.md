# TV → Orange transfer experiment, 2026-10-09

No production changes. Two saved 1280×720 RGB frames: Emergency Guard and Luigi.
TV runs the client, Orange runs a temporary HTTP/1.1 receiver on port 18773,
accepting only TV IP 192.168.1.3. Persistent connection, three warmups and ten
measured requests per frame/format. Response is a small JSON acknowledgement;
no OCR, image decode, translation or OSD is included. Both temporary processes
exited and the receiver closed its port after the test.

## Results

TV ping to Orange, 20 packets: min **1.155**, mean **2.551**, max **3.661 ms**;
zero loss. This is round-trip latency, not a measured one-way delay.

The following are median HTTP upload plus small-response times with
`TCP_NODELAY` enabled on the experiment receiver:

| Payload | Emergency Guard | Luigi |
|---|---:|---:|
| Raw RGB, 2,764,800 bytes | 112.14 ms | 108.04 ms |
| Raw grayscale, 921,600 bytes | 39.10 ms | 38.71 ms |
| PNG, 568,820 / 601,168 bytes | 26.20 ms | 27.06 ms |
| JPEG quality 90, 181,904 / 190,146 bytes | 10.81 ms | 11.17 ms |
| JPEG + base64 JSON, 242,557 / 253,545 bytes | 13.53 ms | 14.08 ms |

TV warmed encoding, measured separately (five repetitions): PNG median
419.53 / 420.88 ms; JPEG median 18.35 / 17.94 ms. JSON/base64 packing measured
once per frame: 4.66 / 4.82 ms. Sum-of-medians encode+transfer estimates:

- PNG: **445.72 / 447.94 ms**.
- JPEG binary: **29.16 / 29.12 ms**.
- JPEG/base64/JSON: **36.54 / 36.85 ms**.

These sums are not a measured whole OCR transaction. Raw byte materialization,
grayscale conversion, Orange image decode and OCR are excluded from the HTTP
numbers. JPEG is lossy and **not admitted for exact STRICT OCR parity**; this
test does not establish that grayscale conversion preserves the input contract.
RGB is the lossless transport measurement with no image codec.

The first receiver run used default TCP settings: JPEG requests took
58–60 ms, raw RGB about 155 ms. Explicit server-side TCP_NODELAY reduced this
overhead by roughly 40–48 ms. This is an experiment receiver finding, **not
proof that the production server has the same setting or delay**. No production
socket settings were changed.

## Evidence

`docs/evidence/gocr-network-20261009/` contains both complete measurements
(`tcp-default.json`, `tcp-nodelay.json`) and the exact client/server scripts.
Scripts executed on real devices; JSON reports include per-format min/max/p95.
The HTTP timing uses the TV monotonic clock throughout, so clock synchronization
between devices is not required.
