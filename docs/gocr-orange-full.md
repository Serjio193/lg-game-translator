# ORANGE_FULL: experimental lossless full-frame relay

This explicitly selected mode sends the existing 1280×720 RGB PicCap frame to
Orange for detector, rectification and recognizer. It does not change capture,
HyperHDR, OCR parameters, translator models/cache or OSD.

```text
TV selected RGB frame → existing local GFR1 socket
  → FramePipeline ORANGE_FULL → authenticated persistent HTTP GFR1 body
  → Orange Image.frombytes RGB → Google detector → native postprocess
  → rectification → Google recognizer → UTF-8 text + source quads + frame SHA
  → TV validates frame identity → existing translation client/result consumer
```

The RGB body is lossless, 2,764,800 bytes plus the existing 28-byte frame header.
No PNG/JPEG/base64 codec or full-frame return trip. Only text, coordinates,
hashes and diagnostics return. TV loads no detector/recognizer model instances
in this mode. Translation uses the existing API and behavior; stabilization,
classification, cache and OSD are not relocated by this change.

## Quality boundary

This is **experimental**, not equivalent to TV system STRICT. The measured
Orange LiteRT CPU path differs on some text/regions even without XNNPACK.
See `gocr-orange-cpu-experiment.md`. Exact transport preserves the frame, but
does not remove those cross-runtime differences. Production is not selected
automatically, and original Google assets/configuration are unchanged.

Orange uses persistent D4/R2 interpreters and native postprocess, with LiteRT
default delegates explicitly disabled. `GOCR_LITERT_DELEGATES=off` applies only
when the LiteRT Python interpreter is present; TV C API behavior is unchanged.
No models or interpreters are loaded per request/crop. The existing worker lock
serializes OCR requests. HTTP connections are reused with TCP_NODELAY.

## Explicit launch

Build the existing postprocess for Orange ARM64:

```sh
cmake -S native/gocr_postprocess -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
export GOCR_POSTPROCESS_LIBRARY="$PWD/build/libgocr_postprocess.so"
python -m gocr_worker.orange_server --assets /home/orangepi/gocr-runtime/assets \
  --bind 192.168.1.11 --port 8772 --token-file /private/transport.token
```

LAN binding requires an existing shared token file (≥32 ASCII characters).
Keep it mode 0600; do not put it in Git, command arguments, logs or URLs.
Original Google assets are validated using the existing canonical hashes.
Missing native postprocess is an error rather than a silent slow fallback.

TV relay (normal translation API address must match the existing installation):

```sh
python3 -m gocr_worker.tv_server --assets /media/developer/gocr-runtime/assets \
  --mode ORANGE_FULL --frame-worker http://192.168.1.11:8772 \
  --token-file /private/transport.token --translator http://192.168.1.11:8765 \
  --socket /tmp/gocr-frame.sock
```

For OCR-only replay, use `gocr_worker.benchmark_server` with the same mode,
frame-worker/token/socket arguments. No translation latency is then measured.
Remote thread counts are selected on Orange, not with TV `--threads`.

The PicCap consumer hook accepts `ORANGE_FULL` in its mode file only after the
updated `native/gocr_frame_transport.c` has been copied by
`scripts/install-gocr-frame-hook.py` and the existing PicCap build deployed.
The installer also refreshes transport files for an already installed hook;
it does not change the existing frame producer. Do not set the production mode
file before the corresponding socket server is running and verified.

## Verification and telemetry

- Authenticated endpoint: `POST /v1/ocr-frame`, Content-Type
  `application/x-gocr-frame`, exact existing GFR1 header + RGB bytes.
- Invalid dimensions/body length, transfer encodings, unauthorized requests and
  frame identity changes are rejected. Errors reset the client connection.
- Response retains the existing `gocr.worker.v1` format and source coordinates.
- `frame_decode`, `orange_request`, `frame_encode`, `frame_rpc`,
  `frame_network`, `frame_to_text` separate costs; network is an estimate from
  RPC minus server work, not a synchronized one-way measurement.
- `scripts/validate-orange-frame-relay.py` compares relay outputs with a saved
  same-Orange reference. It does not claim parity with TV STRICT.
- Six regression tests exercise byte-identical RGB, sequence/time/hash,
  repeated persistent requests, authentication, invalid bodies, remote thread
  ownership, changed identity and no TV model initialization.
  Refreshing an existing hook also verifies producer/build files stay unchanged.

No capture API/settings, production defaults or OSD were changed by this module.
