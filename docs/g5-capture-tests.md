# Milestone 1 — LG G5 capture benchmark

Target: **LG OLED65G51LW / webOS 25**.

The first milestone contains no OCR, translation or TTS. Its only job is to characterize capture on the real TV.

## Required sequence

1. **Build** — produce a native binary that runs on the rooted G5.
2. **Run** — start capture reliably on the TV and identify the working backend.
3. **Maximum resolution** — determine the largest frame the backend can actually return. Do not assume 1080p.
4. **Maximum FPS** — at the maximum working resolution, measure sustained capture FPS and latency.
5. **Resolution fallback** — if FPS is too low, step resolution down and repeat the benchmark.
6. **Find the optimum** — choose practical resolution/FPS points for:
   - whole-screen text detection;
   - higher-quality OCR input.
7. **Region scanning (ROI)** — capture arbitrary screen regions and determine whether ROI can be changed while capture remains active.

## Benchmark rules

Each candidate mode should run long enough to expose stalls rather than reporting a single-frame peak.

Record:

- requested width/height;
- actual width/height;
- pixel format and stride;
- average FPS;
- minimum/maximum frame time;
- dropped/failed frames;
- CPU and memory observations where available;
- whether HDMI/game content is captured correctly.

Initial candidate matrix:

| Requested | Actual | Avg FPS | Frame time | Failures | Result |
|---|---|---:|---:|---:|---|
| 320x240 | TBD | TBD | TBD | TBD | TBD |
| 640x360 | TBD | TBD | TBD | TBD | TBD |
| 960x540 | TBD | TBD | TBD | TBD | TBD |
| 1280x720 | TBD | TBD | TBD | TBD | TBD |
| 1600x900 | TBD | TBD | TBD | TBD | TBD |
| 1920x1080 | TBD | TBD | TBD | TBD | TBD |

If the backend supports larger modes, continue upward until the real limit is found.

## Optimization target

There may be two optimal modes rather than one:

```text
whole screen -> lower resolution / higher FPS -> locate text
                                         |
                                         v
                              coordinates of text
                                         |
                                         v
ROI/crop -> highest useful detail -> later OCR
```

This is especially important for short dialogue appearing above characters rather than in a fixed subtitle area.

## ROI tests

Test at least:

- full screen;
- bottom 25%;
- center 50%;
- small arbitrary rectangle;
- moving the rectangle between frames without recreating the capture pipeline.

For each ROI, record whether cropping occurs **before** or **after** scaling. Pre-scale source-region capture is strongly preferred because it preserves text detail.

## Milestone 1 exit criteria

Milestone 1 is complete only when we have measured on the G5:

- a working native capture backend;
- real maximum capture resolution;
- sustained FPS at that resolution;
- resolution/FPS benchmark data;
- at least one practical operating point;
- arbitrary ROI capture, or a documented reason the backend cannot provide it.

Only then move to text detection/OCR.
