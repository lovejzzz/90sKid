# V45 — Official CIE 1931 2° 1 nm observer

Date: 2026-08-10  
Release class: measured observer revision  
Image-formation baseline: V44 observer integrity / V42 accepted negative

## Decision

V45 changes one quantity only: the colour-matching functions used to observe
the analytical 2383 transmission spectrum. V44 and earlier used a smooth
closed-form approximation sampled at the 20 nm nodes of the public Kodak graph.
V45 uses the official CIE 1931 2-degree, 1 nm table from 380 to 780 nm.

This is not a grade. The following remain frozen:

- AVFoundation extended-linear BT.2020/D65 ProRes RAW input contract;
- V41 chart-bounded input chroma transport;
- all 5279 H-D, mask, three-record and nine-speed-population parameters;
- DIR, MTF, 48 µm processed-density RMS and temporal site realization;
- zero intrinsic 2383 randomness pending measured covariance/NPS;
- 2383 Status-A inversion, LAD placement, H-D, printer lights and Callier term;
- V31 normal-process low-frequency chroma boundary;
- period 2K/Cineon scan observer;
- black, contrast, gamma and 12-bit BT.1886/sRGB delivery.

## Spectral equation

For analytical cyan, magenta and yellow amounts `a`, the projected tristimulus
is evaluated as

```text
T(λ)   = 10 ^ -Σ_k a_k d_k(λ)
XYZ    = Σ_λ w_λ S_xenon(λ) T(λ) [x̄(λ), ȳ(λ), z̄(λ)]
λ      = 380, 381, …, 780 nm
w_λ    = 0.5 at 380/780 nm; 1 otherwise
```

The common 1 nm interval cancels during white normalization. Kodak's plotted
20 nm dye-density and xenon-SPD samples are linearly interpolated. Interpolation
improves numerical integration against the standard observer; it does **not**
turn a 20 nm graph into an unpublished 1 nm material measurement.

## Numerical comparison with V44

The complete 25³ analytical projection cube was evaluated through both
observers before any real-image release render:

| Test | Result |
|---|---:|
| Official CIE rows used | 401 (380–780 nm inclusive) |
| finite output nodes | 46,875 / 46,875 |
| linear-RGB RMS delta | 0.0045691676 |
| maximum absolute node delta | 0.0398455262 |
| maximum dye-free-white channel delta | 3.58 × 10⁻⁷ |
| V44 25³ LUT SHA-256 | `b1c978c915937868f3940bfd5d098e9864b9c1e47617af28f73f40c565356d1c` |
| V45 25³ LUT SHA-256 | `f3e2706c2f51f8d52aac4c72afd381bc5562968dd19421f360646a47910da368` |

The complete 193³ monitor-output lattices were then compared after LAD,
neutral-scale shaping, normal-process colour and gamut boundaries:

| Complete output-lattice test | Result |
|---|---:|
| linear-RGB RMS delta | 0.0002158193 |
| maximum absolute node delta | 0.03810160 |
| mean delta R / G / B | 4.10×10⁻⁷ / 1.69×10⁻⁶ / 3.65×10⁻⁷ |

The nearly fixed white proves the revision does not introduce a global tint.
The larger local deltas occur only after specific dye mixtures weight the
observer differently.

## Runtime-cache incident prevented

The release renderer does not normally integrate 2383 for every pixel. It loads
a complete 193³ record-density-to-monitor lattice. Changing only
`build_2383_projection_lut()` while retaining the V30 lattice would therefore
produce an apparently newer codebase with identical old pixels.

V45 closes that failure mode:

1. `v45_profile.py` selects the official observer and invalidates every derived
   projection table;
2. `build_v45_print_lut.py` builds a separate 193³ lattice;
3. `assets.py` binds V45 to the official table and lattice SHA-256;
4. `pipeline.py` selects the lattice by active profile and fails before render
   if either authority is absent or altered;
5. `bootstrap.py` rebuilds both historical and V45 caches on a clean clone.

V45 lattice SHA-256:
`28ac498942c7ddc923fa3b988b8dd6663266026893f96a744b59c8090bfd3cf7`.

The repository copy of the CIE CSV preserves the official numeric rows while
normalizing line endings. Its SHA-256 is
`bd7973e895a97e543815614b19c51ceff552ae9910a424724ae04ed89bd863a3`;
the downloaded CIE file was also checked against the CIE-published MD5
`17cca777db64b17170f06f67ce9d3ab7` before normalization.

## Why dye-peak normalization was rejected

The published 2383 graph is peak-normalized, but the pipeline first inverts each
separated Status-A response to analytical dye amount. Multiplying one dye curve
by an arbitrary constant mostly divides its inferred amount by the same constant.
Blindly normalizing every dye peak therefore does not recover missing absolute
spectrophotometry; it can create double calibration after LAD and neutral-scale
placement. V45 preserves the plotted relative shapes and confines the upgrade to
the observer.

## Release validation

Three scenes exercise different spectral and spatial failure cases at native
5760×4320 for 24 frames each:

- T020 frames 0–23: foliage, pale highlight and dark bark;
- T032 frames 0–23: rainy cyan-green low contrast and dark columns;
- T007 frames 276–299: water, green detail and local saturation.

Each scene publishes V45 projection and the frozen scan from one shared negative,
plus inherited independent FSD and Panasonic V-709 controls on the site. Stills
are decoded from frame 12 of each final encoded scale-integrated review movie.

The same-negative ablation forms T020 frame 0 once, then changes only the
observer. The scan SHA-256 remains bit-identical. Projection linear-RGB RMS is
`0.00003790398`, its 99.9th-percentile absolute delta is `0.000468791`, and its
maximum absolute delta is `0.00178444`. This is direct evidence that V45 is an
observer correction rather than a hidden change to negative formation or scan
colour.

All six final movies pass the native release gate: 5760×4320, 24 frames,
12-bit 4:4:4 XQ, expected colour tags, black/white limits, dark-opponent tails,
and family-wise Poisson gates for isolated colour impulses. All six BT.1886
masters and sRGB companions also pass the decoded-linear-light consistency
audit. Reference rendering used Archive Exact CPU; measured wall times were
`1013.35 s` (T020), `933.91 s` (T032) and `967.06 s` (T007), with mean algorithm
times of `39.25`, `35.99` and `37.14 s/frame` respectively.

Detailed per-frame results remain in the release audit, delivery audit and
per-scene `timing.json` files. The web manifest retains the public audit summary
without exposing local filesystem paths.

## Remaining uncertainty

V45 improves the standard-observer computation but does not close the physical
measurement loop. Absolute 5279-to-2383 reproduction still requires same-batch
negative and print measurements, characterized processing, measured projector
SPD/flare and a known scanner/telecine response. The public 2383 graph also lacks
tabulated full-resolution dye spectra and print-record stochastic covariance.

## Primary references

- CIE, *CIE 1931 colour-matching functions, 2 degree observer*:
  https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer
- Kodak, *KODAK VISION Color Print Film 2383 / 3383 Technical Data*:
  https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf
- Kodak, historical 2005 2383/3383 sheet:
  https://125px.com/docs/motionpicture/kodak/lab/lab_h12383t.pdf
- Kodak, *LAD for KODAK VISION Color Print Film, H-61B*:
  https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf
