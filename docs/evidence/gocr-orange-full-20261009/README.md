# ORANGE_FULL integration verification

- Authenticated experimental worker deployed separately at
  `/home/orangepi/gocr-orange-experiment-20261009/full-frame`, port 18774.
  Original Google assets and existing LiteRT environment reused read-only.
- Worker restarted after the final HTTP rejection fix; authenticated health
  returns ORANGE_FULL, experimental=true, production_equivalence=false.
- `relay-selftest.json.gz`: all 13 original corpus PNGs, one warmup and five
  measured requests each. Exact text/quads/crop SHA/recognizer-window SHA match
  the saved same-Orange D4/R2 delegates-off reference on every measured request.
- Client and server ran on Orange itself in this replay. It proves endpoint
  decoding and orchestration, **not TV↔Orange network timing**. See the separate
  network experiment for real TV transmission measurements.
- Full Orange unittest suite: **63 tests passed**, with existing native
  postprocess .so and newly compiled ARM64 recognizer probe supplied through
  their required environment variables. Missing fixtures/scripts in the first
  staging attempt were copied, then the complete suite rerun without weakening
  assertions. No test skips were added.
- Host: six ORANGE_FULL tests and 14 existing GOCR integration/profile tests
  passed. Broad Windows discovery cannot run native tests without their .so/probe;
  it initially reported seven environment errors. Full coverage was run on Orange.
- Updated native frame-transport C compiled with GCC `-std=c11 -Wall -Wextra
  -Werror` in WSL. This is a host syntax build, not a deployed ARM PicCap rebuild.

TV 192.168.1.3 failed SSH banner exchange repeatedly during this implementation.
No TV code, production mode file, capture service or OSD was installed/restarted.
Live TV activation remains pending device availability and explicit acceptance
of the already measured cross-runtime OCR differences. STRICT remains unchanged.
