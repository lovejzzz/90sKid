# V56/V57 — projection-colour identifiability boundary

Date: 2026-08-11
Status: diagnostic experiments; **not accepted as measured 5279/2383 colour**

> **V58 addendum:** these experiments inherited a coordinate error that used
> H-61B's simultaneous integral Status-A LAD triplet as three independent
> separation-curve densities. Their proof that projection colour is
> underidentified remains valid, but their rendered hues are not quantitative
> physical endpoints. See
> [`V58_2383_INTEGRAL_LAD_COORDINATE_AUDIT_2026-08-11.md`](V58_2383_INTEGRAL_LAD_COORDINATE_AUDIT_2026-08-11.md).

## Why official spectral corrections barely changed V55

Two separate inherited stages replace physical 2383 colour with the scan:

1. Inside the monitor observer, V30 sets physical hue and saturation weights to
   zero because the old 2383 spectral tables were visually digitized. The
   matching stage consequently takes low-frequency a/b from the period scan.
2. `Emulsion5279Engine._publish_projection_colour` then applies the V31 adapter
   again before delivery. V40+ sets its opponent high-frequency retention to
   zero, so projection supplies luminance while scan supplies a/b.

This is why projection and scan were much more similar than the optical model
suggested, and why large official H-D/dye corrections created only 56–61 dB
review differences in V53–V55. The choice was a defensible historical guard
against inaccurate spectral inputs, but it is not a literal physical projection
observer.

## V56: expose physical spectral colour

V56 bypasses both scan-colour replacements. It keeps V55's vector-traced H-D,
record sensitivity and formed-dye spectra, official CIE observer, neutral
display curve and neutral-highlight guard. It changes only who owns hue/chroma.

On T020, V55-to-V56 projection review PSNR is 32.270 dB. Scan-master decoded
pixels remain bit-identical. The large change proves the scan adapter was not a
minor safety trim; it was the dominant final colour authority.

V56 is visibly more cyan/green and saturated. That result must not be called
correct, because removing the guard also exposes the remaining unidentified
2383 interimage matrix.

## V57: minimum-assumption interimage endpoint

The Archive matrix is:

```text
[[ 1.4105, -0.9566,  0.9152],
 [ 0.4127,  0.6943, -0.2324],
 [-0.5640,  0.6093,  0.8425]]
```

It is a cross-vendor empirical surrogate, not a Kodak measurement. Prior
Digital LAD research already proved that neutral data cannot identify its
off-diagonal coefficients. V57 changes only this matrix to identity, the
least-parametric endpoint, while keeping V56 physical colour authority.

V56-to-V57 projection review PSNR is 33.549 dB; chroma differences dominate.
V57 becomes substantially more yellow/olive. The scan remains bit-identical.
Neither image is evidence-selected: the large interval between them is the
visual consequence of the missing measurement.

## Validation

- V56 lattice SHA-256:
  `e09a7d9f8a06f934d621083dc96d74b42bda96f6b8432652842bbdbc8353bd36`.
- V57 lattice SHA-256:
  `1b22fcfbfb89edbd13d65db9b2362ac9ad8494ea1487cc0bb046f42720684725`.
- Both outputs are 5760 x 4320, 12-bit ProRes 4444 XQ, Rec.709-tagged.
- V56 and V57 scan decoded-frame MD5:
  `604ead3c60971bb038b8470d5b5492ad`, identical to V52–V55.
- All inherited negative/grain/spectral conformance gates remain active.

## Decision

V55 remains the latest evidence-corrected production boundary; it is known to
be scan-colour-referenced. V56 and V57 are diagnostic endpoints, not candidates
to silently replace it.

The missing information is now sharply defined: separated-exposure 2383
Status-A triplets or period DPX-to-theatre Lab measurements spanning saturated
colours. Without those data, an exact 5279/2383 physical hue claim is not
identifiable from public H-D, sensitivity and dye graphs alone. Future work can
still improve the plotted xenon SPD and display appearance transform, but those
cannot identify the chemical interimage matrix.
