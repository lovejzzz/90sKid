# Wavefront Tile Lab v0.1.0 — resident Metal emulsion island

Date: 2026-08-09  
Status: statistically validated Production candidate; **lab-only, not promoted
to V43H and not Archive bit-exact**

## Decision

v0.1.0 is the first Wavefront experiment that changes the compute boundary
rather than trimming one allocation.  One Metal command now owns all five grain
size classes for a fast/medium/slow population:

1. global-coordinate Philox/Bernoulli finite-site formation;
2. disk integration of developed sites and expected activation;
3. separable Gaussian optical spread;
4. OpenCV-compatible subpixel phase translation;
5. sampled-minus-expected deviation and weighted class accumulation.

Only the completed population-deviation plane returns to the recovered NumPy
engine.  The nine population calls replace 45 Python/Metal/CPU class crossings.
The sensitometry, three records, DIR chemistry, calibration, projection and scan
equations are unchanged.

The candidate is substantially faster, but it is not bit-identical.  It stays
behind an explicit lab install until final-observer spatial/temporal statistics
and the acceptable determinism contract are decided.

## Why v0.0.x could not be fundamental

A warmed T020 v0.0.2 profile divided the 17.804 s negative as follows:

| Stage | Seconds |
|---|---:|
| scene/camera to 5279 film RGB | 3.327 |
| film RGB to three records | 0.790 |
| deterministic mean density | 4.876 |
| finite-site multilayer emulsion | 8.781 |

Within the last stage, all 45 CPU optical class calls plus accumulation used
about 2.595 s, DIR coupling used 2.493 s, predicted variance used 0.740 s, and
record mixing/calibration used about 0.779 s.  A row tile or one reused plane
could not change the dominant graph.

## Rejected OpenCL bridge

OpenCV 4.11 exposes the M4 Max through OpenCL.  Individual disk/Gaussian/warp
operators were within `2.4e-7` of the CPU implementation, and a synthetic
five-class resident batch fell from roughly 0.60–0.63 s to 0.52 s.  In the real
engine, however, Metal Philox output had to cross into OpenCL.  The nine
population batches took 5.376 s versus roughly 2.6 s for CPU optics.  The
Metal→host→OpenCL boundary erased the apparent kernel gain.  That route was
rejected and is not the v0.1.0 backend.

## Same-Metal implementation

`engine/src/metal_emulsion_batch_bridge.mm` compiles five safe-math Metal
pipelines and records all class passes into one command buffer per population.
Three private float32 scratch planes are reused across the five classes.  Source
probability and the final population plane use unified shared memory when their
allocation permits it.

`engine/src/metal_emulsion_batch_bridge.py` prepares the existing disk kernels
and OpenCV-equivalent Gaussian coefficients.  OpenCV's `INTER_LINEAR` affine
setup was an important trap: it is not equivalent to simply rounding the input
translation to 1/32 pixel.  For one green-record class, an input translation of
`(0.122951, 0.359559)` becomes `(0.125, 0.34375)`, not `(0.125, 0.375)`.
The bridge now measures OpenCV's effective fixed-point translation on coordinate
ramps and gives Metal the resulting exact table coordinates.

Before that correction, T020's maximum formed-density error was `0.0697505`.
After it, the same maximum is `1.66893e-6`.  This was an implementation error,
not an accepted approximation.

## Native 5.7K performance

All rows are one native 5760×4320 GH7 ProRes RAW frame.  v0.0.2's T020 median is
from three warmed measurements; v0.1.0's median is from five completed negative
formations, including full-observer runs.

| Candidate | T020 negative median | Change |
|---|---:|---:|
| v0.0.2 exact CPU optics | 17.579 s | reference |
| v0.1.0 resident Metal island | 14.757 s | **16.1% faster** |

The new nine-call Metal island itself used 0.71–0.83 s.  The previous Metal
sampler plus CPU optical filters and class accumulation used about 3.15 s in the
warmed profile, so this bounded section is roughly 77% faster.  A complete T020
dual-observer run was 38.805 s versus the earlier v0.0.2 median of 41.363 s;
most remaining time is now outside this island.

Negative-only peak RSS was about 6.67 GiB on T020, versus about 6.83 GiB for the
recent exact v0.0.2 measurements.  The candidate does not claim a formal memory
win until Instruments distinguishes Metal private residency from process RSS.

T032 and T007 negative times were 15.409 s and 14.799 s.  The Metal population
island remained approximately 0.72 s on both, so the gain is not specific to one
scene.

## Accuracy boundary

The Philox counters, trial counts, seeds, class weights, kernel definitions and
phase identities are unchanged.  Remaining differences are float32 accumulation
order between OpenCV/Accelerate CPU filters and Metal threads.

| Scene | Maximum formed-density delta |
|---|---:|
| T020 frame 0 | `1.6689301e-6` |
| T032 frame 0 | `8.5830688e-6` |
| T007 frame 276 | `1.0490417e-5` |

T020's complete observer comparison is deliberately reported separately from
negative error.  A tiny negative probability change can cross a later
finite-site print-grain threshold and change an isolated grain, so maximum pixel
delta is a poor summary by itself.

| T020 observer | changed 16-bit values | median changed delta | 99th percentile | changed after 12-bit quantization | maximum 12-bit delta |
|---|---:|---:|---:|---:|---:|
| 2383 projection | 0.1633% | 1 code | 2 codes | 0.0104% | 28 codes |
| scan | 0.0482% | 1 code | 58 codes | 0.0051% | 19 codes |

The signed mean differences are `-5.74e-5` and `+1.99e-5` of a 16-bit code for
projection and scan.  Per-channel means and standard deviations agree to much
less than one 16-bit code.  The large isolated maxima are consistent with a
stochastic threshold flip, but that interpretation still requires visual,
temporal and NPS confirmation.  Therefore v0.1.0 is **not** described as
quality-equivalent yet and is not the default renderer.

### Completed spatial/temporal audit

The subsequent three-frame T020 audit isolated formed-minus-mean record density
in five 512×512 regions.  Against exact v0.0.2, the maximum spatial RMS ratio
error was `1.35e-7`, temporal-difference RMS ratio error `2.92e-7`, normalized
radial NPS-band delta `1.49e-8`, lag-1 temporal-correlation delta `4.41e-9`, and
density-tail ratio error `4.63e-7`.  Maximum crop density error was
`1.19e-6`.  All preregistered gates passed by large margins.

Two complete T020 frames were then carried through both observers. Projection
and scan spatial RMS, temporal RMS, normalized NPS, lag-1 correlation and tail
statistics remained within roughly `1.6e-6` of the exact reference. v0.1.0 is
therefore a **statistically equivalent Production candidate**. It is still not
an Archive path because Metal/OpenCV accumulation order is not bit-identical.
The default renderer remains unchanged.

## Reproduction

```text
PYTHONPATH=engine/src:. python3 engine/src/benchmark_v43h_wavefront_tiles.py \
  <source.MOV> --decoder <prores_raw_float_decode> --cache <frame.npy> \
  --output <result> --reference <v0.0.2-reference> --frame <absolute-frame> \
  --v010 --marginal-workset-pixels 250000
```

The switch installs `engine/src/wavefront_tile_lab_v010.py` only for that
process.  Normal `Emulsion5279Engine` configuration remains unchanged.

## Next boundary

The next useful work is no longer another grain-class micro-optimization:

1. compare final-observer grain NPS, patch statistics and temporal stationarity;
2. investigate a resident deterministic mean-density island (4.6–5.3 s/frame);
3. profile the 24 s dual observer and move shared 2383/scan intermediates before
   considering more stochastic changes;
4. keep an exact CPU/archive path even if a statistically equivalent production
   Metal path is eventually accepted.
