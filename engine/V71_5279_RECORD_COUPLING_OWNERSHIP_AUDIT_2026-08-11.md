# V71 — 5279 record-coupling ownership audit

Date: 2026-08-11
Status: **research-only; identity candidate justified, native image gate still pending**

## Decision

The direct `SUBEMULSION_DYE_RECORD_MIX` operator has no independently identified
physical observable in the current model. It sits between mechanisms that
already have distinct owners:

1. spectral-sensitivity overlap maps incident camera RGB into three record
   exposures;
2. each exposed record forms its own dye hue;
3. coloured masking couplers and imperfect dye absorption are represented by
   Kodak's net spectral dye-density curves;
4. imagewise interlayer density suppression is represented by DIR transport;
5. the printer or scanner spectrally integrates the complete masked negative.

The V71 separation-wedge audit finds that the extra direct mix contributes
roughly `1–2.5%` off-record deterministic response, dominates the current
negative's weak colour-grain covariance, and drives separation/neutral gamma
ratios below one. The current DIR operator contributes much less and acts in
the expected opposite direction. Significant cross-channel response remains in
the spectral printer observer even when direct record mixing is identity.

The evidence-first candidate is therefore to withdraw the direct record mix to
identity while leaving measured H-D, 48 µm RMS, MTF, net dye spectra and DIR
unchanged. That candidate is **not yet promoted** in V71: a native chart/scene
ablation and all release gates must pass first.

## Mechanism reconstruction from primary Kodak material

Kodak's *Exploring the Color Image* describes the mask as a spectral
cancellation inside each dye-forming layer. A yellowish magenta-forming coupler
is consumed where magenta dye forms, holding blue absorption approximately
constant; a reddish cyan-forming coupler similarly compensates cyan's unwanted
green/blue absorption. After printer-light compensation, the three dye images
control red, green and blue light approximately independently.

Kodak US 6,686,136 describes a different cross-record mechanism: mobile
developer inhibitor released during development retards density formation in
other colour records. It calls the scanned signals confounded by both
interlayer chemical interaction and residual off-peak dye absorption. These
are respectively owned by DIR and spectral integration in the current model.

Kodak US 5,298,376 defines increased colour saturation through interlayer
interimage effect: development in one record inhibits development in other
records, increasing the difference between a colour separation and an
otherwise similar neutral exposure. That mechanism is not equivalent to
forming neighbouring dye directly from the source record.

Kodak US 5,314,793 supports fast/medium/slow layers with different speed and
granularity inside one dye-forming record. It does not disclose a 5279 matrix
in which a cyan-forming speed population directly deposits magenta or yellow
record density.

## Four operators that must not be conflated

| Operator | Domain | Physical meaning | Evidence status |
|---|---|---|---|
| `FILM_RECORD_SENSITIVITY_RGB` | incident RGB → record exposure | spectral sensitivity overlap | required approximation because scene spectra are unavailable |
| `SUBEMULSION_DYE_RECORD_MIX` | developed source population → destination record density | direct off-record dye-density allocation | no distinct 5279 evidence found |
| DIR receiver/causer transport | developed population → inhibition in another population | mobile inhibitor / interimage effect | mechanism supported; coefficients unmeasured |
| net dye spectra + observer integral | analytical CMY → measured/printed density | dye absorption, mask consumption and spectral receiver overlap | 5279 graph supported; scanner/printer details bounded |

The second operator is the only one whose role is not separately identified.
Its comment calls it a bounded structural estimate, but the recovered spectral
and Status-M work in V51/V61 now gives mechanisms three and four more complete
ownership than when that estimate was introduced in V20/V21.

## Audit method

At neutral record log exposures `-3.0 / -2.5 / -1.0 / 0.0`, V71 perturbs each
of the three physical record exposures by `±0.001 log E` and computes
destination-by-source Jacobians at four stages:

1. H-D response immediately after direct record mixing;
2. developed Status-M record density after deterministic DIR;
3. analytical CMY amount recovered from the full D-min + net-dye spectral
   model;
4. 5279 transmission integrated against the 2383 printer records.

Four paired conditions isolate current mix/current DIR, mix only, DIR only and
identity with neither cross-record operator. The neutral derivative is the row
sum because neutral exposure moves all three source records together. The
diagonal-to-row-sum ratio is the local separation/neutral gamma ratio.

## Results

### 1. Neutral H-D is unchanged

The maximum neutral-gamma difference across all ablations is
`0.0002384 D/log E`, within the `0.0003` finite-difference gate. This is expected:
the direct mix is column normalized and DIR is constructed as a departure from
the neutral axis.

Consequently, the published neutral H-D curves cannot select the direct mix.

### 2. Direct mix owns the negative's deterministic off-record slope

Current developed Status-M result:

| log E | max off-diagonal D/log E | off-record fraction range | separation/neutral gamma-ratio range |
|---:|---:|---:|---:|
| -3.0 | 0.00301 | 1.86–2.43% | 0.9757–0.9814 |
| -2.5 | 0.00718 | 1.76–2.30% | 0.9770–0.9824 |
| -1.0 | 0.00405 | 1.06–1.42% | 0.9858–0.9894 |
| 0.0 | 0.00197 | 0.84–1.08% | 0.9892–0.9916 |

With DIR disabled but direct mixing retained, the off-diagonal values become
slightly larger. Therefore almost the complete effect belongs to direct
mixing, not DIR.

### 3. DIR-only is small and directionally different

With identity record mixing and current deterministic DIR:

- maximum off-diagonal slope is `0.000417 D/log E`;
- off-record fractions remain below about `0.09%`;
- separation/neutral gamma ratios are approximately `1.0000–1.0009`.

That direction agrees with Kodak's interimage description: development in a
causer record suppresses receiver records and can increase separation gamma
relative to neutral gamma. The magnitude is still only a model prior; this
audit does not claim that 5279's real DIR effect is this small.

### 4. Spectral printing already creates cross-channel response

Under identity record mixing and zero interimage DIR, the negative-printer
Jacobian still has maximum off-diagonal terms of about
`0.0235–0.0390 density/log E`, depending on exposure. Those terms arise from
the vector-traced net dye spectra, the physical D-min/mask and broad printer
record sensitivities.

Thus removing the direct mix does not make the whole system an artificial
three-channel diagonal matrix. It removes one unmeasured density-allocation
operator while retaining the evidenced spectral cross-talk and mask behaviour.

## Relationship to V70 grain covariance

V70 showed that direct record mixing also owns almost all of the current
formed-negative same-position grain correlation (`about 0.007–0.034`). Its
withdrawal would move the unmeasured negative covariance to the conservative
independent-record endpoint while preserving each record's published 48 µm
RMS through the existing calibration.

This does **not** assert that real 5279 records are independent. It asserts that
the real covariance is unknown, and that inventing it through an operator which
also changes colour separation is not a neutral assumption.

## Next image gate

The next candidate should change one variable only:

```text
SUBEMULSION_DYE_RECORD_MIX[fast, medium, slow] := identity
```

It must then prove:

1. exact neutral H-D retention;
2. less than 2% error against every published 48 µm marginal RMS point;
3. unchanged processed-stock MTF, DIR coefficients, spectra, RAW decode,
   exposure, black, gamma and view policies;
4. no primary-colour impulses or gamut failures at native 5.7K;
5. measured chart and three diverse native scenes reviewed against V66;
6. projection, DPX, pointwise scan and historical managed scan clearly named,
   with no claim that a change in saturation is a measured 5279 correction.

If that isolated candidate passes, it is more defensible than retaining a
non-identity operator solely because an older render looked familiar.

## Artifacts

- implementation: `src/audit_v71_record_coupling_ownership.py`
- machine-readable audit:
  `research_runs/v71_record_coupling_ownership_audit.json`
- audit SHA-256:
  `88b97963771cb6a2c554fab52cb0ff7c0643b96243bb2f90aa63b7ecbb1993fb`
- implementation SHA-256:
  `d95eec5dff775af1abbc987155019f911a8c72c4ddf338adb3db13c903154107`

## Primary sources

1. Eastman Kodak Company, [*Exploring the Color
   Image*](https://www.kodak.com/content/products-brochures/Film/Exploring-the-Color-Image.pdf),
   pp. 42–44 on coloured masking couplers and unwanted absorption.
2. Eastman Kodak Company, [US 6,686,136 B1, *Color negative film element and
   process for developing*](https://patents.google.com/patent/US6686136B1/en),
   on record-specific dye formation, masking couplers, DIR and scanned-signal
   confounding.
3. Eastman Kodak Company, [US 5,298,376, *Photographic silver halide material
   with improved color saturation*](https://patents.google.com/patent/US5298376A/en),
   on separation/neutral density difference and interimage inhibition.
4. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements
   exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en),
   used only for within-record speed-layer architecture.
5. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
   H-1-5279t, March 2003, especially neutral H-D, spectral sensitivity and net
   dye-density graphs.
