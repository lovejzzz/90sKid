# 2026-08-03 research run: 2383 analytical dye density and cross-vendor interimage holdout

## Outcome

This run identifies and corrects a structural error in V21's 2383 projection
model. V21 treated the three Status-A integral densities produced by the print
stock characteristic curves as if they were independent cyan, magenta and
yellow dye amounts. It then multiplied those values by the published dye
spectra. This counts unwanted spectral absorption twice and produces the wrong
cross-channel signs in the finished projection.

The research candidate separates the missing operations:

1. each separated-light 2383 principal Status-A curve is nonlinearly inverted
   through the exact ISO Status-A spectral product to recover analytical dye
   amount;
2. a 3x3 matrix is applied to log print exposure before the three
   characteristic curves, with the official LAD exposure subtracted and added
   around the matrix;
3. the physical 2383 branch supplies near-neutral colour response, while the
   existing H-61-style finite-colour calibration remains active only after
   relative chroma has become meaningful;
4. one neutral-derived per-channel display curve supplies monitor contrast and
   black without borrowing the scan's hue;
5. only genuinely neutral clear-print highlights receive an explicit neutral
   guard where the inverse becomes poorly conditioned.

The candidate passes independent finite-colour, brightness, saturation and
neutral-scale gates and therefore qualifies for a RAW A/B. It is not yet a
released V22; the production source and master remain V21 until the camera-file
test passes.

## New measured evidence

### 2003 IS&T density transfer experiment

Ado Ishii's *Color Management Technology for Digital Film Mastering* reports
more than 400 Status-M colour exposures for each camera negative printed to
EK2383. For EK5279/EK2383, the reported Status-A regression uses 401 patches and
has RMS errors `R 0.022 / G 0.023 / B 0.027 D`. The paper states that EK5218,
EK5246, EK5248 and EK5279 have similar tone-curve behaviour and publishes this
least-squares 5218-to-2383 printing-density matrix:

```text
4.049  0.303  0.072
0.472  3.090  0.191
0.248  0.397  2.913
```

All six cross-channel terms are positive. Normalized by the diagonal, they are
approximately `0.075/0.018`, `0.153/0.062`, and `0.085/0.136`. This directly
contradicts V21's local negative-printer mapping, whose corresponding values at
LAD were `0.270/-0.019`, `0.044/0.042`, and `0.043/0.017`.

Primary proceedings PDF:
<https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055>.

### Independent finished-look transforms

The local machine contains independently supplied 2383 transforms from
Blackmagic Design, Adobe and FilmVision. Their files were evaluated in place;
the LUTs were not copied into the project. Blackmagic's Rec.709 files explicitly
declare Cineon Log input and Rec.709 gamma 2.4 output. Its ACES LMT declares AP0
linear input/output. Adobe officially describes its 5218-to-2383 simulation as
negative film output followed by 2383 theatrical projection, so it is treated
as a complete negative-plus-print result rather than a pure positive-stock
measurement.

At the neutral midtone, the cross-vendor median row-normalized log-output
Jacobian is:

```text
1.000   0.029  -0.046
0.153   1.000   0.087
0.037   0.213   1.000
```

The most stable signs across vendors are `R<-B negative`, `G<-R positive`,
`G<-B positive`, and `B<-G positive`. V21's delivered monitor branch had
`R<-B positive` and `G<-B negative`, confirming that the previously reported
residual hue rotation was measurable rather than subjective.

Source hashes and paths are stored in `metrics.json`. Important format detail:
CLF serializes a 3D LUT blue-fastest, while `.cube` serializes red-fastest. The
first BMD LMT reading was rejected and repeated after correcting this ordering.
The ACES CLF specification confirms the serialization rule:
<https://docs.acescentral.com/clf/guides/>.

Adobe's official output-simulation description:
<https://helpx.adobe.com/after-effects/desktop/adjust-colors/color-management/color-management.html>.

## Physical model placement

Kodak's analytical workflow patent says that Status-A density is an integral
measurement of base, gelatin and all dyes, whereas analytical density is
proportional to dye amount. It requires separated colour exposure plus uniform
exposure in the other records to measure interimage effects, converts the three
Status-A readings to analytical densities, and applies a matrix if the nominally
constant dye amounts move:
<https://patents.google.com/patent/US20020118211A1/en>.

Adobe's later film-preview patent places the matrix in log RGB print exposure
before the positive characteristic curves and gives the LAD-preserving form:

```text
adjusted = M * (captured - LAD) + LAD
```

It fits the matrix against measured DPX-to-theatre-Lab patches distributed
through the input space:
<https://patents.google.com/patent/US8654192B2/en>.

The research candidate follows this placement. Its matrix is:

```text
 1.4105  -0.9566   0.9152
 0.4127   0.6943  -0.2324
-0.5640   0.6093   0.8425
```

This is an identified preview-model matrix, not a claimed Kodak factory value.
It was fit only to the cross-vendor local mid-gray Jacobian. Its condition number
is about `2.42`, so it is not close to singular. The six finite chromatic patches
and all other brightness levels were held out.

## Nonlinear analytical-density conversion

The prior exact ISO experiment already proved that exact densitometer weighting
alone cannot reproduce 2383's simultaneous-neutral interimage trajectory. That
falsification remains valid. However, it also supplied the correct operation for
each separated principal curve.

For a single dye amount `a_j`:

```text
D(lambda) = a_j * dye_j(lambda)
T(lambda) = 10^(-D(lambda))
D_A,k = -log10(sum[T(lambda) W_k(lambda)] / sum[W_k(lambda)])
```

For each R/G/B principal curve independently, the main Status-A value is
inverted through this spectral equation to obtain a nonlinear dye-amount curve.
The three recovered amounts are then combined under the xenon spectrum. This
avoids solving impossible arbitrary Status-A cube corners and avoids extending
the LAD inverse matrix to the toe and shoulder. It is also consistent with the
IS&T paper's warning that a simple 3x3 density matrix cannot represent the full
density range; that work used a 3x13 polynomial regression for the full range.

## Held-out results

### Six finite chromatic directions

The matrix fit used infinitesimal mid-gray derivatives only. Six
mean-preserving Cineon excursions of `+/-0.060` were then rendered and compared
in Oklab against seven finished transforms: Resolve D55/D60/D65, Adobe
5218/2383, and FilmVision SD1/SD2/SD3. BMD's AP0 LMT was excluded from this
finished-Rec.709 holdout because adding an ODT would introduce another model.

| result | mean hue error | median | maximum |
|---|---:|---:|---:|
| V21 monitor | 9.20 deg | 7.94 deg | 14.62 deg |
| candidate hybrid monitor | **4.71 deg** | **3.83 deg** | **10.18 deg** |

Every candidate patch magnitude lies within the minimum-to-maximum envelope of
the seven vendor transforms. The candidate deliberately stays toward the low
side of that envelope for the red/cyan pair rather than returning to the
over-saturated projection failure seen in earlier versions.

### Brightness holdout

Four neutral levels were selected by the candidate physical output code. The
comparison target at each level is the median local Jacobian of the seven
finished vendor cubes. Off-diagonal RMSE:

| display code | V21 monitor | candidate physical/hybrid |
|---:|---:|---:|
| 0.18 | 0.418 | **0.068** |
| 0.35 | 0.159 | **0.049** |
| 0.50 | 0.232 | **0.034** |
| 0.70 | 0.370 | **0.047** |

The fit used only the 18% scene/mid-gray point. The other three values therefore
test the nonlinear toe and shoulder behaviour. The deepest level was the
failure that exposed the earlier LAD-linear analytical conversion; the
nonlinear principal-curve inverse fixes it without a shadow-specific hue term.

### Neutral and black gate

Across 85 neutral samples from -12 to +9 stops:

- output luminance is monotonic;
- 18% remains approximately `0.17997`;
- the -12-stop black floor is `7.11e-7`;
- the +9-stop peak is `0.97460`;
- maximum luma deviation from V21 is `0.00162`;
- maximum RGB spread is `0.00368`, occurring near the clear-print shoulder.

The neutral highlight guard begins only in the bright shoulder and only while
the scan reference remains near neutral. It does not affect the six colour
patches or the four local coupling tests.

## Rejected paths

1. **Treat every vendor LUT as the same input space.** Rejected. Resolve is
   explicitly Cineon; BMD LMT is AP0; Adobe represents 5218 plus 2383.
2. **Read CLF with `.cube` index order.** Rejected and repeated after consulting
   the ACES specification.
3. **Apply only the published 5218/2383 printing-density ratios.** Helpful for
   diagnosis but insufficient after the spectral projection stage.
4. **Use only the LAD inverse hard-dye matrix.** It improved the midtone but
   regressed the deepest brightness holdout, exactly as the IS&T paper warns.
5. **Use the physical branch directly on a monitor.** Hue improved, but
   saturation reached 1.4-2.5 times the vendor median.
6. **Keep the old near-neutral scan fallback.** It preserved finite saturation
   but made local near-neutral response numerically identical to V21, erasing
   the photochemical coupling that this run identified.
7. **Apply one neutral RGB curve to all colours without finite-colour
   calibration.** It preserved the local matrix but produced excessive
   cyan/yellow saturation. The accepted hybrid uses this physical path only
   close to neutral and blends to the already validated H-61 finite-colour
   calibration above relative chroma 0.12.

## Release decision

The synthetic gates pass. Proceed to a research implementation in the main
algorithm and render short original-resolution 12-bit ProRes 4444 projection
and scan A/Bs from the GH7 ProRes RAW source. Do not publish V22 until:

1. the production implementation reproduces these metrics;
2. the scan branch is byte/metric-equivalent to V21 apart from shared emulsion
   stochasticity;
3. real-frame skin, foliage, saturated signs, black and clipped highlights show
   no new failure;
4. the new projection does not regain the excessive saturation of V16/V17.

## Reproducible artifacts

- `research_runs/2026-08-03_vendor_2383_targets/analyze_vendor_luts.py`
- `research_runs/2026-08-03_vendor_2383_targets/metrics.json`
- `research_runs/2026-08-03_vendor_2383_targets/run_cross_vendor_holdout.py`
- `research_runs/2026-08-03_vendor_2383_targets/cross_vendor_holdout_metrics.json`

SHA-256 at the accepted research state:

- analyzer: `825af0bcd3111809e0aaedb115982491891289249d7312c18e857f1c43d00462`
- local metrics: `4110c0df3bb791d7a7263c358176b00d9b96d68c0a8f5ab8cd17533dd1cef13e`
- holdout script: `9ece2a58a208acf096c3a86aeb6c09de5c16727e92cf00328377813f110dd8d8`
- holdout metrics: `588f6919f3ed436a0222bee5bc08388f252c89da22b77c2d8541cd01be50ba00`

## V22 production release

The pre-release hybrid described above was superseded by the final D60-relative
monitor calibration. The physical film model remains analytical; the monitor
calibration subtracts the D60 neutral response at the same mean Cineon code,
keeps Oklab L unchanged, and applies only the remaining a/b excursion through a
25-cube lattice. This prevents an absolute vendor white point from becoming a
global magenta cast.

The final six-direction holdout is:

| result | mean hue error | median | maximum |
|---|---:|---:|---:|
| V21 monitor | 9.20 deg | 7.94 deg | 14.62 deg |
| analytical, uncalibrated | 4.71 deg | 3.83 deg | 10.18 deg |
| V22 D60-relative | **2.61 deg** | **1.46 deg** | **6.90 deg** |

All six saturation magnitudes remain within the envelope of the seven finished
vendor transforms. On the held-out GH7 frame, the percentage of evaluated
pixels whose hue lies inside the Resolve D55-D65 bracket increases from 20.2%
to 45.9%; the joint hue/chroma bracket increases from 10.9% to 34.8%.

The 13-term cubic compression was rejected because it regressed real-frame hue
and could not preserve the nonlinear correction. A matrix-strength sweep also
rejected manually weakening the interimage coupling: the full identified
strength performed best among the tested 0/25/50/75/100% values.

Production checks at 5760x4320, 12-bit show no channel clipped at 1.0, luma
p99.99 near 0.958 and maximum near 0.987. Projection and scan masters share the
same negative-emulsion realization frame by frame. V22 versus V21 median luma
difference is 0.0016 and median RGB difference is 0.0068, confirming that the
release changes colour rather than manufacturing a contrast difference.

Final artifacts:

- projection: `outputs/native_5k_v22_dual_6f_d60_relative/projection/05_emulsion_master_prores4444.mov`
- Period 2K / Blu-ray: `outputs/native_5k_v22_dual_6f_d60_relative/bluray_scan/05_emulsion_master_prores4444.mov`
- production source SHA-256: `4f7cf1224efaf5dba580c5fec3bc271fc9f518bbb0a1004cd604716c83998451`
- calibration lattice SHA-256: `eb3a545fbef5901ccebf9f9afe42dc766d81f4dac6c78700a614335eb7839743`
- final six-colour metrics SHA-256: `9da86ec405045acc3253229c38ec50a44ea8337d55f3f1f489a79122f817747f`
- real-frame metrics SHA-256: `2422dfa67b54a75073e8907f83c29b554643a1d0e753ad1e0a894c07c1516133`

Remaining limits are explicit: the D60 target is a vendor display transform,
not a Kodak factory chemistry measurement; no photographed 5279 target or
theatre spectroradiometric reference was available; and the release clip is a
six-frame original-resolution proof rather than a long-form render.
