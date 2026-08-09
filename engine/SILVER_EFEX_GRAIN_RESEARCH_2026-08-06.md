# Nik Silver Efex grain research

Date: 2026-08-06
Status: local archive and ARM64 lookup/mix reconstruction complete; controlled UI black-box confirmation pending
Scope: possible lessons for the 5279 reconstruction, not a claim about DxO's proprietary implementation

## Bottom line

Silver Efex supports the project's central premise more strongly than a generic noise-overlay product: the stock/type selects a measured spatial model, and a tone-conditioned finite-particle realization replaces/mixes the pixel density. It does not merely add Gaussian noise. DxO's public documentation also explicitly links grain scale/hardness to perceived detail and sharpness.

The installed engine discloses enough compiled structure to reconstruct the central lookup and mixing equations, but Silver Efex is still a monochrome still-image system. It cannot supply the missing three-record colour covariance, 5279 sensitometric particle populations, or motion-picture frame-to-frame statistics.

## Evidence ladder

### 1. Official, public evidence

- Silver Efex exposes a branded film-grain selector plus **Intensity** and **Grain Size**. DxO describes the selectable simulations as known for fidelity, behaviour, and realistic appearance.
- Color Efex documentation is more explicit about provenance: its branded grain models are based on real colour-negative and slide stocks analyzed by DxO Labs, distinct from the older generic grain filters.
- DxO states that the branded grain filter simulates grain only, not the film's colour and contrast rendering. This separation is directly relevant to our baseline-film policy: stochastic morphology, sensitometry/colour, and artistic grading should remain separable.
- The legacy generic engine describes grain in terms of grain elements per pixel and hardness. Coarser grain increases apparent detail/sharpness; finer grain feels more natural.
- DxO's film-science page gives the strongest public implementation clue: its calibrated profiles do not use universal Gaussian-noise characteristics. DxO derives complex grain matrices from silver-halide crystals in calibrated test images and analyzes how the result differs in shadows, midtones, and highlights. This establishes tone-conditioned measured morphology as a design principle, though it still does not disclose the matrices or renderer.

Official sources:

1. [Nik Silver Efex user guide](https://userguides.dxo.com/nikcollection/en/silver-efex/)
2. [Nik Color Efex user guide](https://userguides.dxo.com/nikcollection/en/color-efex/)
3. [Nik Silver Efex product page](https://www.dxo.com/en/nik-collection/nik-silver-efex/)
4. [DxO — The science of film](https://www.dxo.com/en/technology/science-of-film)

### 2. Read-only evidence from the installed Nik Collection 8 package

The standalone app at `/Applications/Nik Collection 8/Nik 8 Silver Efex.app` is a universal x86_64/ARM64 Mach-O shell. Its dynamic-link table shows that image processing is delegated to the shared `DxOCorrectionEngine.framework`; the app executable mainly exposes the Qt/QML interface models (`FilterParametersModelGrainType` and `FilterParametersModelRealGrain`). The algorithm is compiled, not shipped as readable source, so the following findings come from database records, exported symbols, embedded diagnostic strings and resources—not decompiled source-code reconstruction.

The local application database contains two different grain families:

- **Silver Efex / Film Grain (Branded)** — engine key `Grain`; 42 rows including `Original`.
- **Color Efex / Film Grain** — engine key `Film_Grain_1`; four generic presets.
- **Color Efex / Film Grain (Branded)** — engine key `Grain`; five colour-film entries.

Silver Efex branded dictionaries expose only:

```json
{
  "GrainType": "KodakTriX400",
  "GrainIntensity": 100.0,
  "GrainSize": 1.0
}
```

The Silver Efex UI schema confirms exact public control ranges: `GrainIntensity` is 0–200% with 100% default, and `GrainSize` is 1–10 with 1 default. Its `GrainType` entry is explicitly marked `blackWhiteOnly`. `GrainFilmFormat`, automatic sizing and random seed exist in the correction engine but are not exposed by this Silver Efex panel.

The current installed list includes Kodak TMax 100, TMax 400, TMax 3200, Tri-X 400, BW400CN, multiple Ilford/Adox/Agfa/Fuji/Foma/Rollei stocks, and several instant-film types. The stock identity is therefore not merely a label on one shared size slider; it is an input to an internal model.

All 41 named Silver Efex stocks in this installed database use the same preset values (`GrainIntensity = 100`, `GrainSize = 1`); only `GrainType` changes. Therefore the visible stock-to-stock differences at their defaults must come from data or logic selected by the stock identity, rather than hidden per-preset changes to the two exposed sliders.

The legacy generic Color Efex dictionaries expose a different parameterization:

```json
{
  "contrast": 50.0,
  "grainSliderSoftness": 0.0,
  "grainSliderStrength": 450.0,
  "protect_hilights": 10.0,
  "protect_shadows": 10.0
}
```

This confirms a meaningful architectural split between generic procedural grain and calibrated/branded models. It does **not** reveal how the branded models are computed; that part remains compiled or packaged inside the product.

Additional read-only strings in the installed DxO correction engine provide stronger implementation evidence:

- `GrainFilmFormat` with `24x36`, `Medium`, and `Large`
- `GrainSizeAuto`, described by the engine as computing an optimal grain size from film format and image size
- `GrainRandomSeed`, where zero disables randomization for backward compatibility
- errors referring to a grain-patch archive and extraction of named patches
- stock-specific assets such as `patch_KodakTriX400.tif` and `patch_KodakTmax400.tif`
- separate `opacityshadows`, `opacitymidtones`, and `opacityhilights` controls

Together these strings are strong local evidence consistent with a hybrid renderer: measured stock-specific grain patches or matrices, resolution/film-format-aware scaling, explicit randomization, and tone-region-dependent contribution. They do not prove the precise compositing law, patch-selection algorithm, or whether all of these controls are used by the current Silver Efex path, so those details remain hypotheses for black-box testing.

The compiled engine also names the processing stages and failure paths: `GrainPrecalculateFilter`, `GrainBlurAndMixFilter`, `FilmGrainModel`, `RandomizeGrainFromSeed`, rotated local patches, randomization from offsets, patch resize/downscale, and `PatchTexturisation_T`. Parameters adjacent to those stages include `uniformLookup`, `binomialLookup`, `blurWeights`, `grainStrength`, `imageSize`, and `originalWidth`. Internal assertions mention 512×512 and 256×256 intermediate buffers. This substantially narrows the architecture: a stock patch is loaded, transformed/randomized and rescaled; a precalculation stage uses uniform/binomial lookup data to form an image-conditioned grain field; a later stage blurs and mixes it with the image. The lookup construction and central mixing equation have now been reconstructed from the local ARM64 engine and are recorded below. The fixed buffer dimensions still do not, by themselves, prove the final visible tile period.

Other nearby strings mention coarse and fine luminance grain plus chrominance grain, as well as `grainsaturation` and `asymmetricgrain`. These may belong to shared Color Efex/FilmPack paths rather than Silver Efex's monochrome branded-grain filter, so they are recorded as investigation leads—not as Silver Efex facts.

### 3. What may be inferred, but is not yet proved

An early review of the original Nik release reported Nik's own description that the engine conditions grain on each pixel's exposure and constructs the image from grain instead of laying a noise texture over it. This is unusually consistent with both the current DxO science statement and the user's visual observation, but it is a secondary historical report rather than current implementation documentation. Source: [PhotographyBLOG's 2008 Silver Efex review](https://www.photographyblog.com/pages/reviews/reviews_nik_silver_efex_pro.php).

The most plausible useful properties to test are:

1. **Tone-conditioned amplitude** — whether variance changes across equal-area flat patches of different density.
2. **Tone-conditioned morphology** — whether the normalized power spectrum or autocorrelation changes with density, rather than only its amplitude.
3. **Signal formation versus overlay** — whether local mean, edge profile, or microcontrast changes when grain is enabled.
4. **Stock-specific NPS** — whether two film types differ after matching global RMS and nominal size.
5. **Resolution normalization** — whether grain size is defined in output pixels, physical image scale, or a resolution-aware internal coordinate system.
6. **Seed behaviour** — whether identical settings are deterministic, randomly renewed on export, or tied to image coordinates/content.
7. **Patch repetition** — whether autocorrelation or phase-correlation reveals a finite texture atlas, and whether randomization hides its boundaries.
8. **Format-aware scale** — whether the same source exported at several resolutions preserves an inferred physical grain size when `GrainSizeAuto` is active.

No conclusion on these points should be presented as fact until the black-box probes are measured.

### 4. Contemporary patch-based prior art (not Nik evidence)

A 2003-priority motion-picture grain patent describes a database of pre-established grain patterns, selection by luminance interval and random number, scaling, deblocking, blending and clipping. It is not assigned to Nik or DxO and must not be used as proof of Silver Efex's formula. It is useful because it documents the same broad implementation family suggested by the installed engine's patch/archive/resize/randomize/mix symbols—and also exposes the failure modes we must avoid: blockwise luminance decisions, repeat periodicity, boundary filtering, additive display-space blending and clipping. Source: [WO 2005/057936 family — database of film-grain patterns](https://patents.google.com/patent/AU2004298261B2/en).

## Local resource registry and measured stock patches

The installed resource archive, `/Library/Application Support/DxO/Nik Collection 8/Frameworks/data/dop.gpa`, is a `DGPA` 1.0 archive with 99 contiguous PNG payloads. Every payload is a 1000 × 1000 RGB8 image. A static 262-record engine registry maps rendering-profile names to resource IDs, categories and monochrome flags. Reproducible read-only extraction and measurement tools are in `src/extract_dxo_gpa_readonly.py`, `src/extract_dxo_rendering_registry.py`, and `src/analyze_dxo_grain_library.py`.

Confirmed registry/archive joins include:

| Silver Efex stock | Resource ID | Extracted patch |
|---|---:|---|
| Fuji Neopan Acros 100 | 1750 | `013_id1750_type14.png` |
| Ilford HP5 Plus 400 | 1752 | `018_id1752_type14.png` |
| Kodak Tri-X 400 | 1756 | `023_id1756_type14.png` |
| Kodak T-Max 100 | 1760 | `024_id1760_type14.png` |
| Kodak T-Max 400 | 1761 | `025_id1761_type14.png` |

The B&W patches are neutral or within one 8-bit code value across channels, so the Silver Efex path is not sourcing independent RGB speckle. Their morphology is stock-specific. On identical 512² FFT crops:

| Stock | Luma RMS | lag-1 correlation | skew | excess kurtosis |
|---|---:|---:|---:|---:|
| Neopan Acros 100 | 0.03008 | 0.242 | +0.080 | -0.060 |
| HP5 Plus 400 | 0.04782 | 0.301 | -0.233 | -0.219 |
| T-Max 100 | 0.03383 | 0.347 | -0.400 | +0.567 |
| T-Max 400 | 0.04898 | 0.357 | +0.163 | +0.045 |
| Tri-X 400 | 0.04732 | 0.416 | +0.158 | +0.258 |

This rules out a single universal Gaussian field controlled only by size and amplitude: after accounting for RMS, the spatial correlation and distribution shape still differ by stock.

## Reconstructed lookup equations

The following is reconstructed directly from the current installed ARM64 `DxOCorrectionEngine` slice. Addresses and constants are version-specific but make the findings independently checkable.

### Deterministic uniform lookup (confirmed)

The engine constructs a 256 × 256 float lookup using unsigned 32-bit integer hashing. For row `y` and each subsequent `x`:

```text
state = y × 1025
state = state XOR (state >> 6)
state = state × 1025

h       = state XOR (state >> 6)
h       = h × 9
h       = h XOR (h >> 11)
h       = h × 32769
U[y,x]  = (h AND 65535) / 65535
state   = state + 1025
```

This is a deterministic uniform-variate map, not the final grain texture and not Gaussian noise.

### Tone-conditioned binomial lookup (confirmed central law)

`GrainPrecalculateFilter` requires a 512 × 512 destination. It first builds cumulative `log(k!)` values through 2047, then constructs an inverse-binomial-CDF lookup. If normalized image density/luma is `p`, uniform variate is `u`, and `N` is the effective number of grain sites, the table represents:

```text
B(p,u;N) = inverse_CDF(Binomial(N,p), u) / N
```

The implementation uses `min(p,1-p)` and mirrors the result above 0.5. It directly accumulates a binomial recurrence for small expected counts and uses log-factorial/Stirling-domain evaluation for larger counts. The deterministic pseudo-random sequence used during table construction is:

```text
state = state × 1664525 + 1013904223     (uint32)
u     = state × 2^-32
```

`N` is derived piecewise from `grainSliderStrength` after `g = trunc((500 - grainSliderStrength)/5)`, then normalized by inverse image area using `originalWidth`, with a hard upper bound of 1,000,000. The exact slider-to-`N` compatibility mapping is less important than the statistical law:

```text
E[B]   = p
Var[B] = p(1-p)/N
```

Mean preservation and tone-dependent variance therefore emerge from a finite-site density model rather than from an added variance curve.

### Spatial blur weights (partially confirmed)

The engine evaluates and normalizes Gaussian weights equivalent to `w(k) ∝ exp(-0.5(k/sigma)^2)`. Assembly supports a scale term of the form:

```text
sigma² ∝ (size_parameter/100) × 1.5 × (1-softness)
         × min(image_width/originalWidth, 1)
```

The exact public-slider-to-internal-size mapping still needs a controlled UI sweep, so this relation must not be copied literally into the 5279 model yet.

## Reconstructed mixing equations

### Luma/density mix (confirmed)

The input luminance is:

```text
Y = 0.299R + 0.587G + 0.114B
```

Let `G` be the spatially filtered grain-bearing value from the stock/binomial path. The engine obtains `alpha` from grain strength and a tone taper `A(Y)`, then interpolates toward the stochastic density candidate:

```text
alpha = grainStrength × A(Y)
Y'    = (1-alpha)Y + alpha G
```

This is the decisive distinction from an overlay. Grain participates in constructing the rendered density/luma; an independent noise delta is not simply added at the end.

### Exact tone taper (confirmed)

```text
if Y < 0.2:
    A(Y) = ((((1811.956543Y - 876.202087)Y
              + 117.616173)Y + 0.764699578)Y + 0.25)
elif Y > 0.8:
    A(Y) = ((((1811.956543Y - 6371.624023)Y
              + 8360.749023)Y - 4855.216797)Y + 1054.385376)
else:
    A(Y) = 1
```

Representative values are about 0.25 at black, 0.484 at 0.05, 0.808 at 0.10, 0.971 at 0.15, 1.0 from 0.2 to 0.8, then a symmetric fall to about 0.25 at white. Grain contribution is deliberately reduced in the deepest shadows and highlights.

### Colour-preserving density change (confirmed shared-engine path)

For RGB use in the shared engine, chroma is transported deterministically around the new luma instead of receiving independent RGB noise:

```text
D_in  = 0.28 - (Y  + epsilon)^2
D_out = 0.28 - (Y' + epsilon)^2
C'i   = Y' + (Ci-Y) × D_out/D_in
C'i   = clamp(C'i, 0, 1)
```

For Silver Efex monochrome, `R=G=B=Y`, so this collapses to `R'=G'=B'=Y'`. The shared colour path changes density while preserving a deterministic relation to source chroma; it cannot generate isolated RGB impulses. This directly supports V40's removal of V39's duplicate high-frequency opponent-colour reinjection.

### Confidence boundary

- **Confirmed from local code/data:** stock→resource mapping, measured 1000² patches, 256² integer uniform lookup, 512² inverse-binomial lookup, LCG constants, Rec.601 luma, tone polynomial, luma interpolation and shared-engine colour transport equation.
- **Strongly inferred from data flow:** the exact ordering of transformed stock patch, uniform lookup and binomial lookup in every branded-grain path.
- **Still awaiting UI black-box confirmation:** public intensity/size slider mapping, seed renewal across repeated exports, automatic physical-size scaling, and whether every shared-engine branch is used by Silver Efex 8 rather than another Nik/DxO product.

## Controlled probe design

Prepared input:

`outputs/silver_efex_probe/gray_ramp_patches_16bit.tif`

The 2048 × 2048, 16-bit TIFF contains a continuous upper ramp and 16 constant lower patches. The experiment will keep conversion and finishing controls neutral, apply one branded grain at a time, and export losslessly.

Minimum test set:

- Original/no grain control
- Kodak TMax 100
- Kodak TMax 400
- Kodak Tri-X 400
- one coarse high-speed stock
- two repeated exports with identical settings

Measurements:

- per-patch mean, RMS, skew, kurtosis, and extreme-tail rate
- radial and directional noise-power spectrum
- autocorrelation length and anisotropy
- edge-spread/MTF change relative to the no-grain control
- cross-patch normalization to distinguish amplitude scaling from morphology changes
- bit-identical and correlation comparison between repeated exports
- phase-correlation and periodicity search for repeated patch structure
- resolution sweep with constant crop and constant film-format setting
- block-boundary and periodicity maps to reject 8×8/256/512 tiling artefacts

## Evidence-bounded working model

The narrowest algorithmic model consistent with the confirmed code and the remaining ordering uncertainty is:

```text
Pstock            = measured grain patch/matrix selected by GrainType
s                 = scale(image dimensions, film-format state, GrainSize)
Pseed             = randomize(offset, rotation, seed, resize(Pstock, s))
u(x)              = mapped uniform variate from Pseed/uniformLookup
G(x)              = inverse_CDF(Binomial(N, Y(x)), u(x)) / N
Gblur(x)          = normalized spatial filtering of G using blurWeights
alpha(x)          = GrainIntensity × A(Y(x))
Yout(x)           = (1-alpha(x))Y(x) + alpha(x)Gblur(x)
```

The stock-patch-to-uniform-map ordering remains an inference. The inverse-binomial law, tone taper and final interpolation are confirmed. The public UI test is now primarily needed to map sliders, seed behaviour and resolution normalization, not to decide whether the core is an additive overlay.

The likely perceptual advantage over ordinary noise overlays comes from the combination rather than one trick: real non-Gaussian morphology, a density/exposure-conditioned local response, physical-size normalization, and random patch realization. The result can change apparent edge detail because the local image and the grain-bearing field are mixed together; a uniform independent RGB noise layer cannot reproduce that relationship.

## Relevance to the 5279 pipeline

Safe lessons for a future version:

- Keep stock morphology separate from intensity and viewing scale.
- Couple apparent sharpness to the stochastic image-formation stage, not to a later sharpening slider.
- Audit flat-field RMS and NPS as a function of density, not at one middle-gray point.
- Treat generic grain and film-calibrated grain as different model classes.
- Define morphology in an emulsion/film coordinate system and derive output-pixel scale from image dimensions, rather than fixing grain radius in pixels.
- Make random seed explicit and reproducible for scientific comparison. In motion-picture film, each frame samples a different physical area of emulsion, so its microscopic realization is new; model that as adjacent, non-overlapping film coordinates rather than as a display-space overlay refresh.
- Replace any post-image additive-grain concept with finite-particle density realization inside each emulsion layer.
- Keep chroma stochasticity limited to physically coupled dye-layer density covariance; never synthesize independent red/green/blue impulses.
- Apply gate weave and scanner motion to the already formed film image and its grain together. Do not move or refresh a noise layer independently of the image.

Unsafe transfers:

- Do not copy monochrome Silver Efex grain into RGB channels.
- Do not infer 5279 layer covariance from a black-and-white result.
- Do not infer motion behaviour from a still-image engine.
- Do not tune V40 by eye against Silver Efex; V40 remains the evidence-bounded repair of V39.

## Decision

Silver Efex confirms the architectural direction for V41, but not its 5279 constants. V41 should generalize the finite-site law per 5279 emulsion record:

```text
D_l(x,t) = inverse_CDF(Binomial(N_l(E_l), p_l(E_l)), u_l(P_l, x, t)) / N_l(E_l)
```

where `l` is an emulsion layer/population, `P_l` is a 5279-appropriate spatial morphology, and cross-layer covariance is introduced only through shared latent occupancy and known dye/DIR coupling. Tone response must come from 5279 sensitometry rather than Silver Efex's B&W taper. Temporal change should sample a new, non-overlapping emulsion region for each physical frame; gate weave then moves the formed image and grain together. This still produces frame-to-frame grain renewal, but avoids the signature of an independently refreshed display-space overlay.

This does not justify changing the frozen V40 renderer. V40 remains the controlled repair of V39 and must be released only after native every-frame colour-tail, covariance, delivery and provenance gates pass. Silver Efex's strongest immediate confirmation is that V40's removal of independent high-frequency opponent-colour reinjection is correct.

### Concrete V41 direction

| Question | Silver Efex finding | V40 state | V41 decision |
|---|---|---|---|
| Is grain an overlay? | No: inverse-binomial density candidate plus interpolation | Already finite-site/Bernoulli in formed density | Keep this foundation; do not add a later noise pass |
| What determines shape? | Stock-specific measured 1000² patch plus blur/scale | Multi-population disk/cloud kernels | Add an evidence-gated 5279 morphology/correlation field; do not import B&W Nik patches |
| What determines tone variance? | `p(1-p)/N` plus an explicit highlight/shadow taper | Kodak post-process RMS and record sensitometry | Keep Kodak boundary; test a finite-particle lookup without copying Nik's B&W taper |
| What happens to colour? | Shared path moves chroma deterministically; no independent RGB impulses | Three-record density, DIR/interimage coupling; V40 removes duplicate HF opponent path | Keep layer covariance physical and audit extreme opponent tails |
| Why does sharpness feel coherent? | Density realization and measured morphology alter local microcontrast together | Density-domain MTF and stochastic development are coupled | Measure joint edge/flat-field MTF–NPS rather than add sharpening |
| What should move frame to frame? | Not answered: Silver Efex is still-image software | Each frame has a new finite-site seed | Retain new physical emulsion per frame, but apply weave/scan transforms to image and grain together |

The first V41 experiment should therefore be an A/B implementation, not a wholesale replacement:

1. Preserve V40 colour, sensitometry, MTF, DIR and delivery exactly.
2. Replace only the spatial uniform-site field with a reproducible correlated copula whose NPS/autocorrelation is fitted to a 5279 flat-field/reference scan.
3. Feed that field into the existing finite-site record-density formation.
4. Renormalize at Kodak's 48 μm post-process granularity boundary.
5. Reject the candidate unless it improves flat-field NPS, edge/texture coherence and temporal perception without worsening colour-tail gates.
