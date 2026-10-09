# G5 system STRICT CONV dispatch investigation

Date: 2026-10-09. This is evidence about the current LG system runtime, not
Google-native oracle parity and not a production optimization.

## Scope and identity

Reference is `/usr/lib/libtensorflow-lite.so`, TFLite 2.17.0, SHA-256
`cace8a26cd74882b359fcdf1061c2f5e99dd6422a1e7455d4352b6bf68e70138`.
Detector threads=2, recognizer threads=2, explicit XNNPACK=false, STRICT.
Google assets/config, arithmetic flags, capture, API, OSD and production settings
are unchanged. `nice=-5` is not integrated. No replacement runtime/kernel is used.

Evidence: `docs/evidence/gocr-strict-conv-20261009/`.
Original per-op measurements remain in
`docs/evidence/gocr-strict-runtime-20261009/emergency-ops.json` and `luigi-ops.json`.

## Method and proof boundaries

The opt-in `conv_dispatch_probe.cpp` is an isolated LD_PRELOAD forwarding library:

- Intercepts the actual system `Register_CONVOLUTION_MULTITHREADED_OPT()` call.
  Copies its 48-byte registration and wraps only Prepare/Eval; calls original
  function pointers with unchanged context/node arguments. Init/Free are unchanged.
- Matches actual nodes to original model metadata using unique input/output tensor
  pairs. Detector context must contain all 167 CONV nodes; recognizer context is
  kept separate. No delegate-only execution-plan callback is invoked.
- Counts actual Eigen device, transpose, gemmlowp DispatchGemmShape, gemmlowp
  MultiThreadGemm and ruy TrMul calls while inside a particular CONV Eval.
- Records the actual KernelBase object supplied to MultiThreadGemm: its Name()
  and Run function pointer. Does not modify the object/vtable or replace Run.
- Records temporary tensor index/type/allocation/size/address and their changes.
- Forwards glibc malloc/calloc/realloc/free unchanged; counters apply to the main
  Eval thread only. Worker-thread allocations and internal noninterposable calls
  are not covered. Requested bytes are not RSS, memory writes or packing time.

Profiler/probe timings include instrumentation and warmups where explicitly
marked. They locate work; they are not an A/B speedup claim. Callback wrappers,
KernelBase Name() inspection and allocation counters do not change arithmetic,
but numerical transparency is still checked against the uninstrumented runtime.

Dynamic symbols alone are not call evidence. The findings below use forwarding
call counts, actual registration/object addresses, tensor types and disassembly
of this exact pinned library. TensorFlow 2.17 source is an interpretation aid;
it is not proof that LG compiled an unmodified upstream source tree.

## Registration and actual dispatch

Observed registration:

| Stage | System ELF offset | Evidence |
|---|---:|---|
| Register_CONV_2D | 0x35e4a0 | branch to MULTITHREADED_OPT PLT |
| Register_CONVOLUTION_MULTITHREADED_OPT | 0x35e478 | actual interposition |
| Prepare&lt;kMultithreadOptimized=2&gt; | 0x36c790 | original registration pointer |
| Eval&lt;kMultithreadOptimized=2&gt; | 0x391ed0 | original registration pointer |
| float32 EvalImpl&lt;2,1&gt; | 0x38f80c | disassembly + Eigen caller return offset |
| int8 EvalImpl&lt;2,9&gt; | 0x3892fc | disassembly + actual per-channel gemmlowp call |
| per-channel int8 DispatchGemmShape | 0x382528 | actual per-node forwarding calls |

All 167 CONV nodes share the same registration, but they do not share one
execution backend. Eleven float32 nodes invoke Eigen; 156 int8 nodes invoke the
observed per-channel gemmlowp DispatchGemmShape. This is not hybrid float/int8:
the observed input/filter types are float32/float32 or int8/int8 respectively.

Float32 caller offset recorded by Eigen GetThreadPoolDevice is 0x38fcf0, the
return from the instruction at 0x38fcec in EvalImpl&lt;2,1&gt;. The following native
multithreaded convolution implementation is an internal, stripped code region.
The exact Eigen contraction microkernel and worker packing subroutines have
not been dynamically isolated.

INT8 `cpu_backend_gemm::Gemm` contains both ruy and gemmlowp branches. Actual
calls select gemmlowp for every detector int8 CONV in these observations. TrMul
interposition sees zero calls. This does not prove ruy is absent from the library
or from every unobserved/internal path.

Actual KernelBase selection is recorded separately in `kernel-corpus/dispatch.json`.
All 156 INT8 detector nodes select the object whose actual Name() returns
`NEON, 4x2, depth 16, accumulating two within signed int16`; its Run pointer has
system ELF offset 0x3233a4. Each has 26 observed MultiThreadGemm calls for 26 Evals
in the final corpus gate. This establishes the selected concrete gemmlowp kernel
object for the observed path, including nodes 12/16/96/100.
Its Run address is corroborated by the pinned binary vtable and NEON disassembly;
this is stronger than merely finding a kernel symbol. It does not provide a
separate dynamic entry counter or exclusive timing of the inner Run loop.

## The expensive nodes

Reference median is the earlier Emergency node profiler, not a newly measured
uninstrumented per-op latency. Shapes and all top-20 CONV details are in
`summary.json`. Node 80 from the old mixed top-20 is DEPTHWISE, so the table below
includes the next CONV (46) instead. Ordering follows reference total time.

| Node | Reference median ms | Actual path |
|---:|---:|---|
| 83 | 53.18 | Eigen float32 |
| 167 | 53.67 | Eigen float32 |
| 84 | 44.90 | Eigen float32 |
| 168 | 45.86 | Eigen float32 |
| 96 | 35.26 | gemmlowp per-channel int8 |
| 12 | 33.66 | gemmlowp per-channel int8 |
| 100 | 33.57 | gemmlowp per-channel int8 |
| 16 | 32.71 | gemmlowp per-channel int8 |
| 25 | 18.49 | gemmlowp per-channel int8 |
| 105 | 18.95 | gemmlowp per-channel int8 |
| 21 | 19.14 | gemmlowp per-channel int8 |
| 78 | 14.91 | gemmlowp per-channel int8 |
| 109 | 18.46 | gemmlowp per-channel int8 |
| 162 | 13.61 | gemmlowp per-channel int8 |
| 94 | 14.42 | gemmlowp per-channel int8 |
| 81 | 11.00 | gemmlowp per-channel int8 |
| 50 | 14.00 | gemmlowp per-channel int8 |
| 101 | 12.15 | gemmlowp per-channel int8 |
| 13 | 11.58 | gemmlowp per-channel int8 |
| 46 | 10.26 | gemmlowp per-channel int8 |

Nodes 83/84/167/168: input 1x92x160x64, filter 7x5x5x64, output
1x92x160x7. Nodes 12/16/96/100: input 1x184x320x16, filter64x1x1x16,
output 1x184x320x64. The different types and paths matter more than the common
CONV registration name.

In the 52-Invoke corpus probe, nodes 12/16/96/100 spend approximately
99.95–99.96% of their Eval wall time inside DispatchGemmShape. This boundary
includes packing, compute, output processing and synchronization, not arithmetic
alone. It leaves very little time in TFLite wrappers for these expensive 1x1
nodes. Node 94's GEMM boundary is 73.61%; about 26.39% lies outside it. Separating
that remainder into im2col/copy/other work requires another targeted probe.

## Repeated work, caching and allocation

Cold/warm follow-up: Emergency+Luigi, one warmup and five measurements per frame,
one persistent detector/recognizer pair, 12 actual detector Invokes.

| Nodes | Prepare calls/node | Transpose calls/node | Warm malloc calls/Eval | Warm requested bytes/Eval |
|---|---:|---:|---:|---:|
| 83/84/167/168 | 1 | 1 | 27 | 29,474,164 |
| 12/16/96/100 | 1 | 0 | 5 | 2,316 |

Node 83 has 40 malloc calls on its first Eval, then exactly 27 on every remaining
Eval. The other three listed float heads have 27 throughout. The four large
heads alone request about 112.4 MiB cumulatively per Invoke on the main thread.
This is allocation request volume, not 112 MiB of additional persistent RAM or
proof that all those bytes are zeroed, copied or packed every time.

Each listed float head has a 44,800-byte float temporary with allocation type 3
(arena RW persistent), unchanged address/size throughout. Its size equals the
7x5x5x64 float filter; actual TransposeFloatTensor runs only once. Together with
the EvalImpl branch and upstream OpData interpretation this identifies the
cached HWCN weight tensor. Re-transposing those weights is not a steady-state
bottleneck. No full TFLite im2col temporary is allocated for these observed
multithreaded float heads; Eigen can perform its own patch gathering/packing.

The listed 1x1 INT8 nodes have no temporary tensors, consistent with no im2col
tensor needed for this geometry. Their five small heap requests recur; these
are not evidence of full filter copying/repacking. Larger spatial nodes have
stable arena temporaries recorded in dispatch.json.

Prepare is called once for every detector CONV across 52 Invokes of the 13-frame
corpus. Existing native orchestration allocates interpreter tensors during
setup, not on each fixed-shape Invoke. Recorded temporary addresses/sizes remain
stable. This does not claim to observe every internal arena operation.

Two pthread_create calls occur in the first node 83 Eval; subsequent listed
float heads do not create threads. Other creation counts are recorded separately.
The earlier scheduler evidence establishes persistent worker TIDs. Worker
wakeup/wait latency has not been separated from packing/compute in this probe.
The MULTITHREADED registration name does not imply every gemmlowp operation
actually uses multiple workers; its internal small-work fallback is unresolved.

Still unknown: exclusive matrix packing time, which original operand is packed
on each dispatch branch, whether all packing blocks are reused across Invokes,
worker allocator activity, memcpy/memset byte counts/time, exact Eigen microkernel
selection, and kernel compiler flags. No claim of removable repeated packing
is made from upstream source or exported symbol presence alone.

## Tracefs limitation

No perf executable is installed. Tracefs exists and accepts private uprobe
definitions. LG offers traceon/traceoff/stacktrace/enable_event/disable_event,
but no histogram trigger. Enabling a private uprobe returns errno 95
`Operation not supported`; histogram registration had returned errno 22.
The unsupported capability could be ARM32 compatibility or trace-instance
support; its cause is not established. No global-tracing workaround is applied.

`uprobes-unavailable.json` records the failure and cleanup. Private probes and
instance are removed, and both inventories were verified empty afterward.
There is no dynamic inner-NEON entry/timing result from that attempt.

## Parity and timings

Corpus: all 13 saved 1280x720 frames, one warmup plus 3 measurements/profile/frame.
Uninstrumented original native modules versus isolated probe, same system runtime.
All 4 input and 11 output hashes match on all 78 measured full OCR calls; decoded
proposals, deduped pieces, component membership, source quads, scores, crop SHA,
recognizer input-window SHA and UTF-8 match exactly. Cold/warm follow-up adds
20 measured full OCR calls with the same exact gate. Final kernel-object probe
adds a separate 13-frame gate with one warmup/one measured call per mode/frame.
Each gate remains strict; matching text alone cannot admit a different tensor.

Uninstrumented medians in the 3-repeat diagnostic corpus:

| Frame | Detector Invoke ms | Full OCR ms |
|---|---:|---:|
| Emergency Guard | 1353.65 | 1871.94 |
| Luigi | 1311.83 | 1748.59 |

These are contextual reference observations, not a long speed benchmark or
evidence of a new optimization. Probe wall times are intentionally not treated
as production performance. The prior CONV 82.45% profiling finding still stands.

## Safe next candidate

The best concrete investigation target is the repeated Eigen workspace
allocation in the four float heads: 27 main-thread malloc requests and about
29.47 MB requested per head/Invoke, while HWCN weights are already cached.
First measure exclusive allocation/zeroing/copy time and identify buffer
ownership/lifetime in the actual system binary. Allocation volume alone cannot
justify a speedup estimate or prove safe buffer pooling.

Do not cache outputs/patches across frames, alter GEMM order, replace kernels,
or patch opaque OpData/arena pointers. A generic malloc cache/interpreter patch
is not introduced. No overhead has yet been shown both safely removable from
outside this opaque runtime and worth the risk. Production remains unchanged;
there is no experimental optimization backend to integrate at this stage.

## Reproduction and verification

```sh
bash scripts/build-gocr-conv-probe.sh "$SDK" "$TF_SOURCE" /tmp/libgocr_conv_probe.so
python3 -B scripts/probe-gocr-conv-dispatch.py --assets assets \
  --output conv-dispatch-corpus --probe /tmp/libgocr_conv_probe.so \
  --repeats 3 fast-corpus/*.ppm
python3 scripts/analyze-gocr-conv-dispatch.py docs/evidence/gocr-strict-conv-20261009 \
  --operators docs/evidence/gocr-strict-runtime-20261009/emergency-ops.json
```

Build requires the pinned 2.17 source commit
`ad6d8cc177d0c868982e39e0823d0efbfb95f04c` for public ABI headers only.
The probe is not linked into native production modules and is not a default
CMake target. Source changes are confined to diagnostics/tests/project map/report.
ARM SDK probe build and 43 targeted host tests pass; 39 existing targeted G5
tests pass; all 43 tests including the new gate tests pass on G5 as well.
