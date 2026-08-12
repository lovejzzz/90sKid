# V82 — three-record Bernoulli compatibility

Date: 2026-08-11
Status: **analytic research only; no sampler or image profile promoted**

## Decision

V81's pairwise Fréchet bounds are necessary but not sufficient for a colour
negative. Red, green and blue activation must come from one nonnegative joint
distribution over eight possible event states. Three independently chosen
pair-correlation controls can satisfy every two-record bound and even produce a
positive-semidefinite 3×3 correlation matrix while still admitting no valid
RGB Bernoulli distribution.

V82 therefore rejects three independent record-pair correlation sliders as a
future sampler interface. The single common-`alpha` family introduced by V81 is
jointly valid at all 60 tested record-population/exposure triplets and all five
tested endpoints, but `alpha` remains unmeasured. V72 pixels remain unchanged.

## Exact three-record condition

Let record activation marginals be `pR`, `pG`, `pB`; pairwise joint activation
probabilities be `qRG`, `qRB`, `qGB`; and the three-way joint activation be
`t = P(R=G=B=1)`.

All eight Bernoulli cell probabilities are nonnegative if and only if `t` lies
inside:

\[
\begin{aligned}
t_{min}=\max(&0, q_{RG}+q_{RB}-p_R, q_{RG}+q_{GB}-p_G,\\
             &q_{RB}+q_{GB}-p_B),\\
t_{max}=\min(&q_{RG},q_{RB},q_{GB},\\
             &1-p_R-p_G-p_B+q_{RG}+q_{RB}+q_{GB}).
\end{aligned}
\]

The pair targets define a valid three-record Bernoulli law only when
`t_min <= t_max`. Positive semidefiniteness of the correlation matrix does not
enforce these eight probability inequalities.

## V72 activation result

The audit covers 20 neutral log-exposures from `-4.0` through `+0.75`, three
fast/medium/slow population triplets and therefore 60 RGB activation triplets.

For an equal requested pair correlation:

| requested pair correlation | all three pair bounds valid | joint RGB law valid | total triplets |
|---:|---:|---:|---:|
| 0.80 | 52 | 52 | 60 |
| 0.90 | 30 | 30 | 60 |
| 0.95 | 15 | 15 | 60 |
| 0.99 | 0 | 0 | 60 |

V81 found 13 individually feasible pair/exposure cases at `rho=0.99`. V82 adds
the stronger colour-film result: no fast, medium or slow RGB triplet can support
all three pair correlations at `0.99` simultaneously.

## Independent pair-alpha grid

V82 also sweeps independent shared-event fractions for RG, RB and GB:

```text
alpha_RG, alpha_RB, alpha_GB in {0, .25, .50, .75, 1}
```

Across `60 × 125 = 7,500` triplet/parameter sets:

- 4,038 are jointly feasible;
- 3,462 are jointly impossible;
- 1,484 are positive-semidefinite but still have no nonnegative eight-cell
  Bernoulli distribution.

One concrete counterexample occurs at log exposure `-4`, fast population, with
activation probabilities `[0.027264, 0.030324, 0.026696]` and pair alphas
`[0, .25, 1]`. Its correlation matrix minimum eigenvalue is positive
(`0.03137`), but the required three-way interval has width `-0.006393`; no value
of `P(111)` can make every cell nonnegative.

This is why a covariance matrix alone cannot define colour-film grain. It can
be a legal continuous Gaussian statistic and still be an illegal finite-site
event law.

## Why the V81 common-alpha family survives

V81's construction uses one selector:

1. with probability `alpha`, all three records compare their own activation
   probability against one shared uniform variable;
2. otherwise the three records use independent uniforms.

Its pairwise joints are

\[
q_{ij}=\alpha\min(p_i,p_j)+(1-\alpha)p_ip_j
\]

and its three-way joint is

\[
t=\alpha\min(p_R,p_G,p_B)+(1-\alpha)p_Rp_Gp_B.
\]

The audit explicitly reconstructs all eight cells. Every tested endpoint
`alpha = 0/.25/.50/.75/1` is nonnegative, normalized and marginally exact for
all 60 triplets.

This validates one uncertainty architecture. It does not identify real 5279:

- physical sites in different records are not an aligned RGB lattice;
- one latent cause may couple unmatched fast/medium/slow populations;
- DIR can add asymmetric and spatially displaced dependence later;
- pair cross-power phase and cloud offsets remain unknown;
- public 5279 material provides no `alpha`.

## Production consequence

- no V82 image pixels exist;
- no three independent pair-correlation controls are added;
- no covariance matrix is accepted merely because it is PSD;
- the V81 single-common-event family is retained only as a mathematically valid
  uncertainty coordinate;
- any future image sampler must publish all eight achieved joint cell
  probabilities, not only an RGB covariance matrix;
- V79's managed projection remains the release safety boundary until a physical
  upstream candidate passes both observers without it.

## Next bounded experiment

Before any native image render, the next audit should test whether a
single-common-event sampler can preserve each record's processed 48 µm RMS
after DIR without post-density rescaling. If it cannot, the architecture must
be rejected before subjective comparison. If it can, `alpha` endpoints may be
rendered as explicitly labelled uncertainty cases—not as a V5279 coefficient.

## Artifacts

- implementation: `src/audit_v82_three_record_bernoulli_polytope.py`
- machine-readable audit:
  `research_runs/v82_three_record_bernoulli_polytope_audit.json`
- implementation SHA-256:
  `7358f331f1069e9f0cc5b64418aea799ee6573691d38536d4cc3f9d054775d1d`
- audit SHA-256:
  `084b88f969ab0accc46eda086050abfd341a012b35ea10ef39fc5f39ae06ced0`

## Evidence boundary

The eight-cell compatibility equations are probability identities, not
empirical film claims. The material boundary remains Kodak's 2003 5279 sheet:
processed H-D, MTF, spectral and marginal 48 µm granularity curves, with no
three-record joint activation distribution, covariance or cross-NPS.
