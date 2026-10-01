# Codex handoff

## Project goal

Build a real-time game translator for a rooted LG OLED65G51LW (G5, webOS 25).

Do not start with OCR. Milestone 1 is capture characterization.

## Current priority

1. Cross-compile the native probe for ARM webOS.
2. Package/install it on the rooted TV.
3. Identify the working private capture backend/library on this exact G5.
4. Implement actual frame capture.
5. Benchmark maximum resolution and sustained FPS.
6. Step resolution down when FPS/latency is poor and record the matrix.
7. Implement arbitrary ROI/source-region capture.

## Important constraints

- Measurements from the real G5 override assumptions from older LG models.
- Do not claim 1080p support until measured.
- Preserve upstream licenses/attribution for any reused code.
- Prefer a small native daemon/probe over importing an entire Ambilight stack.
- Keep commits small and document commands/results in `docs/`.

## Upstream research targets

- https://github.com/adeze/lg-hue-sync
- https://github.com/poiedk/lg-hue-sync
- https://github.com/webosbrew/hyperion-webos
- https://github.com/TBSniller/piccap

Inspect the capture implementation and private LG symbol loading in these projects before inventing API signatures.

## Expected benchmark output

For every tested mode record requested/actual dimensions, pixel format, stride, frame bytes, average FPS, frame-time range, failures/drops and capture latency.

## Definition of done for Milestone 1

See `docs/g5-capture-tests.md`.
