# Google runner experimental: LG G5, 2026-10-09

Production was not switched. STRICT remains the reference/default, not ground
truth for Google quality. No model/config/threshold/anchor/pyramid/grouping/window
value was changed. The new profile is an explicit webOS experiment, not Google
Android numerical parity.

## Configuration and implementation

| Setting | STRICT | FAST_XNNPACK | GOOGLE_RUNNER_EXPERIMENTAL |
|---|---|---|---|
| `GOCR_PROFILE` | `strict` (default) | `fast_xnnpack` | `google_runner_experimental` |
| Native detector interpreter threads | 2 | 2 | 4, read/validated from binarypb |
| Detector XNNPACK | off | on | on |
| Recognizer interpreter threads | 2 | 2 | 2, unchanged |
| Detector inputs / outputs | 4 / 11 | 4 / 11 | 4 / 11 |
| Model, config, postprocess, rectification, recognizer | same | same | same |

```sh
GOCR_PROFILE=google_runner_experimental python3 -m gocr_worker.worker_full \
  --assets /media/developer/gocr-runtime/assets \
  --detector-threads 4 --recognizer-threads 2 image frame.png
```

The new profile deliberately ignores legacy `--threads` for its 4/2 contract;
conflicting explicit detector/recognizer counts fail. Native/delegate failure,
Python backend selection and non-RGB1280×720 inputs fail without fallback. TV_CROP
rejects experimental profiles. STRICT and FAST selection/defaults are preserved.

The existing decoder was moved unchanged into `gocr_worker/runner_config.py` so
the CLI and worker reuse one parser. Startup validates field 7, threads=4,
multiple_inputs=true, cache_max_size=5, XNNPACK=true and all input/output names.
The original model's names were independently read through the G5 TFLite C API:
`input_features`, `_1`, `_2`, `_3`; `Identity` through `Identity_10`.

Our actual backend is one persistent detector interpreter/delegate per worker,
allocated once for the selected fixed pyramid shapes. Native input buffers and
proposal storage are reused; postprocess/rectification/recognizer are unchanged.
No new native binary was required. Existing `.so` hashes are in `runtime.json`.
Google's cache size 5 is validated and recorded, **not implemented as five
interpreters**. Google pool/cache policy is still unknown; allocating five copies
would be an unsupported guess and consume TV memory.

## What the Google evidence proves and does not prove

The original binarypb and recovered protobuf descriptor prove the contract in
[google-grouprpn-runtime-contract.md](research/google-grouprpn-runtime-contract.md).
The eight pinned Google assets retain their verified hashes. Encoded cached-runner
fields are 1,3,6,8,12,16,17; `warm_up_shapes` field 18 is absent. This proves no
explicit warm-up shapes are encoded; it does not prove there is no internal warm-up.
`num_inference_threads` is not encoded, so pool worker count is not established.

Downloaded the existing full research artifact from GitHub Actions run
37907719847. The ARM64 library matches SHA-256
`d9cfafb045a296708246727f3c0473895790bcd5ae61265713459bb5bd515203`.
Analyzed the existing xrefs plus expanded disassembly around RunWithContext,
InsertInterpreter, AllocateModelTensors and InterpreterFactoryCallbackXNNPack.
Source-library provenance and exact address windows are preserved in evidence.

| Question | Evidence-backed conclusion |
|---|---|
| One interpreter or pool? | A pooled-cached runner is selected; cached-pool strings and insertion/allocation paths exist. Number of actual live interpreters for this detector is unknown. |
| `cache_max_size=5`? | Encoded capacity value is proven. Cache key, eviction rule, relationship to pool size and eager/lazy population are not proven. |
| Weight cache? | Binary contains in-memory/file weight-cache strings. Factory at `0x73f3e8` conditionally forwards object member `+24` into its delegate-option block (`0x73f58c–0x73f5b0`). Pointer type, whether non-null for GroupRPN and cache lifecycle are not proven. |
| Warm-up? | No field-18 shapes encoded; automatic warm-up remains unknown. Benchmark performs one explicit warm-up per profile/frame. |
| Special XNNPACK options? | Factory has the `XNNPackDelegate` message and initializes a block with constant 3 at `0x73f588–0x73f590`, forwarding it to `0xde6dd8`. This constant does not establish a portable option layout or complete flag semantics. |
| Threadpool? | Four interpreter threads are encoded. Sharing, pool ownership, affinity and scheduling policy are not proven. |
| FP16/QS8/F32 forcing or additional flags? | No complete runner-owned flag mapping has been recovered. Symbol/string availability does not prove a mode is enabled. No forcing/relaxed flags were added to webOS. |

The disassembler's nearest exported JNI symbol has `outside_size:true`: it is
not a valid function owner for these stripped addresses. We do not infer runner
ownership from that symbol label. Expanded factory and its called creation target
provide more control-flow context, but no Android runtime observation or native
oracle. On webOS the existing 2.17 options default returns flags=3; only
`num_threads` is overridden. Weight-cache pointer and cache-file path are null.
Equal constants between different binaries do not establish equivalent options.
Thus no speculative weight cache, extra pool or precision flags were enabled.

## Timing: saved frame to UTF-8 only

All 13 existing corpus frames, one warm-up and five timed OCR passes per profile.
Three persistent workers coexist. Order rotates across all six permutations,
offset by frame index; each frame records the actual orders. Debug export/hash,
tensor comparison and postprocess replay happen outside timed OCR. Background
capture remained running; thermal state was not independently controlled.
There are nine color game frames, three saved grayscale game frames and one
video-only negative control, mostly related scenes from a few games.

| Frame | STRICT ms | FAST ms | GOOGLE experimental ms |
|---|---:|---:|---:|
| Rumble Dish dialogue | 1471 | 445 | 479 |
| Saving Your Game | 1733 | 718 | 783 |
| Yoshi choice first | 1490 | 456 | 530 |
| Yoshi choice second | 1472 | 457 | 789 |
| Main Story description | 1911 | 851 | 1123 |
| Shipshape dialogue | 1645 | 491 | 547 |
| Brave volunteer | 1520 | 431 | 592 |
| Video only | 1371 | 312 | 394 |
| Subtitle grayscale | 1489 | 428 | 509 |
| Dialogue grayscale | 1558 | 456 | 463 |
| Wildwoods book | 1684 | 642 | 705 |
| Emergency Guard | 1850 | 819 | 914 |
| Luigi | 1774 | 758 | 1140 |
| Median of frame medians | **1558.338** | **456.812** | **591.963** |
| Detector Invoke median | **1324.540** | **284.762** | **367.090** |

Ratio of summed frame-median total times: Google experimental is **2.338×**
faster than STRICT, but takes **1.235×** FAST time. This run does not identify the
cause of four-thread timing variability; threadpool contention/thermal effects
remain hypotheses, not diagnoses.

## Raw tensors, proposals, geometry and text

Saved all 11 raw output hashes for every timed pass, four input hashes, per-head
element-wise differences, decoded proposal arrays, actual deduped pieces and
component membership. Diagnostic membership comes from replaying the unchanged
native postprocess after the measured pass; removed/group proposals are marked
-1. Components precede group-head refinement and do not map directly to final
sorted line IDs. Every OCR sample retains quads, crop SHA, recognizer-window SHA
and UTF-8 text. No tensor/crop bit-equality gate is imposed on the new profile.

| Comparison | STRICT ↔ Google experimental | FAST ↔ Google experimental |
|---|---:|---:|
| Regions, base / candidate | 109 / 109 | 109 / 109 |
| Matched by polygon IoU ≥0.5 | 102 | 109 |
| Mean / median / minimum IoU | 0.954113 / 0.979862 / 0.514983 | 1 / 1 / 1 |
| Exact text matches in matched regions | 93 / 102 | 109 / 109 |
| Unicode Levenshtein sum | 12 | 0 |
| Unmatched base / candidate regions | 7 / 7 | 0 / 0 |
| Changed output heads across 13 frames | 143 / 143 | 0 / 143 |
| Changed float32 elements | 5,738,003 / 5,738,005 | 0 / 5,738,005 |
| Largest absolute tensor difference | 21.064280 | 0 |
| Element-weighted mean absolute difference | 0.197826 | 0 |

All four inputs match across all profiles. FAST and Google experimental have
identical hashes, decoded proposals, deduped pieces, components, final quads,
crops, recognizer-window hashes and text on all 13 frames. All five repetitions
per profile are stable. This is corpus-scoped webOS equality, not Android parity.
STRICT matches the previous 13-frame STRICT corpus in text, geometry and hashes.

Emergency Guard: STRICT 858 pieces +77 group proposals →326 deduped pieces,
21 components; FAST/Google experimental 864+77 →321,21. Luigi: STRICT 735 total
proposals →267 pieces,18 components; FAST/Google experimental 739 →266,17.
On Luigi the unmatched STRICT region has empty recognition. Six unmatched
regions on each side are in the noisy book illustration; Shipshape adds `700`.
These matching counts do not prove missing real text or ground-truth accuracy.

Specific text differences from STRICT (FAST and Google experimental are equal):

- `Chapter 1: Wildwoods` ↔ `Chapter I: Wildmoops`.
- `Demo` ↔ `Demd`.
- `Attack ComboS` ↔ `Attack Combos`.
- Cyrillic `В` ↔ Latin `B` on two menu frames.
- `Choose a different Yoshi.` ↔ `Choose a different Yoshi`.
- `✓A Sudden Island Arrival` ↔ `A Sudden Island Arrival`.
- `M` ↔ `AA`, and noisy illustration `222` ↔ `227`.

The prior suspicious text differences are unchanged. Without a Google-native
oracle this report makes no claim that Google quality is worse/better. The
project's no-unexplained-quality-loss gate is **not satisfied**; the new profile
must not become production default.

## Reproduce, verification and next step

```sh
python3 scripts/decode-gocr-runner-config.py assets/gocr_group_rpn_text_detection_config_2024_q4.binarypb \
  --assert-current-android-contract
python3 scripts/benchmark-google-runner.py --assets assets --repeats 5 \
  --output results.json docs/evidence/gocr-google-runner-20261009/corpus/*.png
```

Use the real detector config filename for `CONFIG.binarypb`; original assets and
native libraries must be provided locally, not from Git. The committed PNG replay
corpus preserves every measured RGB hash. Raw report comparisons reuse legacy
field names `strict_text` / `fast_text` to mean base / candidate in each named pair.

30 targeted Windows tests and 40 G5 tests passed, including native image and
postprocess regressions. Native build was reused; no C++ algorithm changed.
Source-size and diff checks passed. No PicCap/capture/API/OSD settings, production
mode or services were switched/restarted. Test runtime files are isolated under
`/media/developer/gocr-runtime`. Source commit also persists the previously local
native GOCR prerequisites so the new profile is usable from a fresh checkout.

Evidence directory: `docs/evidence/gocr-google-runner-20261009/`: `results.json`,
`summary.json`, `contract.json`, `config-field-presence.json`, `runtime.json`,
`artifact-provenance.json`, expanded runner disassembly and replay corpus.
Google binaries/models and the large downloaded artifact remain outside Git.

Next useful step is a **Google-native Android oracle** for these exact RGB frames:
record original runner inputs/shapes, delegate options, pool lifecycle, raw heads,
final regions and text. That can distinguish runtime differences from our
clean-room postprocess/decoder behavior. Increasing thread count alone did not
resolve the observed differences from STRICT. Four inputs, eleven outputs,
four threads and delegate selection are repeated; exact pool, weight cache,
warm-up and Android numeric execution remain unresolved.
