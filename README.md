# LG Game Translator

Real-time game text capture, translation and voice-over for **rooted LG webOS TVs**.

Initial hardware target: **LG OLED65G51LW (G5 / webOS 25)**.

## Milestone 0 — prove capture first

Before OCR, translation or TTS, we need measurements from the real TV. The capture probe will:

- discover LG video-capture libraries/backends available on the TV;
- record library paths and basic platform information;
- test requested output sizes: 320x240, 640x360, 1280x720, 1920x1080;
- report actual width, height, pixel format, stride, frame bytes, latency and FPS;
- dump a frame when the backend permits it;
- investigate source-region/ROI capture for short dialogue anywhere on screen.

No assumption is made that 1080p works. The probe exists specifically to establish that experimentally.

## Intended pipeline

```text
PS5 / other HDMI source
        |
        v
LG internal video capture
        |
        +--> low-cost text-region detector
        |        |
        |        +--> high-quality ROI/crop
        v
       OCR -> translation -> Russian TTS
```

A fixed subtitle region is not sufficient: games can show short dialogue above characters, menus and arbitrary UI locations.

## Research references

The capture implementation is being researched against these open-source projects:

- `adeze/lg-hue-sync` — compact native on-TV capture/analysis daemon.
- `webosbrew/hyperion-webos` — mature LG capture backend knowledge.
- `TBSniller/piccap` — webOS frontend/integration around hyperion-webos.

Code reused from another project must retain its required license and attribution. The first probe is intentionally small so we can understand the G5/webOS 25 path before importing larger components.

## Repository layout

- `probe/` — scripts/native experiments for capture discovery.
- `docs/` — measurements and reverse-engineering notes.

## Safety

This project targets TVs owned and rooted by the user. Do not expose the TV's root shell or debug services to the public Internet.

## G5 screen capture

PicCap capture measurements and the verified 1920×1080 screen frame are documented in [docs/g5-piccap-screen-capture.md](docs/g5-piccap-screen-capture.md).

## Roadmap

The agreed OCR, translation, overlay and TTS direction is documented in [docs/roadmap.md](docs/roadmap.md).
