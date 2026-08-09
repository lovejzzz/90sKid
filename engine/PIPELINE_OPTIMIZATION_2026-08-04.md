# V27 rendering-pipeline optimization on Apple M4 Max

Date: 2026-08-04
Machine: 16-core Apple M4 Max (12 performance + 4 efficiency), 40-core GPU,
48 GB unified memory, Metal 4

## Constraint

Optimization is accepted into the strict path only when the decoded image is
identical to the V27 reference. The release image model, neutral scale, black,
gamma, contrast, DIR behaviour, grain realization, temporal seed and 12-bit
Rec.709 delivery remain unchanged. Faster statistically equivalent or visually
lossless experiments are recorded separately and are not silently substituted.

## Reference profile

The native 5760 x 4320 T020 profile showed that decode and ProRes write were not
the problem:

| Reference stage | Mean seconds/frame |
| --- | ---: |
| RAW decode read | 0.187 |
| Scene preparation + mean negative | 28.926 |
| Stochastic emulsion | 15.816 |
| Period scan observer | 19.258 |
| ProRes write | 0.142 |
| Formal total including finalization | about 64.5 |

One-frame function profiling measured an approximately 18.5 GB resident peak.
The largest individual costs were the multilayer development arrays, the
spectral density cube, 45 finite-population binomial samples, Gaussian/DIR
filters, and three-channel neutral-axis interpolation. The 40-core GPU was not
used by the reference path.

## Strict optimizations accepted

1. Panasonic camera-cube interpolation is a fused, parallel Numba kernel. It
   fell from about 3.84 s to 0.27 s in the first isolated run and to about
   0.014 s after warm-up. Its float32 result is exactly identical.
2. The 5279 spectral density cube uses the same fused kernel strategy. It fell
   from about 4.09 s to 0.27 s initially and about 0.013 s warm, with exact
   float32 identity.
3. The V27 neutral-factor table changed from three full-frame `np.interp`
   traversals to one parallel traversal: 1.87 s to 0.27 s, exact identity.
4. Pointwise activation, gamut compression and granularity interpolation reuse
   buffers without changing operation order.
5. Mean-negative development reuses expired H x W x 3 x 3 buffers. Peak memory
   fell from about 18.5 GB to 12.1 GB in the frame benchmark and about 12.5 GB
   in the formal renderer. The complete frame hash remained identical.
6. On this M4 Max the best strict single-worker topology is 16 OpenCV threads,
   12 finite-population workers and 12 Numba threads. The best safe throughput
   topology is two low-memory frame-range workers, each using 8 / 8 / 8 / 8
   OpenCV, binomial, Numba and exact-array workers.
7. Parallel range outputs are concatenated with ProRes stream copy. There is no
   decode/re-encode generation between the worker segments and final master.

## Measured result

| Path | Formal wall time | Effective seconds/frame | Relative to original V27 |
| --- | ---: | ---: | ---: |
| Original V27, 24 frames | 1547.08 s | 64.46 | 1.00x |
| Strict optimized, one worker, 2 frames | 95.84 s | 47.92 | 1.35x |
| Strict optimized, two workers + concat, 2 frames | 58.58 s | 29.29 | 2.20x |
| Strict row-parallel, one frame | 30.80 s | 30.80 | 2.09x |
| Strict row-parallel, two workers, 2 frames | 44.06 s | 22.03 | 2.93x |
| Strict all-8 topology, two workers, 2 frames | 39.27 s | 19.63 | 3.28x |
| Strict maximum topology, three workers, 3 frames | 54.06 s | 18.02 | 3.58x |

During the low-memory two-worker check, swap-outs did not increase. Swap-ins
increased by only 213 16-KB pages (about 3.4 MB), consistent with touching
previously swapped application pages rather than render-pressure eviction.

The original V27 and optimized two-frame ProRes masters both report 5760 x
4320, `yuv444p12le`, 12-bit, Rec.709 primaries/transfer/matrix. After decoding
the first two frames to RGB48, both produced the same aggregate SHA-256:

`d6fbb0b9dc28c9cdc93a62cfa497edf6e18ac3900d6bbd73da78c473cdb73f8c`

The pre-encode frame-0 array also remained identical across thread counts and
the optimized path:

`8743a072485ebe0f968b07e33b9e8b5a3a809c28e792e4f071d6b04afa29a35a`

### Exact row-parallel pointwise kernels

The optimized profile exposed a second class of costs that had been hidden by
the original interpolation and memory overhead: repeated pointwise scans of
the nine-population arrays. These operations were split into independent row
ranges while preserving the exact per-pixel NumPy operation order.

On the cached native T020 log-exposure frame, the exact density mapping fell
from 5.01 s at one row worker to 0.51 s at twelve; sub-emulsion activation fell
from 0.97 s to 0.107 s. Every tested worker count (1, 2, 3, 4, 6, 8 and 12)
produced the same two SHA-256 values. The same technique now covers RGB gamut
compression, OKLab out-of-gamut fitting and independent DIR destination-layer
updates. The complete pre-encode frame remains byte-identical to the original.

The single-frame strict benchmark is now 30.80 s with an approximately 12.0 GB
peak. A later topology sweep found that two 8/8/8/8 workers fully occupy all
sixteen CPU cores and align with the eight frozen random stripes. It renders
two frames in 39.27 s, or 19.63 s/frame. Its decoded RGB48 aggregate SHA-256 is
still `d6fbb0b9dc28c9cdc93a62cfa497edf6e18ac3900d6bbd73da78c473cdb73f8c`.

Three 5/5/5/5 workers reach 18.02 s/frame and remain byte-identical for the
first three decoded frames. They keep roughly 36.6 GB of frame buffers live and
caused 9,780 16-KB swap-out pages (about 160 MB) during the 54-second test. This
is exposed as an explicit maximum-throughput mode, not the default. Four
workers would exceed the 48-GB physical-memory envelope before application and
OS memory and were deliberately not launched.

## Experiments not accepted into the strict path

### Fully fused sensitometric mixing

The full CPU fusion reduced the frame to about 38.7 s, but tiny float32 order
differences reached rare gamut-boundary pixels. A record-only version retained
99.947% exact 16-bit values and changed only about 0.0067% after 12-bit
rounding, with PSNR about 108.7 dB, but it is not bit-exact and therefore stays
experimental.

### Matrix substitution

Replacing NumPy's two-stage matrices with a combined OpenCV matrix saved very
little end-to-end time and created most of the rare boundary differences. It
was rejected.

### More random stripes

Changing 8 logical random stripes to 12 reduced the stochastic-emulsion test
from 15.99 s to 13.81 s. RGB standard deviations and 1st/99th percentiles were
essentially unchanged, but the particular grain realization changes because
the deterministic random streams are keyed by stripe. This is a good future
plugin default, not a V27 reproduction optimization.

### Generic MPS / PyTorch

- A native 3 x 3 matrix was faster in OpenCV CPU (about 0.033 s) than MPS with
  transfer (about 0.087 s).
- A sigma-3.1 Gaussian operation showed real GPU potential: approximately
  0.162 s OpenCV versus 0.059 s MPS including transfer. The generic PyTorch
  kernel did not match OpenCV's exact truncation/border result.
- A generic MPS sensitometric implementation took about 12.13 s round-trip,
  slower than NumPy (5.43 s) and much slower than fused Numba (0.57 s), mainly
  because generic search/index/einsum operators create a poor graph for this
  workload.

The conclusion is not to avoid the GPU. It is to create one custom Metal
compute island that keeps several convolution and pointwise stages resident on
the GPU, with explicitly matched kernels and borders, rather than launching a
chain of generic operators.

### Custom Metal parity prototype

A runtime-compiled Metal kernel was then tested with an explicit 25-tap,
sigma-3.1 separable RGB Gaussian kernel and OpenCV `BORDER_REFLECT` indexing:

| Native 5.7K convolution | Time |
| --- | ---: |
| OpenCV `sepFilter2D` | 0.1664 s |
| Custom Metal, mean GPU time over 5 runs | 0.00370 s |

The approximately 45x kernel speedup confirms the custom compute-island
direction. Against the OpenCV float32 reference, maximum error was
`4.768e-7`, mean error was `8.812e-9`, and no sample exceeded half of one
12-bit linear code value. It is therefore numerically transparent for a
production path, but it is not bit-exact and remains separate from Archive
exact mode. The timing excludes source-file loading and output-file writing;
an OFX implementation would keep host/GPU buffers resident rather than use
files between stages.

The next trace instrumented every real V27 Gaussian call. One native frame
contains 197 calls across 106 signatures and spends 4.960 s in OpenCV
Gaussian filtering. The ten most expensive signatures account for 3.962 s.
They include the full-frame sigma-18 optical scatter, repeated sigma-4.8,
sigma-3.1, sigma-6.0 and sigma-1.9 DIR operations, plus scan-aperture filters.
The prototype now reproduces OpenCV's float auto-kernel convention and both
`BORDER_REFLECT` and `BORDER_REFLECT_101` for scalar and RGB planes.

Running those ten signatures on already-resident Metal buffers measured
0.172 s of GPU work (0.187 s including command waits), a 21.14x wall-speedup
over their 3.962 s OpenCV total. Maximum crop error was `7.749e-7`; no sample
exceeded half of one 12-bit linear code value.

### Cached Metal bridge and scheduling result

A persistent Objective-C++ bridge now caches the Metal device, command queue,
runtime-compiled library, pipelines, kernels and reusable scalar/RGB buffers.
Across 36 representative full-frame calls it measured 0.413 s including CPU
copies, versus 2.521 s in OpenCV: 6.11x faster at the actual bridge boundary.

The full one-frame renderer fell from the strict optimized benchmark's
46.775 s to 44.644 s. It issued 33 eligible Metal calls in 0.471 s of bridge
wall time and retained the approximately 12.3 GB memory peak. Against the
strict pre-encode image it reached 113.68 dB PSNR; 99.9424% of 16-bit channel
values were identical, and only 0.004782% changed after 12-bit rounding. Mean
change was 0.0000545 of a 12-bit code. Rare maximum changes of 13.25 codes occur
where sub-code convolution differences cross the fixed eight-step gamut
bisection boundary, so Metal remains an explicit production-numerical-parity
mode rather than Archive exact.

The dtype trace then found that two large optical-scatter Gaussians and one
scan-grain Gaussian were accidentally promoted to float64 by Python-list luma
weights. They consumed about 1.60 s and could not enter the float32 Metal bridge.
This historical behaviour remains frozen in Archive exact. The explicit OFX-like
float32 CPU path measures 28.83 s/frame and reaches 138.53 dB against Archive:
only 0.000391% of 12-bit channel codes change and the maximum change is one code.

With float32 spatial weights and Metal together, the production path measures
26.62 s/frame. It reaches 113.69 dB; 99.99533% of 12-bit channel codes match
Archive exact, 0.0128% of pixels change in any channel, mean absolute change is
0.000056 of a 12-bit code, and the rare maximum is 14 codes at the fixed gamut
bisection boundary. The three precision policies are therefore explicit:

- **Archive exact:** historical float behaviour and byte identity.
- **Production float32:** OFX-realistic CPU precision, maximum one 12-bit code.
- **Fastest Metal:** float32 plus GPU Gaussian, production numerical parity.

The independent T032 holdout confirmed the precision hierarchy. Archive exact
measured 31.70 s, production float32 CPU 29.55 s, and float32 Metal 27.58 s.
Float32 CPU reached 138.65 dB, changed 0.000336% of 12-bit channel codes and
again had a maximum difference of one code. Metal reached 111.57 dB; 99.99264%
of 12-bit channel codes matched, 0.0197% of pixels changed in any channel, and
the rare maximum was 15 codes. The higher Metal boundary count on the brighter,
more colourful holdout supports treating this as gamut-boundary sensitivity,
not a global black, gamma or colour transform drift.

### Unified-memory zero-copy and layout result

Native 5760 x 4320 NumPy allocations are naturally aligned to the M4 Max's
16-KB VM pages and their byte lengths are exact page multiples. The Metal bridge
can therefore wrap contiguous input and output arrays with
`newBufferWithBytesNoCopy`. A 36-call full-size microbenchmark fell from about
0.413 s for the cached-copy bridge to 0.268 s with direct shared buffers, while
retaining identical kernel output. The full production frame measured 26.40 s
and was byte-identical to the previous Metal production result.

A second prototype taught the kernel arbitrary NumPy row/pixel/channel strides
and successfully read scalar and RGB views directly from H x W x 3 x 3 arrays.
Maximum convolution error remained `4.17e-7`, with no sample above half a
12-bit linear code. However, forcing all 36 eligible calls through interleaved
stride-9 reads did not improve the 26.40-s frame: bridge time rose from roughly
0.50 s to 0.67 s because non-coalesced GPU access cancelled the saved CPU
packing. The production bridge therefore uses zero-copy only for contiguous
planes and packs interleaved views. The OFX design should create its nine
emulsion layers in planar GPU storage from the outset; a generic "never copy"
policy is not optimal even on unified memory.

Two simultaneous Metal worker processes were also tested, because it would be
easy to assume that the CPU throughput topology transfers directly to the GPU.
It does not on this machine:

| Two-frame path | Wall time | Effective seconds/frame |
| --- | ---: | ---: |
| Strict CPU, two workers | 58.58 s | 29.29 |
| Production Metal, two workers | 61.58 s | 30.79 |

The processes contend for the same GPU and add duplicate host/device traffic.
The Metal ProRes output nevertheless measured 84.86 dB average decoded YUV
PSNR and 0.999997 SSIM against strict CPU ProRes. The renderer now refuses a
multi-process Metal request instead of silently selecting this slower topology.

The measured M4 Max scheduling policy is therefore:

- **Archive exact best measured throughput:** two CPU range workers at 8/8/8/8;
  16.59 s/frame measured, with no three-frame memory-pressure tradeoff.
- **Retired maximum topology:** three CPU range workers at 5/5/5/5 now measure
  17.13 s/frame after row-parallel layer work, so they are slower as well as
  more memory-heavy.
- **Production interactive latency:** one Metal-assisted renderer at
  16 OpenCV / 12 binomial / 12 Numba / 12 exact-array workers; 21.53 s for
  the measured single frame.
- **Resolve OFX:** allow Resolve to schedule frames; maintain one shared Metal
  queue/cache per plugin instance and avoid a second process-level GPU
  scheduler.

## Current commands

Strict single-worker renderer:

```bash
python3 src/render_v27_scan_master.py INPUT.mov OUTPUT \
  --decoder /tmp/prores_raw_float_decode \
  --reuse-v26-projection V26_PROJECTION_DIR \
  --frames 24 --opencv-threads 16 --binomial-workers 12 \
  --numba-threads 12 --accelerated-cpu-exact
```

M4 Max throughput renderer:

```bash
python3 src/render_v27_parallel_scan_master.py INPUT.mov OUTPUT \
  --decoder /tmp/prores_raw_float_decode \
  --reuse-v26-projection V26_PROJECTION_DIR \
  --frames 24 --workers 2
```

Production numerical-parity, single-frame latency renderer:

```bash
python3 src/render_v27_scan_master.py INPUT.mov OUTPUT \
  --decoder /tmp/prores_raw_float_decode \
  --reuse-v26-projection V26_PROJECTION_DIR \
  --frames 1 --opencv-threads 16 --binomial-workers 12 \
  --numba-threads 12 --accelerated-cpu-exact \
  --metal-gaussian-production
```

Quality-aware automatic scheduler:

```bash
python3 src/render_v27_optimized.py INPUT.mov OUTPUT \
  --decoder /tmp/prores_raw_float_decode \
  --reuse-v26-projection V26_PROJECTION_DIR \
  --frames 24 --policy archive-exact
```

For one-frame interactive work, `--policy production-float32` selects the
one-code-bound CPU path and `--policy fastest` selects Metal. For two or
more frames it selects the faster two-worker strict CPU path; therefore the
fastest balanced batch result is also Archive exact. `--throughput maximum` now
retains the measured-faster dual topology; the explicit parallel renderer can
still run three workers for research.

## DaVinci Resolve / OFX direction

The plugin should preserve two modes:

- **Archive exact**: reproduces the frozen V27 CPU image and seed exactly.
- **Production stochastic**: counter-based per-pixel/per-frame random streams,
  12 logical partitions, and a custom Metal convolution/pointwise island. It
  preserves the measured grain distribution and temporal independence without
  tying output to a CPU stripe partition.

Resolve already schedules frame requests concurrently, so the OFX plugin
should not create an uncontrolled second frame scheduler. It should expose one
frame's memory requirement, accept the host's render scale and ROI, keep static
LUTs in GPU buffers, and cache only stock/profile constants. The next useful
engineering step is a custom Metal implementation of the DIR/MTF/scan-aperture
convolution island with a CPU parity harness; generic GPU rewrites are not a
reliable path to either speed or calibration fidelity.

## Roundtable audit, stochastic split and accepted exact work

The two-round multi-model audit and the main-agent decisions are recorded in
`ROUNDTABLE_AUDIT_2026-08-04.md`. It changed the priority order in three ways.

First, conditional exact instrumentation now accounts for the stochastic stage.
Across T020/T032, PCG64/binomial consumes 5.68/6.09 seconds, stochastic DIR
coupling 2.21/2.34 seconds, predicted variance 1.38/1.41 seconds, and record-mix
accumulation 0.83/0.83 seconds. The paired disk and Gaussian filters together
consume only 1.36/1.40 seconds. Gaussian-only work is therefore no longer the
first target.

Second, an exact neutral H-D specialization removes crossover mixing whose
chromatic departure is identically zero. Complete T020 and T032 output arrays
retain their frozen SHA-256 values (`8743...a35a` and `f8bb...4183`), while the
mean-negative stage fell from 8.07 to 7.39 seconds on T020 and from 8.15 to 7.59
seconds on T032 in the profiling runs.

Third, the proposed residual convolution saved only about 0.66 seconds in the
stochastic stage and produced a maximum 14-code 12-bit difference. It is kept
as an explicit experiment and is not selected by any default policy.

The Metal bridge also exposes an experimental per-flight asynchronous API.
Every command owns its kernel and temporary buffers, and Python retains the
page-aligned no-copy arrays until completion. A two-job native microbenchmark
was 1.12x faster than serial submission with identical GPU output. The existing
synchronous renderer remains unchanged until plane batching passes end-to-end
quality tests.

Two additional Archive-exact memory rewrites were then accepted. Predicted
variance reuse reduced its T020 substep from 1.38 to 0.56 seconds, and planar
record-mix reuse reduced 0.83 to 0.33 seconds. T032 reproduced both gains. Both
complete holdout hashes remain unchanged. With instrumentation disabled, the
strict T020 frame now measures 28.56 seconds, versus the previous 30.00-second
strict result and the original 64.46-second reference. This is a 4.8% gain over
the previous optimized path and about 2.26x over the starting point without an
output-bit change.

The next exact pass cached one contiguous probability plane per population and
row-parallelized layer distribution, both release fields and final density
formation. The mean-negative stage fell from 7.34 to 4.22 seconds on T020 and
4.30 seconds on T032; all holdout hashes remained frozen. The current
instrumentation-free T020 strict result is 25.28 seconds with an 11.61 GB peak
resident set, versus 30.00 seconds and 12.33 GB before this pass. Production
float32 CPU is now 23.69 seconds at 138.53 dB/max one code, while the explicit
fastest Metal path is 21.53 seconds at the previously measured 113.69 dB/max 14
codes. Batch Archive export now measures 16.59 seconds/frame with two workers;
three workers measure 17.13 and are no longer selected automatically.
## Exact scan-tail parallelization: quality-first result

The remaining scan branch was split at mathematically safe boundaries. Only
pointwise Cineon code mapping, Spirit primary-correction tails, Blu-ray finish,
neutral balancing, grain compositing, and optical-scatter compositing run in row
stripes. Spirit aperture, 5279 MTF, chroma-grain integration, and both optical
scatter Gaussian fields remain whole-frame operations with their original
border rules.

Native 5760 x 4320 Archive results:

- T020: 21.62 s/frame; scan render 3.21 s (previous exact 25.28 / 6.06 s).
- T032: 22.31 s/frame; scan render 3.19 s.
- T020 SHA-256 stayed `8743a072485ebe0f968b07e33b9e8b5a3a809c28e792e4f071d6b04afa29a35a`.
- T032 SHA-256 stayed `f8bb2357e3f1c86e8bc7fe7d64842c9e1af3f00754d19e7e3dce0821a7054183`.
- A real two-frame ProRes render completed in 30.16 s, or 15.08 s/frame,
  and retained decoded RGB48 hash
  `d6fbb0b9dc28c9cdc93a62cfa497edf6e18ac3900d6bbd73da78c473cdb73f8c`.

The CPU Production path now measures 21.28 s/frame, only 0.34 s faster than
Archive exact. That trade is rejected as a default: its tiny gain no longer
justifies changing even one code. Metal Production measures 19.24 s/frame and
remains an explicit preview/latency option, not the quality master.

A four-frame sustained export completed in 60.94 seconds, or 15.24
seconds/frame. Its first four decoded RGB48 frames exactly matched the original
V27 master at SHA-256
`2a4a80a8e761073c71547202955dddf6d62f1ad2151043e63c40677a6428f776`.
This confirms that the 15.08-second two-frame result was not an accidental
single-frame timing win. Re-profiling 8, 12 and 16 exact-array workers retained
12 as the best single-frame choice; raising the binomial pool from 12 to 16
slightly reduced the stochastic substage but slowed the full frame through
memory-bandwidth and scheduling contention.
