# V67 Cineon display-layer ownership audit

Date: 2026-08-11
Status: research-only; no image profile promoted

## Conclusion

V66 makes the scan *data coordinate* more correct. It does not make the final
Rec.709 viewing transform uniquely correct, because Cineon does not define one.
The current “open scan” and “Blu-ray scan” are two display policies applied
after the Cineon data, not intrinsic properties of 5279.

No V67 image profile is promoted. There is no evidence-based reason to replace
one unmeasured display curve with another.

## Source boundary

Kodak's scanner-calibration method says a data telecine can output 10-bit log
printing-density values without scene-by-scene grading. It also explicitly
states that those data are not suitable for direct viewing on a normal monitor;
a film-calibrated monitor can provide a reasonable representation.

Kodak's separate best-light telecine patent describes the other path: scanned
negative ordinarily appears flat, so a stock-dependent 1D LUT is applied for a
video image. The neutral scale, black, white and skin-tone result are adjusted
empirically. That is a grading/viewing choice, not a universal Cineon inverse.

Primary sources:

- [Kodak scanner calibration to printing density, EP1309188A2](https://patents.google.com/patent/EP1309188A2/en)
- [Kodak best-light telecine calibration, US20060152583A1](https://patents.google.com/patent/US20060152583A1/en)
- [Kodak H-387 Digital LAD and Cineon calibration aims](https://www.kodak.com/content/products-brochures/Film/Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf)
- [DFT Spirit 2K data sheet](https://www.dft-film.com/downloads/datasheets/DFT-Spirit-2K-datasheet-11-09.pdf)

## Ownership table

### Standard or calibration aim

- 10-bit Cineon code range;
- 0.002 printing density per code value;
- reference-black aim at code 95;
- neutral LAD/mid aim at code 445, i.e. 0.700 D above code 95.

### Active model, but not a measured device fact

- the current 5279-to-2383 printing-density spectral integration;
- the Spirit-inspired 2048-line aperture prior;
- the neutral “high” reference generated from scene-linear value 10.0.

### Viewing or finishing choice

- 0.008 D soft toe below reference black;
- linear-display peak placement at 0.90;
- power curve derived from the unstandardized scene-10 high anchor;
- lower-scale gamma 1.20 in the “Blu-ray” finish;
- the finish blend interval from linear luma 0.12 to 0.30.

The audit re-implemented the current display map parametrically and closed it
bit-for-bit before changing any variable.

## What the current Blu-ray finish actually does

On T020 frame 0 at 1440×1080, removing only the Blu-ray finish and retaining
the current open display map gives:

- linear RGB MAE: `0.00480035`;
- OKLab median/P95: `0.02763 / 0.03817`;
- changed 12-bit components: `85.806%`;
- median linear luma: `0.04352 → 0.05514`;
- P99 linear luma: unchanged at `0.50300`.

The neutral scale shows the intent more clearly:

| Scene level relative to 18% | Open-map luma | Blu-ray-finish luma |
| ---: | ---: | ---: |
| −2 stops | 0.04409 | 0.03328 |
| −1 stop | 0.10022 | 0.08914 |
| 0 stops | 0.18000 | 0.18000 |
| +1 stop | 0.28516 | 0.28569 |
| +2 stops | 0.40949 | 0.40949 |

Therefore the finish is essentially a deliberate lower-scale contrast/black
decision. It is not responsible for highlight placement and it must not be
described as 5279 sensitometry.

## Which provisional parameter matters most

The 0.008 D soft toe is numerically minor on this frame; removing it leaves the
median and P99 almost unchanged and mainly affects the deepest sub-reference
samples.

The high anchor is not minor. Moving its scene-linear definition from 10.0 to
4.0 raises P99 luma from `0.503` to `0.579`. Moving it to 1.0 raises P99 to
`0.998` and clips about `0.95%` of luma samples. Changing only peak placement
from 0.90 to 1.00 raises P99 to `0.538`.

This large identifiability interval proves that choosing a replacement by eye
would be an artistic grade disguised as calibration.

## Correct next architecture

The engine should expose three distinct products:

1. **Cineon data master** — printing-density code values, with no display look.
2. **Named calibrated viewing transform** — for example a measured 5279→2383
   film-print emulation under a specified projector/screen observer.
3. **Named finished master** — a reference-derived Blu-ray/DI grade, explicitly
   separated from the film baseline.

Until the second or third target is measured, V66's existing display products
remain useful witnesses but provisional viewing policies. The next engineering
step is therefore an actual Cineon/DPX data export and explicit view-policy
metadata—not another guessed gamma.

## Reproducibility

- Script: `src/audit_v67_cineon_display_ownership.py`
- Audit: `research_runs/v67_cineon_display_ownership_audit.json`
- Diagnostic stills: `research_runs/v67_cineon_display_stills/`

No engine pixels or V66 assets changed in V67.
