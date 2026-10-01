# G5 capture test log

Target: LG OLED65G51LW / webOS 25.

## Phase A — environment discovery

Run:

```sh
chmod +x probe/env-probe.sh
./probe/env-probe.sh > /tmp/lg-game-translator-probe.txt 2>&1
cat /tmp/lg-game-translator-probe.txt
```

Record the output here or attach it to a GitHub issue.

## Phase B — capture matrix

Do **not** fill these with assumed values. They are measurements to collect after the backend is identified.

| Requested | Actual | FPS | Capture latency | Pixel format | Result |
|---|---|---:|---:|---|---|
| 320x240 | TBD | TBD | TBD | TBD | TBD |
| 640x360 | TBD | TBD | TBD | TBD | TBD |
| 1280x720 | TBD | TBD | TBD | TBD | TBD |
| 1920x1080 | TBD | TBD | TBD | TBD | TBD |

## Phase C — ROI

Test whether the backend can change source region while capture is active. This is important for short dialogue appearing above characters: a low-resolution whole-screen detector can locate text, followed by a higher-quality crop of only that region.
