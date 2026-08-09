# 5279 OFX / Metal pipeline architecture

Date: 2026-08-05
Target: Apple M4 Max, Resolve OFX, native 5760 x 4320 float processing

## Precision policies

The implementation must expose precision honestly instead of hiding numerical
substitution behind one quality switch.

| Policy | Reference | Current native T020 | Measured parity |
| --- | --- | ---: | --- |
| Archive exact | Frozen V27 NumPy/OpenCV order | 21.62 s/frame CPU | Byte-identical |
| V35 Production | Float32 spatial math + Philox-u32 Metal finite sites | 25.99 s/frame, two masters | Statistically equivalent; <0.1% high-pass-energy delta over 24 frames |
| Rejected preview paths | Metal Gaussian or convolution reassociation | 24.27-25.18 s/frame | Rare 2383 threshold outliers; not releasable |

T032 independently measured 138.65 dB/max one 12-bit code for Production
float32 and 111.57 dB/max 15 codes for Metal. The rare Metal maximum is a
fixed eight-iteration gamut-bisection boundary response, not a global black,
gamma or colour drift.

Archive exact remains the conformance oracle. V35 Production is an independent
but validated stochastic realization, not a byte-identical replacement. The
Metal Gaussian and algebraically reassociated convolution experiments remain
rejected even when their mean error is tiny: the nonlinear 2383/print-grain
boundary can magnify rare floating-point changes into isolated large code
deltas. Quality gates therefore include tails and threshold counts, not PSNR or
mean error alone.

## Why the GPU layout must be planar

At 5760 x 4320, one float32 scalar plane is 94.9 MiB, one RGB frame is
284.8 MiB and nine emulsion planes are 854.5 MiB. The current CPU model stores
fast/medium/slow x RGB populations as `H x W x 3 x 3`. A Metal stride prototype
read those views correctly without copies, but stride-9 access was not
coalesced: saved CPU packing and slower GPU reads cancelled each other.

The OFX implementation should use `plane x y` storage for all nine-population
buffers. A dispatch can still expose record/population indices, but adjacent
threads must read adjacent x samples. RGB display buffers remain interleaved
only at host input/output boundaries.

## Proposed resident compute graph

```mermaid
flowchart LR
    A["Resolve input GPU image"] --> B["Camera LUT + V-Log/scene preparation"]
    B --> C["Optical scatter + sensor treatment"]
    C --> D["RGB records + H-D / activation"]
    D --> E["9 planar finite-population fields"]
    E --> F["Counter RNG + dye-cloud integration"]
    F --> G["DIR intra/inter-layer compute island"]
    G --> H["Mean + formed record density"]
    H --> I["Spirit aperture / Cineon observer"]
    I --> J["5279 MTF + Blu-ray grain management"]
    J --> K["Gamut + neutral scale + Rec.709 output"]
    K --> L["Resolve output GPU image"]
```

No intermediate stage should round-trip through CPU memory. Static camera,
sensitometry, density, neutral-scale and Gaussian tables live in private Metal
buffers. One plugin instance owns its pipeline states, argument buffers and a
bounded reusable buffer ring, but it must submit through the Metal context and
command queue supplied by the OFX host. It must not create a process-global
device or queue. Pipelines compile at instance creation, never on the first
timed frame.

## Buffer lifetime and target memory

The CPU prototype peaks near 12.2 GB because broadcasting creates several
simultaneous H x W x 3 x 3 temporaries. The GPU version should reuse explicit
buffers according to lifetime, not expression syntax.

| Lifetime group | Native size | Reuse rule |
| --- | ---: | --- |
| Input/output RGB | 2 x 284.8 MiB | Host-owned; do not duplicate |
| Scene/record RGB ping-pong | 2 x 284.8 MiB | Reuse after record exposure |
| Activation / layer density | 2 x 854.5 MiB | One may overwrite after RNG parameters are captured |
| Deviation / DIR correction | 2 x 854.5 MiB | Ping-pong; never allocate per source layer |
| Mean / formed density | 2 x 284.8 MiB | Reuse scene RGB buffers after negative formation |
| Gaussian scalar scratch | 2 x 94.9 MiB | Shared serially by population dispatches |
| LUTs / kernels / counters | under 128 MiB target | Persistent per stock/profile |

The practical one-frame target is 4–6 GB of plugin-owned GPU memory. With
Resolve scheduling more than one frame, the plugin must report/limit in-flight
work rather than multiplying this allocation without bound.

## Scheduling contract with Resolve

Resolve owns frame-level parallelism. The plugin must not reproduce the Python
range-worker scheduler inside OFX. It should:

1. keep one pipeline/resource cache per plugin instance and use the host-owned
   Metal command queue;
2. use command-buffer/event ordering for stages inside one frame;
3. begin with one serial render in flight per instance; raise that bound only
   after measured memory and host scheduling tests;
4. avoid simultaneous independent GPU queues for the same instance;
5. seed stochastic work from frame number, layer, population, size class and
   pixel coordinates, never from host request order.

The desktop benchmark explains this rule: two simultaneous Metal processes
were slower than two CPU workers because they contended for one GPU and repeated
host/device traffic. After exact row-parallel layer and scan-tail processing,
two 8/8/8/8 CPU workers achieve 15.08 s/frame with the frozen decoded hash. The
previously measured three-worker topology was slower and retained the
memory-pressure disadvantage. The scheduler therefore uses two workers for
both balanced and maximum requests.

## Deterministic stochastic kernel

The Archive realization uses fixed NumPy PCG64 stripes. V35 Production now uses
Philox4x32-10 and direct Bernoulli trials: each 32-bit Philox word is compared
with `floor(float32_probability * 2^32)`. Across the observed source domain the
probability representation error is at most 2.27e-10. The identity contract is:

`stock/profile, frame, record, population, size class, x, y, sample lane`

The current seed formula uniquely encodes frame, record, population and size
class, while global pixel position and a sampler-domain tag occupy the Philox
counter. Production asserts 45 unique identities per frame and records the
audit in each manifest. This makes every microscopic site independent of
threadgroup and request order. The production domain audit observed 22 trial
counts from 1 through 30 and probabilities from 1.685e-7 through 0.986325; those
extrema are part of the conformance suite. The implementation need not reproduce
the historical PCG64 mosaic, but it may not change Kodak 48-um RMS, NPS, layer
covariance or the fast/medium/slow exposure transition.

## ROI and render-scale rules

OFX v1 must advertise `supportsTiles=false` and request/process the complete
frame. Global-coordinate Philox makes point sampling tile-stable, but it does
not make the full emulsion graph tile-safe. Spatial stages require explicit
halos, and Gaussian support is technically unbounded; the sigma-18 optical
scatter, DIR diffusion, grain kernels and Spirit 2K aperture each need a tested
finite-error policy before ROI rendering can be enabled. Reflected borders must
refer to the true frame boundary, never an arbitrary tile boundary.

Resolve render scale changes physical pixel pitch. All radii derived at 5760
pixels must multiply by the current render scale exactly as the CPU model does.
The plugin must not merely downsample a full-strength grain result.

## Parity harness gates

Every GPU island is accepted only after all of these pass:

- T020 and T032 native 5.7K holdouts plus neutral/ramp/primary synthetic charts;
- finite values and identical black/gamma/luma policy;
- per-stage max, mean, percentiles, PSNR and 12-bit changed-code fraction;
- deterministic repeat hash for the same frame and parameters;
- independence from threadgroup, tile and request order;
- temporal mean, variance, high-pass difference energy, chroma covariance and
  autocorrelation across at least 24 frames and multiple spatial crops;
- density tails, display clip fractions and nonlinear threshold-event counts;
- peak memory, command time, end-to-end time and host copy count;
- Rec.709 1-1-1, 12-bit ProRes verification after host export.

The formal unified-scheduler fastest master is
`outputs/performance_v27/formal_scheduler_fastest_1f/T020`. It reports
5760 x 4320 `yuv444p12le`, Rec.709 primaries/transfer/matrix and 12 bits. Against
the formal Archive ProRes frame it measures 84.63 dB decoded YUV PSNR and
0.999997 SSIM.

## Next implementation order

1. Keep the stochastic operator profiler as a parity tool and optimize the
   measured PCG64/binomial, DIR, predicted-variance and record-mix costs in that
   order rather than assuming convolution dominates.
2. Replace the Python bridge's process-global Metal state with a host-injected,
   per-instance context and a bounded asynchronous flight ring. Each flight must
   own or retain its buffers until a completion handler releases them.
3. Batch independent planar Gaussian/DIR work behind that lifetime contract,
   then test single-process frame-N GPU / frame-N+1 CPU overlap.
4. Port the nine-plane activation, finite-population accumulation and DIR
   correction into one planar Metal island only after the lower-cost exact and
   batching experiments define the remaining ceiling.
5. Keep Philox-u32 Bernoulli sampling as **Production stochastic**, with per-frame
   identity assertions and immutable provenance. It cannot replace PCG64 in
   Archive exact.
6. Port the Spirit/Cineon/MTF/neutral-scale observer as a second resident island.
7. Replace the ctypes prototype with a full-frame, serial-per-instance OFX
   image/texture bridge using the host queue. Add render-scale and 24-frame
   thermal/parity conformance before attempting ROI halos or tiled rendering.
