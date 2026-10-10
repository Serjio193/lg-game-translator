# Default full-frame PP-OCR and OSD deployment

2026-10-09, explicitly selected by user. TV selected RGB 1280×720 frame → authenticated persistent relay → Orange existing PicCap detector + PP-OCRv6 small NPU → existing MADLAD API → TV existing OSD queue. OCR and translation compute run on Orange; TV still orchestrates translation RPC per region and owns the new OSD admission publisher. This is not a claim of server-side translation orchestration.

## Installed startup

Orange user unit `lg-game-ppocr-full.service` is enabled, active, Restart=on-failure, user linger already enabled. Runtime remains in `/home/orangepi/ppocr-full-experiment-20261009`; artifacts are retained dependencies of the default chain, despite the historical directory name. Models, token and existing translator/crop service are not replaced. Unit restart and translator health checked.

TV `piccapautostart` now starts `/media/developer/gocr-runtime/tv-autostart.sh` before the existing status activation. Supervisor restarts the frame relay on exit. Relay environment PP_OCR_FULL_OSD=1 enables `gocr_worker/osd_publisher.py`. Startup marker `/media/developer/ppocr-full-osd.enabled` chooses the new OSD feed. Installed PicCap's supported TV_FULL selector enables the frame socket; relay's actual execution mode is ORANGE_FULL. No model contexts are loaded by that relay. Old startup backed up as `/media/developer/gocr-runtime/piccapautostart.before-ppocr-full-default`.

Current IPs are explicit existing deployment settings: TV 192.168.1.3, Orange 192.168.1.11, full OCR 18775, translator 8765. LAN full-frame endpoint uses existing private token file; no secrets are included in deployment templates.

## OSD bridge

Existing installed `translation-watcher.js` is generated/minified. `scripts/install-ppocr-osd-feed.py` supports its quoted path literals, saves `.before-ppocr-full`, and redirects only admission/slot reads when the marker exists. HDMI control, model provider, queue, minimum five-second display, window recovery and renderer remain unchanged. Generated watcher syntax checked on TV. Source checkout's previous watcher is not overwritten.

New admission feed: `/tmp/ppocr-full-osd-admission.json` and `/tmp/ppocr-full-osd-slot-NN.json`. Three distinct completed observations of normalized text + overlapping region are required; duplicate sequences do not increment. Changed text creates a new identity, disappearance removes the track. Unchanged track freezes initial placement. At most twenty display entries. The restored PicCap classification/panel-heading policy now gates MADLAD and OSD explicitly; the initial two-word display filter has been removed. See docs/evidence/ppocr-policy-restored-20261009/README.md for native source provenance and remaining tracker boundaries. The existing completed translations are not canceled by this publisher; they are shown only when their current admission matches.

Appearance: original frame/box/line count, background median sampled from crop edges and homogeneity check, black/white contrast foreground. Homogeneous regions get solid cover; uncertain regions stay transparent. Original glyph erasure mask, detailed foreground palette and icon pixel extraction have not yet been carried across. This is a functional initial OSD attachment, not preservation of all previous appearance behavior. Three-observation display can add multiple OCR cycles; no latency reduction claimed.

## Verification

Enabled/active Orange unit, manual restart, TV supervisor and transport process, idempotent startup (single relay), fresh PP-OCR sequence 409 after restart, OCR returned in 3.02 s and cached whole response in 3.31 s. Capture approximately 58 FPS. Reboot was not performed; actual reboot recovery remains unverified.

After bridge installation, OSD log reports 15 active pairs and applicationManager reports overlay process running on HDMI4. This is launch/diagnostic proof; physical appearance must be confirmed by the user. Seven PP-OCR Python tests, six GOCR transport/integration tests and two existing Node OSD admission/queue suites passed. Shell syntax and diff checks passed. No GitHub push performed by this deployment.

## Rollback

Stop/disable Orange full-frame unit only after choosing a replacement. On TV remove `/media/developer/ppocr-full-osd.enabled` to restore old watcher feeds, restore backed-up piccapautostart, stop supervisor/relay, remove `gocr-mode.conf` to select previous PicCap OCR, and restart PicCap service. Preserve installed original model assets and old crop service. Backups and user changes must not be deleted during rollback.

User subsequently confirmed: Russian text is visible on the TV. Exact mask/color/placement quality and reboot recovery remain separately unverified.

Current deployed PicCap full-frame mode now uses demand-only fresh sampling and
fixed 64-bit monotonic microseconds. Build/device tests and live before/after
latency: `docs/evidence/ppocr-fresh-frame-20261009/README.md`. No physical TV
reboot test has been performed.

Default TV relay now uses native LZ4 lossless block transport, with original
GFR1/RGB contract and raw fallback when not smaller. Required TV library:
`/media/developer/gocr-runtime/liblz4-tv.so`. Results and exact OCR/geometry
checks: `docs/evidence/lz4-transfer-20261009/README.md`.

2026-10-10: default Orange unit selects PP_OCR_CTC_LIBRARY for the validated
class-major native decoder. Original Python path remains available by removing
that setting and restarting; the RKNN bridge/preallocation experimental backend
is unchanged. Exact corpus and complete saved-frame response gates passed:
`docs/evidence/ppocr-native-ctc-20261010/README.md`.

## Accepted configuration, 2026-10-10

User accepted native class-major CTC as the default. Keep original RKNN models/bridge and reference Python decoder for rollback. Acceptance gates: 18-crop exact text/confidence, adversarial semantics tests and three complete saved-frame response comparisons. Preallocated RKNN output experiment remains research-only. Future performance changes must repeat the frozen quality gate; known clipped/glyph errors are not hidden from the corpus.

Capture-side patch is archived as patches/piccap-ocr/fresh-frame-demand.patch. Apply only against the documented current PicCap source snapshot with LF-normalized files, using git apply --unidiff-zero; patch reverse-check passed on that snapshot. It does not snapshot or commit unrelated changes in the external PicCap checkout.

2026-10-10: default PP_OCR_EXACT_CROP_CACHE=1 enables bounded exact-grayscale
crop RAM cache (16 MiB payload, 256 entries). Text/confidence/TSV reused only
when mode, shape, loaded model identity and ALL input bytes match. New pixels,
empty/error responses and appearance/policy updates follow normal processing.
Rollback: remove setting and restart Orange unit. Gates/live evidence:
`docs/evidence/ppocr-crop-cache-20261010/README.md`.

2026-10-10: default PP_OCR_RECOGNIZER_WORKERS=3 uses one frame queue and three
exclusive persistent contexts on NPU cores 0/1/2. Shared exact cache coalesces
in-flight duplicates. PP_OCR_CORE_LIBRARY points to the native wrapper around
the original unchanged bridge. Raw-output/TSV and complete endpoint gates pass;
uncached saved-frame OCR improves 1.76–2.03x. Rollback: workers=1 and restart.
Build, memory, timings and deployment evidence:
`docs/evidence/ppocr-three-workers-20261010/README.md`.
