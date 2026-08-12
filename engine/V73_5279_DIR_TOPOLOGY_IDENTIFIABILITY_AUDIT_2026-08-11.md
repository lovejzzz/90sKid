# V73 5279 DIR topology identifiability audit — 2026-08-11

## Decision

V73 is a research-only audit. It changes no image profile: V72 remains the
current evidence-minimal release.

The active 5279 DIR mechanism has legitimate physical ownership. Mobile
developer inhibitor can act on adjacent colour units, alter separation gamma
relative to white-light gamma, and sharpen local dye-image boundaries. It is
therefore not the same unsupported operator as the direct record-mix matrix
withdrawn in V72.

Its **specific implementation is nevertheless only a prior**. The current code
connects every one of the 54 possible cross-record fast/medium/slow source and
receiver pairs. Period Kodak multilayer examples instead show selective,
asymmetric DIR species and placements. No public 5279 document found in this
audit identifies its separation-wedge gamma ratios, causer/receiver layers or
inhibitor transport distances. V73 consequently retains the restrained V72
mechanism but does not promote its dense tensor as a recovered 5279 formula.

## Why this needed to be revisited

The earlier work got the broad architecture right:

1. V21 moved DIR from a post-summed image adjustment into fast/medium/slow
   development before record summation.
2. V34 removed deterministic **intralayer** developer adjacency because Kodak's
   published processed-stock MTF already includes that response.
3. V39 retained zero-mean stochastic population coupling before the published
   48 µm RMS normalization.
4. V70 showed that the remaining stochastic DIR term contributes almost none
   of the current same-position cross-record covariance.
5. V71 showed that deterministic cross-record DIR is small, physically distinct
   from direct record mixing, and moves separation gamma in the expected
   direction.

What had never been written out was the complete topology implied by the
constants. “Population-domain DIR” sounded more identified than it actually
was. V73 expands that hidden prior and measures its complete practical effect.

## What the primary evidence says

### Stock-specific 5279 evidence

H-1-5279 supplies neutral sensitometric curves, processed-stock MTF, spectral
sensitivity, net dye-density spectra and diffuse RMS granularity measured with
a 48 µm aperture. It does not publish:

- colour-separation versus white-light wedge gammas;
- a DIR compound list or per-layer coverage;
- barrier/scavenger placement;
- inhibitor diffusion distances;
- joint spatial covariance between the three developed records.

Neutral H-D and marginal RMS therefore cannot solve a DIR transport tensor.

### Period multilayer architecture evidence

Kodak US 5,314,793 states that a dye-forming unit can contain two or three
speed-differentiated emulsion layers, normally with the fastest layer farthest
from the support and the slowest nearest it. This supports the existence and
ordering of populations; it does not transfer the patent example's recipe to
5279.

Kodak US 5,455,150 is especially useful as a falsification witness for a
universal topology. Its worked multilayer negative places different DIR
couplers in medium/high red, medium/high green and low/high blue layers, with
different coverages and species. The lowest red and lowest green examples have
no stated DIR coupler, while the lowest blue does. It also includes interlayers,
BAR couplers, masking couplers, developer scavengers and a small off-hue cyan
coupler in the blue layers. This proves that real layer chemistry can be
selective and asymmetric.

Kodak US 6,686,136 defines the relevant observable cleanly. A mobile inhibitor
released during development interacts with adjacent layer units and retards
development in other colour records. It defines `gamma ratio` as separation-
exposure gamma divided by white-light gamma and notes that the ratios need not
be equal among records. Its preferred low-interimage examples are scan-oriented
consumer elements, not 5279; their numeric limits cannot be adopted here.

## Current tensor exposed

For destination record (d), source record (s), receiver population (j)
and source population (i), the active deterministic coefficient is

\[
T_{d,s,j,i} = 0.085\,R_{d,s}\,P_{j,i}\,G^{release}_i\,G^{receiver}_j.
\]

The machine-readable audit expands all coefficients. Its structural summary is:

| Quantity | Active V72 prior |
|---|---:|
| Nonzero cross-record population edges | 54 / 54 |
| Adjacent-record / remote R-B mean transport | 2.6389× |
| Source share: fast / medium / slow | 33.48% / 41.32% / 25.21% |
| Receiver share: fast / medium / slow | 29.67% / 43.76% / 26.58% |

The physical B-G-R order is represented only coarsely: R-G and G-B transport is
about 2.64 times the remote R-B path, but every population talks to every
population. The numerical restraint is real; the selectivity is not.

At the project's fixed 24.9 mm / 5760 px film mapping, the source-population
Gaussian sigmas are:

| Population | Sigma | FWHM |
|---|---:|---:|
| fast | 20.75 µm | 48.86 µm |
| medium | 13.40 µm | 31.56 µm |
| slow | 8.21 µm | 19.34 µm |

These are model transport ranges, not measurements of 5279. The fast FWHM's
numerical proximity to Kodak's 48 µm granularity aperture is coincidental: one
is an assumed inhibitor-field width, the other an instrument aperture used to
integrate density variance.

## Deterministic separation audit

The audit central-differences uniform fields at log exposures `-3.0`, `-2.5`,
`-1.0` and `0.0`, with V72 identity direct record formation held fixed. It
compares the current DIR strength to exactly zero interimage DIR.

At developed Status-M record density:

- maximum absolute off-record derivative is `0.00041723 D/logE`;
- maximum separation/neutral gamma-ratio change is `0.00086358`;
- the current local gamma ratios span approximately `1.0000–1.00086`;
- zero DIR returns approximately identity ratios, within float32 derivative
  resolution;
- maximum neutral-gamma change between the two conditions is `0.00017881`,
  consistent with the intended neutral-trajectory preservation plus finite
  difference/float32 resolution.

The much larger `0.03880` maximum off-diagonal derivative at **printer density**
must not be attributed to DIR. That stage already integrates the real net
dye/mask spectra through printer receivers, so spectral unwanted absorption and
mask compensation remain cross-channel even when DIR is zero. This confirms
V71's ownership separation.

The result reproduces V21's old `~0.00041 D` bound with the current V72 profile.
The mechanism is not accidentally large; if anything, its stock-specific colour
effect is too weakly identified to tune from normal pictures.

## Same-RAW practical ablation

T020 frame 0 was decoded once through the official Panasonic/Final Cut Pro RAW
boundary, reduced to 1440×1080 and rendered deterministically with no stochastic
grain. Current DIR was compared with zero interimage DIR.

| Observer | Linear RGB MAE | OKLab P95 | RGB absolute P99 | Changed 12-bit components |
|---|---:|---:|---:|---:|
| 2383 projection | 0.00004458 | 0.001009 | 0.001477 | 6.27% |
| managed scan | 0.00003230 | 0.000934 | 0.001052 | 4.45% |

Median OKLab difference is zero in both branches. The term is spatially and
chromatically localized rather than a global saturation or cast control. A
normal camera frame cannot tell us whether the nonzero edge pixels are the
correct 5279 response; only a controlled separation/neutral measurement can.

## What was almost mistaken for evidence

Three earlier facts remain valid but do not determine the coefficients:

1. **MTF above 100% supports developer adjacency, not this cross-record tensor.**
   V34 correctly lets the published processed MTF own deterministic intralayer
   sharpness once. The neutral MTF graph cannot solve interimage colour
   transport.
2. **48 µm RMS constrains marginal variance, not DIR topology.** Stochastic DIR
   is followed by per-record RMS normalization, so many coupling models can pass
   the same Kodak curves.
3. **A pleasing local-colour or grain change is not a wedge measurement.** The
   real-frame delta is well below a creative grading move and can be confounded
   by scene illuminant, RAW white balance, dye spectra and observer transforms.

## Release boundary

The evidence-minimal decision is deliberately asymmetric:

- the unidentified direct dye-record mix was removed in V72 because it had no
  distinct physical observable in the model and duplicated other cross-channel
  mechanisms;
- DIR remains because it owns a real, distinct development mechanism supported
  by period Kodak chemistry;
- its dense 54-edge topology is explicitly classified as a restrained prior,
  not as “the 5279 matrix”;
- zero DIR, a sparse patent-shaped tensor and any retuned diffusion scale are
  all rejected as release changes until stock-specific measurements discriminate
  among them.

The next useful experiment is therefore not another picture-based saturation
tweak. It is a measurement design for processed 5279 colour-separation and
white-light step wedges, plus uniform patches at several exposures for native
auto/cross spectra. That data would jointly constrain gamma ratio, population
transport and stochastic covariance without asking an artistic image to answer
a chemical question.

## Reproducible artifacts

- audit code: `src/audit_v73_dir_topology_identifiability.py`
- machine-readable result:
  `research_runs/v73_dir_topology_identifiability_audit.json`
- image profile: unchanged V72

| Artifact | SHA-256 |
|---|---|
| `src/audit_v73_dir_topology_identifiability.py` | `3b25a80d6ffb03b91ce4fbf04641fda9475adfa20c09b46e1f89e2172238baf1` |
| `research_runs/v73_dir_topology_identifiability_audit.json` | `226e3e7420cdd5375127cd16dc7c884c529683c017bd733384714b24c425eaac` |

## Primary sources

1. Eastman Kodak Company, [*KODAK VISION 500T Color Negative Film 5279 / 7279*, H-1-5279](https://125px.com/docs/motionpicture/kodak/5279.pdf).
2. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en), especially the two/three-speed layer architecture and support order.
3. Eastman Kodak Company, [US 5,455,150, *Color photographic negative elements with enhanced printer compatibility*](https://patents.google.com/patent/US5455150), especially the explicit selective multilayer DIR/coupler recipe in Example 2. This is an architecture witness, not a 5279 formula.
4. Eastman Kodak Company, [US 6,686,136 B1, *Color negative film element and process for developing*](https://patents.google.com/patent/US6686136B1/en), especially mobile adjacent-layer inhibition and the separation/white-light gamma-ratio definition.
5. Eastman Kodak Company, [US 5,298,376, *Photographic silver halide material with improved color saturation*](https://patents.google.com/patent/US5298376A/en), on DIR placement, barrier layers and interimage saturation.
