# V80 — 5279 cross-record covariance bounds

Date: 2026-08-11
Status: **research-only; post-formation covariance mixing rejected**

## Decision

V80 rejects a post-formation 3×3 covariance matrix as the next image model.
Even an extreme positive correlation can move one aggregate opponent/luma ratio
toward the current delivery, but it simultaneously changes luma amplitude,
fails at other exposures, preserves severe nonlinear colour tails, changes the
scan, and violates the finite nonnegative-density boundary.

The missing 5279 statistic is therefore not one scalar or one channel matrix.
A defensible future candidate must form level-, spatial-frequency- and
speed-population-dependent shared finite events during activation/development.
It must preserve bounded site/dye identities and higher-order joint tails before
record density exists.

V72 pixels and the V79 managed projection boundary remain unchanged.

## Question inherited from V70 and V79

V70 established that Kodak's public 48 µm red-, green- and blue-record RMS
curves constrain only the diagonal of a joint covariance. V79 then showed the
visible consequence: with V72's conservative independent-record endpoint, the
direct projection contains unacceptable primary-colour tails, while the release
pipeline hides them with a historical display-space opponent low-pass.

The natural next question was whether the display filter could be replaced by
a physically earlier positive cross-record covariance while keeping every
published marginal RMS value fixed.

V80 answers a deliberately limited version of that question. It does not claim
to synthesize a real coating.

## Mathematical bound

Let the already formed V72 density residual be

\[
\delta\mathbf D(x,y)=\mathbf D_\text{formed}-\mathbf D_\text{mean}.
\]

Within each physical-frequency band, V80 measures its complex 3×3 spectral
covariance \(C_b\), retains the three diagonal powers, and substitutes the
positive-semidefinite equicorrelation target

\[
R_\rho=
\begin{bmatrix}
1&\rho&\rho\\
\rho&1&\rho\\
\rho&\rho&1
\end{bmatrix},\qquad
C_{b,\rho}=\operatorname{diag}(\sigma_b)R_\rho
\operatorname{diag}(\sigma_b).
\]

A whitening/recolouring operator maps \(C_b\) to \(C_{b,\rho}\). The sweep is

```text
ρ = 0 / 0.50 / 0.80 / 0.90 / 0.95 / 0.98 / 0.99 / 0.995 / 0.999
```

After inverse transformation, every record is rescaled around its unchanged
finite-realization mean until its original 48 µm aperture RMS is recovered.
Across T020 and uniform logE −1/0 fields, the worst marginal closure error is
`5.28e-10` relative. Frequency-band target covariance errors are at floating-
point noise scale.

This makes the test strict about the public second-order observable. It does
not preserve finite Bernoulli site identities or higher-order statistics, which
is precisely what the failure exposes.

## T020 native-strip result

The real fixture is the centered `5760×384` density strip from T020. Width and
physical pixel scale remain native; only vertical extent is reduced.

| Endpoint | luma RMS | opponent RMS | opponent/luma | isolated >0.08 | minimum formed density RGB |
|---|---:|---:|---:|---:|---|
| current V72 managed | 0.02369 | 0.00575 | 0.2429 | 0 | `[0, 0, 0]` original bound |
| direct, original covariance | 0.02382 | 0.02299 | 0.9654 | 37,904 | original bound |
| direct, ρ=0.90 | 0.03700 | 0.01195 | 0.3229 | 18,496 | `[-0.233, -0.064, -0.518]` |
| direct, ρ=0.99 | 0.03849 | 0.01018 | 0.2646 | 10,446 | `[-0.221, +0.020, -0.604]` |
| direct, ρ=0.995 | 0.03861 | 0.01008 | 0.2611 | 9,900 | `[-0.217, +0.035, -0.614]` |
| direct, ρ=0.999 | 0.03874 | 0.01000 | 0.2582 | 9,488 | `[-0.210, +0.056, -0.625]` |

At ρ `0.99`, the ratio looks superficially close to the managed value, but:

- luma RMS is `1.625×` current;
- opponent RMS is still `1.770×` current;
- `10,446` severe isolated colour events remain instead of zero;
- only `15` samples cross below zero, but their magnitude reaches about
  `−0.60 D`, so this is not a harmless floating-point epsilon.

Moving to `0.999` improves the aggregate ratio only slightly and still leaves
`9,488` severe events. Second-order correlation does not specify the joint tail.

## One constant correlation cannot span exposure

| Uniform field | current opponent/luma | direct ρ=0.99 | direct ρ=0.999 |
|---|---:|---:|---:|
| log E −1 | 0.2545 | 0.4674 | 0.4510 |
| log E 0 | 0.3316 | 0.3493 | 0.3232 |

An extreme fixed correlation nearly matches the higher-exposure aggregate but
misses the lower-exposure result badly. This is expected from a multilayer
negative: fast/medium/slow activation shares change with exposure, and the
three records do not have identical marginal amplitudes or native NPS.

The required joint statistic must therefore depend on exposure and population,
not merely record labels.

## Scale behaviour improves for the wrong reason

At ρ `0.999`, exact 3×3 integration retains:

| Field | luma retained | opponent retained |
|---|---:|---:|
| T020 strip | 51.26% | 56.54% |
| uniform log E −1 | 47.53% | 65.32% |
| uniform log E 0 | 44.36% | 61.62% |

This is much less split than the current managed projection's roughly
`43–46%` luma versus `96%` opponent retention. It supports V79's causal
diagnosis: an upstream covariance can preserve high-frequency colour structure
through the same aperture instead of concentrating all surviving colour at low
frequency.

But the amplitude, tails, exposure dependence and density bounds all fail.
Better scale behaviour alone cannot validate the construction.

## The scan proves this is not a projection-only knob

Changing negative covariance necessarily changes both observers. At ρ `0.999`:

| Uniform field | scan luma current → candidate | scan opponent current → candidate |
|---|---:|---:|
| log E −1 | 0.01404 → 0.02133 | 0.00983 → 0.00512 |
| log E 0 | 0.01603 → 0.02472 | 0.01045 → 0.00503 |

Thus a true negative-layer correction cannot be used merely to make the
projection look different from the scan. It changes the density data supplied
to both. Any future candidate must pass both observers and the DPX coordinate.

## Why the density bound failure matters

The original V72 formed strip has exactly zero negative-density samples. Every
post-formation covariance endpoint, including ρ `0`, creates some below-zero
record densities. The operation linearly combines already developed residuals
whose finite positive bounds and skewed tails differ by record, exposure and
population. Matching a covariance matrix does not preserve that feasible set.

Clipping the negatives would be worse: it would silently alter mean density,
48 µm RMS, covariance and tails after the fact. V80 therefore records the
violation and rejects the operator instead of repairing it cosmetically.

## Corrected physical direction

The next plausible architecture is a shared-event model, not density mixing:

1. keep each record's Kodak-constrained mean H-D and 48 µm marginal RMS;
2. let some finite activation/development events have shared latent causes
   across selected speed populations;
3. keep record-specific dye formation—one shared cause need not mean one dye;
4. make shared fractions exposure dependent through the existing activation
   probabilities;
5. allow spatial cross-spectra to differ by population/cloud size;
6. preserve binomial bounds and non-Gaussian joint tails before DIR and dye
   density;
7. propagate the same formed negative to projection, scan and DPX;
8. classify every shared-event coefficient as an uncertainty prior until real
   5279 cross-NPS measurements exist.

General Kodak patent literature establishes that interchannel correlation is a
separate statistic worth measuring. It does not disclose these 5279 shared-
event coefficients. The architecture may therefore be researched as bounded
endpoints, never fitted by taste and renamed as stock truth.

## Production consequence

- no V80 image profile is promoted;
- V72 and its managed projection delivery remain current;
- no post-formation covariance matrix is added to the engine;
- no negative density is clipped to rescue the experiment;
- the next candidate, if pursued, must operate at finite-event formation and
  pass density bounds, marginal RMS, native tails, 2K scale, scan and DPX gates.

## Artifacts

- implementation: `src/audit_v80_cross_record_covariance_bounds.py`
- machine-readable audit:
  `research_runs/v80_cross_record_covariance_bounds_audit.json`
- implementation SHA-256:
  `e1fe12ea3a06e495f63a61cf56e5c50f8ef5af8d349d86a80ee1c782135a7640`
- audit SHA-256:
  `822866a699906a393916330e676165bbf9412a885dc63365e649d97c280ea192`

## Primary-source boundary

1. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
   H-1-5279t, March 2003: marginal 48 µm granularity, H-D, MTF and spectral
   curves; no cross-record covariance or cross-NPS.
2. Eastman Kodak Company, [US 5,641,596, *Adjusting film grain properties in
   digital images*](https://patents.google.com/patent/US5641596): marginal
   standard deviation, spatial correlation and interchannel correlation are
   distinct level-dependent measurements.
3. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements
   exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en):
   general fast/medium/slow multilayer architecture, not 5279 cross-record
   coefficients.
