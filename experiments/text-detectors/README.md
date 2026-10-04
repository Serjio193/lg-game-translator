# Bounded text-detector comparison on the G5

This is an isolated diagnostic executable, not a new capture service or a
production PicCap dependency. It reads a saved P6/P5 image. The two backends are:

- `contrast`: local adaptive contrast thresholds, connected components and
  horizontal grouping of components with similar character geometry.
- `ppocr`: PP-OCRv5 mobile detection through ncnn, followed by local threshold/
  connected-component boxes. No OpenCV, Python runtime on TV, recognition model,
  GPU or second capture is required.

The neural postprocessor is a prototype for horizontal text: no rotated polygons
or exact DBNet polygon unclip. It must not be treated as equivalent to official
PaddleOCR accuracy. Each backend returns coordinates in the original input size;
OCR crops should come from that original, not the resized detector input.

## Pinned dependencies

ncnn source: `https://github.com/Tencent/ncnn`, revision
`9f9d4ec8150d840b570e735323499b12a354483a`. The included `NCNN-LICENSE.txt`
preserves BSD-3-Clause and third-party notices. Neural preprocessing follows
its `examples/ppocrv5.cpp` (Copyright 2025 Tencent, BSD-3-Clause).

Converted mobile detection weights: `https://github.com/nihui/ncnn-android-ppocrv5`,
revision `671ac4a72299a86ddee160131ba88fed748df425`, paths:

- `app/src/main/assets/PP_OCRv5_mobile_det.ncnn.param`
- `app/src/main/assets/PP_OCRv5_mobile_det.ncnn.bin`

Download from that exact raw GitHub revision and save as `model.param` and
`model.bin`. Verify SHA256 before running:

- param: `358f459680ae0e7a73e477469e529ce116f68c629019ec7a0b6457d2d9117934`
- bin: `857a96bc963725105b78a178dfcc3c0c3db1a7b9eef32244367b2cb105ccf60b`

The model originates in PaddleOCR/PP-OCRv5 (Apache-2.0 upstream project).
Weights are not vendored or redistributed in this repository.

## Build outside the main probe

Set `SDK` to buildroot-nc4, `NCNN_SOURCE` to the pinned source checkout,
`NCNN_BUILD` and `BENCH_BUILD` to separate build directories:

```sh
cmake -S "$NCNN_SOURCE" -B "$NCNN_BUILD" \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/buildroot/toolchainfile.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DNCNN_VULKAN=OFF -DNCNN_OPENMP=OFF \
  -DNCNN_RUNTIME_CPU=OFF -DNCNN_BUILD_TOOLS=OFF \
  -DNCNN_BUILD_EXAMPLES=OFF -DNCNN_BUILD_BENCHMARK=OFF -DNCNN_BUILD_TESTS=OFF
cmake --build "$NCNN_BUILD" -j4
cmake -S experiments/text-detectors -B "$BENCH_BUILD" \
  -DCMAKE_TOOLCHAIN_FILE="$SDK/share/buildroot/toolchainfile.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DNCNN_SOURCE="$NCNN_SOURCE" -DNCNN_BUILD="$NCNN_BUILD"
cmake --build "$BENCH_BUILD" -j4
g++ -std=c++11 -Wall -Wextra -Werror \
  experiments/text-detectors/test_contrast.cpp \
  experiments/text-detectors/contrast.cpp experiments/text-detectors/image.cpp \
  -o /tmp/lg-detector-contrast-test
/tmp/lg-detector-contrast-test
```

The target executable is ARM32 Linux/webOS, not an Android binary. ncnn is linked
statically; libc/libstdc++ use the existing target runtime. OpenMP is disabled;
this experiment genuinely uses one inference thread. Linux may schedule it on
any permitted core; no affinity was forced. Multiple processes are not launched
concurrently for the different detector cases.

## Run

Copy the executable, model and chosen PNM frame into
`/tmp/lg-text-detector-bench` on the TV. The known real-video frame used for the
report is `docs/evidence/text-detectors/burned-text.png`; convert losslessly to
P6 RGB PPM on the PC. For the bottom ROI test, crop rows 540–719 from that frame.

```sh
nice -n 15 timeout 30 /tmp/lg-text-detector-bench/lg-text-detector-bench \
  ppocr /tmp/lg-text-detector-bench/text.ppm 640 8 1000 \
  /tmp/lg-text-detector-bench/model
```

CLI: `backend image max_edge iterations period_ms model_prefix`.
Output is JSON with elapsed and process CPU time, peak RSS, and boxes. Model load
and warmup are excluded from steady-state detection timings; resize and
postprocessing are included. Peak RSS includes startup. There is no OCR in this
executable; OCR in the installed PicCap continues independently during the test.

`run_tv.py --output OUTPUT_DIR` measures a brief baseline then both backends at
320/640/960 with eight paced iterations each. It monitors PicCap and HyperHDR and
terminates its own probe if the source disconnects, HyperHDR stops or two
consecutive FPS samples fall below 80% of the initial baseline. Remote timeout
also bounds each process. It does not stop or reconfigure either existing app.

Additional runs used:

```sh
python experiments/text-detectors/run_tv.py --backends ppocr --edges 640 \
  --iterations 4 --period-ms 5000 --output build/detector-bench/rare-full
python experiments/text-detectors/run_tv.py --backends ppocr --edges 640 \
  --image bottom.ppm --output build/detector-bench/bottom-roi
```

See `docs/text-detector-comparison.md` for results and limits. No detector is
enabled permanently in PicCap by these experiments.

The game comparison used `--image game.pgm` and the default six cases. Its stored
input is `docs/evidence/text-detectors/game/input.png`, converted losslessly to
PGM. The additional ROI run used `--backends ppocr --edges 320 --image
game-bottom.pgm`; that image is rows 540–719 of the same input. Original game
capture remains 1280×720; these smaller sizes apply only to detector processing.

`export_example.py CASE_DIR OUTPUT_DIR` creates PC-side annotated evidence and
parses OCR TSVs using the existing Pillow package. The follow-up game cases used
`run_tv.py --edges 320 640 --iterations 5 --image FRAME.pgm`; see
`docs/text-detector-followup.md` for the crops, recognition and limits.

The expanded ARM32 comparison adds PP-OCRv3/v4/v6, EAST and CRAFT diagnostic
backends to the runner. Results and the DBNet18 conversion limitation are in
`docs/text-detector-expanded-comparison.md`. This does not enable a detector in
PicCap.
