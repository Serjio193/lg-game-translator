# Two GOCR deployment bundles for speed testing

The two profiles are intentionally identical in Google model parameters. The only variable is where line recognition runs.

## Bundle A — TV_FULL

Path: `config/gocr/gocr_tv_full.json`

LG:
- captures the existing 1280x720 frame once per second;
- runs Google GroupRPN;
- produces the rectified Google crop;
- runs the Google Latin/Cyrillic recognizer;
- sends UTF-8 text + geometry to Orange Pi.

Orange Pi:
- translates only.

Use this profile to measure whether recognition is cheap enough to keep on TV.

## Bundle B — TV_CROP

Path: `config/gocr/gocr_tv_crop.json`

LG:
- runs exactly the same Google detector and grouping;
- produces exactly the same Google crop;
- sends crop pixels + geometry.

Orange Pi:
- runs exactly the same Google recognizer;
- translates.

Use this profile to measure whether moving recognition off-TV lowers total latency or TV CPU load enough to justify crop transport.

## Non-negotiable parity rule

Do not tune detector or recognizer values independently between the two profiles.

The following remain Google production values:
- detector threshold;
- anchors;
- detector max/reference size;
- GroupRPN grouping constants;
- line height;
- recognizer input width;
- input quantization;
- CTC blank;
- LM/FST/prior parameters when enabled.

If a value must change for a debugging experiment, create a separate profile. Do not silently edit either benchmark profile.

## What to compare

For each identical captured frame, record:

```
TV_FULL:
capture_ts
detector_ms
crop_rectify_ms
recognizer_ms
total_tv_ms
bytes_sent
translation_ms
end_to_end_ms

TV_CROP:
capture_ts
detector_ms
crop_rectify_ms
copy_or_encode_ms
bytes_sent
network_ms
recognizer_ms_orangepi
translation_ms
end_to_end_ms
```

Also compare text output line-by-line. Speed results are meaningless if the two paths do not produce the same recognizer input and equivalent text.

## Recommended test sequence

1. Replay the same stored 1280x720 frames through both profiles.
2. Verify identical detector quads.
3. Verify byte-identical rectified crops before transport.
4. Verify equivalent recognizer output.
5. Only then compare timing.
6. Finally test live 1-frame-per-second operation on LG.

The proprietary Google model/config binaries are intentionally not committed. The profiles refer to extracted runtime assets by filename.
