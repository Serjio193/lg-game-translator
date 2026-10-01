# LG G5 PicCap screen capture report

Date: 2026-10-02

Device: LG OLED65G51LW, webOS 25 / webOS 11.2.0

Capture path: PicCap `libvtcapture` with `DISPLAY_OUTPUT`, NV12

## Result

PicCap captured the TV's currently displayed screensaver at 1920×1080. The received frame reports NV12, Y and UV strides of 1920 bytes, and 3,110,400 bytes per frame. The decoded PNG was visually checked; it contains the TV's visible screen image.

The PicCap status endpoint reported approximately **14.6 FPS** at 1920×1080 over ten consecutive one-second checks. This is the service's capture-rate metric, not an independent frame-by-frame timing over a long recording. At 640×360 the status metric was about 59.4 FPS, and at 1280×720 it was about 59.3 FPS. Those two rates were momentary readings; a sustained timing run was not completed for them.

| Requested | Received frame | Format | Stride Y/UV | Bytes/frame | PicCap FPS metric | Evidence |
|---|---:|---|---:|---:|---:|---|
| 640×360 | 640×360 | NV12 | 640/640 | 345,600 | ~59.4 (momentary) | Captured and decoded |
| 1280×720 | 1280×720 | NV12 | 1280/1280 | 1,382,400 | ~59.3 (momentary) | Captured and decoded |
| 1920×1080 | 1920×1080 | NV12 | 1920/1920 | 3,110,400 | ~14.6 (10 one-second status checks) | [Saved frame](g5-piccap-1920x1080.png) |

## Test method and limits

PicCap was configured through its private Luna service API (`luna-send`) to send NV12 frames to a temporary LAN receiver. Each resolution's received FlatBuffers message supplied the dimensions, strides and plane data lengths. The 1920×1080 frame was converted to PNG and inspected. The custom receiver observed short connections (one to fourteen frames) and then a disconnect, so it does not provide a long independent FPS benchmark. The 1920×1080 sustained figure above comes from repeated PicCap status reads while the service was running.

The captured content was the TV screensaver, not a game. This verifies screen capture at the stated dimensions, but does not verify game-specific content, ROI cropping, or sustained receiver throughput. PicCap was returned to its standard destination (`127.0.0.1:19400`) and left configured at 1920×1080; status showed video capture running and connected after the test.
