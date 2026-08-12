# V62: 2383 interimage stage ownership and profile-identical observer lattice

Date: 2026-08-11
Source validation: `NJARAW_S001_S001_T020.MOV`, frame 0
Working audit: 1440 x 1080 deterministic density
Release validation: native 5760 x 4320, 12-bit ProRes 4444

## Outcome

V62 fixes two related ownership errors without adding a colour grade.

First, the physical 2383 log-exposure stage no longer uses the archived
three-by-three matrix fitted to mixed finished-look LUTs. The matrix remains
available to reproduce historical versions, but the evidence-corrected V62
profile selects identity and labels it explicitly as an **unmeasured minimum-
assumption endpoint**. This does not assert that real processed 2383 has no
chemical interimage effect.

Second, V62 has its own 193-cube pointwise projection observer lattice. V61
corrected the negative Status-M coordinate but continued to load V60's lattice
for the `archive_pointwise` microscopic grain delta. The mean print and the
grain-induced density departure were therefore being viewed through different
negative models. V62 makes both use one profile-identical observer.

## What was wrong with the archived matrix

The archived matrix is:

```text
 1.4105  -0.9566   0.9152
 0.4127   0.6943  -0.2324
-0.5640   0.6093   0.8425
```

Its row sums are `1.3691 / 0.8746 / 0.8878`, not one. A neutral departure is
therefore separated into three different print-exposure slopes. The subsequent
per-record neutral shapers conceal most of that separation on the gray axis,
but they cannot identify or correct the off-neutral chemistry.

The original fit did not use a 5279-to-2383 wedge or same-process theatre
measurement. It used the local response of:

- Resolve Cineon-log to Rec.709 2383 display LUTs;
- an Adobe transform explicitly combining 5218 and 2383;
- three FilmVision creative/technical looks without a documented common input
  contract in their files; and
- a Blackmagic AP0-to-AP0 ACES LMT containing its own 1.4 saturation operation.

The unchanged analyzer was rerun against the still-installed source files. Its
code SHA-256 is
`825af0bcd3111809e0aaedb115982491891289249d7312c18e857f1c43d00462`;
the reproduced metrics SHA-256 is
`4110c0df3bb791d7a7263c358176b00d9b96d68c0a8f5ab8cd17533dd1cef13e`.
These transforms remain useful display brackets, but they are not chemical
measurements in one commensurate 5279/2383 coordinate.

## Re-reading the primary evidence

The physical placement itself was not the mistake. US 8,654,192 correctly
places an interimage matrix in LAD-centred log print exposure before the three
positive-stock characteristic curves:

```text
adjusted log exposure = M * (captured log exposure - LAD) + LAD
```

However, the patent requires pairs of input DPX and projected theatre Lab from
the same film workflow, distributed through the input space and including
saturated hues. We never had those measurements.

US 2002/0118211 describes the chemical experiment more directly: step one
colour exposure while giving uniform exposure to the other two records,
process the print, measure Status-A, convert all three readings to analytical
density, and observe whether the nominally constant dye amounts move. The
identity matrix is the no-effect endpoint of that experiment; it is not a
substitute for performing it.

Ado Ishii's 2003 experiment did measure 401 EK5279-to-EK2383 colours and
reported RMS Status-A errors of `0.022 / 0.023 / 0.027 D` for a 3x13 polynomial.
It did not publish the EK5279 coefficients. The published EK5218 3x3 matrix is
a useful cross-stock witness, but the paper explicitly says each negative stock
needs its own profile and warns that a 3x3 model is insufficient through the
full density range.

Primary sources:

- https://patents.google.com/patent/US20020118211A1/en
- https://patents.google.com/patent/US8654192B2/en
- https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055

## Stage-local result after V61

With the corrected V61 ISO Status-M/joint analytical negative coordinate, the
identity endpoint preserves the cross-channel response already produced by the
negative spectrum and 2383 record sensitivities. Across neutral scene levels
from -4 to +4 stops, the largest local off-diagonal in print log exposure is
about `0.124` in the deepest tested shadow and `0.054-0.082` through most of the
scale.

The archive matrix raises this to roughly `0.664-0.753`. The per-record neutral
shaper changes diagonal slopes but leaves those row-normalized off-diagonals
essentially intact. In other words, the old matrix was compensating an earlier
upstream/display model, not revealing newly measured 2383 chemistry.

## Real-frame ablation

On T020 frame 0, identity versus archive changes:

| stage | result |
|---|---:|
| print principal-density MAE | 0.28938 D |
| print-density P99 absolute | 1.73592 D |
| physical projection linear-RGB MAE | 0.017542 |
| physical projection OKLab median / P95 / P99 | 0.02358 / 0.09584 / 0.12627 |
| monitor projection linear-RGB MAE | 0.00000207 |
| monitor projection P99 | 0.0 |
| monitor 12-bit component fraction changed | 0.1913% |

The large physical difference and nearly absent monitor difference are both
important. V31's declared normal-process delivery takes low-frequency colour
from the period scan while retaining the print branch's tone/texture boundary.
Consequently, the old matrix was capable of severely rotating the internal
physical print while being hidden by a downstream scan-referenced monitor
adapter. That is stage ambiguity, not validation.

V62 does not move the old matrix into the display stage. The display already
has an explicit owner and should not inherit a chemistry-shaped inverse fit.

## V61 lattice mismatch

V61 used V61's direct analytical model for mean print formation but V60's
193-cube lattice for the pointwise grain observer delta. On the same T020 frame:

| comparison | linear-RGB MAE | P99 absolute | OKLab P99 |
|---|---:|---:|---:|
| V60 direct vs V60 lattice | 0.000173 | 0.001188 | 0.002609 |
| V61 direct vs loaded V60 lattice | 0.001647 | 0.020747 | 0.015229 |

The second mismatch is about 9.5 times the first in mean absolute error. This
violates the project's central image-formation claim: a microscopic density
change cannot be called part of the image if it is observed through a different
version of the film model than the mean density.

V62's generated lattice is:

```text
engine/cache/print_2383_monitor_output_lut_193_v62.npy
SHA-256 b26660989bc9d5baaa4719e21e9f41a1b9b9d85729ab228316a15914de75b22e
```

The complete pipeline binds this lattice only to V62. Historical versions keep
their previous assets and remain reproducible.

A controlled three-channel sinusoidal `0.002 D` microscopic perturbation also
checks the quantity the lattice is actually used for: output delta rather than
absolute output. V62 direct-versus-lattice delta has MAE `0.00019993` and P99
`0.00161046`, comparable to V60's internally matched baseline MAE `0.00020511`
and P99 `0.00157565`. The V62 repair therefore restores the historical lattice
interpolation floor instead of introducing a new approximation class.

## Evidence boundary

V62 is more accurate in the scientific sense that every asserted operation has
the right owner and unsupported coefficients are not presented as physical
facts. It is not a complete measurement of 5279 printed to 2383.

The remaining decisive measurement is one of:

1. same-process separated RGB exposure wedges with Status-A-to-analytical
   density conversion;
2. the unpublished 401-patch EK5279/EK2383 density set or equivalent; or
3. DPX inputs paired with measured theatre Lab/XYZ under a documented printer,
   ECP-2D process, projector SPD, optics, screen and flare condition.

Until then, V62's identity is the honest physical endpoint. A future measured
matrix can replace it at the existing LAD-centred log-exposure stage without
changing the rest of the architecture.

## Native delivery validation

V62 was rendered through the production Metal path on T020 frame 0 at the
source raster, `5760 x 4320`. Both professional masters are 12-bit ProRes 4444
(`yuv444p12le`) with BT.709 primaries, transfer and matrix metadata. The
separate scale-integrated review companions are `1920 x 1440`, 12-bit ProRes
4444 with sRGB transfer metadata.

Measured production timing was:

| operation | seconds |
|---|---:|
| negative formation | 14.3529 |
| both output observers | 15.4510 |
| delivery encoding preparation | 0.4620 |
| algorithm total | 30.2659 |
| end-to-end wall time | 41.2809 |

The production provenance recorded 45 unique sampler identities with no
duplicates and bound the V62 observer lattice by SHA-256
`b26660989bc9d5baaa4719e21e9f41a1b9b9d85729ab228316a15914de75b22e`.

The final V61-to-V62 review-file comparison is deliberately separated from the
earlier direct-model ablation. It includes the corrected V62 lattice and the
normal delivery path:

| observer | decoded result |
|---|---:|
| projection linear-RGB MAE | 0.00088726 |
| projection linear-RGB P95 / P99 | 0.0034799 / 0.0057584 |
| projection OKLab median / P95 / P99 | 0.0018775 / 0.0052416 / 0.0090410 |
| projection PSNR | 56.41 dB |
| scan | frame-bit-identical after decode |

Thus the version change reaches the branch it owns: projected-print local
response and texture change, while the scan branch remains frozen. The modest
monitor magnitude does not validate the old or new physical 2383 colour; it
shows that the scan-referenced low-frequency display adapter still dominates
the visible mean colour. The adapter is an explicit viewing-policy boundary
and must not be used as evidence for print chemistry.

Visual inspection of both V62 scale-integrated review stills found no new
green veil, isolated RGB speckles, clipped black discontinuity or delivery
gamma mismatch. That inspection is a regression check, not a colourimetric
measurement of 5279 or 2383.

## Reproducible artifacts

- `src/audit_v62_interimage_stage_ownership.py`
- `research_runs/v62_interimage_stage_ownership_audit.json`
- `research_runs/2026-08-03_vendor_2383_targets/metrics.json`
- `src/v62_profile.py`
- `src/build_v62_print_lut.py`
- `cache/print_2383_monitor_output_lut_193_v62.npy`
- `../outputs/native_5k_v62_interimage_lattice_1f/T020/`

Audit JSON SHA-256:

```text
2e8e25007f9059005fa794e8df163dbc4ea26912d11655ae9a2c6b7297b4801b
```
