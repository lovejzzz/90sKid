# V81 — shared finite-event Bernoulli bounds

Date: 2026-08-11
Status: **analytic research only; no sampler or image profile promoted**

## Decision

If cross-record covariance is explored again, the mathematically valid
architecture is shared finite Bernoulli events during activation—not linear
mixing of completed density.

However, V81 also proves that an arbitrary common correlation such as V80's
ρ `0.99` is generally impossible even before density formation. Different
records have different activation probabilities. Their Fréchet bounds therefore
limit the maximum achievable correlation while exact Bernoulli marginals are
preserved.

Across 20 neutral log-exposure samples, three matched speed populations and
three record pairs (`180` pair/exposure cases), a target correlation is
mathematically feasible in:

| target correlation | feasible cases | fraction |
|---:|---:|---:|
| 0.80 | 172 / 180 | 95.56% |
| 0.90 | 129 / 180 | 71.67% |
| 0.95 | 75 / 180 | 41.67% |
| 0.99 | 13 / 180 | 7.22% |

Thus V80's equal ρ `0.99` sweep was not merely unmeasured. For most active
population/record pairs it lay outside the feasible finite-site set. This
strengthens V80's rejection of post-formation covariance fitting.

## Exact Bernoulli bound

For two finite activation indicators

\[
X_i\sim\operatorname{Bernoulli}(p_i),\qquad
X_j\sim\operatorname{Bernoulli}(p_j),
\]

their joint activation probability must satisfy

\[
\max(0,p_i+p_j-1)
\leq P(X_i=1,X_j=1)
\leq \min(p_i,p_j).
\]

The maximum positive correlation is therefore

\[
\rho_{ij}^{\max}=
\frac{\min(p_i,p_j)-p_ip_j}
{\sqrt{p_i(1-p_i)p_j(1-p_j)}}.
\]

It reaches one only when the two Bernoulli marginals are identical. Near the
toe or shoulder, a small absolute difference in activation probability can
produce a much lower maximum correlation because one population has much less
remaining variance.

## A bounded shared-event family

V81 defines one valid positive-dependence uncertainty family:

1. draw a Bernoulli selector \(Z\sim\operatorname{Bernoulli}(\alpha)\);
2. if \(Z=1\), matched record populations compare their own probabilities
   against one shared \(U\sim U(0,1)\);
3. if \(Z=0\), each record uses an independent uniform variable.

For each record,

\[
P(X_i=1)=p_i
\]

exactly. Counts remain finite and nonnegative. Pair covariance and correlation
are

\[
\operatorname{Cov}(X_i,X_j)
=\alpha[\min(p_i,p_j)-p_ip_j],
\]

\[
\rho_{ij}=\alpha\rho_{ij}^{\max}.
\]

This automatically makes correlation exposure dependent even when α is held
constant. It also specifies a joint tail rather than only a covariance matrix.

The construction is a mathematical bound, not evidence that 5279 has aligned
sites or a common latent activation variable.

## Current V72 activation limits

The following ranges cover the nine matched fast/medium/slow record pairs at
each neutral exposure:

| log E | minimum possible positive maximum | highest possible positive maximum |
|---:|---:|---:|
| −3.0 | 0.9148 | 0.9892 |
| −2.0 | 0.9131 | 0.9977 |
| −1.0 | 0.8444 | 0.9953 |
| 0.0 | 0.7808 | 0.9611 |
| +0.5 | 0.7508 | 0.9445 |

Examples explain the exposure dependence:

- at logE `−1`, fast green/blue activations are `0.8557/0.8926`, limiting
  their correlation to `0.8444` even under a fully common latent event;
- at logE `−1`, slow red/green activations are much closer at
  `0.3814/0.3792`, allowing up to `0.9953`;
- at logE `0`, fast green/blue are already near saturation at
  `0.9715/0.9824`, but their unequal remaining variances limit correlation to
  `0.7808`;
- at logE `+0.5`, the same fast pair falls to a maximum of `0.7508`.

One symmetric ρ cannot represent these nine populations. The V80 result that
one fixed density correlation failed across logE `−1/0` was therefore not an
accident of the observer; it contradicted the activation geometry upstream.

## Why α still cannot be selected

The shared-event family solves mathematical problems that V80 could not:

- exact Bernoulli marginal probability;
- finite, nonnegative counts;
- exposure-dependent feasible correlation;
- a defined higher-order joint event structure;
- no post-density clipping.

It does not solve the stock-identification problem:

- physical silver-halide grains in different records are not one aligned site
  lattice;
- fast/medium/slow site counts, cloud sizes and offsets differ by record;
- a common optical/development cause may couple different populations, not
  only matched fast-fast, medium-medium and slow-slow pairs;
- DIR can introduce asymmetric and spatially delayed dependence after
  activation;
- positive common activation is not the only possible source of cross-power;
- no public 5279 document identifies α, topology, cross-frequency phase or
  exposure dependence.

Consequently α may be swept as an uncertainty coordinate, but it cannot be
fitted to make the output resemble remembered film and then called a 5279
measurement.

## Correct next implementation boundary

A future research sampler could test α endpoints while preserving the current
engine's exact deterministic and marginal contracts, but it must satisfy all of
the following before any picture comparison matters:

1. use shared latent events inside the class/population binomial sampler;
2. preserve each record/population's Bernoulli marginal exactly;
3. preserve each record's published post-process 48 µm RMS after DIR;
4. never create negative microscopic or final record density;
5. keep absolute-frame deterministic identity across CPU/Metal execution;
6. publish the achieved exposure- and population-dependent cross-covariance,
   not only the requested α;
7. pass native higher-order colour-tail gates before display management;
8. propagate one identical negative into projection, scan and DPX;
9. keep V79's managed delivery as the release boundary until a physical
   endpoint succeeds independently;
10. label the entire sweep as an uncertainty study.

V81 does not yet authorize that sampler implementation. It first establishes
the feasible set which such an implementation must obey.

## Production consequence

- no V81 image pixels exist;
- no α is added to V72;
- no ρ matrix is added after density formation;
- V79's managed projection remains the honest release safety boundary;
- future covariance experiments now have an exact finite-event mathematical
  contract and can be rejected before rendering if they violate it.

## Artifacts

- implementation: `src/audit_v81_shared_finite_event_bounds.py`
- machine-readable audit:
  `research_runs/v81_shared_finite_event_bounds_audit.json`
- implementation SHA-256:
  `5586e922a4980fa90b4c479c95c02f73d40e30636ade4e5e5c254011a7a28c30`
- audit SHA-256:
  `0a5d7a20c17af3a4cde189c8dc97d4f7198888374fd099ae1da5c99f1734e3e5`

## Primary-source boundary

V81's Fréchet/Bernoulli equations are probability identities, not empirical
5279 claims. The stock evidence boundary remains:

1. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
   H-1-5279t, March 2003: neutral H-D and marginal granularity, not joint
   site-level statistics.
2. Eastman Kodak Company, [US 5,641,596, *Adjusting film grain properties in
   digital images*](https://patents.google.com/patent/US5641596): interchannel
   correlation is distinct from standard deviation and spatial correlation.
3. Eastman Kodak Company, [US 5,314,793, *Multicolor photographic elements
   exhibiting an enhanced speed-granularity relationship*](https://patents.google.com/patent/US5314793A/en):
   general multilayer speed architecture only; no 5279 cross-record shared-site
   topology.
