# Complete PP-OCR replay on Orange — 2026-10-09

Isolated experiment: saved lossless RGB 1280×720 frame on TV → persistent authenticated HTTP → Orange grayscale conversion → existing PicCap PP-OCRv5 detector/region/line extraction → installed PP-OCRv6 small NPU recognition → text and geometry returned to TV. No translator or OSD calls, stabilization or suppression in this replay; all regions recognized each time. Production selection remains TV_FULL GOCR as previously explicitly requested; this experiment does not switch it.

Existing PicCap C++ detector sources copied unchanged from E:/Github/piccap/hyperion-webos/unicapture. ncnn revision 9f9d4ec8150d840b570e735323499b12a354483a, ARM64 build, one detector thread, Vulkan/OpenMP/runtime CPU dispatch off. FP16 detector options disabled by existing source. Unsupported optional ARM82/84/86 code disabled after an initial Illegal instruction; generic ARM64 NEON build succeeded. No model thresholds, grouping or weights edited.

Detector assets match installed TV hashes:
- bin: 857a96bc963725105b78a178dfcc3c0c3db1a7b9eef32244367b2cb105ccf60b
- param: 358f459680ae0e7a73e477469e529ce116f68c629019ec7a0b6457d2d9117934

Installed recognition mode 4 includes Tesseract-assisted control-icon geometry. Matching existing LD_LIBRARY_PATH was required for that feature; an initial exploratory run without it is not the final reported run. This is not a pure PP-OCR network benchmark. Crops are processed sequentially in this probe; existing native TV line pool uses two clients. Therefore no claim of exact scheduling parity or speedup over the original TV PP-OCR pipeline follows.

One warmup and five measured repeats per frame. Local and relay regions/text match exactly, all repeated results identical. This is transport/repeatability evidence, not cross-architecture detector raw-map parity.

| Frame | Regions | Local Orange OCR median | Relay Orange OCR median | TV frame to returned text median | Estimated RPC overhead |
|---|---:|---:|---:|---:|---:|
| Fresh Emergency | 18 | 1970.5 ms | 1937.8 ms | 2090.8 ms | 123.8 ms |
| Saved Emergency | 19 | 1991.7 ms | 2081.4 ms | 2241.2 ms | 122.7 ms |
| Luigi | 14 | 1421.2 ms | 1420.2 ms | 1581.8 ms | 123.3 ms |

TV encode/materialization/hash median: 19.2–22.5 ms. Relay detector: 118.4–126.6 ms. Main cost is crop recognition/processing: 1293–1904 ms. Medians of stages need not sum exactly to median whole transaction. RPC overhead is request elapsed minus server elapsed, not synchronized one-way latency.

Quality observations: Demo, Attack Combos and guard read correctly. Luigi description assembled as a complete region with [button]. Emergency's final `of damage you take.` remains a separate region. Fresh Emergency instruction lost its R/button placeholder; saved Emergency preserved `[button] R`. Some non-text/icon regions produce o/B. Thus quality is not perfect and integrating translation/OSD requires existing policy and button handling; no unconditional forwarding of all regions is appropriate.

Verification: ARM64 ncnn and detector shared library builds completed, three host frame-contract/TSV tests passed, Python scripts compiled, LAN endpoint rejected unauthenticated request with 401. Temporary server stopped after replay. No full live translation/OSD rollout or long thermal test was performed.

Raw measurements: local.json and relay.json. Files/scripts remain an explicit experimental harness.

## Paired placement test

The two placements were remeasured on identical saved RGB inputs on the TV clock: one warmup each, five measurements each, alternating order. Translation and OSD excluded. TV variant reuses exact PicCap detector/line extraction and two persistent crop clients per block, installed authenticated mode-4 crop server. Orange-full variant reuses the same detector code and processes crops sequentially. No crop cache, temporal suppression, classification or admission included in either replay. This is an isolated cold-recognition-path comparison, not the complete production application with its caches/policies.

| Frame | TV detector + crop RPC | Orange full + full-frame RPC | Reduction |
|---|---:|---:|---:|
| Fresh Emergency | 2232.64 ms | 2194.76 ms | 1.70% |
| Saved Emergency | 2438.39 ms | 2277.05 ms | 6.62% |
| Luigi | 1729.60 ms | 1601.00 ms | 7.44% |

All ten results on each frame matched in region coordinates, line coordinates and text across both placements. Float detector scores/raw probability maps were not included in this equality gate. Detector medians: TV 243–262 ms, Orange 122–171 ms. These observations show a modest benefit on the saved Emergency/Luigi frames and negligible benefit on fresh Emergency, not a large or long-session-validated speedup. Capture service remained running, so normal TV load was present. ncnn emitted existing compatibility diagnostics; weights were not rewritten in response.

`placement.json` preserves every paired sample. `scripts/benchmark-ppocr-placement.py` reproduces this experiment, with the experimental transport server explicitly launched beforehand. ARM32 detector replay library built with the existing webOS toolchain and existing pinned ARM32 ncnn library. Test process and temporary Orange endpoint exited afterward; translation health stayed OK. Production selection remains unchanged.

## Live speed audit and selector correction

The installed PicCap binary recognizes TV_FULL/TV_CROP but not ORANGE_FULL. Writing ORANGE_FULL previously left the native PP-OCR branch active; the separate saved result sequence 1330 at 22:31 did not prove ongoing full-frame operation. Corrected by using its supported TV_FULL full-frame socket selector and restarting the actual PicCap service process with SIGTERM. The socket relay process still explicitly runs ORANGE_FULL against the Orange PP-OCR endpoint: no detector/recognizer instance is loaded by that TV relay. Capture recovered to approximately 58 FPS. This compatibility selection is temporary until deployment of the newer hook and is not a claim that the physical OCR executes on TV.

A stale HTTP connection initially caused BrokenPipeError; the existing client discarded it and subsequent calls succeeded. Live sequences 50, 53, 56, 60, 63 confirmed five updating PP-OCR responses, each with 24 regions and 24 cache hits. Frame-to-text 2.80–3.09 s; full pass including sequential cached translation requests 3.09–3.39 s. Main crop processing 2.49–2.71 s; detector 124–199 ms; full-frame RPC overhead 120–132 ms plus TV materialization/hash ~20–22 ms. Aggregate cached model latency 35.7–55.8 ms, distinct from ~0.28–0.34 s total sequential translation RPC overhead. Per-line recognizer timing is not yet populated in this wire adapter, so its legacy aggregate recognizer=0 is missing telemetry, not zero recognition work.

The earlier new-text response used 11.36 s for a long instruction and 1.95 s for its separately translated suffix: 15.69 s total including OCR. This is a single historical response, not the current cached timing. OSD remains unconnected to this result branch. No reboot/autostart persistence is claimed.
