# V23 — new-source generalization and dye-cloud morphology

Date: 2026-08-03

## Test material

- `NJARAW_S001_S001_T020.MOV`: tree bark, mushrooms, bright foliage and sky.
- `NJARAW_S001_S001_T032.MOV`: wet green/cyan exterior framed by dark pillars.
- Both sources are Panasonic GH7 / Atomos Ninja ProRes RAW HQ, 5760 × 4320,
  24000/1001 fps, ISO 500, 5500 K and 180-degree shutter.

## Colour decision

The V22 analytical-dye / LAD interimage / neutral-subtracted D60-relative
monitor model generalized to both new scenes without output clipping or a new
saturation failure. A D55/D60/D65 median relative-chroma lattice was tested and
produced no material improvement over the V22 D60-relative result. It was
rejected rather than promoted as a cosmetic version change.

Metrics:

- `colour_generalization_metrics.json`
- `v23_colour_candidate_metrics.json`

## Grain decision

V22's three discrete dye-cloud sizes were replaced by a five-point quadrature
of a restrained continuous/log-normal-like population:

```
weights = [0.10, 0.24, 0.34, 0.22, 0.10]
radius  = [0.62, 0.78, 0.98, 1.22, 1.55]
optical = [0.78, 0.88, 1.00, 1.12, 1.25]
phase step = 2.3999632297 radians
correlation scale = 0.86
```

The weighted radius remains approximately one. Amplitude is re-normalized to
Kodak 5279's published per-record diffuse RMS measurement at a 48-micrometre
aperture. The maximum cloud class remains a minority because Kodak literature
warns that diffuse dye clouds can improve an aperture RMS number while moving
energy into visually objectionable low-frequency mottle.

Uniform validation retained approximately 0.5–1.3% maximum 48-micrometre RMS
error and less than approximately 0.00038 D temporal mean drift. The candidate
also reduced the isolated maximum density excursion in the T020 validation
frame from about 0.479 D to 0.403 D.

Metrics: `grain_candidate/metrics.json`

## Projection acceleration

The complete pointwise 5279-record-density to 2383 monitor rendering is
tabulated from the exact analytical renderer on a 193-cubed lattice. Stochastic
negative formation, negative and print MTF, and final print fine grain remain
outside the lattice.

On held-out T020/T032 frames, the 99th-percentile Oklab delta-E was about
0.31–0.36 and mean delta-E about 0.05–0.06. Pointwise projection rendering was
about 14 times faster. A 49-cubed lattice and then a 97-cubed lattice were
rejected because their real-frame tail errors were unnecessarily high.

Metrics: `projection_lut_validation/metrics.json`

## Timing protocol

The user changed the validation length from three seconds to one second while
the two concurrent jobs were live. The safely closed 25-frame intermediate
MOVs were stream-copied to their first 24 frames without re-encoding. Each
formal source therefore produces two 12-bit 5.7K ProRes 4444 masters from one
shared emulsion realization, lasting 1.001 seconds. The real wall-clock values
printed at completion of frame 24 were 3472.0 seconds for T020 and 3551.5
seconds for T032; concurrent wait was approximately 59 minutes 11.5 seconds.
The in-memory stage arrays were not serialized on KeyboardInterrupt and are not
reconstructed. This limitation is explicit in the timing files and manifests.

## Sources

- Kodak, *The Essential Reference Guide for Filmmakers*.
- Kodak, *KODAK VISION 500T 5279 / 7279 Technical Data*.
- Eastman Kodak, US 5,314,793, multilayer speed and granularity architecture.
- Eastman Kodak, US 4,536,472, dye-cloud diffusion and low-frequency mottle.
- Eastman Kodak, EP 0,905,561, speed-layer coupler coverage and spectrally
  differentiated dye records; used as a structural scanning-film precedent,
  not as a 5279 formula.
- IS&T, *Noise Power Spectra of Photographic Dye Images*; reversal-film
  measurement used only as a morphology prior, not as 5279 amplitude data.
