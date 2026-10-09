# Project map

- `native/ppocr_detector_replay/`, `scripts/ppocr_frame_replay.py`: isolated
  ARM64 replay of existing PicCap detector/region code with installed Orange PP-OCR.
- `scripts/benchmark-ppocr-full-orange.py`, `serve-ppocr-frame-probe.py`,
  `benchmark-ppocr-frame-relay.py`: local and authenticated lossless frame-to-text
  benchmarks and the selected full-frame service; deployment is explicit below.
- `translator/`: существующий translation server и кэш; native OCR postprocess
  его модель, API и настройки не меняет.
- `gocr_worker/`: Google assets validation, detector binarypb parser,
  TFLite execution и head decode, recognizer, TV_CROP/TV_FULL orchestration.
- `gocr_worker/frame_client.py`, `orange_server.py`: explicit experimental
  ORANGE_FULL, lossless full-frame relay and authenticated persistent Orange OCR.
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
- `native/gocr_detector_native/conv_dispatch_probe.cpp`, `scripts/probe-gocr-conv-dispatch.py`:
  isolated forwarding diagnostics for actual CONV dispatch and repeated allocations,
  with corpus-wide exact parity. `build-gocr-conv-probe.sh` builds only this probe.
- `scripts/trace-gocr-conv-uprobes.py`: private, temporary tracefs call probes;
  reports unsupported kernel instrumentation and verifies cleanup.
- `scripts/analyze-gocr-conv-dispatch.py`: per-node evidence summary, separate from timing benchmarks.
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

- `gocr_worker/scheduler_observation.py`, `scheduler_experiment.py`: read-only Linux thread evidence and test-process-only affinity/scheduler controls.
- `scripts/benchmark-gocr-strict-scheduling.py`, `analyze-gocr-strict-scheduling.py`: isolated system STRICT 2/2 affinity matrix, exact gates, traces and summaries.

- `gocr_worker/scheduler_series.py`: persistent 10-minute corpus A/B series, cached strict references and one-time warmup; minute-by-minute results are summarized by the existing scheduling analyzer.

- `deployment/ppocr-full/`: installed default Orange full-frame user service,
  TV relay supervisor/startup, with source templates and rollback documented in
  `docs/ppocr-full-default-osd.md`.
- `gocr_worker/osd_publisher.py`, `scripts/install-ppocr-osd-feed.py`: optional
  bridge from completed PP-OCR results to existing OSD admission/queue and feed selection.

- `gocr_worker/capture_timing.py`: telemetry-only recovery of deployed ARM32
  capture timestamps; live selected-frame detector latency methodology and
  bounds in `docs/evidence/ppocr-detector-latency-20261009/README.md`.

- `gocr_worker/lz4_block.py`, `scripts/probe-lz4-transfer.py`,
  `benchmark-lz4-transfer.py`, `validate-lz4-block.py`: bounded native lossless
  frame compression, isolated LAN benchmarks and exact input checks.

- `scripts/ppocr_stage_profiler.py`, `profile-ppocr-stages.py`: opt-in original-call
  stage timing and saved-frame equivalence, with live profiler normally disabled;
  findings in `docs/evidence/ppocr-stage-profile-20261009/README.md`.

- `native/rknn_bridge_experiment/`, `scripts/benchmark-ppocr-quality-gate.py`:
  quality-first frozen-crop tests, original bridge per-call stage timings and
  isolated output-preallocation experiment; not installed as production.

- `native/ppocr_ctc/`, `scripts/ppocr_native_ctc.py`: exact class-major native
  token selection; original label mapping/statistics.mean confidence retained.
- `scripts/benchmark-ppocr-ctc.py`, `validate-ppocr-native-ctc.py`: quality/speed
  gates for default opt-in native decoder; see `docs/evidence/ppocr-native-ctc-20261010/README.md`.

- `scripts/ppocr_crop_cache.py`, `benchmark-ppocr-crop-cache.py`: bounded exact
  OCR-input RAM reuse and unchanged/one-pixel quality gates; selected explicitly
  by PP_OCR_EXACT_CROP_CACHE, independent of the translation database cache.
