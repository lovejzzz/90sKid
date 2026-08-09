# V43H Wavefront Tile Lab

Date: 2026-08-09  
Machine: Apple M4 Max, 48 GB unified memory  
Holdout: `NJARAW_S001_S001_T020`, absolute frame 0, 5760 × 4320

## Decision

Keep the row-wavefront implementation as an isolated research path. Do not
enable it in V43H Production or change any release pixels.

Every tested tile size preserved the full-frame Philox identity and produced
the same formed 5279 density, projection and scan. The optimized 1M candidate
was nevertheless about 3.1% slower in repeated negative-formation tests and did
not materially lower process peak RSS. Quality passed; performance did not.

The experiment clarifies the useful RenderMan lesson: queueing only the random
point sampler is too narrow. A future resident Metal implementation needs one
planar compute island covering finite-site sampling, dye-cloud integration and
DIR, with buffers reused across those stages. Tiling a single already-fast
kernel adds scheduling without shortening the lifetime of the dominant
`H × W × 3 × 3` emulsion tensors.

## Safety boundary

Only finite-site Philox/Bernoulli point generation was split into full-width row
tiles. The following operations stayed whole-frame and in their accepted V43H
order:

- disk integration and Gaussian optical spread;
- reflected film-frame borders;
- subpixel population offsets;
- inter/intra-layer DIR coupling;
- 5279 MTF and density calibration;
- 2383 projection and period scan observers;
- BT.1886 reference encoding.

This boundary matters. Absolute-coordinate Philox makes a random sample
tile-stable, but it does not make a reflected spatial filter tile-safe. An
arbitrary work tile may never be treated as the edge of the physical frame.

## Exact coordinate contract

The Metal kernel reconstructs the full-frame pixel identity as

```text
globalIndex = (originY + localY) * fullWidth + originX + localX
```

The existing seed continues to identify frame, record, population and size
class. The Philox counter continues to contain the global pixel index, sample
lane and sampler-domain tag. No seed, probability, trial count or floating-point
filter was changed.

The optimized prototype rounds regular tile heights to page-aligned full-row
groups. At 5760 pixels, the requested worksets became:

| Requested elements | Actual maximum elements | Rows |
| ---: | ---: | ---: |
| 250,000 | 184,320 | 32 |
| 500,000 | 368,640 | 64 |
| 1,000,000 | 921,600 | 160 |

Page-aligned source/result planes allow Metal to view regular tiles without a
per-tile staging copy. A bounded background feeder keeps up to three command
buffers ready while the CPU computes the unchanged expected optical response.

## Native-frame evidence

The first implementation copied every tile into and out of an aligned staging
buffer. It established exactness but exposed the cost of treating each tile as
an independent transfer:

| Candidate | Negative formation | Full physical frame | Sampler wall sum | Exact formed/projection/scan |
| --- | ---: | ---: | ---: | --- |
| Accepted full-frame sampler | 18.782 s | 42.983 s | 0.568 s | reference |
| 250k staged wavefront | 21.963 s | 48.697 s | 4.681 s | yes, zero delta |
| 500k staged wavefront | 22.554 s | 47.915 s | 4.708 s | yes, zero delta |
| 1M staged wavefront | 20.177 s | 43.772 s | 4.091 s | yes, zero delta |

The zero-copy background-feeder revision reduced the 1M candidate's sampler
wall sum to 1.505 s and completed the full physical frame in 43.755 s. Its three
saved arrays remained byte-identical to the full-frame reference:

| Array | SHA-256 |
| --- | --- |
| formed 5279 density float32 | `43dcb77057f8a21956a74c8105da10a83294cd33934006382ba077e9853e72be` |
| projection uint16 signal | `f909c68f278e0c6b5a4929a556dce937ecd7a0d90a4310150dc581ae68f0aee1` |
| scan uint16 signal | `3e25af9c3ab0424fc5d31d9da70dfa2bb81f3e87359d0748b3d18d116c200a80` |

Thus the float formed density, not merely the final 12-bit delivery, had zero
changed values and zero maximum difference.

## Alternating repeated measurement

Three full-frame and three optimized 1M/three-flight negative formations were
run in alternating order from the same cached decoded RAW frame.

| Path | Seconds | Median | Peak RSS median | Sampler wall median |
| --- | --- | ---: | ---: | ---: |
| full frame | 19.143, 19.709, 18.919 | 19.143 s | 7.2909 GiB | 0.538 s |
| 1M wavefront | 19.734, 20.020, 18.932 | 19.734 s | 7.2914 GiB | 1.460 s |

The wavefront median is 3.09% slower. Its process peak is effectively unchanged
(about +0.5 MiB, well below useful significance). Although the sampler's own
additional result allocation is one 94.9 MiB plane instead of the accepted
full submit's aligned source plus result planes, the whole process is dominated
by multi-plane activation, layer-deviation, coupling and observer tensors. The
local lifetime improvement therefore does not move the end-to-end peak.

## What was learned from RenderMan XPU

The applicable XPU pattern is not “make every kernel tiled.” It is:

1. express related divergent stages as coherent queues;
2. keep planar data resident across those stages;
3. schedule bounded work without CPU/GPU synchronization at every boundary;
4. reuse buffers when the previous stage's lifetime ends;
5. preserve deterministic global work identity regardless of queue order.

Our exact global-coordinate contract is ready for that architecture. The
current ctypes prototype is not: the CPU still owns full-frame probability,
filter, nine-layer and DIR arrays, and only the shortest GPU stage is queued.

## Next evidence-gated experiment

Build a separate resident planar island, still outside the release renderer:

```text
activation planes
  -> Philox/Bernoulli site formation
  -> disk/Gaussian dye-cloud integration
  -> per-population accumulation
  -> DIR coupling
  -> formed density
```

The island should use a small persistent buffer ring and one command graph, not
one command buffer per row tile. It is accepted only if:

- formed density is float32 byte-identical, or a separately approved Production
  stochastic contract passes all density/NPS/temporal gates;
- projection and scan are identical at the 12-bit delivery boundary;
- median time improves over repeated, thermally interleaved runs;
- peak resident memory decreases materially rather than theoretically;
- T020, T032, T007 and synthetic neutral/primary/ramp holdouts all pass.

Until then the default remains the validated full-frame Quality-XPU schedule.

## Reproduction

The harness is `engine/src/benchmark_v43h_wavefront_tiles.py`. It records raw
float density hashes, encoded observer hashes, identity audit, Metal submission
statistics, stage timings and peak RSS. Candidate output artifacts stay in the
untracked `work/` tree and are not published to Git.

## Sources

- Pixar, *RenderMan XPU: A Hybrid CPU + GPU Renderer*, HPG 2025:
  https://research.pixar.com/docs/2025.HPG.CFKGRSFJBRNSS.pdf
- Pixar HPG 2025 XPU slides:
  https://highperformancegraphics.org/untracked/2025/presentations/Pa2_2_RenderManXPU.pdf
- RenderMan 27 XPU architecture documentation:
  https://renderman.atlassian.net/wiki/spaces/REN27/pages/654573626/XPU%2BArchitecture
- OpenFX GPU rendering reference:
  https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html
- Apple Metal command-buffer best practices:
  https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/CommandBuffers.html
