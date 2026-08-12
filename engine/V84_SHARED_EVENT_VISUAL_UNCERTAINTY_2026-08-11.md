# V84 · Shared finite-event visual uncertainty

Date: 2026-08-11
Status: paired native-scale crop experiment; **no image-profile promotion**

## Why this experiment exists

V83 proved that the only legal V81/V82 common-event family can pass Kodak's
marginal 48 µm RMS boundary after stochastic DIR. That was necessary but not
sufficient. V84 asks what those equally legal density laws do after the two
actual V72 observers and after exact 3×3 scale integration.

The aim is not to choose the most attractive image. It is to test whether
shared sites solve the electronic-colour-noise problem without moving another
measured or visible quantity.

## Paired finite-site construction

One real ProRes RAW frame was decoded through the existing Final Cut Pro /
AVFoundation Standard ProRes RAW contract:

- source: `NJARAW_S001_S001_T020.MOV`, frame 0;
- decoded raster: 5760×4320 extended-linear RGB;
- native-scale research crop: `(x=2592, y=1872, w=576, h=576)`;
- active image model: V72;
- experimental negative sampler: exact CPU common-event law;
- endpoints: `alpha=0/.25/.50/1`;
- outputs: current managed projection and Cineon/scan display observers.

For every matched site, every endpoint consumes the same selector, one common
uniform and three independent uniforms. Alpha changes only the predicate
`selector < alpha`. The comparison is therefore paired: it does not change the
seed, class geometry, activation probability, DIR, mean image or observer.

The deterministic projection and scan images are bit-identical at all four
endpoints. The stochastic crop changes only because the joint finite-event law
changes.

## Negative-density result

Measured through the same 48 µm aperture:

| alpha | rho RG | rho RB | rho GB |
|---:|---:|---:|---:|
| 0.00 | 0.010 | 0.017 | 0.017 |
| 0.25 | 0.235 | 0.184 | 0.190 |
| 0.50 | 0.448 | 0.348 | 0.362 |
| 1.00 | 0.852 | 0.687 | 0.707 |

The marginal record RMS remains essentially unchanged across endpoints:

```text
alpha 0: R/G/B = 0.01070 / 0.01593 / 0.04125 D
alpha 1: R/G/B = 0.01076 / 0.01615 / 0.04069 D
```

Only 8–12 microscopic density samples per endpoint touch the active
non-negative bound in the 576² crop. The observer result is therefore not a
clipping artifact.

## The crucial observer result

Sharing records does reduce opponent-colour power, but it does not remove
energy. It redirects a large part of that energy into common luminance grain.

### Projection

| alpha | luma RMS | opponent RMS | opponent / luma |
|---:|---:|---:|---:|
| 0.00 | 0.00646 | 0.00896 | 1.387 |
| 0.25 | 0.00729 | 0.00857 | 1.176 |
| 0.50 | 0.00817 | 0.00833 | 1.020 |
| 1.00 | 0.00993 | 0.00750 | 0.755 |

### Scan

| alpha | luma RMS | opponent RMS | opponent / luma |
|---:|---:|---:|---:|
| 0.00 | 0.00979 | 0.01143 | 1.166 |
| 0.25 | 0.01090 | 0.01092 | 1.001 |
| 0.50 | 0.01199 | 0.01055 | 0.880 |
| 1.00 | 0.01402 | 0.00933 | 0.665 |

From alpha 0 to alpha 1:

- projection luminance RMS rises **53.8%**;
- scan luminance RMS rises **43.2%**;
- projection opponent RMS falls **16.3%**;
- scan opponent RMS falls **18.4%**;
- total RGB RMS still rises **25.6%** in projection and **23.3%** in scan.

This is why alpha 1 looks less like three unrelated coloured plates yet more
aggressively grainy. Marginal record RMS did not move, but covariance changed
the variance of every linear combination seen by a projector or scanner.

## Frequency and scale

The redistribution occurs across the observable band, not only in a few
outliers. At 64–116 lp/mm, projection opponent/luma changes from `1.407` at
alpha 0 to `0.757` at alpha 1; scan changes from `1.194` to `0.672`.

Exact 3×3 linear-light integration retains roughly:

- 50.7–51.5% of projection luminance RMS;
- 52.9–55.7% of projection opponent RMS;
- 52.1–53.6% of scan luminance RMS;
- 51.9–55.1% of scan opponent RMS.

Thus a 2K view does not erase the distinction. Shared events slightly increase
opponent retention while simultaneously increasing native luma power.

## Tail result

The broad dark opponent tail does become smaller: projection opponent P99.99
falls from about `0.384` at alpha 0 to `0.330` at alpha 1, and scan from `0.388`
to `0.330`. But isolated median-residual event counts do not improve
monotonically. A covariance control cannot replace the established native tail
gate.

## Decision

**No shared-site alpha is promoted.**

- `alpha=1` is rejected as a default: it is an extreme near-common lattice,
  raises visible total grain by about 23–26%, and has no 5279 measurement.
- `alpha=.25` and `.50` are retained only as diagnostic witnesses. Their
  opponent/luma ratios happen to look more balanced, but projection and scan
  prefer different numerical points and no official target defines “balanced.”
- The experiment confirms that covariance is central to the perceived
  electronic-noise problem, but direct site alignment is not thereby proven to
  be its physical cause.
- Real red-, green- and blue-sensitive crystals occupy different coating layers.
  Conditional on the scene exposure, large same-position activation sharing is
  not the minimum physical assumption. DIR, dye spectra, printer/scanner
  integration and other measured-stage mechanisms should carry joint structure
  before an aligned-site prior is promoted.

## More important next question

The scene crop exposes a large blue-record marginal:

```text
48 µm RMS blue / red ≈ 3.86
48 µm RMS blue / green ≈ 2.59
```

That imbalance is inherited from the digitized Kodak graph and is the main
reason independent records generate visible coloured texture. Before using
unmeasured site sharing to hide it, the next audit must return to the official
5279 granularity figure and verify:

1. curve legend/channel assignment;
2. the graph's exposure coordinate mapping;
3. diffuse Status-M density meaning and whether the three plotted curves can be
   treated as simultaneously observable RGB residuals;
4. the mapping from analytical record RMS through masked dye spectra to
   projection and scan colour;
5. whether our local spatial calibration is over-interpreting a
   microdensitometer measurement as per-pixel visible covariance.

## Artifacts

- implementation: `src/audit_v84_shared_event_visual_uncertainty.py`
- machine-readable audit:
  `research_runs/v84_shared_event_visual_uncertainty_audit.json`
- 16-bit sRGB research crops:
  `research_runs/v84_shared_event_visual_uncertainty/T020/`
- implementation SHA-256:
  `ac8c3b8b69c94ccb044f74f902708f4565830d689b52a808c8417a41429f8b87`
- audit SHA-256:
  `ecb6da42cca96a179bd07cb3dd14b817b3d68e12ec2b8a6dce50a2f5429a6b1c`

## Evidence boundary

This is one scene crop and one paired stochastic realization. It is strong
enough to reject the idea that shared sites are a free chroma-noise correction,
but not to estimate a stock coefficient. Public 5279 evidence still contains
no cross-record activation covariance, cross-NPS or physical site-registration
measurement.
