# Exact-pixel PP-OCR crop cache — 2026-10-10

## Contract

Per-engine RAM LRU cache wraps existing Engines.recognize; no persistent database and no translated-text reuse. Key: engine model name/directory/layout, recognition mode, width/height, SHA256 of EXACT immutable grayscale input bytes. Hash hit also compares complete stored bytes, protecting against collisions. Cache instance is tied to one loaded engine/process/decoder configuration; restart clears it. Runtime model-identity change clears entries. Recognition is deterministic on tested inputs. No fuzzy matching, downsampling, image-difference tolerance, text substitution or geometry anchoring added.

Values contain original status and crop-local TSV (including exact confidences and control-icon geometry). Coordinates, detector, RGB appearance, policy, translation selection and fresh OSD observation are recomputed normally. Only successful nonempty/non-whitespace text retained; empty/error/oversize responses not cached. Bytes/shape/mode changes require backend call. LRU caps: 16 MiB retained pixel/TSV payload plus bounded Python object overhead, at most 256 entries. Thread-safe lookup/storage; concurrent same-key misses may both compute rather than holding cache lock during NPU work. Existing worker remains sequential/locked.

Default service explicitly PP_OCR_EXACT_CROP_CACHE=1. Removing flag/restarting restores uncached behavior. Cold/new crop retains existing cost. `crop_cache` diagnostics report cumulative and per-frame hits, misses, recognize_calls, evictions and payload size. Counters refer to outer engine calls (including icon helper), not hardware operator counts.

## Gates

18 frozen crops: uncached baseline, first cached recognition, then five alternating uncached/cached repetitions. Status and complete TSV exact (text, confidence, glyph geometry). Every repeated cached call skipped engine. One grayscale pixel toggled on every crop; each caused an additional engine call, regardless of whether visible text changed. These are literal original OCR input pixels; different RGB colors producing identical grayscale input may correctly reuse OCR while appearance still resamples RGB.

Three saved full frames: baseline/first-cache and five alternating repeats; full regions exact. Actual service endpoint: five repeated requests/frame, complete text/geometry/policy/appearance match first pass and archived pre-cache native-CTC responses. No new errors; known baseline failures are not corrected by cache.

| Saved frame | Uncached OCR median | Cached repeated OCR median |
|---|---:|---:|
| Fresh Emergency | 1718.60 ms | 113.32 ms |
| Saved Emergency | 1910.12 ms | 112.49 ms |
| Luigi | 1340.22 ms | 111.39 ms |

Cold first cache pass 1735.02 / 1883.02 / 1308.22 ms respectively. Exact repeated-frame tests had 19/20/15 hits and zero recognize calls. Actual installed endpoint repeated OCR medians approximately 110 ms each. Recognizer-only median-of-18-case-medians: uncached 58.257 ms, cached 0.054 ms. Tests ran while production service remained active; no isolated thermal/inference throughput claim.

## Live result

TV initially unreachable, then user enabled screen and live series collected: ten frames, 9–10 regions, 5–7 hits and 3–4 misses per pass. Some moving/non-text/empty regions continue recognition. OCR median 332.36 ms; frame to returned text 392.83 ms (335.89–597.34); complete pass median 392.96 ms in this series. It is a different scene than prior 1.80 s live series, so not a same-frame universal speedup. First/new dialogue and MADLAD miss latency remain distinct.

Final observed cache: 68 entries, 673000 payload bytes. Capture connected/videoRunning, ~58.57 FPS. OSD diagnostics remain active. New sequence/time identity maintained on cache hits; repeated cached text is admitted only from actual captured observations. No physical reboot/long churn test performed.

## Verification/deployment

Four cache unit tests cover exact hit, one-pixel change, dimensions/mode/model identity, forced hash collision, LRU/payload bounds, invalid size, empty/error/whitespace/oversize rejection. Twelve PP-OCR host tests pass. Saved corpus and actual endpoint checks run on Orange. Library/models/decoder unchanged; service restart active, translator health OK. Whitespace-only rejection refinement deployed after live collection; repeated benchmark still describes successful non-whitespace cases.

Files: scripts/ppocr_crop_cache.py, benchmark-ppocr-crop-cache.py; optional server startup wrapper and per-frame telemetry in existing pipeline. Reports comparison.json, endpoint.json, live.json retain timings and quality evidence. This is OCR result reuse, separate from existing MADLAD translation database cache.
