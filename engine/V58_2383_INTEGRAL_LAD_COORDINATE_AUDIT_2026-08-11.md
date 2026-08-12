# V58: 2383 integral LAD coordinate audit

Date: 2026-08-11
Status: **evidence correction; validated one-frame candidate**

## Finding

V30 through V57 placed Kodak H-61B's processed 2383 LAD aim
`1.09 R / 1.06 G / 1.03 B Status-A` directly on the three published
red-, green- and blue-exposure principal H-D curves. That is a coordinate
error. The H-61B values are three simultaneous **integral** densitometer
readings of one neutral print patch. Each reading contains the desired dye,
the unwanted absorptions of the other two dyes and D-min. A principal H-D
curve, by contrast, reports the response to one separation exposure.

Kodak's digital-cinema patent explicitly distinguishes integral density from
analytical dye amount and says the three dye amounts are required to calculate
patch colour. Its 2383 example converts the full Status-A triplet to analytical
dye coordinates. A second Kodak patent specifies the corresponding
separation-plus-uniform-exposure experiment for identifying print interimage.

V58 therefore changes one operation only:

1. solve the analytical CMY amounts whose combined vector-traced 2383 dye
   spectra reproduce the official integral LAD triplet;
2. forward each solved amount through its own Status-A measurement product to
   obtain the principal separated-curve density;
3. invert the three published 2383 H-D curves at those principal densities;
4. use the same principal triplet in the neutral-curve and LAD-viewing anchors.

The V55 empirical interimage matrix, 5279 negative, grain, DIR, MTF, scan
observer, scan-referenced projection colour policy, black and output transfer
are frozen. This isolates the density-coordinate correction.

## Equations

For analytical dye amounts `a=(c,m,y)`, vector-traced dye spectra `S_j(lambda)`
and ISO Status-A weights `W_k(lambda)`:

```text
D(lambda) = sum_j a_j S_j(lambda)

D_A,k(a) = -log10(
    sum_lambda W_k(lambda) 10^(-D(lambda))
    / sum_lambda W_k(lambda)
) + Dmin_k
```

The three-variable Newton solve uses the exact Jacobian

```text
d D_A,k / d a_j =
    sum_lambda W_k T S_j / sum_lambda W_k T
```

and closes `D_A(a) = [1.09, 1.06, 1.03]`. For each record `j`, the principal
density is then evaluated with only `a_j S_j(lambda)` present in the spectral
density. Those three values, not the integral triplet, are the inputs to the
separation H-D inverse.

The public sheet does not publish a D-min spectrum. V58 preserves the existing,
explicit approximation that the three vector-curve minima are additive
Status-A channel terms. This remaining approximation is reported rather than
hidden.

## Numerical result

| quantity | R / C | G / M | B / Y |
|---|---:|---:|---:|
| official processed LAD Status-A | 1.090000 | 1.060000 | 1.030000 |
| solved analytical dye amount | 1.054585 | 1.030030 | 0.962692 |
| corrected principal H-D density | 0.989858 | 0.882334 | 0.841938 |
| old principal target | 1.090000 | 1.060000 | 1.030000 |
| principal correction | -0.100142 | -0.177666 | -0.188062 |
| print log-exposure correction | -0.026716 | -0.062618 | -0.069934 |

Forward integration of the corrected principal triplet returns the official
LAD with maximum residual below `3.1e-12 D` in float64 (`0.0 D` after the
runtime float32 round trip).

Forward integration of the old triplet instead produces approximately
`1.212731 / 1.268175 / 1.248651 Status-A`, errors of
`+0.122731 / +0.208175 / +0.218651 D`. The old model therefore did not merely
use a different white balance; it placed substantially too much formed dye at
the supposedly official LAD anchor.

## Native RAW isolation render

Input:

`/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV`, frame 0,
5760 x 4320, Apple AVFoundation extended-linear BT.2020/D65 decode, archive
exact CPU, unchanged stochastic identity.

Output:

`outputs/native_5k_v58_integral_lad_coordinate_validated_1f/T020`

- V55-to-V58 projection master PSNR: `63.165919 dB`;
- scale-integrated review linear-RGB MAE: `0.00209071`;
- review mean luma: `0.11307245 -> 0.11308063`;
- median luma delta: `0.0`;
- P05/P95 luma delta: `-0.005703 / +0.005766`;
- V55 and V58 scan masters have the same decoded frame MD5:
  `604ead3c60971bb038b8470d5b5492ad`.

The small delivered difference is expected: the frozen V31 observer still
replaces projection a/b with the scan branch and retains a scan-derived neutral
display curve. It does not weaken the density failure above; it demonstrates
that the later observer had been hiding it.

The master pair is 5760 x 4320 ProRes 4444 XQ, `yuv444p12le`, 12-bit, with
Rec.709 primaries/transfer/matrix tags. Thirty-nine pipeline tests and ten
density/kernel/colour tests pass.

The validated render records model SHA-256
`de3c6a4ee9ca702d504ded069be23e3e18f7da9f0e9d693150c25b914b78b007`
and profile SHA-256
`21b165c8e53a32f9c1ddc1801d90592bf34753bf62b4acacc125122e7ab7847b`;
both match the current source files. It is pixel-identical to the preceding
V58 isolation render (`inf` PSNR), confirming that the later audit helper and
bootstrap hardening did not change image formation.

## Consequences for V56 and V57

V56 and V57 remain valid **identifiability demonstrations**: removing scan
colour and changing an unmeasured interimage matrix can produce very different
answers. Their rendered colours are no longer valid quantitative endpoints,
because both experiments inherited the incorrect LAD coordinate. Any renewed
physical-colour/interimage comparison must branch from V58 and remove one
unidentified operation at a time.

## Evidence boundary and next experiment

V58 should replace V55 as the current evidence-corrected print-sensitometry
baseline. It does **not** make the physical projection colour identified.
Remaining unknowns include:

- 2383 separated-plus-uniform-exposure interimage measurements;
- the 2383 D-min spectral density rather than three integral minima;
- period printer lamp spectrum and printer optical path;
- measured xenon/screen spectral power and theatre flare;
- a measured appearance transform from theatre XYZ/Lab to the delivery display.

The next falsifiable experiment is a V58-derived physical observer with the
empirical final-LUT matrix removed. It must retain the corrected LAD coordinate,
report raw spectral XYZ before any display curve, and separate chromaticity from
tone mapping. It must not reuse V56/V57's rendered colour as a target.

## Primary sources

1. Eastman Kodak, *LAD—Laboratory Aim Density for KODAK VISION Color Print
   Film*, H-61B: <https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf>.
2. Eastman Kodak, *KODAK VISION Color Print Film 2383/3383*, March 2005,
   H-1-2383t: <https://www.archives.gov/files/preservation/products/resources/2383-TI.pdf>.
3. Eastman Kodak, US 2002/0163657 A1, analytical-density 2383 model:
   <https://patents.google.com/patent/US20020163657A1/en>.
4. Eastman Kodak, US 2002/0118211 A1, integral/analytical density and print
   interimage measurement method:
   <https://patents.google.com/patent/US20020118211A1/en>.
5. Ado Ishii, *Color Management Technology for Digital Film Mastering*,
   11th Color Imaging Conference, 2003. The 401-patch EK5279/EK2383 result is a
   measured composite Status-M-to-Status-A transform; it does not publish a
   separable 2383 interimage matrix:
   <https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055>.
