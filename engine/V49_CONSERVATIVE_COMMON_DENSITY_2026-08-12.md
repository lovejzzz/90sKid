# V49 — Conservative common-density formation

Date: 2026-08-12

Public profile key: `v49r`

Public version: V49

## Why V48 failed visually

V48 produced its deterministic 5279-to-2383 mean through the direct physical
observer, but added a separately managed formed-minus-mean residual in display
RGB. That residual belonged to a different observer graph. In lifted shadows it
could therefore appear as isolated red, green, and blue points: the visual
signature of electronic chroma noise rather than formed photographic density.

The defect was not excessive grain strength alone. It was an ownership error:
the stochastic image left the material-density graph and was reintroduced after
colour formation.

## Evidence boundary

Kodak's published 5279 granularity curves constrain the marginal Status-M RMS
of the three analytical records. They do not publish the cross-record
covariance, cross-power spectrum, or event registration needed to identify a
unique coloured-grain law. Releasing independently sampled record residuals as
RGB colour would therefore be more specific than the evidence permits.

V49 retains the part that can be stated conservatively: one scalar density
field shared by all three records. This is a hypothesis boundary, not a claim
that real 5279 has perfectly registered record events.

## Publication transform

For record residuals `delta_D_c` and local published marginal RMS `sigma_c`,
V49 computes

```text
z_common      = (1 / sqrt(3)) * sum_c(delta_D_c / sigma_c)
sigma_common  = min_c(sigma_c)
delta_D_common = sigma_common * z_common
D49_c          = max(0, Dmean_c + delta_D_common)
```

The normalized symmetric sum does not privilege a colour record. The minimum
local marginal makes the released common component no stronger than any Kodak
marginal. Remaining opponent-density variance is withheld as unidentified; it
is not suppressed later as a creative denoise operation.

Most importantly, this transform occurs while the image is still a formed
negative. Both observers then see that same negative:

```text
decoded linear scene
    -> 5279 exposure and multilayer formation
    -> V49 common formed density
       -> 2383 / xenon / CIE observer
       -> scan / DI observer
```

There is no display-RGB grain overlay or formed-minus-mean RGB reinjection.

## Measured A/B result

The paired T020 768-pixel crop audit is stored in
`engine/research_runs/v49_public_common_density_t020_crop/audit.json`.

| Observer | Luma residual RMS | Opponent residual RMS | Opponent / luma | Opponent p99.9 |
| --- | ---: | ---: | ---: | ---: |
| V48 projection | 0.001319 | 0.001313 | 0.995 | 0.007644 |
| V49 projection | 0.001264 | 0.000489 | 0.387 | 0.002182 |
| V49 scan | 0.001802 | 0.000727 | 0.403 | 0.003177 |

Against the same deterministic mean, V49 preserved essentially the same
projection luma activity while reducing projection opponent RMS by 62.8% and
opponent p99.9 by 71.5%. The audit gates also require equal density deltas in
the three negative records and direct material observers for both outputs.

## Native-frame verification

A full 5.7K, 12-bit ProRes 4444 T020 frame was rendered through both observers.
The physical output completed without display-space reinjection and without the
isolated coloured specks visible in V48. On the test machine the measured core
time was 28.58 seconds per frame; total one-frame wall time, including source
decode and file finalization, was 41.06 seconds.

## What V49 does not claim

- It does not identify the real 5279 cross-record stochastic covariance.
- It does not replace the published marginal curves with a fitted aesthetic.
- It does not add art-direction, bleach bypass, or display-space chroma cleanup.
- It does not prove one particular 2383 batch, printer light, projector, or
  scanner response.

Those uncertainties stay explicit until a measured 5279 reference can resolve
them.
