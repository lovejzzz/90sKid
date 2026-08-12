# V86 · Observer covariance envelope and shadow spectral-LUT audit

Date: 2026-08-11
Image release: **V72 remains current**
Research status: **audit; no released pixels changed**

## Question

V85 confirmed that Kodak's red, green and blue 48 µm Status-M RMS curves were
transcribed correctly. V86 asks two narrower questions:

1. With those three marginal variances fixed, how much can any mathematically
   legal three-record covariance change visible luma and opponent grain?
2. Is the current observer numerically faithful at the same density scale as
   the published grain?

The reproducible audit is
`src/audit_v86_observer_covariance_envelope.py`; its machine-readable result is
`research_runs/v86_observer_covariance_envelope_audit.json`.

## Evidence retained

- Kodak H-1-5279t gives three processed-film RMS diffuse-density curves through
  a 48 µm aperture. It does not give cross-record covariance, cross-power
  spectra or joint tails.
- ISO 10505 requires Status-M spectral products for colour-negative RMS
  granularity.
- V61's joint Status-M inverse, V72's identity record formation, and every
  V85 trace value remain unchanged.

Sources:

- [Kodak VISION 500T 5279 technical data, March 2003](https://static1.squarespace.com/static/5790488dbe65943e37169f37/t/57ab931e29687fe82091402d/1470862111007/KODAK%2B500T.pdf)
- [ISO 10505:2009](https://www.iso.org/standard/50747.html)

## Covariance envelope

For each published exposure, V86 uses a symmetric one-sigma secant of the
deterministic density observer in linear Rec.709. The diagonal covariance stays
equal to Kodak's three RMS values. Minima and maxima are solved over the exact
three-dimensional correlation elliptope: every positive-semidefinite 3x3
correlation matrix with unit diagonal.

In the useful `−3.0 ... −0.5 logE` region:

- an all-common positive event is generally the **maximum-luma** endpoint;
  luma RMS reaches about `1.48x ... 1.67x` the independent-record value;
- the same all-common event is generally the **minimum-opponent** endpoint;
  it moves energy from coloured difference into common density rather than
  deleting grain;
- maximum opponent RMS is only about `1.17x ... 1.27x` the independent value,
  and often requires alternating or negative record correlations that a
  finite shared-development event may not be able to realize;
- scan, direct 2383 projection and the current scan-referenced projection do
  not share one perceptual optimum.

This independently explains V84: shared sites can reduce chromatic noise, but
they pay for it with stronger luminance and total RGB grain. No public evidence
selects the exchange rate.

The PSD envelope is deliberately an outer mathematical bound. V81/V82
Bernoulli feasibility and V83 DIR/RMS closure must still reject correlations
that cannot arise from nonnegative finite event probabilities.

## New precision finding: the shadow spectral map is too coarse

The current joint Status-M-to-2383-printer-density lattice has size `29^3` over
`0 ... 2.8 D`, a `0.1 D` cell width. The complete monitor-output cache is
`193^3` over `−0.16 ... 2.8 D`, a `0.0154167 D` cell width. Both use continuous
trilinear interpolation: this is **not code-value quantization**. However, the
downstream 193 cube cannot restore curvature already approximated by the
upstream 29 cube.

V86 therefore evaluates the same V61 joint spectral equations directly—without
the 29 cube—at the neutral mean and every `±1 sigma` record perturbation.

- At `−3.0 logE`, neutral net Status-M density is approximately
  `(0.04452, 0.04449, 0.04449) D`.
- At that neutral point, runtime minus direct printer density is
  `(+0.01101, +0.00767, +0.00237) D`.
- The worst tested shadow error is `+0.013987 D` in the red printer record for
  a green-record `+1 sigma` perturbation.
- From `−2.5 ... 0 logE`, the worst error falls below `0.000366 D`.

The error is therefore localized to the toe, not evidence that the entire
mid-scale colour model is wrong. Because red printer density is overestimated
more than green or blue, the inferred display consequence is disproportionate
red suppression—a cyan/green shadow direction. Both V72 observers inherit the
same upstream printing-density mapping, so this is a plausible common cause of
the recurring green shadow impression. That hue statement is an inference from
the signed density error; it is not a Kodak measurement.

## Nonlinearity boundary

Across `−3.0 ... −0.5 logE`, full-sigma versus half-sigma observer responses
usually agree within roughly `3% ... 12%`. The deepest toe and the direct-print
shoulder are much less linear because of physical/display boundaries and LUT
cell crossings. V86 therefore does not pretend that a single infinitesimal
Jacobian exactly predicts all visible grain tails.

## Decision and V87 gate

V86 changes no pixels. It identifies a precision defect with a clear next gate:

1. replace or densify the 29-cube joint spectral printer stage;
2. rebuild scan and projection from the same direct spectral authority;
3. require shadow printer-density error below `0.001 D`;
4. require mid-scale drift below `0.001 D`;
5. compare baseline, scan and projection on identical decoded frames before
   declaring a new image release.

Only after that shared shadow error is closed should the project return to
choosing—or refusing to choose—a finite-event cross-record covariance.
