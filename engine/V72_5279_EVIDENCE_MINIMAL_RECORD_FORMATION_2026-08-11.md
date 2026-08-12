# V72 — 5279 evidence-minimal record formation

Date: 2026-08-11
Status: **accepted as the current evidence-minimal baseline; not a measured 5279 covariance model**

## Decision

V72 replaces one unidentified operator with identity:

```text
SUBEMULSION_DYE_RECORD_MIX[fast, medium, slow] := I3
```

Everything else remains V66: Panasonic ProRes RAW decoding, exposure, the
vector-traced 5279 H-D and 48 µm RMS curves, finite sites, DIR, processed-stock
MTF, net dye/mask spectra, 2383 spectral printing, Cineon printing density,
black, gamma and both named viewing branches.

This is a promotion of an **evidence boundary**, not a claim that real 5279
colour records are independent. The old matrix was introduced as a bounded
structural guess. V70/V71 showed that it nevertheless owned almost all of the
model's weak same-position colour covariance and about `1–2.5%` of
deterministic off-record response. No public 5279 observable selected those
coefficients.

V72 passes the marginal-RMS, native scene, chart, paired colour-tail and full
engine-regression gates. Identity is therefore more defensible than retaining
the guessed matrix, while the real joint covariance and exact interimage
coefficients remain explicitly unknown.

## What the renewed layer research changes

The period Kodak architecture evidence strengthens the V71 distinction between
four mechanisms which had previously been conflated.

Kodak US 5,455,150 gives a concrete multilayer colour-negative example with
lowest/medium/high sensitivity red and green coatings and lowest/high
sensitivity blue coatings. Within each record, progressively faster layers use
different silver-halide populations and coupler/DIR packages. The red layers
principally contain cyan-forming coupler, green layers magenta-forming coupler,
and blue layers yellow-forming coupler. DIR compounds are placed selectively
by layer and population.

That is consistent with the engine's finite fast/medium/slow architecture, but
not with a generic symmetric rule that directly deposits every source
population into all three destination dye records. It supports this ownership:

1. spectral overlap changes which record is exposed;
2. the exposed layer principally forms its own dye hue;
3. mobile DIR changes development in receiving layers;
4. coloured mask consumption and imperfect dye absorption appear in the net
   spectral density and in printer/scanner integration.

The same patent example also contains small amounts of off-hue coupler in some
blue layers. That is an important warning: exact identity is **not** proven to
be the chemical truth. A real stock can contain asymmetric, population-specific
cross-components. But this example is not disclosed as the 5279 coating recipe,
and it gives no 5279 joint grain covariance. It therefore cannot justify the
old smooth, column-normalized three-by-three matrices either.

The accurate conclusion is narrower:

> Identity is the minimum-assumption endpoint for an unidentified direct
> density-allocation operator. It is not a substitute for a measured 5279
> separation wedge or cross-power spectrum.

## Single-variable isolation

V72 uses V66's complete profile and then changes only the direct population
record map. The regression test verifies exact retention of:

- vector-traced 5279 sensitometry;
- vector-traced net dye and D-min spectra;
- processed-stock MTF parameters;
- deterministic and stochastic DIR topology/strength;
- exposure-dependent 48 µm granularity targets;
- V66's printing-density Cineon coordinate and observer lattice.

The test also found a state-ownership omission: older profiles did not restore
`SUBEMULSION_DYE_RECORD_MIX` after V72 had changed it. V37 now restores the
checksum-frozen archive matrix, so `V72 -> V66` and every older-profile
downgrade are history independent.

## Quantitative gates

### 1. Published 48 µm marginal RMS

The physical circular-aperture audit covers the full modelled exposure range.
Worst absolute relative error is `1.2840%`, below the existing `2%` limit.

This validates only the three marginal record amplitudes. It still does not
identify the off-diagonal covariance, spatial cross-spectrum, higher-order
tails, exact coating recipe or exact DIR coefficients.

### 2. T020 native 5.7K scene

The delivered-master-derived comparison against V66 gives:

| Branch | linear RGB MAE | OKLab Δ p95 | median absolute luma change | midtone luma ratio |
|---|---:|---:|---:|---:|
| 2383 projection | 0.000848 | 0.00513 | 0.000363 | 1.00841 |
| managed scan | 0.000938 | 0.00655 | 0.000412 | 1.00481 |

No white clipping is introduced. The original native colour-tail gate passes
both branches.

### 3. T003 frame 160 DKC-Pro chart

The outdoor chart is used as a paired transport diagnostic only; its scene SPD
and the manufacturer's Lab reference illuminant/observer are not identified.

| Branch | neutral max OKLab Δ | neutral max luma-ratio change | colour median chroma ratio | max hue shift |
|---|---:|---:|---:|---:|
| 2383 projection | 0.000725 | 0.290% | 1.01746 | 0.710° |
| managed scan | 0.000893 | 0.348% | 1.01848 | 0.540° |

The small `1.7–1.8%` median chroma increase is the expected consequence of
removing a matrix which deliberately reduced separation. It is not fitted to
the chart and is not labelled a measured saturation correction.

### 4. Correcting a false cross-scene grain gate

The T020-derived absolute projection-tail thresholds fail on T003 under both
V66 and V72. T003 contains many real high-contrast chromatic chart/foliage
edges, so an edge-based isolated-pixel statistic is not portable as an
absolute stock property.

The same-seed paired comparison is the valid regression question:

| T003 projection tail | V66 | V72 | change |
|---|---:|---:|---:|
| dark opponent p99.99 | 0.039726 | 0.039702 | -0.000024 |
| median-band opponent p99.99 | 0.049912 | 0.049805 | -0.000107 |
| isolated >0.06 / million | 10.9947 | 10.9062 | -0.0884 |
| isolated >0.08 / million | 0 | 0.0571 | +0.0571 (one native pixel; within limit) |

The managed scan passes its absolute tail gate in both versions. All paired
no-regression gates pass.

### 5. Engine regression

The complete compact suite passes:

```text
Ran 57 tests in 271.706s
OK
```

This includes V72 isolation, V66 restoration, profile conformance, Cineon DPX,
finite-density/FSD, ROI kernels, RAW highlight handling and V41 colour
transport.

## What V72 means visually

V72 should be close to V66. It does not change tone, black, gamma, exposure,
grain strength or view transforms. It slightly restores colour separation and
removes an invented source of cross-record grain correlation. The historical
managed scan remains visibly more monochromatic because that behaviour belongs
to its explicit hidden-mean opponent-grain finish, not to the 5279 negative.

Therefore V72 is more correct as a model boundary even if a viewer prefers a
previous version's softer colour separation. Preference is not used as stock
evidence.

## Remaining uncertainty and next experiment

V72 does not finish the stock. The largest unresolved negative-side quantities
are now stated cleanly:

1. the 2D auto-NPS of each 5279 record versus exposure;
2. the complex R-G, R-B and G-B cross-power spectra;
3. population-specific DIR causer/receiver topology and range;
4. any asymmetric off-hue coupler contribution in the actual 5279 recipe;
5. scanner noise/MTF/crosstalk separated from film structure.

The next safe research step is a V73 topology audit of the current DIR prior
against period layer-order and coupler-placement evidence. It must remain an
identifiability study unless stock-specific data are found; a generic patent
example must not be promoted into a 5279 coefficient table.

## Artifacts

- profile: `src/v72_profile.py`
- native/chart gate: `src/audit_v72_identity_record_mix_candidate.py`
- machine-readable native/chart audit:
  `research_runs/v72_identity_record_mix_candidate_gate.json`
- 48 µm audit: `research_runs/v72_5279_aperture_rms_audit.json`
- T020 absolute colour-tail audit:
  `research_runs/v72_native_colour_grain_gate.json`
- paired T003 inputs:
  `research_runs/v66_native_colour_grain_gate_t003.json` and
  `research_runs/v72_native_colour_grain_gate_t003.json`
- native review renders:
  `outputs/native_5k_v72_identity_record_mix_candidate_1f/T020` and
  `outputs/native_5k_v72_identity_record_mix_candidate_1f/T003_frame160`

Checksum-locked authored evidence:

| Artifact | SHA-256 |
|---|---|
| `src/v72_profile.py` | `b8b3ef823109cb174fc8a247c4de037ae0bedbc6ec2824bee0f46a1518951857` |
| `src/audit_v72_identity_record_mix_candidate.py` | `d84896960aa671234c16fc1f21e45b1a56f5b4e81e6c82bf521a3c4d3b0bd40a` |
| `research_runs/v72_identity_record_mix_candidate_gate.json` | `e2c2bb8a7ee5689fc92fcdb9e5f388cc16c4a6a656647ebea2c486d6e51ce338` |
| `research_runs/v72_5279_aperture_rms_audit.json` | `81e5234b473afa39a63720d11de0a6a669c584070c621c65db77e7e430f60b0e` |
| `research_runs/v72_native_colour_grain_gate.json` | `be7b3ca4812ec69dfe13a82cff66e13fd6eaa07c47831a5c53d76631d5012e58` |
| `research_runs/v72_native_colour_grain_gate_t003.json` | `ab9d677e091669e509b036f79eec8bc6a6455e90847a190589e31f02fe755842` |
| `research_runs/v66_native_colour_grain_gate_t003.json` | `4ff957776ba01c99f672ef72e8d1453ecf1e784cb1abcae114a1d4aa763084c4` |

## Primary sources

1. Eastman Kodak Company, [*KODAK VISION 500T Color Negative Film 5279 / 7279*, H-1-5279](https://125px.com/docs/motionpicture/kodak/5279.pdf), neutral H-D, processed-stock MTF, 48 µm diffuse RMS, spectral sensitivity and net dye-density graphs.
2. Eastman Kodak Company, [US 5,455,150, *Color photographic negative elements with enhanced printer compatibility*](https://patents.google.com/patent/US5455150), especially the population-specific red/green/blue layer recipes and DIR/coupler placement. This is used only as period Kodak architecture evidence, not identified as the 5279 formula.
3. Eastman Kodak Company, [US 5,298,376, *Photographic silver halide material with improved color saturation*](https://patents.google.com/patent/US5298376A/en), on interlayer interimage inhibition and separation-versus-neutral gamma.
4. Eastman Kodak Company, [US 6,686,136 B1, *Color negative film element and process for developing*](https://patents.google.com/patent/US6686136B1/en), on record-specific dye formation, masks, DIR and scan-signal confounding.
5. Eastman Kodak Company, [*Exploring the Color Image*](https://www.kodak.com/content/products-brochures/Film/Exploring-the-Color-Image.pdf), pp. 42–44 on coloured masking couplers and unwanted dye absorption.
