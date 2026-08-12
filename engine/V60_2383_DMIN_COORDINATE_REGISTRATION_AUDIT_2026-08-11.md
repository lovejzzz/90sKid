# V60 — 2383 spectral-base / H-D D-min coordinate registration

Date: 2026-08-11
Status: evidence-reconciled image revision
Image change from V59: analytical-density origin only

## Why V59 was not the endpoint

V59 correctly restored the fourth `Visual Neutral` path from Kodak's March
2005 2383 spectral-dye-density graph. A second cross-check then compared the
Status-A density of that residual spectrum with the minima of the independently
vector-traced H-D graph:

| Channel | Visual-Neutral residual integrated as Status A | H-D curve D-min | Difference |
|---|---:|---:|---:|
| Red | 0.07203 | 0.04442 | +0.02761 |
| Green | 0.07655 | 0.04835 | +0.02820 |
| Blue | 0.10038 | 0.10358 | -0.00320 |

This is not a surprise for two representative product graphs that are neither
a joint batch measurement nor numerical specifications. It is nevertheless a
real coordinate inconsistency. V59 equated their total densities directly, so
the red and green H-D minima requested less absorption than the spectral base;
the inverse could only clamp those cases to zero dye amount.

## V60 registration

V60 retains the spectral shape recovered in V59, but treats each H-D minimum as
the zero-analytical-dye coordinate. For Status-A channel \(j\), the density used
to invert the curve is

\[
D_{registered,j}(a)=D_{spectral,j}(D_{base}+aD_{dye})
-D_{spectral,j}(D_{base})+D_{min,j}^{H-D}.
\]

Consequences:

- zero dye amount maps exactly to the corresponding vector H-D D-min;
- the nonlinear interaction between base and dye transmission is preserved;
- projected light still contains the full V59 wavelength-dependent base;
- the official simultaneous LAD target remains `1.09 / 1.06 / 1.03`;
- no arbitrary spectral reshaping is invented to force two published drawings
  to agree point by point.

## Numerical closure

The D-min-registered LAD inverse gives:

- principal H-D coordinates: `0.9897172 / 0.8820604 / 0.8421485`;
- analytical C/M/Y amounts: `1.0550362 / 1.0296745 / 0.9633866`;
- maximum inverse residual: below `1e-7`;
- forward Status-A result: exactly `1.09 / 1.06 / 1.03` within float32
  tolerance;
- analytical amount at each curve's own D-min: zero within `1e-12`.

The amounts return close to V58, which is expected: V58 already used the H-D
D-min origin, but lacked the wavelength-dependent base in projected
transmission. V60 combines the useful part of both coordinate systems instead
of allowing one graph to overwrite the other.

The SHA-locked 193-cube LUT is
`3e13d55aac10971db769d1e2d44fecc421872623c05ea87c06454f7b03e7ed83`.

## Native-frame validation

`NJARAW_S001_S001_T020.MOV`, frame 0, was rendered at 5760 × 4320 in
Archive Exact CPU mode and delivered as 12-bit ProRes 4444 XQ.

- all 65 regression tests and every V60 conformance gate pass;
- the V60 scan frame remains bit-identical to V58/V59 (decoded MD5
  `604ead3c60971bb038b8470d5b5492ad`);
- V59/V60 projection PSNR is 67.644 dB, SSIM 0.999900;
- V58/V60 projection PSNR is 69.051 dB, SSIM 0.999927;
- native pipeline compute was 36.26 s; wall time including output finalization
  was 46.90 s.

V60 being closer to V58 than V59 is structurally expected and is not used as a
quality criterion: the D-min registration restores V58's correct zero-density
origin while retaining V59's newly recovered wavelength-dependent base.

## Interpretation

This is a coordinate correction, not an aesthetic adjustment. It improves
internal physical consistency but cannot uniquely recover Kodak's laboratory
calibration. A truly identified model would require spectra and Status-A values
from the same processed 2383 samples, plus the negative-to-print 3-D calibration
and actual viewing chain. Until then, V60's split authority is explicit:

- spectral *shape*: Kodak's 2005 Visual Neutral and C/M/Y graph;
- density *origin and scale*: Kodak's 2005 vector H-D curves and H-61B LAD;
- downstream colour/interimage: still the inherited empirical, scan-referenced
  boundary, unchanged in this revision.

## Sources

1. Eastman Kodak, [KODAK VISION Color Print Film 2383/3383 technical
   information](https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf).
2. Eastman Kodak, [LAD for KODAK VISION Color Print Film,
   H-61B](https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf).
3. Eastman Kodak, [Motion-picture terminology: special-dye-density and
   D-min](https://www.kodak.com/en/motion/page/glossary-of-motion-picture-terms/).
