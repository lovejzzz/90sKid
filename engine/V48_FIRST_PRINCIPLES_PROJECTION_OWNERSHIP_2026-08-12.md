# V48 — First-principles projection ownership

Date: 2026-08-12
Status: public visual release

## Decision

V48 returns to a smaller model. It changes no RAW decode, 5279 negative,
finite-site realization, H-D curve, 48 µm RMS curve, MTF, dye/mask spectrum,
2383 material response, Cineon scan or delivery transfer.

It changes one observer-ownership error inherited by V46: the deterministic
2383 projection no longer borrows low-frequency colour from the scan. The
direct 5279 → 2383 → xenon/CIE observer owns the projected print's mean colour.
The former scan-referenced transform is evaluated only as a signed stochastic
delta safeguard, because public 5279 evidence still does not identify the
three-record cross-NPS needed to remove that safeguard safely.

## First-principles decomposition

The released projection is

\[
P_{48}=P_{2383}^{mean}
+\left[M(P_{2383}^{formed},S^{formed})
-M(P_{2383}^{mean},S^{mean})\right],
\]

where `M` is the frozen V46 containment transform. It may shape only the
random difference in brackets; it cannot replace the projected print's mean
hue/chroma. The scan branch `S` is unchanged.

This is deliberately less ambitious than estimating a new 5279 grain law.
Kodak publishes neutral H-D, processed MTF, marginal diffuse RMS at one 48 µm
aperture, spectral sensitivity and net dye-density curves. Those data do not
determine native NPS, cross-record covariance, exact fast/mid/slow coating
ratios or the stock's DIR tensor. V48 does not fill those gaps by taste.

## Same-negative audit

T020 frame 0 was decoded once and one Production Metal V46-compatible negative
was observed through both publication policies.

- V48 deterministic mean equals the direct 2383 mean bit-for-bit.
- The managed stochastic projection delta is preserved exactly within float32
  roundoff.
- The scan and formed negative are shared, not re-rendered.
- Minimum formed density is `0 D`; no sample crosses below zero.
- V48 versus V46 projection linear-RGB MAE is `0.0022000`; P95 is `0.0075853`.

The small delta is expected. This is not a grade designed to make projection
look dramatically different. It removes a hidden cross-branch ownership
substitution.

## Release output

- source: `NJARAW_S001_S001_T020.MOV`, frames 0–23;
- native master: 5760×4320, 24 frames, 24000/1001 fps;
- codec: ProRes 4444 XQ, 12-bit 4:4:4;
- reference transfer: Rec.709 primaries / BT.1886;
- QuickTime companion: Rec.709 primaries / sRGB transfer;
- declared review: 1920×1440 linear-light area integration;
- exchange data: 24 code-exact Cineon RGB printing-density DPX frames.

Core algorithm time was `1251.71 s`, or `52.15 s/frame`; complete wall time,
including review and source-delivery finalization, was `1436.42 s`.

## Remaining boundary

V48 is a more honest baseline, not a completed empirical characterization of
5279. The active native NPS, fast/mid/slow population law and restrained DIR
topology remain named hypotheses. Replacing them requires calibrated uniform
5279 scans or multi-aperture measurements, not another visual preference.

## Primary sources

1. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*, H-1-5279t, March 2003.
2. Eastman Kodak Company, US 5,641,596, *Adjusting film grain properties in digital images* (1997): spatial, level and interchannel statistics are separately measured quantities.
3. Eastman Kodak Company, US 6,686,136 B1, *Color negative film element and process for developing*: DIR/interimage architecture, not a disclosed 5279 coefficient table.
4. Eastman Kodak Company, *Exploring the Color Image*: dye formation, coloured masking couplers and unwanted absorption.
