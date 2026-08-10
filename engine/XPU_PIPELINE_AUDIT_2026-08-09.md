# Quality-XPU pipeline audit — 2026-08-09

## Decision

V43H now defaults to `quality-xpu`: the existing exact Metal/CPU finite-site
formation followed by two concurrent CPU observer branches. RAW read-ahead and
asynchronous four-master writes remain diagnostic modes, not production
defaults.

This is an evidence-gated scheduling change. It does not alter the emulsion,
colour, observer, transfer-function, or encoder mathematics.

## Why this is an XPU-shaped schedule

Pixar describes RenderMan XPU as a single renderer that uses CPU and GPU
together and dynamically distributes work between them. Its architecture also
keeps CPU fallback available when a feature is not yet supported by the GPU.
Those principles are useful here, but a frame reconstruction is not a path
tracer and should not copy its scheduling policy blindly.

The 5279 graph uses heterogeneous work where the evidence supports it:

1. Metal realizes the exact Bernoulli finite-site field while CPU/OpenCV forms
   its expected optical density. The two jobs already overlap inside each of
   the 45 layer/population/record identities.
2. After the one shared negative exists, the 2383 projection observer and the
   Spirit/2K scan observer are independent. A persistent two-worker executor
   evaluates them concurrently.
3. ProRes writes stay ordered and synchronous. Starting four native 5.7K
   writes while the next negative is forming competes for unified-memory
   bandwidth and makes the complete render slower.

References:

- [Pixar, The Evolution of RenderMan](https://renderman.pixar.com/the-evolution-of-renderman)
- [Pixar RenderMan 27, XPU Architecture](https://renderman.atlassian.net/wiki/spaces/REN27/pages/654573626/XPU%2BArchitecture)
- [RenderMan XPU: A Hybrid CPU + GPU Renderer](https://graphics.pixar.com/library/RenderManXPU/paper.pdf)

## Native 5.7K benchmark

Source: `NJARAW_S001_S001_T020.MOV`, frames 0–1, 5760 × 4320, Production
Metal, four 12-bit ProRes 4444 masters. The runs include companion creation and
final colour metadata. Times can vary with temperature and other machine load;
the isolated stage result is the more useful signal.

| Schedule | Observer s/frame | Effective s/frame | Relative to sequential |
| --- | ---: | ---: | ---: |
| sequential | 31.531 | 69.382 | baseline |
| quality-xpu / parallel observers | 28.650 | 64.592 | 6.9% faster |
| parallel observers + RAW prefetch | 27.989 | 65.070 | 6.2% faster |
| all overlaps, including async writes | 35.871 | 78.399 | 13.0% slower |

RAW decode itself costs only about 0.25 seconds per frame. Read-ahead saved too
little waiting time to justify making the default graph more complex. The full
overlap schedule reduced explicit encoder waiting but slowed negative formation
and observation enough to lose roughly nine seconds per delivered frame.

## Exactness gate

Every comparison decoded the delivered masters to `rgb48le` and hashed each
native frame. Sequential and quality-XPU hashes were identical for all eight
frame/branch pairs:

- 5279 → 2383 projection: exact
- 5279 → Spirit/2K scan: exact
- FSD finite-density comparison: exact
- deterministic camera witness: exact

Therefore the accepted scheduler changed zero decoded RGB48 samples. The
existing Production identity audit also still requires 45 unique sampler calls
per rendered frame.

## Rejected shortcuts

- Generic GPU Gaussian/observer replacements remain rejected for masters.
  Earlier tests found rare downstream 2383 threshold differences even when
  float error looked numerically tiny.
- Concurrent Numba kernels are not allowed under its installed `workqueue`
  threading layer. A narrow global launch lock preserves correctness while
  NumPy, OpenCV, and Metal work outside those kernels may still overlap.
- Simultaneous native-frame writers are not a free pipeline stage on unified
  memory. Lower encoder wait does not matter when it starves the scientific
  kernels.

## Next optimization boundary

The next credible large speedup is a resident Metal finite-site compute island:
keep the probability, expectation, realized count, and optical integration
buffers resident across a batch instead of transferring ownership at each
kernel boundary. It must reproduce the present 45 identities and pass the same
decoded 12-bit exactness gate before it can replace the current implementation.
