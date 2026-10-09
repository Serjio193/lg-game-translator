# LZ4 lossless frame transport — 2026-10-09

## Implementation and provenance

Native library sources downloaded unchanged from https://github.com/lz4/lz4/tree/v1.10.0/lib (lz4.c/lz4.h/lib/LICENSE). Only the BSD library, not CLI, was built. TV ARMv7 flags: -shared -fPIC -O3 -mcpu=cortex-a9 -mfloat-abi=softfp -mfpu=neon. Orange uses existing liblz4.so.1 version 1.10.0. No system package installed. Sources/builds under ignored build/lz4-source; third-party source is not human-maintained project code.

SHA256:
- lz4.c 9396f7de527bc8435de9c7569fb7998e56545a84b4f3c2d808c0235c01774539
- lz4.h 26b82efc53d1570f3b54eef02e9c4764c1ad374ff03cac04e2ced5ea4d4c552f
- TV shared library 1f3099238df96f80072f579c972f993f49b9cc6727c7850b6313c37b05aecb58

TV default relay now explicitly enables PP_OCR_FRAME_COMPRESSION=lz4 and PP_OCR_LZ4_LIBRARY=/media/developer/gocr-runtime/liblz4-tv.so. Library is a persistent startup dependency. Lz4Block uses reusable native state/buffers, acceleration=1, validates exact input and decoded length. HTTP Content-Encoding=lz4-block compresses complete original GFR1 header+RGB payload. Orange validates authentication, encoding, bounded input length, decompression length and original frame contract before OCR. Normal fingerprint/sequence/coordinate checks still run. If compression is not smaller, client sends original identity block. Without explicit env setting transport stays raw. Unknown encodings rejected. Per-connection decoder buffers avoid shared-thread mutation.

Malformed decompression regression exposed old error-handler drain-after-consumption blocking; reject now tracks whether body has already been consumed, so an invalid compressed body returns 400 immediately. Authentication and limits not weakened.

## Isolated alternating transport test

Actual TV → Orange LAN, persistent HTTP/TCP_NODELAY, one warmup and ten samples for each mode/frame, alternating order. 90 measured transfers; every SHA256 of complete decoded original packet matched. Source GFR1/RGB materialized before timing. Results include TV compression, upload, Orange decompression/hash and acknowledgement. No OCR/translation/OSD. Small receiver is temporary, authenticated, port 18777, stopped after test.

| Frame | Raw total | LZ4 acceleration 1 total | LZ4 acceleration 4 total | LZ4-1 bytes |
|---|---:|---:|---:|---:|
| Fresh Emergency | 112.67 ms | 63.36 ms | 61.95 ms | 911705 |
| Saved Emergency | 111.78 ms | 61.64 ms | 62.47 ms | 902854 |
| Luigi | 111.04 ms | 60.82 ms | 64.12 ms | 939550 |

Original bytes 2,764,828. Acceleration=1 chose stable ~13.0–13.7 ms compression and ~5.0–5.3 ms decompression including output copy in this receiver. Acceleration=4 did not consistently beat it. Reduction ~49–50 ms / 44–45% in measured whole transport transaction. This is not a 45% complete OCR speedup.

## Full pipeline validation

Raw vs LZ4 requests to actual PP-OCR endpoint on all three saved frames: exact pixels/fingerprint, returned regions, source quads, recognition text, confidence/policy and appearance dictionaries. Timing fields excluded from equality. Actual payloads differ by 7 bytes from transfer-probe size due to sequence/header values. Original numerical OCR path unchanged.

Ten live LZ4 frames had 19–20 regions (previous live raw series had 16–17, so whole OCR latency is not directly comparable):
- network-overhead median 58.57 ms, range 54.58–76.35 ms (raw previous median 128.39 ms);
- TV compression median 13.39 ms;
- Orange decompression median 2.62 ms;
- selected-frame → detector upper estimate median 265.67 ms, range 253.43–415.86 ms;
- capture-to-relay median 28.37 ms;
- detector median 114.77 ms;
- frame-to-text median 2223.33 ms; includes more crop recognition work than previous frame;
- capture status ~59.67 FPS.

Do not attribute all detector endpoint before/after difference solely to LZ4: images/regions/CPU timings differed. Isolated saved-frame transport test is the reliable compression comparison.

## Verification

Host and real-TV native codec validator: six round trips (constant/repeating/incompressible bytes, two accelerations), six invalid size/block checks. Integration test uses a deterministic codec stand-in to verify authenticated transport and exact pixels/sequence/identity, invalid decoded-length rejection. Six existing full-frame and six GOCR integration tests pass; Python syntax and diff checks pass. Orange unit active, translation health OK. No physical TV reboot tested. Rollback: PP_OCR_FRAME_COMPRESSION=raw in TV launch script, restart relay; Orange still accepts raw. Retain native library/transport-token permissions.

Raw reports: transfer.json, live.json, ocr-parity.json.
