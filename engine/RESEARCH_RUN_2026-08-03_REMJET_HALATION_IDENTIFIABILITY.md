# 2026-08-03 research run: 5279 rem-jet halation identifiability

## Outcome

The current V23 red-halation term is **not identifiable from the available
5279 evidence**, and removing it did not earn a release. Kodak's 5279 sheet
confirms an acetate base with rem-jet backing; Kodak's general film guide and
processing manual establish that rem-jet absorbs exposing light that would
otherwise reflect from the support and that it is removed before development.
None of those sources publishes a 5279 residual-halation point-spread function,
amplitude, colour vector or exposure threshold.

V23's inherited two-Gaussian term therefore remains an explicitly empirical
legacy assumption, not a measured stock characteristic. A controlled original-
RAW A/B found that disabling it was technically safe but visually
indistinguishable at normal size. Absence of published parameters does not
prove that real 5279 has zero residual halation, so the production model was
not changed. V23 remains current. No V24, formal master, website change, Git
commit, saved Sites version or deployment was created.

## Safety and prior-state audit

- No 5279 renderer, encoder, build or deployment process was active when this
  run began. The unrelated long-running Roundtable and EduTool preview
  processes were left untouched.
- All three original sources were present. The tested files remained 5760 x
  4320, 24000/1001, 12-bit ProRes RAW HQ and were decoded by AVFoundation to
  Apple extended-linear BT.2020 float32.
- V23 was the highest formal version. Its two one-second source clips each
  retained separate 2383 projection-monitor and Spirit/Cineon/Blu-ray masters,
  manifests and representative stills.
- The site subrepository was clean on `main` at
  `abd6549f95dd27c607ab6a3181efaccb61364874`.
- Sites project `appgprj_6a702784adc88191ab6e183be09436b5` was active,
  owner-only custom access, with saved version 6 sourced from that exact commit
  and a live URL at <https://emulsion-5279.skylab.chatgpt.site>.
- No file under `sources/` was changed.

## Falsifiable question

Does primary evidence plus controlled highlight-edge A/B support V23's inherited
optical-scatter operator strongly enough to prefer it over the same pipeline
with the operator disabled?

The current operator is:

```text
s = smoothstep(0.90, 3.50, scene-linear luma)
h = 0.035 G(sigma=5.5 px) * s + 0.014 G(sigma=18 px) * s
RGB' = RGB + h [1.0, 0.22, 0.045]
```

At a 24.9 mm image width and 5760 samples, the two sigmas correspond to about
`23.8 um` and `77.8 um` on film. These values, both weights, the red-biased
colour vector and the scene-linear threshold are V6-era empirical parameters.

The hypothesis could advance only if a primary source constrained those values
or if the enabled state produced a stable visual/measurement advantage on
independent RAW highlight boundaries without clipping, black lift, coarse
grain or branch contamination.

## Sources and evidence boundary

### 1. Kodak H-1-5279, March 1996, pages 1 and 3-4

The stock-specific sheet identifies 5279 as acetate safety base with rem-jet
backing and publishes the processed stock's record MTF. It does not publish a
halation edge-spread function, rem-jet density spectrum, residual reflection,
or separate highlight-dependent halo measurement. Archived primary document:
<https://cinematography.net/Files/V500T.PDF>.

### 2. Kodak, *The Essential Reference Guide for Filmmakers*, pages 31-33

Kodak defines rem-jet as a jet-black carbon layer on the base side and assigns
it antihalation, antistatic, lubrication and scratch-protection functions. Its
diagram contrasts film with and without the layer. It also states that rem-jet
is removed before development. Official PDF:
<https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf>.

### 3. Kodak, *Processing KODAK Motion Picture Films, Module 2*, pages 2-7 to 2-11

The ECN-2 equipment manual documents prebath, water jets and mechanical removal
of rem-jet before developer entry. This confirms that rem-jet acts during camera
exposure but is not a surviving coloured image component. It provides removal
engineering, not 5279 optical residuals. Official PDF:
<https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-2.pdf>.

### 4. Eastman Kodak US 5,962,207, lines 539-550 / 741-745

The contemporary Kodak patent describes antihalation layers as preventing
support-reflected light from spreading the image. It lists multiple possible
absorbers and support constructions, showing why a generic mechanism does not
identify one stock's residual PSF. It concerns a different construction and is
mechanism evidence only: <https://patents.google.com/patent/US5962207A/en>.

## Fact, inference and unknown

- **5279-specific fact:** the stock used an acetate base with rem-jet backing.
- **General Kodak fact:** rem-jet is a carbon-black absorbing layer intended to
  minimize reflected exposing light and is removed before development.
- **Identifiability result:** the published MTF is the magnitude response of the
  combined processed film system. A single `MTF_total(f)` cannot uniquely
  factor into an emulsion/acutance term and a separate exposure-dependent halo
  kernel. The data sheet also supplies no edge phase or high-exposure halo
  series. Infinitely many component kernels can fit the same total MTF.
- **Model assumption:** a red-biased residual is physically conceivable because
  layer depth and spectral absorption differ, but `[1, 0.22, 0.045]` is not
  established by the carbon-black description or the 5279 sheet.
- **Unknown:** 5279's rem-jet optical density spectrum, support-interface
  reflectance, layer-depth scattering, highlight edge-spread function and the
  amount already folded into the published record MTF.

## Controlled original-RAW A/B

Three representative frames were decoded from the original 12-bit ProRes RAW:

- T002 frame 97: the prior all-frame inventory's strongest highlight excursion;
- T020 frame 12: V23's sunlit tree/sky representative frame;
- T032 frame 12: V23's low-contrast wet green representative frame.

All were area-reduced in extended-linear light to 1440 x 1080. The current V23
operator and the no-scatter candidate shared Panasonic colour conversion,
`+0.45` stop exposure, H-D curves, DIR, one fixed developed dye-cloud density
deviation field, 5279/2383 MTF, print/scanner observers and output finishing.

An initial draft called NumPy's binomial sampler separately for the two
probability arrays. Although the seed was the same, data-dependent binomial
sampling advanced the generator differently and decorrelated later layers. Its
grain-dominated metrics were rejected. The final test forms the V23 microscopic
realization once and adds that exact developed density-deviation field to both
means. Grain still forms the image, but it is a genuine controlled variable.

### Scatter activation before negative formation

| frame | pixels above 0.90 source threshold | pixels above half activation | mean added linear luma | max added linear red |
|---|---:|---:|---:|---:|
| T002 f97 | 4.4816% | 2.2535% | 0.00043094 | 0.049000 |
| T020 f12 | 4.8902% | 0% | 0.00001985 | 0.004016 |
| T032 f12 | 0.1339% | 0% | 0.00000038 | 0.002816 |

### Current minus no-scatter viewing consequences

The table reports the magnitude of the controlled difference; neither side is
treated as measured truth.

| frame / branch | linear RGB MAE | Oklab dE p99 | abs luma delta p95 | changed 8-bit pixels | clipping either side |
|---|---:|---:|---:|---:|---:|
| T002 projection | 0.00052620 | 0.003678 | 0.002165 | 46.26% | 0% |
| T002 scan | 0.00002794 | 0.000716 | 0.0000074 | 1.31% | 0% |
| T020 projection | 0.00034688 | 0.003317 | 0.002002 | 31.41% | 0% |
| T020 scan | 0.00000445 | 0.000034 | <0.0000001 | 0.24% | 0% |
| T032 projection | 0.00014673 | 0.002532 | 0.001301 | 9.48% | 0% |
| T032 scan | 0.00000022 | <0.000001 | 0 | 0.017% | 0% |

The projection monitor's nonlinear colour/view calibration spreads very small
record-density changes over many quantized display pixels; changed-pixel count
therefore overstates visible magnitude. Normal-size manual review could not
reliably distinguish either side. The 24x maps correctly localized the strongest
differences to bright leaves, windows and sky boundaries. No side introduced a
global magenta/blue cast, raised black, clipping, branch leakage or 8/16 mm-like
coarse grain. Exact-black changes were at most about `0.00045` percentage point.

## Release decision

No release. Disabling the legacy term is technically safe on these samples, but
it is not proven more faithful. Keeping it is also not validated by stock-
specific quantitative evidence. Removing an unsupported parameter solely
because it is unsupported would silently assert a zero residual, which the
available evidence cannot justify.

Production `src/emulsion_experiment.py`, V23 masters and the website remain
unchanged. No formal video, release screenshot, Changelog entry, site build,
Git commit, saved Sites version or deployment was created.

## Reproducible artifacts

- `research_runs/2026-08-03_remjet_halation_identifiability/run_ab.py`
- `research_runs/2026-08-03_remjet_halation_identifiability/metrics.json`
- current, no-scatter, side-by-side and 24x difference PNGs for all three frames
  and both branches

SHA-256:

- script: `3767b2620154bc73a27efca7e5c2b65cdb27ba44b16a818c9b3154721f70a952`
- metrics: `c3e6677686419b306d2fe8475464e574ffc23622f27d60c57ae655c3846fa8eb`

The script passes Python bytecode compilation and the metrics file passes strict
JSON parsing.

## Next priority

Do not tune halo colour, size or strength by taste. The highest-value next test
is to find a processed 5279 high-contrast edge/point-source scan with known
format, exposure, lens, processing and scanner MTF, ideally paired with the same
setup on a rem-jet-removed control or a measured sensitometric edge. Fit a
radial, exposure-dependent edge-spread residual only after subtracting lens and
scanner response, and require an independent held-out edge before changing V23.
If no such measurement can be recovered, retain the term only as explicitly
empirical and prioritize a better-identified research question.
