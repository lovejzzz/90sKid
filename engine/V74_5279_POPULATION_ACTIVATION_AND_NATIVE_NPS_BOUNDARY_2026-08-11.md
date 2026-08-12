# V74 5279 population activation and native-NPS boundary — 2026-08-11

## Decision

V74 is research-only. It changes no pixels; V72 remains the current image
profile.

The fast/medium/slow architecture is physically useful and internally
consistent, but its current numbers are not a recovered 5279 coating formula.
The public H-D curves cannot identify them because the engine partitions and
then exactly recombines the published mean. The public 48 µm RMS curves cannot
identify them either because a record/exposure normalization forces the summed
field back to those curves.

The audit also confirms a more important native-resolution fact: at 5760-pixel
width, the current model predicts and produces approximately `5.1–7.0×` more
single-pixel density RMS than remains after a 48 µm aperture. The old 1920-wide
conformance strips accurately validate the published aperture RMS, but they do
not preserve this native pixel-to-aperture ratio because sub-population clouds
rasterize differently at one-third scale.

This does **not** prove that the native texture is too strong or wrong. It proves
that the visually decisive native NPS remains a prior even when the Kodak RMS
gate passes.

## What was revisited

The audit reconciles four layers of earlier work:

1. V14/V21 use a same-era Kodak patent as a structural witness for multiple
   speed populations.
2. V24 selected a visually finer candidate after V23 looked like early CCD or
   16 mm.
3. V48 removed raster anisotropy and represented continuous site/pixel
   integration isotropically.
4. V50 recovered the actual vector paths of the 5279 48 µm RMS graph and noted
   that the finite-site model does not independently predict its amplitude.

All four statements remain true. What was missing was one calculation that
showed their ownership simultaneously at native width.

## Active three-population prior

The current population centres are

\[
c_{r,p} = c^{fast}_r + [0,\;0.5,\;1.3]_{p},
\]

with a record-specific logistic transition width. For log exposure (x_r),

\[
p_{r,p}(x)=\frac{1}{1+\exp[-(x_r-c_{r,p})/w_r]}.
\]

The three shared capacity fractions are `126:149:161`, or approximately
`0.289 / 0.342 / 0.369`. These values and offsets come from a representative
Kodak multilayer patent example, not a disclosed 5279 recipe.

### Mean ownership

The engine obtains the published record density first, then partitions its net
density with normalized weights

\[
q_{r,p}=\frac{p_{r,p}C_p}{\sum_k p_{r,k}C_k}.
\]

Summing the three layers therefore returns the same published H-D mean by
construction. This is desirable—it prevents a generic patent from overriding
5279 data—but it also means neutral H-D cannot validate the offsets, widths or
capacity fractions.

### Variance ownership

Before DIR and final normalization, the 48 µm variance contribution is
approximately

\[
V_{r,p}=K^{48}_{r,p}\,C_{r,p}^{2}\,p_{r,p}(1-p_{r,p}),
\]

where (K^{48}) includes finite site count, the five size-class kernels and
the 48 µm aperture. The summed prediction is multiplied by

\[
a_r(x)=\frac{\sigma^{Kodak}_{48,r}(x)}
{\sqrt{\sum_p V_{r,p}(x)}}.
\]

Consequently the Kodak curve identifies the final marginal amplitude, not the
internal population law.

## Exposure-dependent layer behaviour

The active prior produces a coherent qualitative progression:

| Exposure | Fast variance share | Medium variance share | Slow variance share |
|---|---:|---:|---:|
| logE −4 | 78–84% | 14–18% | 3–4% |
| logE −2 | 59–70% | 22–30% | 8–11% |
| logE −1 | 29–45% | 28–31% | 28–40% |
| logE 0 | 14–26% | 20–21% | 53–65% |

Thus dark exposure is dominated by the fast/coarser population, while higher
exposure progressively transfers variance to slow/finer populations. This is
the physical idea behind “shadow grain differs from highlight grain.” It is a
plausible mechanism, not a measured 5279 layer-share curve.

Mean-density shares are less extreme than variance shares: no single
population exceeds about `63.5%` over the published exposure domain. Grain
therefore cannot be inferred by looking only at which layer carries the mean
density.

## Native spatial result

At 24.9 mm mapped to 5760 pixels, one reference sample is `4.3229 µm` wide.
The active effective population cloud radii span about `1.71–4.47 µm`. These
are **effective correlation radii**. Earlier code copied representative ECD
ratios into reference-pixel values and then applied a scale; that was not a
physical conversion from a measured 5279 crystal diameter to dye-cloud radius.

The native single-pixel / 48 µm RMS ratios for fast, medium and slow populations
are:

| Record | Fast | Medium | Slow |
|---|---:|---:|---:|
| red/cyan | 4.95× | 6.57× | 7.65× |
| green/magenta | 4.66× | 6.72× | 7.90× |
| blue/yellow | 5.40× | 6.36× | 7.42× |

The slow population is spatially finer: the large aperture removes more of its
point-sample variance. As slow layers dominate at higher exposure, the combined
native/48 µm ratio rises from approximately `5.1–5.7×` in deep exposure to
about `6.9–7.0×` near logE 0.

This is the current model's precise meaning of “coarser shadows, finer
highlights.”

## 5760-wide realization gate

A new 5760×192 uniform strip tests logE `−3`, `−1` and `0`. It forms the actual
45-class stochastic negative and independently measures the 48 µm aperture.

| logE | Native unfiltered Sigma-D R/G/B | Native / 48 µm ratio R/G/B |
|---:|---|---|
| −3 | 0.07364 / 0.09938 / 0.22541 | 5.36 / 5.25 / 5.74 |
| −1 | 0.04428 / 0.05317 / 0.12521 | 6.42 / 6.29 / 6.58 |
| 0 | 0.04603 / 0.04757 / 0.10044 | 6.88 / 6.91 / 6.93 |

The maximum 48 µm target error is `1.55%`; the maximum analytic-versus-realized
native-ratio error is `1.53%`. Both pass the 3% statistical gate.

The unfiltered values are negative-record density at a 4.32 µm model sample.
They are not display RGB noise: negative MTF, dye spectra, 2383/scan aperture,
display resampling and observer grain management still follow. Nevertheless,
this is the high-frequency reservoir from which visible motion is formed.

## Why the previous 1920-wide gate was insufficient for this question

The established physical-RMS audit uses a 1920-wide strip so the aperture has
non-degenerate support at tractable cost. It measured an unfiltered/48 µm ratio
near `3×`. At that scale several cloud radii fall below one raster pixel and
the site kernels are re-integrated at a different grid.

That gate remains valid for its declared purpose: it proves aperture-weighted
marginal RMS. It cannot prove the 5760-native NPS. The new native strip does not
replace the existing gate; it prevents us from using the narrower result to
make a broader texture claim.

## The V24 provenance matters

The active morphology still inherits V24 `fine35_integrated`. V24 was selected
from perceptual T020/T032 candidates after V23 read as early CCD or 16 mm. It
reduced large-cloud probability and changed observer opponent-grain
integration. It was never fitted to a measured 5279 Wiener spectrum.

With the published 48 µm RMS held fixed, the active V24 morphology raises the
native single-pixel/48 µm ratio by about `19–23%` relative to V23 across the
published exposure domain. In spatial terms it is **finer**, not more 16 mm-like:
it moves variance toward higher native frequencies. But the larger point-sample
fluctuation can look harsher or more actively “boiling” if display integration
does not remove the corresponding frequencies correctly.

This finding does not justify reverting to V23. V23 was another hypothesis,
not measured truth. It does require us to stop calling the V24 NPS an objective
5279 result merely because its 48 µm RMS passes.

## The normalization multipliers expose the missing model

Across logE `−4..0`, the unscaled finite-site prediction requires these
multipliers to reach Kodak's measured RMS:

| Record | Minimum | Maximum | Max/min variation |
|---|---:|---:|---:|
| red | 1.07× | 3.16× | 2.96× |
| green | 1.24× | 5.41× | 4.35× |
| blue | 3.07× | 11.80× | 3.84× |

The large blue multiplier is not a processing failure—the final blue 48 µm
curve is accurate. It is evidence that the current site counts, activations and
cloud kernels do not independently predict blue-record granularity.

A site-count ablation makes the non-identifiability explicit. Scaling every
effective site population from `0.25×` to `4×` changes unnormalized variance
and higher-order tails substantially, yet the exposure/record multiplier returns
all versions to the same published 48 µm RMS. Marginal RMS therefore cannot
choose the site count or tail distribution.

## Accuracy boundary

The current algorithm is accurate where it claims measured authority:

- summed neutral H-D;
- processed-stock MTF;
- per-record 48 µm RMS versus exposure;
- physical 35 mm frame-width mapping;
- density-domain formation rather than a display overlay.

It remains hypothetical in precisely the places that decide “organic” texture:

- the complete exposure-dependent NPS;
- fast/medium/slow speed offsets and capacity shares;
- effective site counts and standardized tail distribution;
- physical dye-cloud radii;
- cross-record auto/cross spectra;
- scanner contribution separated from negative structure.

The right response is not to weaken grain until it looks pleasant. It is to
carry the current NPS as a named hypothesis and seek native, calibrated uniform
5279 scans at multiple exposures. A frequency-resolved Wiener spectrum, or a
sufficient multi-aperture series under an explicitly selected spectrum family,
could then replace the V24 visual selection with measurement.

## Reproducible artifacts

- audit code: `src/audit_v74_population_activation_ownership.py`
- machine-readable result:
  `research_runs/v74_population_activation_ownership_audit.json`
- image profile: unchanged V72

| Artifact | SHA-256 |
|---|---|
| `src/audit_v74_population_activation_ownership.py` | `6beee0017320710d08fa3f105a2e52fb60c074f88344fbc1a4dd579b00ea3193` |
| `research_runs/v74_population_activation_ownership_audit.json` | `1b6b7ae17558c85f00ef73b1f426b12df61691ce3d8b4eaac5d8e289cf44c209` |

## Primary sources

1. Eastman Kodak Company, [*KODAK VISION 500T Color Negative Film 5279 / 7279*, H-1-5279](https://125px.com/docs/motionpicture/kodak/5279.pdf), neutral H-D, processed MTF and 48 µm diffuse RMS.
2. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en), multiple speed populations and representative architecture; not a 5279 recipe.
3. Eastman Kodak Company, [*The Essential Reference Guide for Filmmakers*](https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf), graininess, granularity, aperture and system magnification.
4. J. H. Altman, Kodak Research Laboratories, [“The Measurement of rms Granularity,” *Applied Optics* 3(1), 35–38 (1964)](https://doi.org/10.1364/AO.3.000035), on aperture dependence.
5. R. M. Pointer, Kodak Limited Research Division, [“A Study of Colour-Film Granularity and Print-Image Graininess,” *Journal of Photographic Science* 41(2) (1993)](https://doi.org/10.1080/00223638.1993.11738479), on colour-negative Wiener spectra and print-image graininess.
6. ISO 10505:2009, [*Photography — Root mean square granularity of photographic films — Method of measurement*](https://www.iso.org/standard/50747.html); its scope does not include Wiener-spectrum estimation.
