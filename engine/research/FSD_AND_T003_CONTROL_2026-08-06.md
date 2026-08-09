# V40 controlled pipeline comparison and T003 chart audit

Date: 2026-08-06

## Three matched outputs

V40 presents three outputs from the same decoded RAW frame, colour transform, black, gamma and 2383 observer:

1. Physical 5279: the V40 three-record emulsion, fast/mid/slow populations, DIR, MTF and published 48 µm RMS constraint.
2. Finite-Site Density (FSD): an independent finite-density architecture reconstructed from the local Silver Efex engine audit.
3. Deterministic no-grain: the same observer graph with stochastic sites replaced by expected density.

FSD is not merged into the physical 5279 model and is not described as a recovered Kodak recipe.

## FSD definition

`G = inverse_binomial_cdf(N, p, u) / N`

`Y_out = (1 - alpha) * Y + alpha * G`

Production comparison parameters:

- site count `N = 176`
- inverse-CDF table `512 × 512`
- native-pixel correlation sigma `0.597`
- strength `1.0`
- open-interval uniform samples only
- finite-site density formed after the deterministic observer in the IEC 61966-2-1 signal domain
- deterministic signal-domain opponent colour held fixed; only the density excursion is gamut-limited
- no independent RGB impulses

The open-interval rule is essential. An early table endpoint allowed `u = 1`, producing rare, very large impulses like the withdrawn V39 failure.

## Single-frame calibration

Calibration used T031 frame 132 only. T002 and T007 remain holdouts.

| Metric vs deterministic baseline | Physical V40 | FSD |
| --- | ---: | ---: |
| Luma RMS | 0.01835963 | 0.01820251 |
| p99.9 absolute residual | 0.1003182 | 0.1048896 |
| High-pass RMS, sigma 1 | 0.01260623 | 0.01252579 |
| Lag-1 x | 0.433395 | 0.438079 |
| Lag-1 y | 0.444060 | 0.438308 |
| Opponent residual RMS | 0.0042702 | 0.0015189 |
| Radial low/mid/high | 0.01255 / 0.24062 / 0.70846 | 0.01148 / 0.23191 / 0.72019 |

FSD is close to physical V40 in luma morphology and robust tail amplitude. Its much lower opponent residual is intentional: FSD does not model three dye records or interlayer chemistry.

An initial FSD implementation formed scalar density in display-linear luma and
then compressed chroma when a stochastic result approached the RGB gamut
boundary. The later sRGB transfer made this stochastic chroma rescaling visible
as sparse orange/primary impulses in dark warm pixels. It was rejected by the
native-frame release gate. The corrected control forms its scalar density in
the post-observer IEC 61966-2-1 signal domain and holds the existing opponent
field fixed. On the strongest T002 probe, isolated impulses above both 0.06 and
0.08 fell to zero without blur or desaturation. This domain is part of FSD's
definition and is not a claim about 5279 negative chemistry.

## Deterministic graph audit

The generic V40 dual-observer graph evaluated a mean-only branch as `(negative_mean + mean_density - mean_density)` and passed through duplicate zero-delta branches. A reduced graph directly evaluates the same deterministic expectation and removes those cancellation paths. The generic and reduced graphs differ only by tiny floating-point cancellation residuals; the reduced graph is the correct definition of a no-grain baseline, not an approximation of the physical output.

## T003 DKC-Pro audit

Source: `NJARAW_S001_S001_T003.MOV`, ProRes RAW HQ, 5760 × 4320, 24000/1001 fps. Frame 160 was selected from the stable chart interval. The target is a DGK Color Tools DKC-Pro 5 × 7 with 18 published CIELAB patches.

The container identifies Panasonic DC-GH7, ISO 500 and fixed 5500 K white balance. The Bayer metadata at frame 160 independently exposes CCT 5500, red factor `2.4228515625`, blue factor `1.4375` and a 3×3 colour matrix. The standard 128-bit extended-linear AVFoundation decoder requests no override, so the remaining warmth is not missing white-balance metadata.

Neutral patches 2–5 in the Apple standard extended-linear BT.2020/D65 decode measured:

- mean R/G: `1.1723949`
- mean B/G: `0.7482520`
- mean D65 delta u-prime/v-prime: `0.0273480`
- maximum D65 delta u-prime/v-prime: `0.0280940`

The neutral series is consistently warm, not green. This rejects the hypothesis that every supplied clip shares one fixed green RAW-decoding error.

The manufacturer recommends patches 2–4 for RAW white balance. Those patches measure mean R/G `1.17467` and B/G `0.74491`; their individual ratio spans are `1.91%` and `1.20%`. This does not show an exposure-dependent green drift. Diagnostic neutral gains would be `[0.85130, 1.0, 1.34245]`, but they are not applied to the As Shot baseline.

Six additional boundaries were found:

- Gray-scale gamma is not identifiable from this frame. Measured Y/reference Y for patches 2–5 is `[4.2590, 4.0592, 3.8768, 3.4167]`, a `0.31789` stop span. Since patch lightness and left-to-right position are perfectly correlated, input nonlinearity cannot be separated from an illumination or reflection gradient.
- The RAW white patch is extended-linear `[4.1955, 3.5471, 2.5679]`, so it is not clamped at unit display white. The official V-709 witness reaches 1.0 in one channel of patch 1.
- Saturated cyan patch 10 produces a small negative red component (`-0.01524`) in V40's intermediate Rec.709-like film-light basis. The combined signed-basis 5279 record exposures would nevertheless all be positive (`[0.07428, 1.38148, 1.68329]`). V40's current pre-record basis clip raises the first record exposure by `19.29%` while changing the other two by less than `0.05%`; in deterministic output this moves cyan by delta u-prime/v-prime `0.00226` in scan and `0.00203` in projection. This is a genuine gamut-boundary model choice, not a RAW or highlight clip. It must be tested independently from V39's rejected stochastic model before any production change.
- The DKC-Pro is not an equal-height 3×6 grid: a printed title strip sits above patches 7–12. The first audit mistakenly sampled that strip and falsely made the synthetic primaries look catastrophically unstable. The sampling geometry was withdrawn and replaced with row-specific native-resolution interiors; patch MAD is now generally `1.4–5.2%` per channel rather than the former text-contaminated values.
- Under an explicitly diagnostic D50/Bradford assumption after that correction, synthetic primaries 7–12 have median absolute hue residual `10.69°` and median chroma ratio `0.663`, while natural patches 13–18 measure `7.75°` and `0.923`. Cross-group 3×3 fits generalize moderately in hue: training on naturals and testing primaries gives `5.30°` median / `10.11°` maximum; the reverse gives `6.69°` / `10.41°`. A camera/input characterization residual is therefore plausible—not disproved—but the unknown outdoor SPD and unspecified reference illuminant still make a production matrix unjustified.
- Patch 6 is a published `L*=23` dark gray, not a zero-reflectance black trap. It cannot identify sensor black, lens flare or the final display black pedestal. Those remain separate pipeline tests.
- The neutral channel ratios drift slightly across the row (patches 2–4 span `1.91%` in R/G and `1.20%` in B/G), but brightness and horizontal position change together. This is a bound on the possible error, not evidence for a channel-wise nonlinear correction.

It does not identify a new camera matrix, black offset or white balance. The chart was shot under directional outdoor illumination, so illuminant SPD, as-shot metadata, lens transmission, target angle and surface reflection are not separately identifiable. V40 therefore retains the Apple standard input transform and as-shot metadata, with no global minus-green or magenta correction.

A native-frame boundary audit shows why this must not be described as a global
failure. On representative T002/T007/T031 frames, only `0–0.0054%` of pixels
with all three combined record exposures above `0.01` change by more than 1%
when the intermediate basis is clipped. T003 rises to `0.0696%`, concentrated
in the chart's saturated colours. Most other negative basis values live near
the decoded black/noise boundary and already produce non-physical negative
record exposures. The correction target is therefore a narrow saturated-colour
gamut mapping, not wholesale restoration of V39's signed stochastic path.

## T003 through the deterministic V40 colour chain

The corrected neutral samples were also passed through the deterministic
Period 2K and normal 2383 branches, with stochastic grain disabled. The real
chart's maximum neutral-group delta u-prime/v-prime grows from `0.001103` at
the Apple input to `0.001928` in the scan and `0.001731` in projection (ratios
`1.75×` and `1.57×`). That observation alone is still spatially confounded.

Two synthetic controls remove the chart gradient while retaining the four
measured exposure levels:

- Constant D65-neutral RGB remains stable: maximum delta u-prime/v-prime is
  `0.0001735` in scan and `0.0001555` in projection. There is no evidence that
  V40 creates a shared neutral-to-green crossover.
- Constant measured warm chromaticity is exposure dependent: maximum delta
  u-prime/v-prime becomes `0.002530` in scan and `0.002204` in projection;
  brightest-to-darkest endpoint distances are `0.004294` and `0.003620`.

This is a real property of the present model, not the outdoor chart geometry.
Colour negative stocks can reproduce off-neutral exposures nonlinearly because
the three records and dye curves are not one scalar tone curve, so the existence
of the effect is plausible. Its magnitude is not yet validated for 5279. It is
therefore recorded as the next colour-model uncertainty—not corrected with a
grade or global matrix.

A temporal audit optical-flow tracked the corrected grid at frames 80, 100, 120, 140, 160, 180 and 200. Mean R/G stayed within `1.17467–1.18127`, B/G within `0.74491–0.74879`, gray scale span within `0.30381–0.32350` stops and log slope within `1.13733–1.14692`. This rejects a one-frame accident or transient reflection, but because the chart angle and ordered gray geometry remain similar, it still cannot separate response nonlinearity from a stable spatial illumination/reflection term.

The decisive retest is fixed exposure under uniform D65 and tungsten illumination, with the chart shot in its normal orientation and rotated 180 degrees, plus exposure brackets. A slope that follows spatial orientation is illumination; a slope that remains attached to patch reflectance warrants a RAW-linearity investigation.

Recommended capture protocol:

1. Fill at least one third of the frame width with the chart, keep it normal to
   the lens, and remove hands/foliage that can add coloured bounce.
2. Use one measured high-quality D65 source and one tungsten source separately;
   record their SPD/CCT and keep ISO, shutter, aperture, focus and metadata WB
   fixed within each series.
3. Record normal and 180-degree chart orientations at the same position, then
   bracket exposure at `-2, -1, 0, +1, +2` stops without changing ISO.
4. Record a capped-lens frame for the decoded sensor-offset boundary and a
   scene black trap for lens/room flare. The DKC-Pro L*=23 patch is neither.
5. Do not derive a production WB, gamma or matrix until the orientation pair
   separates spatial illumination from patch response and both illuminants
   give a compatible camera characterization.

Reference: DGK Color Tools, *Complete Guide to the DKC-Pro Color Chart* — https://dgkcolor.tools/wp-content/uploads/2019/09/Complete-Guide-to-the-DKC-Pro-Color-Chart_Final.pdf
