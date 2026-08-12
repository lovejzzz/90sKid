# V77 frequency ownership and projection-grain observer — 2026-08-11

## Decision

V77 is research-only. It changes no image pixels and does not promote the
current-coordinate `formed_density` projection-grain candidate. V72's inherited
`archive_pointwise` observer remains active.

The direct candidate is not a fundamental correction. With the same formed
negative it leaves the deterministic projection and complete scan bit-identical,
changes only stochastic projection modulation, and nearly doubles the number
of mean-relative isolated opponent events above `0.06` on T020 after V76 XQ:
`70 → 137`. Both paths have zero mean-relative isolated events above `0.08`.

V77 also corrects an audit assumption. The old V40/V44 whole-image “isolated
colour impulse” gate is not valid as an absolute grain gate under higher-fidelity
delivery: the deterministic no-grain image itself contains isolated natural
chromatic detail. Future grain-tail comparisons must subtract the same-path
deterministic mean before classifying stochastic impulses.

## Why the V40 decision had to be reopened

V40 selected `archive_pointwise` because the then-current full formed-density
projection failed colour-tail gates. V44 retained it. V51–V64 later rebuilt the
5279 dye spectra, ISO Status-M coordinate, 2383 characteristic curves, D-min
registration and print-density observer, but the projection-grain decision was
never repeated in those corrected coordinates.

V77 forms one V72 negative and renders both observers from it. The single
variable is:

```text
PROJECTION_GRAIN_DELTA_OBSERVER =
    archive_pointwise | formed_density
```

The scanner, stochastic identity, colour-publication policy, grain strength,
opponent management, transfer and codec are frozen.

## Real-frame result

On native 5760×4320 T020 frame 0:

- projection linear RGB MAE: `0.0009853`;
- projection OKLab median/P95/P99: `0.00178 / 0.00880 / 0.01882`;
- deterministic projection change: exactly zero;
- scan maximum absolute change: exactly zero.

The formed-density candidate raises native projection luma band RMS gradually
from about `+1%` in the middle frequencies to approximately `+9%` in the
128–170 lp/mm band. Opponent change ranges from slightly below the archive at
low frequency to about `+8%` in the highest band. It is a modest high-frequency
redistribution, not a new image-formation regime.

### Paired stochastic-tail result

After separately encoding formed and deterministic-mean projection through the
same V76 maximum-budget XQ path, then subtracting them:

| Metric | Archive pointwise | Formed density |
|---|---:|---:|
| Opponent P99.9 | 0.05432 | 0.05451 |
| Opponent P99.99 | 0.06551 | 0.06575 |
| Median-residual isolated >0.06 | **70** | **137** |
| Median-residual isolated >0.08 | 0 | 0 |

The extreme amplitude is similar, but the direct path creates materially more
medium-strength sparse colour events. There is no evidence-based reason to
promote it.

## Where the old whole-image tail came from

The projection branch was reconstructed stage by stage with exact parity to the
production function. The table shows whole-image dark opponent P99.99; this
includes deterministic scene detail and is diagnostic only.

| Stage | Archive | Formed density |
|---|---:|---:|
| raw observer delta added | 0.32494 | 0.32557 |
| 2383 MTF applied | 0.21515 | already included |
| projection opponent finish | 0.07918 | 0.08101 |
| OKLab gamut compression | 0.07868 | 0.08049 |
| perceptual mean preservation | 0.07194 | 0.07407 |
| scan-referenced colour publication | 0.04342 | 0.04542 |

The deterministic mean alone measures `0.04176` and already contains two
whole-image isolated events above `0.08`. Therefore the old requirement that a
high-fidelity completed image contain none cannot distinguish film grain from
real one-pixel chromatic detail. The previously delivered default-XQ V72 frame
passed mainly because compression reduced the complete-image statistic to
`0.03463` and zero >0.08 events.

This does **not** mean V76 should deliberately restore compression as a defect
filter. It means the regression must own the stochastic delta it claims to test.

## Physical-frequency audit

All spectra use common physical bands in line pairs per millimetre:

`0–4–8–16–24–32–48–64–96–128–170 lp/mm`.

The audit includes uniform logE `−3`, `−1` and `0` fields at native width,
their exact 3×3 linear-light review integration and maximum-budget XQ delivery.

### Direct versus archive

The two projection observers remain close across exposure:

- logE −3: direct luma is about 3% lower at low frequency and 10% higher in the
  highest band;
- logE −1: nearly identical below 48 lp/mm, rising to about +2% at the top;
- logE 0: nearly identical below 48 lp/mm and about 2% lower at the top;
- opponent bands are generally within about 3% on uniform fields.

This exposure-dependent sign change confirms that the candidate is not simply
a better or finer version of the old result.

### Viewing integration owns a large part of apparent grain

For uniform logE `−1` and `0`, exact 5760→1920 area integration retains:

| Branch | Luma RMS retained | Opponent RMS retained |
|---|---:|---:|
| projection, logE −1 | 46.6% | 96.9% |
| projection, logE 0 | 43.4% | 97.0% |
| legacy scan, logE −1 | 82.9% | 90.2% |
| legacy scan, logE 0 | 82.3% | 89.9% |

The current projection opponent management has already moved colour modulation
to lower spatial frequencies before display integration. Consequently the
opponent/luma RMS ratio rises from `0.254 → 0.527` at logE −1 and
`0.339 → 0.757` at logE 0 when viewed at 1920—approximately `2.08×` and
`2.23×` increases.

This is an important explanation for the earlier “fine 35 mm sharpness but
coarser colour texture” impression. It is not caused solely by grain radius.
Luma grain is strongly averaged by the declared viewing aperture while the
already-low-passed opponent component largely survives.

The exact strength and covariance remain unmeasured. V77 therefore records the
effect rather than choosing a prettier opponent filter.

## Codec result and remaining audit

Across the nonzero uniform fields, maximum-budget XQ retains about `92–97%` of
total scale-integrated luma/opponent RMS. However, the radial result reveals a
small redistribution: midband opponent energy is reduced while a tiny
near-Nyquist opponent floor is added in projection. A scalar high-pass RMS is
therefore not sufficient to choose a grain codec.

The next audit must compare default XQ, maximum-budget XQ, VideoToolbox XQ and
FFV1 against the same uniform formed-minus-mean NPS, band by band. V76 remains
an implemented delivery candidate while this finer validation is completed.

## Accuracy boundary

V77 supports four statements:

1. the old and direct projection-grain observers are both priors;
2. corrected V51–V64 coordinates do not make the direct observer clearly safer;
3. scale integration changes luma/opponent balance because their current NPS
   shapes differ;
4. whole-image colour-tail gates must not use deterministic scene detail as a
   proxy for stochastic grain failure.

It does not identify 5279's missing joint three-record Wiener spectrum. That
still requires calibrated uniform negative scans or a sufficiently rich
multi-aperture measurement.

## Reproducible artifacts

- audit: `src/audit_v77_frequency_and_projection_grain_observer.py`
- result: `research_runs/v77_frequency_and_projection_grain_observer_audit.json`
- source: T020 frame 0 plus 5760-wide uniform logE −3/−1/0 fields
- production image profile: unchanged V72

## Primary sources

1. Eastman Kodak Company, [*KODAK VISION 500T Color Negative Film 5279 / 7279*, H-1-5279](https://125px.com/docs/motionpicture/kodak/5279.pdf), processed MTF and 48 µm marginal RMS curves.
2. R. M. Pointer, Kodak Limited Research Division, [“A Study of Colour-Film Granularity and Print-Image Graininess,” *Journal of Photographic Science* 41(2) (1993)](https://doi.org/10.1080/00223638.1993.11738479), on colour-negative Wiener spectra, print-image graininess and viewing magnification.
3. J. H. Altman, Kodak Research Laboratories, [“The Measurement of rms Granularity,” *Applied Optics* 3(1), 35–38 (1964)](https://doi.org/10.1364/AO.3.000035), on aperture-dependent RMS.
