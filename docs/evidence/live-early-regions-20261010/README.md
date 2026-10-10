# Early regions in the installed live path — 2026-10-10

Installed four relay modules on TV: frame_pipeline, live_translation,
osd_publisher, tv_server; only the relay process restarted through its existing
supervisor. Backup: /media/developer/gocr-runtime/backups/pre-live-early-regions-20261010/.
No capture/model/threshold changes; native installed policy unchanged.

Real selected-frame collection returned empty screens while the console slept.
Therefore the timings below are **saved Emergency Guard RGB replay on TV**,
using installed modules, real Orange OCR and translation endpoints, temporary
OSD publisher files. No replay text was shown on the TV.

First run: ready block 555.2 ms; first sentence preview request 562.1 ms;
Bergamot response 786.4 ms; second sentence response 935.5 ms; complete frame
OCR 1031.5 ms. Both sentence previews were cache misses. This proves early
request/response overlap, not physical display latency. Later runs overlap
ongoing production requests and are not standalone speed comparisons.
Three passes retained counts [1,1], [2,2], [3,3]: region events and final replies
never count as separate captures. See saved-replay.json for exact values.

Installed native policy: Go back!/Are you ready? = TRANSLATABLE_TEXT;
Items./Mario!/Attack Combos. = NON_TRANSLATABLE_LABEL. No single-word bypass.
Tests: 19 live translation + 19 PP-OCR + 5 source admission + 2 sentence-boundary
Python tests; Node admission and translation-pairs tests passed.

Open physical checks: fresh console dialogue, display before remaining OCR,
mask over untranslated tail, typewriter pause, and icon residual R in recognized
Hold [button] R... text. The latter existed in replay OCR and is not corrected
by this transport integration.
