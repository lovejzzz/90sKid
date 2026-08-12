# V69 named Cineon view policy and grain-ownership audit

Date: 2026-08-11
Status: delivery/view architecture; no 5279 image profile promoted

## Conclusion

V68 made a real printing-density DPX available. V69 asked the necessary next
question: can the existing “Blu-ray scan” be reconstructed from that DPX alone?

It cannot. The historical branch also consumes an undisclosed deterministic
mean image and uses it to reshape the stochastic modulation. Therefore it is a
two-input delivery treatment, not a Cineon viewing transform.

V69 now exposes two named, single-input policies that are pure functions of the
DPX data:

1. `cineon_open_monitor_v66`;
2. `cineon_bluray_pointwise_v66`.

The old result remains reproducible as
`legacy_managed_bluray_v40_to_v66`, but its provenance now says plainly that it
is historical grain management, not 5279 and not standard Cineon behaviour.

## What was hidden in the old scan branch

After mapping both the formed and deterministic-mean negatives through the
same Cineon curve, the historical branch:

- decomposes their difference into Rec.709 luma and opponent components;
- low-pass filters opponent modulation with a nominal `0.55 px` sigma at 2K;
- retains only `55%` of the remaining high-frequency opponent component;
- suppresses the whole signed delta near display black according to the mean
  image's luma;
- adds that managed delta back to the deterministic mean.

This requires the unexported mean negative. It cannot be reproduced by a LUT,
OCIO view, DPX reader or downstream DI system that receives only the scanned
film data.

## Three explicit T020 results

All outputs use the same V66 formed negative, the same frame-zero stochastic
realization and the same 5760×4320 printing-density codes.

| Branch | Input ownership | Purpose |
| --- | --- | --- |
| Cineon open monitor | one DPX | provisional open negative monitor |
| Cineon Blu-ray pointwise | one DPX | same lower-scale finish, no hidden mean |
| Legacy managed Blu-ray | DPX + hidden deterministic mean | historical V40–V66 delivery witness |

The legacy master's decoded MD5 remains
`d43af174bd6859ff5be73b7a1ad34de8`, matching V66/V68 exactly.

## What actually changes

At 1920×1440 review scale, pointwise versus legacy managed gives:

- linear RGB MAE: `0.00360626`;
- OKLab median/P95/P99: `0.01015 / 0.03338 / 0.05122`;
- median luma: identical at `0.03850`;
- P99 luma: identical at `0.50475`.

So this is not primarily a black, gamma or highlight change.

On a native-resolution 1024×1024 centre crop:

| Branch | High-pass luma RMS | High-pass opponent RMS |
| --- | ---: | ---: |
| Open monitor | 0.003045 | 0.004663 |
| Pointwise Blu-ray | 0.002756 | 0.003732 |
| Legacy managed Blu-ray | 0.002657 | 0.001448 |

Relative to the DPX-pure pointwise finish, the legacy branch removes only about
`3.6%` of high-frequency luma RMS but removes about `61.2%` of high-frequency
opponent RMS. That is the real visual ownership of the former “scan” look: it
is chiefly a colour-grain suppression policy.

## Accuracy decision

V69 does **not** declare the more colourful pointwise grain to be the true 5279
answer. Kodak publishes marginal R/G/B granularity, but the project still lacks
stock-specific cross-record covariance and a measured period-scanner chroma
aperture/electronic response. Independent colour records can produce real
opponent grain, while scanner optics and channel processing can reduce it.

Consequently:

- the DPX is the authoritative scan-data product;
- the two single-input policies are honest, reproducible views;
- the legacy managed output remains an explicitly named finish witness;
- none of the three may be used to infer the missing cross-record covariance;
- choosing a permanent chroma-grain strength by eye would again turn taste into
  a false emulsion measurement.

This finding also helps explain earlier feedback that some versions looked like
coarse digital colour noise while others felt unusually smooth: the difference
was partly downstream opponent-grain management, not only silver-halide size.

## Reproducibility

- Implementation: `emulsion5279/view_policy.py`
- Native audit: `src/audit_v69_cineon_view_policy.py`
- Audit JSON: `research_runs/v69_cineon_view_policy_audit.json`
- Comparison output:
  `outputs/native_5k_v69_cineon_view_policy_1f/T020/`
- Cineon code realization MD5: `52d3069d29d149852d6536c6d76ea9fd`

The next evidence target is no longer “more or less colour noise.” It is the
joint spatial covariance of the three developed 5279 records after optical
scan integration, separated from the scanner's own channel MTF and noise.
