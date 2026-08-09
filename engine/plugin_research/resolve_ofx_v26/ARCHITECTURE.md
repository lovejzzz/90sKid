# Resolve OFX preparation — 5279 emulsion pipeline

Status: research baseline, not a shipping plugin.  The V26 reference renderer
remains the source of truth.

## Measured CPU reference cost

V25 corrected, 5760x4320, one shared emulsion and two simultaneous observers:

| Stage | T020 seconds/frame | Share of wall time |
|---|---:|---:|
| Decode / read | 0.68 | 1.0% |
| Scene transform + deterministic negative | 32.64 | 47.5% |
| Stochastic multilayer emulsion | 16.05 | 23.3% |
| Projection + scan observers in parallel | 18.71 | 27.2% |
| Write both encoders | 0.31 | 0.5% |

T032 gives the same conclusion.  Codec and storage are not the main problem;
the cost is repeated full-frame floating-point image passes on the CPU.

## Host facts already verified locally

- The installed DaVinci Resolve OpenFX SDK is dated 12 May 2026.
- Its sample framework supports float RGBA images and CPU, Metal, CUDA and
  OpenCL render paths.
- The installed Apple M4 Max has 40 GPU cores, unified 48 GB memory and Metal 4.
- Resolve's sample keeps compiled Metal pipelines per host command queue and
  submits work to the supplied queue without forcing a device-wide wait.
- OFX can bracket a sequence with Begin/EndSequenceRender, supply a render
  window, request regions of interest, render tiles and abort stale renders.

These properties match this algorithm well, provided randomness is a function
of absolute pixel coordinates rather than tile scheduling.

## Proposed product boundary

The plugin should not decode ProRes RAW and should not perform artistic grading.
Resolve supplies a float image in a declared working space.  Version 1 should
accept scene-linear V-Gamut, DaVinci Wide Gamut and ACEScg, then output the
selected film appearance in display-linear Rec.709/D65.  Resolve applies the
final OETF or output transform.  This avoids repeating the V25 error of treating
a viewing EOTF as source encoding.

User-facing baseline controls:

1. Input primaries / transfer declaration.
2. Exposure before 5279.
3. Observer: 2383 projection monitor or period 2K scan.
4. Physical format: 35 mm reference locked initially.
5. Project grain seed.
6. Preview / Reference quality.

Saturation, lift, contrast, creative halation and look presets remain outside
the physical baseline.

## GPU graph

### Cached once per device / parameter revision

- Panasonic/working-space transforms.
- 5279 H-D and granularity tables.
- 193^3 analytical 2383 monitor lattice.
- Period 2K scan tables.
- Small disk/Gaussian filter coefficients.
- Fixed spectral and record-mixing matrices.

The cache key must include model version, observer, colour-space selection and
all parameters that affect a table.  It must be scoped per Metal command queue
or CUDA/OpenCL context, following the Resolve SDK examples.

### Per-frame GPU passes

1. **Input + exposure + record projection** — fuse matrices, transfer decode,
   exposure and three record projections into one kernel.
2. **Mean negative** — evaluate H-D, three-speed activation and deterministic
   DIR fields; keep mean density in a temporary float texture/buffer.
3. **Finite sites** — use a counter-based RNG keyed by
   `(project_seed, frame, x, y, record, speed, size_class)`.  This is stable
   across tiles, thread order, render retries and machines.
4. **Dye-cloud integration** — fixed small-support disk kernels plus separable
   Gaussian passes.  Process the 45 record/speed/class populations in parallel;
   accumulate only the nine speed-layer deviations needed by DIR.
5. **48 micrometre calibration + stochastic DIR** — fuse variance prediction,
   exposure-dependent target RMS and record mixing where register pressure
   permits.
6. **Selected observer only** — unlike the research renderer, an OFX instance
   normally emits one branch.  Do not calculate projection and scan together.
7. **Output** — preserve alpha and return display-linear float RGBA.  Resolve is
   responsible for Rec.709 OETF / delivery tags.

## Exactness modes

**Reference** must preserve the finite binomial law, five size classes, three
speed layers, per-frame seeds, DIR coupling, 48um calibration, MTF and full
observer.  GPU and CPU realizations need not be bit-identical if their random
number engines differ, but deterministic means, probability laws, RMS, NPS and
temporal independence must pass the same tests.

**Preview** may use a documented approximation for viewport interaction:
half/quarter render scale, Gaussian approximation only where `np(1-p)` is large,
and a smaller observer lattice.  Grain radii remain physical units and scale
with render scale.  Export always defaults to Reference.

No mode may replace the emulsion with a static noise plate.

## Tiling and temporal determinism

- Declare spatial awareness: blur and DIR require neighbours.
- Expand input ROI by the maximum optical/DIR halo.
- Seed from absolute image coordinates, never tile origin or invocation order.
- Treat `p_Args.time` plus project seed as frame identity.
- Poll OFX abort between major GPU passes and before CPU fallback work.
- Do not request adjacent frames: V26 physical grains are independent film
  frames, so temporal access would waste cache and imply false correlation.

## Optimisation order

1. Port deterministic mean/colour path to Metal and compare to CPU float32.
2. Port the selected scan observer; then the projection observer.
3. Add counter-based finite-site sampling and five-class filters.
4. Add stochastic DIR and 48um RMS normalization.
5. Add CUDA, then OpenCL, sharing constants and test vectors.
6. Add Preview mode only after Reference passes every validation.

This order attacks 47% + 27% of current wall time before the most delicate
random component and produces useful A/B checkpoints.

## Acceptance contract

- Neutral H-D maximum error <= 3e-6 density.
- Mean output RGB maximum absolute difference <= 2e-5 in float reference tests.
- 5279 48um RMS relative error <= 1.5% at the calibrated exposure points.
- Radial NPS low/high-band shares stay within the V26 diagnostic tolerance.
- Absolute lag-1 grain correlation <= 0.02 over flat-field test sequences.
- No output clipping regression; black and highlight reference metrics retained.
- Tile and full-frame renders match within float tolerance.
- Render scale changes physical grain size correctly.
- CPU fallback remains available and visually/statistically equivalent.

## Performance targets (targets, not promises)

First milestone: selected-observer 5.7K Reference under 5 seconds/frame on the
current M4 Max.  Second milestone: 4K Preview at interactive rates.  A real-time
5.7K claim is intentionally deferred until Metal profiling proves it; quality
validation has priority over a marketing frame-rate number.

## Primary implementation references

- Local Blackmagic Design DaVinci Resolve Developer/OpenFX SDK, updated
  12 May 2026, especially GainPlugin, TemporalBlurPlugin and
  RandomFrameAccessPlugin.
- OpenFX 1.5 GPU render and sequence-render documentation:
  https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html
- OpenFX GPU API reference:
  https://openfx.readthedocs.io/en/main/Reference/api/file/ofxGPURender_8h.html
