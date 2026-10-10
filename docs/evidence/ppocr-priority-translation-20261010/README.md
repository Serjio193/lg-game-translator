# Joined-block priority and overlapping translation — 2026-10-10

## Implemented boundaries

Original detector boxes/lines/crops and model inputs are retained. Schedule all
multi-line regions first, then larger area, then original index. A multi-line box
is a geometric proxy for joined dialogue, not a new text classifier. Output
region/line ordering is unchanged. A region is complete only when every original
line has recognized; the entire recognized region text becomes one API request.
No new split by dots is added; MADLAD's existing sentence-batch implementation,
icon/name preservation and cache revision remain unchanged.

Optional Accept: application/x-ndjson on existing authenticated /v1/ocr-frame
uses bounded HTTP/1.1 chunked events over the same connection. Completed bodies
pass the original policy before an event is emitted. Headings require the final
whole-frame panel check and are deferred. Events carry sequence/capture timestamp
and exact frame fingerprint; TV validates them, rejects duplicate IDs, nonfinite
JSON, wrong frame identity, oversized/unterminated/extra streams and disallowed
regions. Final result remains mandatory. Old JSON clients still work unchanged.

TV starts two persistent HTTP translation jobs while reading the OCR stream.
Existing API checks SQLite first; misses use MADLAD. Before accepting a future,
TV compares final line ID, complete source text, quad and translation admission.
Changed source starts a new request; obsolete results cannot enter OSD. Errors
drain pending work before admitting the next frame. Three distinct observations,
existing OSD queue/hold and disappearance/placement rules remain intact.

Important limit: final frame/OSD publication still waits for required translations
and normal stabilization. This stage overlaps generation with remaining OCR; it
does not independently publish one region while another translation is pending.

## Two MADLAD workers and SQLite

Original _model_lock protects model initialization only. A bounded semaphore
permits two inference calls. CTranslate2 inter_threads=2 supplies two workers
sharing weights; selected intra_threads=2 per worker. Same model/tokenizer,
compute-type default, beam_size=1, max_decoding_length=128, sentence segmentation,
icon/name routing and cache identity. Reference supported interface:
https://opennmt.net/CTranslate2/parallel.html (same-device weights shared;
concurrent Python calls release GIL and enable separate batches).

SQLite's former global lock spanned generation. It now protects a per-key Future
registry briefly: different full-reply keys generate concurrently; identical
provider/revision/language/type/normalization/hash AND normalized text share one
computation. DB write transactions remain brief and atomic, collision checks
and normalized-source comparisons retained. Coalesced waiters perform a normal
lookup afterwards, updating hit_count/last_hit_at. Preliminary Bergamot results
remain outside the database. Existing Google provider/settings routes retained.

This branch previously contained only a stale minimal translator/server.py.
Current deployed server and dependencies (also present in the main dirty checkout)
were brought into this branch before the scoped concurrency edits. Deployed
server source matched E:/Github/lg-game-translator/translator/server.py SHA256
e26942b33ff80588c84b498afeeb75b026c7a8d1e6b6228b48a24b1ea4dc03d2. Existing live cache/schema/provider functionality preserved;
no schema migration or new model-revision namespace added by this optimization.

## Quality and timing evidence

Three saved frames: exact original regions, text, confidence, geometry, RGB
appearance and final translation policy versus the prior three-worker endpoint.
Early allowed events: current/Emergency/Luigi = 2/2/1. Raw recognizer model/bridge/
decoder unchanged from the previously passed 18-crop exact-output gate.

Actual installed chunked endpoint + actual translation API: all three fixtures
match archived OCR/policy. Initial cold saved-frame bodies began translation
317–424 ms / 344–434 ms / 265 ms before the rest of OCR completed respectively.
Headings have zero overlap and are correctly deferred. stream-endpoint.json.

Uncached translation benchmark: one warmup, five paired requests per text pair,
two different entire blocks; direct backend bypasses SQLite. Two independent
process runs avoid simultaneously resident benchmark models. All translations
and repeated outputs match the single-worker reference; four source blocks.

| Pair | 1 worker x 4 CPU threads | 2 workers x 2 threads | Ratio |
|---|---:|---:|---:|
| Toothbrush + Uni-Tree replies | 9762.03 ms | 9641.98 ms | 1.01x |
| Gear description + items description | 13633.00 ms | 14160.56 ms | 0.96x |

There is no demonstrated overall throughput improvement from two MADLAD workers
on this sample, and no 2x speedup claim. Selected to support independent blocks
as requested; early OCR/translation overlap is the demonstrated time reduction.
Profiles ran successively, not a thermally balanced alternating A/B; production
service remained active. Cache-hit/no-model work is separate from these numbers.

2 workers x 4 threads: first pair median 11155.83 ms, slower than reference.
The second pair's 17942.48 ms sample is confounded by an accidentally overlapping
experimental process and memory pressure; that overlapping run was stopped and
restarted sequentially. Do not treat that second timing as a clean result.
No production process/settings were changed for these benchmarks. Model was
never swapped. Selected 2x2 rerun occurred after the earlier processes exited.

Installed API: simultaneous cache misses for the two first replies completed in
9845.14 ms; both translations exactly match reference. deployed-madlad.json.
Existing awkward wording is unchanged, not interpreted as an accuracy improvement.

Live: ten fresh captured frames; one body per frame started before full OCR
returned. Cached translation starts overlapped remaining OCR by about 8–99 ms
in examples (headings deferred). Frame-to-text median 312.38 ms, range
243.84–466.66; entire pass median 326.54 ms, range 258.10–484.43. These are mostly
cache hits in one scene, not new MADLAD-generation latency or paired live speedup.
Capture connected/videoRunning, 58.58 FPS. live.json.

## Deployment and rollback

Orange full service updated scripts + optional event handler, translator updated
only server.py, progressive.py and translation_cache.py. Original deployed
dependencies/model files remain. API drop-in workers.conf sets workers=2 /
threads=2; remove it/reload/restart for original 1x4 settings. Existing model-load
behavior retained, model remains resident after first miss.

TV relay PP_OCR_EARLY_TRANSLATION=1; removing flag/restarting selects previous
single JSON result flow. PicCap selected RGB/LZ4/three NPU workers/exact crop cache
and OSD rendering retained. Old scripts backed up before deployment. Relay and
PicCap process restarted to recover fresh capture after backend restarts;
720p/fps60/ocr/nogui settings retained. No physical reboot or new OSD visual proof.
Both Orange units active, API health/status checked; real uncached API warmed
the deployed two-worker model. Persistent translation database not deleted.

Host: 39 translator tests, 20 PP-OCR tests, six Orange-server tests and malformed
LZ4 regression pass. Includes simultaneous different cache keys, same-key
single generation, two inference slots, joined-first ordering/original output
order, actual chunked server/client early-start barrier, stale final-text rejection
and malformed/wrong-identity event stream rejection. Sources all <=500 lines.
