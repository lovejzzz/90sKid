# V83 · Shared finite events through stochastic DIR

Date: 2026-08-11
Status: analytic + direct-sampling research audit; **no image change**

## Question

V81 found an exact finite-event uncertainty family and V82 proved that its
three-record joint law is legal. V83 asks the next, stricter question: if those
events are formed by the current five-size-class, fast/medium/slow V72 model,
does stochastic DIR preserve Kodak's published processed-stock 48 µm diffuse
RMS granularity curves without inventing another completed-density repair?

## A correction to our own description

Re-reading the complete active profile chain found an important documentation
error. Current V72 does **not** inherit V39's `pre_dir_dye_yield` calibration.
It inherits V40's `post_coupling_residual` mode.

The code currently does this:

1. independently predicts each destination record's 48 µm variance before
   stochastic DIR;
2. samples and filters all finite site populations;
3. applies stochastic intralayer and interimage DIR;
4. sums layer density into the three records;
5. multiplies each completed record residual by the target/predicted RMS ratio.

The multiplier is applied after DIR, but its denominator contains neither the
DIR transfer nor cross-record source covariance. Calling the current path
"pre-DIR calibrated" was therefore wrong. V83 reproduces the executable V72
path literally rather than continuing from that mistaken description.

For record `r`, production uses

\[
g_r(E)=\frac{\sigma_{Kodak,r}(E)}
{\sqrt{\sum_p c_{rp}^2\int |A_{48}(f)|^2S_{rp}(f,E)\,df}}
\]

and applies `g_r` to the already DIR-coupled density residual. The stochastic
DIR response is audited rather than silently inserted into this denominator.

## Exact spatial model

The audit reconstructs the discrete Fourier transfer of the production
operators at a 5760-pixel, 24.9 mm film-width scale:

- three records × fast/medium/slow populations × five finite size classes;
- record/population-specific site counts, cloud disks and optical Gaussian
  integration;
- V37 stable balanced subpixel phases;
- V72 identity record summation;
- three stochastic DIR diffusion lengths, including intralayer high-pass and
  interimage low-pass terms;
- Kodak's circular 48 µm aperture.

The 256² transfer grid reproduces the existing spatial
`filtered_kernel_power()` calculation with maximum relative error
`1.27743e-7` over all 45 class kernels.

For matched sites in record pair `i,j`, the V81 common-event family contributes

\[
\operatorname{Cov}(X_i,X_j)
=\alpha\left[\min(p_i,p_j)-p_ip_j\right].
\]

If the two records contain different integer site counts in a size class, only
the smaller count is matched; extra sites remain independent. Distinct size
classes and speed populations remain independent in this bounded experiment.

## Result: marginal RMS closes, but alpha is still not identified

Twenty neutral exposures from `−4.0` to `+0.75 logE` were evaluated at
`alpha = 0/.25/.50/.75/1`. A deliberately conservative ±5% engineering gate
was used; Kodak did not publish a numerical tolerance for the visually
digitized graph.

| alpha | passing exposures | maximum R error | maximum G error | maximum B error | global maximum |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 20/20 | 0.547% | 0.831% | 1.076% | 1.076% |
| 0.25 | 20/20 | 0.535% | 0.816% | 1.065% | 1.065% |
| 0.50 | 20/20 | 0.523% | 0.802% | 1.055% | 1.055% |
| 0.75 | 20/20 | 0.511% | 0.787% | 1.045% | 1.045% |
| 1.00 | 20/20 | 0.499% | 0.772% | 1.035% | 1.035% |

The worst point is near `−2 logE`, where stochastic DIR increases blue-record
RMS by about 1.08% in the current independent model. Increasing shared-event
alpha slightly reduces that gain; it does not break the published marginal
curve.

This is not evidence that `alpha=1` is correct. At `−2 logE`, the processed
48 µm record correlations change from approximately zero at `alpha=0` to:

```text
rho_RG = 0.954
rho_RB = 0.847
rho_GB = 0.809
```

At the five key exposures, full sharing spans roughly `0.714–0.954` depending
on record pair and exposure. Kodak's marginal RMS graph contains no information
that can select among those radically different colour-grain structures.

## Direct finite-event verification

The frequency-domain algebra was checked against an independent, direct
finite-event sampler rather than against another Gaussian covariance transform.
For every matched site the verifier samples the exact mixture of:

- all eight independent RGB Bernoulli outcomes; and
- the four nested outcomes created by one common uniform threshold.

It then filters the actual integer site fractions, runs the production
stochastic DIR function and measures four cropped 384² patches at `−2 logE`.
The 331,776 interior samples per endpoint agree with the analytic result:

| alpha | maximum RMS relative difference | maximum correlation difference |
|---:|---:|---:|
| 0 | 0.525% | 0.0172 |
| 1 | 1.110% | 0.0340 |

Those residuals are consistent with finite patch/seed uncertainty and are far
smaller than the difference between the independent and fully shared laws. The
source spectral matrices remain positive-semidefinite at every frequency and
every tested endpoint.

## Decision

- V81's single-common-alpha family passes the V83 marginal-RMS pre-render gate.
- It receives **permission to be rendered only as labelled uncertainty
  endpoints**, not as the new 5279 baseline.
- V72 pixels and production parameters remain unchanged.
- No new post-density closure, clipping, colour correction or aesthetic choice
  is added.
- The next render must compare at least the independent endpoint against one or
  more restrained shared endpoints through both scan and projection observers;
  it must report achieved density covariance, tail counts and scale-integrated
  luma/opponent spectra.
- `alpha=1` is a mathematical extreme, not a plausible default: its near-common
  48 µm colour texture is useful as a diagnostic upper bound.

## What this changes in our understanding

The public 48 µm curves can validate the **amount** of noise in each analytical
record while remaining almost blind to whether the visible texture is
electronic-looking colour noise or coherent dye-density structure. That is why
earlier versions could satisfy three marginal RMS numbers and still look wrong.
"Grain is the image" therefore requires a joint finite-event law and an
observer/scale test in addition to marginal granularity.

V83 also narrows the calibration issue: the current V72 post-coupling residual
gain is internally close to the Kodak marginal target, but its name and
denominator expose a stage-ownership compromise inherited from V40. It should
not be silently rewritten during the covariance experiment. A future dedicated
audit may compare this architecture with chemically upstream calibration, but
only with the V39 coloured-tail failure kept in the gate.

## Artifacts

- implementation: `src/audit_v83_shared_event_dir_closure.py`
- machine-readable audit:
  `research_runs/v83_shared_event_dir_closure_audit.json`
- implementation SHA-256:
  `ca511d5e0dc3285e55518feb3ec0ff4be5cd33df86cf95c8d7149887f2fbf82a`
- audit SHA-256:
  `a236ce9941a1c3e311bd0b3a9030dbf8647638869be7df8edbb73f555acc42cb`

## Evidence boundary

The common-alpha sampler is valid probability theory, not a disclosed 5279
coating formula. Public 5279 material does not publish physical site alignment,
cross-record covariance, native cross-NPS, three-record higher moments or the
stock-specific stochastic DIR topology. V83 proves consistency with the known
marginal RMS boundary; it does not measure the missing joint law.
