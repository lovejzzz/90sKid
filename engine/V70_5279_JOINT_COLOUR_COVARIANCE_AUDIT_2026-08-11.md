# V70 — 5279 joint colour-covariance ownership audit

Date: 2026-08-11
Status: **research-only; no image profile promoted**

## Decision

The current model still reproduces Kodak's published marginal red-, green- and
blue-record diffuse-RMS granularity within the existing 2% gate. That does not
validate the *joint* colour of the grain. The V70 audit shows that:

1. the formed negative predicts only weak same-position cross-record
   correlation (`about 0.007–0.034` over the tested exposure range);
2. almost all of that weak correlation comes from the unmeasured
   `SUBEMULSION_DYE_RECORD_MIX` prior;
3. the current stochastic DIR transport changes those correlations by less
   than about `0.0006` in the paired ablation;
4. the printing-density scanner coordinate and nonlinear viewing transform
   change the covariance further even though they do not alter the negative;
5. the historical managed Blu-ray branch is the dominant source of
   monochromatic-looking grain, reducing opponent variance from roughly
   `59–61%` in the DPX-pure pointwise view to `21–24%` away from its clipped
   deep-black endpoint.

This corrects an important mental model. Kodak's three 48 µm curves determine
three marginal amplitudes. They do **not** determine whether the resulting
grain should look coloured or monochromatic. That appearance cannot be chosen
by eye and then attributed to 5279.

## Why the earlier research needed to be revisited

The project has repeatedly reached the same evidence boundary from different
directions:

- V21 moved dye-cloud formation and inhibitor release into the development
  graph and correctly separated Status-M, telecine and optical-print observers.
- V29 stated that one aperture-weighted RMS value does not identify a 2D NPS,
  coating formula or DIR matrix.
- V34 removed deterministic DIR adjacency that duplicated the published
  processed-stock MTF, but retained stochastic DIR as an unmeasured morphology
  prior.
- V39 showed why marginal RMS alone could pass while isolated primary-colour
  impulses still looked like electronic noise.
- V46 and V50 corrected the physical 48 µm measurement and the vector trace,
  while continuing to label covariance and NPS as unknown.
- V68 separated formed negative, Cineon printing-density data and display view.
- V69 proved that the historical scan delivery uses an additional hidden mean
  image to suppress opponent-colour grain and is not a function of one DPX.

V70 connects those findings quantitatively rather than treating them as
separate caveats.

## What the public 5279 document actually constrains

Kodak H-1-5279t publishes:

- neutral red-, green- and blue-record characteristic curves;
- processed-stock MTF curves;
- three exposure-dependent diffuse-RMS granularity curves measured with a
  48 µm aperture;
- spectral sensitivity and net spectral dye-density curves.

For a zero-mean record-density residual

\[
\delta\mathbf D = [\delta D_R,\delta D_G,\delta D_B]^T,
\]

the published granularity graph constrains only the diagonal of

\[
\Sigma_D(E)=\operatorname{E}
[\delta\mathbf D\,\delta\mathbf D^T]
\]

after 48 µm integration. It does not publish the three off-diagonal terms, their
spatial cross-spectra, or higher-order joint tails.

Kodak's own grain-matching patent US 5,641,596 makes the missing information
explicit: standard deviation, within-channel spatial correlation and
between-channel spectral correlation are separate statistics, measured from
uniform film patches as functions of signal level. EP 1,627,359 likewise notes
that weak colour-layer correlation appears as coloured grain while high
correlation appears monochromatic. These are general measurement principles,
not 5279 coefficients.

## Current model ownership

| Quantity | Current authority | Status |
|---|---|---|
| neutral H-D | vector-traced Kodak H-1-5279t | stock-specific evidence |
| processed negative MTF | fitted Kodak H-1-5279t curve | stock-specific evidence |
| per-record 48 µm RMS | vector-traced Kodak H-1-5279t curve | stock-specific evidence |
| net dye spectra and mask sign | vector-traced Kodak graph | stock-specific evidence |
| finite fast/medium/slow architecture | bounded Kodak-patent prior | not a disclosed 5279 coating |
| five size classes and cloud kernels | morphology prior constrained only by marginal RMS | unmeasured |
| stochastic DIR coefficients | restrained development-domain prior | unmeasured |
| cross-record dye-population mixing | restrained structural prior | unmeasured |
| Spirit channel MTF / noise / primary correction | evidence-bounded observer | unmeasured for a serial-numbered scanner |
| Blu-ray opponent-grain suppression | historical project finish | not a 5279 property |

The distinction between net dye spectra and population record mixing is
especially important. The vector-traced net spectra already contain dye
unwanted absorption and masking-coupler consumption. DIR separately represents
imagewise interlayer inhibition. A third direct source-to-destination record
mix may be a useful bounded approximation, but its physical ownership is not
independently identified and it must not silently become the authority for
grain colour.

## Audit design

The fixture uses `1920 × 256` uniform fields at log exposures
`-3.0 / -2.5 / -1.0 / 0.0`, six independent emulsion realizations each, with
35 mm width fixed at `24.9 mm`. Every condition uses the same absolute frame
seeds. The four paired conditions are:

1. current record mixing + current stochastic DIR;
2. record mixing only;
3. stochastic DIR only with identity record mapping;
4. independent records with neither prior.

For each, covariance is measured at five stages:

1. formed density after physical 48 µm integration;
2. processed negative after 5279 MTF;
3. quantized 10-bit Cineon printing-density code after the Spirit aperture;
4. DPX-pure pointwise Blu-ray view;
5. historical hidden-mean managed Blu-ray view.

The common/opponent basis is orthonormal:

\[
u_0=(R+G+B)/\sqrt3,\quad
u_1=(R-G)/\sqrt2,\quad
u_2=(R+G-2B)/\sqrt6.
\]

Therefore common plus opponent variance is exactly conserved by the basis
change; the reported fractions are not produced by a subjective luma weighting.

## Results

### 1. Published marginal amplitude still passes

The worst current-profile 48 µm marginal-RMS relative error is
`1.1389%`, below the `2%` gate. Every measured covariance matrix is positive
semidefinite.

This validates only the existing observable contract. It does not validate
off-diagonal covariance.

### 2. Formed-negative correlations are weak and exposure dependent

| log E | corr R-G | corr R-B | corr G-B | opponent variance |
|---:|---:|---:|---:|---:|
| -3.0 | 0.0325 | 0.0129 | 0.0285 | 65.49% |
| -2.5 | 0.0340 | 0.0121 | 0.0281 | 65.79% |
| -1.0 | 0.0245 | 0.0116 | 0.0201 | 65.81% |
| 0.0 | 0.0168 | 0.0074 | 0.0147 | 66.01% |

For three independent records with the same marginals, the orthonormal
opponent fraction is exactly `66.67%`. The current model is only slightly more
common-mode than that endpoint. In other words, the formed negative currently
predicts predominantly coloured, not monochromatic, record fluctuations.

That is a model prediction, not a measured description of 5279.

### 3. Record mixing owns almost all predicted cross-record correlation

With stochastic DIR disabled but record mixing retained, correlations change
by at most about `0.0006`. With record mixing replaced by identity, all three
correlations stay near zero (roughly `-0.0030` to `+0.0028`).

The current stochastic DIR implementation therefore changes morphology and
models development-domain causality, but it is not presently the source of the
visible colour-covariance character. Retuning its coefficient would not solve
the missing 5279 covariance measurement.

### 4. Scanner and display stages materially change perceived grain colour

| log E | formed-negative opponent | Cineon-code opponent | pointwise-view opponent | legacy-managed opponent |
|---:|---:|---:|---:|---:|
| -3.0 | 65.49% | 58.28% | 60.28% | 0.00%* |
| -2.5 | 65.79% | 62.77% | 58.83% | 23.64% |
| -1.0 | 65.81% | 61.30% | 61.21% | 22.80% |
| 0.0 | 66.01% | 60.40% | 60.16% | 21.23% |

`*` At log E `-3.0`, the historical managed branch suppresses the uniform-field
residual at its deep-black visibility boundary. This is a delivery policy,
not evidence that the negative has no grain.

The printing-density observer and display nonlinearities already change the
joint covariance. The historical managed branch changes it much more: it makes
the delivered texture strongly common-mode by design. This confirms V69's
native-scene finding that its major operation is opponent/chroma grain
suppression rather than a different black, midtone or highlight curve.

## Corrected interpretation

The accurate statement is now:

> In a colour negative, the stochastic dye-density field is part of image
> formation, not a display overlay. But the colour of its visible grain is a
> joint property of layer covariance, dye spectra, optical/scanner integration
> and the viewing chain. Per-channel RMS alone cannot determine it.

This also explains why two versions can share identical 5279 marginal density
RMS yet one resembles electronic colour noise and another resembles smoother
35 mm grain. The difference may lie entirely in an unmeasured covariance or in
post-scan opponent filtering.

## Production consequence

No V70 image profile is released.

- The independent-DPX pointwise view is retained as an honest view of the
  current printing-density data, not declared the true Blu-ray appearance.
- The historical managed branch remains available under its explicit name,
  not called a scanner transform or a 5279 property.
- `SUBEMULSION_DYE_RECORD_MIX` and stochastic DIR remain frozen until their
  deterministic colour and stochastic covariance ownership are separately
  audited.
- No global saturation, hue, black, gamma or grain-strength adjustment is
  justified by these results.

## Measurement needed to finish this boundary

A useful 5279 characterization must contain multiple uniformly exposed neutral
and colour-separation patches over the negative's exposure range, processed in
controlled ECN-2 and scanned without grain reduction or sharpening. For each
patch, retain high-bit linear scanner data and measure:

1. per-record mean and 48 µm-equivalent RMS;
2. two-dimensional auto-NPS for every record;
3. complex cross-power spectra for R-G, R-B and G-B;
4. covariance and higher-order joint tails versus exposure;
5. repeated scanner passes or an empty-gate calibration to separate scanner
   noise and channel MTF from film structure.

Only those data can choose between the weakly correlated, common-mode and
intermediate endpoints without turning taste into a stock measurement.

## Artifacts

- implementation: `src/audit_v70_5279_joint_covariance.py`
- machine-readable audit: `research_runs/v70_5279_joint_covariance_audit.json`
- audit SHA-256:
  `819d7825945b64bb1bea6266f2f4bf10afd3cde1294894cd94d57c6b2b32707e`
- implementation SHA-256:
  `50d9d86bb4c5809104a646203300f184d119ed4fc13c3bd7b9e3aa671449b1ee`

## Primary sources

1. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
   H-1-5279t, March 2003, local archival copy
   `references/kodak_5279_H-1-5279t.pdf` and
   [public mirror](https://device.report/m/5e51c79d670196bba47e7f500a4d5cb6b040df42f004110fd5989ce056ea95b1.pdf).
2. Eastman Kodak Company, [US 5,641,596, *Adjusting film grain properties in
   digital images*](https://patents.google.com/patent/US5641596), especially
   the separate level-dependent standard-deviation, spatial-correlation and
   interchannel-correlation measurements.
3. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements
   exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en), used only as evidence for multilayer speed architecture.
4. Eastman Kodak Company, [US 6,686,136 B1, *Color negative film element and
   process for developing*](https://patents.google.com/patent/US6686136B1/en),
   on deliberate interimage interaction, unwanted dye absorption and the
   confounded nature of scanned colour records.
5. Eastman Kodak Company, [*Exploring the Color
   Image*](https://www.kodak.com/content/products-brochures/Film/Exploring-the-Color-Image.pdf),
   on masking couplers and unwanted dye absorptions.
6. [EP 1,627,359 B1, *Method and apparatus for representing image granularity
   by one or more parameters*](https://patents.google.com/patent/EP1627359B1/en),
   used as a general colour-correlation/perception framework, not a 5279
   measurement.
