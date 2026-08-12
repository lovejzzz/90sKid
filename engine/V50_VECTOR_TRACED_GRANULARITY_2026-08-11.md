# V50: vector-traced 5279 granularity authority

Date: 2026-08-11
Status: evidence-based amplitude correction; morphology remains underidentified

## Why this revision was necessary

The reconstructed engine calibrated its density fluctuations to Kodak's
published diffuse RMS granularity graph, but the array used through V49 was a
coarse visual transcription. It also contained a `+1` internal log-exposure
sample beyond the graph's printed `0..4` lux-second domain. That final value was
not a Kodak measurement.

This mattered because the table is not a cosmetic grain-strength control. It
is the stock-specific marginal density standard deviation measured through a
48 µm aperture, and the finite-site field is normalized to it after multilayer
development and DIR coupling.

## Primary source and recovery method

Authority: Kodak, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
H-1-5279t, March 2003, graph F002_0269AC:
<https://static1.squarespace.com/static/5790488dbe65943e37169f37/t/57ab931e29687fe82091402d/1470862111007/KODAK%2B500T.pdf>

SHA-256 of the retrieved PDF:
`f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8`.

The graph is vector artwork, not a raster image. V50 therefore recovers the
three embedded cubic Bezier paths directly. Horizontal position is mapped from
the printed `0..4` graph exposure axis to the engine's `-4..0` internal logE
coordinate. Vertical density sigma is calibrated by a least-squares fit to all
twelve printed logarithmic Sigma-D ticks. The axis-fit residual is 0.4596 PDF
points, approximately 2% graphical reading uncertainty.

Samples at 0.5 logE intervals are versioned in
[`data/5279_granularity_trace_2003.csv`](data/5279_granularity_trace_2003.csv):

| internal logE | red Sigma-D | green Sigma-D | blue Sigma-D |
|---:|---:|---:|---:|
| -4.0 | 0.0054329 | 0.0129243 | 0.0228430 |
| -3.5 | 0.0064795 | 0.0143390 | 0.0258930 |
| -3.0 | 0.0136699 | 0.0190857 | 0.0390398 |
| -2.5 | 0.0106630 | 0.0154977 | 0.0445431 |
| -2.0 | 0.0072010 | 0.0116326 | 0.0313124 |
| -1.5 | 0.0070468 | 0.0094602 | 0.0227724 |
| -1.0 | 0.0068959 | 0.0083289 | 0.0187934 |
| -0.5 | 0.0067482 | 0.0074934 | 0.0158064 |
| 0.0 | 0.0066036 | 0.0067883 | 0.0142716 |

Outside the published domain, V50 holds the nearest measured endpoint through
`numpy.interp`; it no longer invents a continuing falloff.

Relative to the archive transcription, the changes span approximately
`-9.5%..+20.1%` in red, `+6.0%..+24.9%` in green and `-24.1%..+14.8%` in blue.
The largest practical correction is less blue-record density variation at
middle and high exposure.

## What V50 changes—and what it does not

V50 inherits V49 exactly and replaces only:

- the nine-point published log-exposure domain; and
- the red, green and blue 48 µm diffuse-RMS targets.

It does not alter negative H-D curves, spectral dye densities, masking,
multilayer activation, DIR coupling, MTF, print/scan observers, colour
transport, exposure, white balance or output transfer functions. It is not an
artistic grade.

Because density variance passes through nonlinear film and display observers,
changing its measured amplitude can create a very small mean-code shift by
Jensen's inequality. This is an image-formation consequence, not a hidden
colour correction.

## Verification

The physical 48 µm aperture audit passed across the tested exposure range with
a worst relative RMS error of 1.2805% against the new curves, below the 2% gate.

The V47 structural audit at width 1920, four exposures and six independent
frames measured:

- maximum temporal lag-one correlation: 0.0010663;
- maximum independent-frame difference-RMS ratio error: 0.0011187;
- maximum x/y lag anisotropy: 0.0017435;
- no exact point mass at a numerical density bound; and
- positive-semidefinite cross-record covariance.

The two reproducible audit commands are:

```bash
PYTHONPATH=engine/src python3 engine/src/audit_v46_5279_aperture_rms.py --profile v50
PYTHONPATH=engine/src python3 engine/src/audit_v47_5279_structure.py --profile v50
```

A native 5760 × 4320, 12-bit ProRes 4444 XQ T020 frame passed master and review
conformance. Compared with V49, the projection review's high-pass luma RMS moved
from 0.01313 to 0.01384, while blue-green opponent high-frequency RMS decreased
from 0.00600 to 0.00583. The scan review moved from 0.00862 to 0.00897 in
high-pass luma and from 0.00758 to 0.00697 in blue-green opponent RMS. These
small changes agree with the recovered curves: more red/green density structure
and less mid/high-exposure blue structure.

V50's one-frame engine time was 71.5 seconds on the validation run. The V49
six-frame native-motion result averaged 53.7 seconds per frame. The difference
is machine-load noise, not an algorithmic regression: V50 changes table values
only, and its temporal mechanism is identical to the already validated V49
motion path.

## Revisited temporal and image-formation evidence

The JVT film-grain synthesis proposals and current ITU terminology consistently
treat film grain as optical-density variation, temporally independent from one
frame to the next, with exposure-dependent amplitude and spatial correlation.
They also distinguish local, sample-adaptive synthesis from blockwise video
approximations. This supports our density-domain, per-sample architecture, but
does not provide 5279-specific morphology:

- ITU JVT-I013r2, *Film Grain Technology*:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013r2.zip>
- ITU JVT-H022, *Film Grain Simulation*:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H022.zip>
- ITU-T H. Supplement 21, *Film grain characteristics and modelling* (2025):
  <https://www.itu.int/rec/T-REC-H.Sup21/en>

These documents do not contain a hidden 5279 NPS or numerical grain-radius
table. They cannot be used to justify new stock-specific constants.

## Important unresolved model boundary

The current finite-site field is normalized after coupling to meet Kodak's
published aperture RMS. At the darkest tested exposure, the required per-record
normalization multipliers are about 3.06 red, 4.53 green and 12.50 blue; the
blue multiplier remains roughly 3.6–12.5 across the tested range. This shows
that the current site counts and activation curves do not independently predict
the published blue-record marginal amplitude. The RMS authority is correct,
but the microscopic decomposition is not uniquely identified.

A simple non-negative decomposition into constant base/fog variance plus three
`p(1-p)` population terms failed to fit all three published curves with the
current activation centres. It was therefore rejected rather than hidden in
V50.

The following remain unmeasured in the public 5279 documents:

- two-dimensional, exposure-dependent NPS;
- developed dye-cloud radii (crystal ECD is not dye-cloud radius);
- cross-record covariance and higher-order tail distributions;
- base/fog versus image-density variance decomposition; and
- microscopic coating-capacity bounds.

## Decision

V50 is the most accurate public-evidence baseline currently available. It
corrects a demonstrated source-transcription error without claiming that the
entire microscopic emulsion has been measured. The next defensible image change
requires either calibrated uniform 5279 scans for NPS/covariance fitting or a
clearly labelled hypothesis profile. Until then, visual preference alone is
not sufficient authority to change the grain morphology.

Post-audit note: V50 remains the accepted grain-amplitude and numerical base,
but the later vector-path audit found larger transcription errors in the
deterministic negative spectra. Those are isolated in V51; see
[`V51_VECTOR_TRACED_NEGATIVE_SPECTRA_2026-08-11.md`](V51_VECTOR_TRACED_NEGATIVE_SPECTRA_2026-08-11.md).
