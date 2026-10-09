# Project map

- `translator/`: существующий translation server и кэш; native OCR postprocess
  его модель, API и настройки не меняет.
- `gocr_worker/`: Google assets validation, detector binarypb parser,
  TFLite execution и head decode, recognizer, TV_CROP/TV_FULL orchestration.
- `gocr_worker/detector.py`: Python clean-room reference grouping.
- `gocr_worker/native_postprocess.py`: один ctypes ABI вызов на весь массив proposals.
- `native/gocr_postprocess/`: самостоятельная C++ shared library и публичный ABI.
- `native/gocr_detector_native/`: native preprocessing, TFLite, head decode,
  existing postprocess и standalone Invoke benchmark.
- `native/gocr_recognizer_native/`: native rectification, LANCZOS/windows,
  recognizer/CTC/NFC/SHA-256 и единый TV_FULL вызов.
- `gocr_worker/native_recognizer.py`: binding recognizer и полного native OCR.
- `scripts/validate-native-recognizer.py`, `benchmark-native-full.py`: реальный
  TV parity и прогретый A/B до получения текста.
- `scripts/research-gocr-xnnpack-divergence.py`: отдельный numerical-path experiment.
- `gocr_worker/execution_profile.py`: explicit STRICT/experimental FAST_XNNPACK selection.
- `gocr_worker/model_operator_metadata.py`: untimed model node/tensor metadata for STRICT profiling.
- `scripts/profile-gocr-strict-ops.py`: node-level native system TFLite timing and allocated shapes.
- `scripts/build-gocr-strict-runtime.sh`, `scripts/benchmark-gocr-strict-runtimes.py`: isolated ARMv7 candidates and exact detector-runtime gate; never change production.
- `gocr_worker/runner_config.py`: recovered runner decoder shared by CLI and runtime.
- `gocr_worker/runner_diagnostics.py`, `scripts/benchmark-google-runner.py`:
  three-profile tensor/proposal/component/quad/crop/text evidence on saved frames.
- `gocr_worker/profile_comparison.py`, `scripts/benchmark-gocr-profiles.py`:
  offline quad matching, text differences and warmed profile latency comparisons.
- `scripts/profile-gocr-threads.py`, `profile-gocr-invoke-boundary.py`: fresh-process
  thread matrix, per-task CPU/scheduler counters и isolated Invoke comparison.
- `gocr_worker/native_detector.py`, `detector_backend.py`: TV_FULL binding и selection;
  generic images сохраняют Python reference path.
- `native/`: ранее добавленный transport выбранного кадра и benchmark utilities.
- `scripts/benchmark-gocr-postprocess.py`: одинаковые proposals → два backend,
  плюс реальные полные OCR passes на сохранённых кадрах.
- `tests/`: integration и native/reference regression checks.
- `docs/gocr-worker.md`: основной GOCR runtime data flow и ограничения.
- `docs/gocr-native-postprocess.md`: native build/binding/parity/timing contract.
- `docs/gocr-native-detector.md`: detector/runtime build, strict parity и performance.
- `docs/evidence/gocr-native-postprocess-20261009/`: реальные inputs и проверенные результаты.

PicCap frame capture живёт в отдельном `hyperion-webos` repository. Native
postprocess работает после tensor decode, не управляет capture scheduler/settings.
