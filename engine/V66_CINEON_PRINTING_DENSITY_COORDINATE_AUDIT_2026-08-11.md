# V66 Cineon printing-density coordinate audit

Date: 2026-08-11
Status: implemented and native-release verified

## Result

V66 corrects a category error in the scan branch. V64 converted the modeled
Spirit receiver density 82% toward three independent ISO Status-M analytical
records. That may be a plausible *device-observer prior*, but it is not the
data coordinate Kodak assigns to Cineon. A calibrated Cineon data scan encodes
**printing density**: the density a film printer's spectral light and the
receiving print stock see through the negative.

V66 therefore calibrates the scanner output to the active model's
5279-to-2383 printing density above D-min before applying the unchanged Cineon
code law. It does not add a look, white-balance correction, saturation fit or
film-stock LUT.

## The distinction that was previously blurred

Three different quantities had been allowed to share the word “density”:

1. **5279 analytical/Status-M density** — a densitometric measurement of the
   processed negative under the ISO Status-M receiver functions.
2. **Printing density** — spectral transmittance of that negative integrated
   against printer illumination and target print-record sensitivities.
3. **Display light** — a view transform from Cineon printing-density data to a
   monitor encoding. This is not part of Cineon's density definition.

The V61 joint inverse made the first coordinate coherent. V58–V64 improved the
second coordinate for the 5279→2383 path. The scan branch nevertheless still
used the first coordinate as its final calibration target. V66 connects the
correct already-existing model to the Cineon encoder.

Kodak H-387 states the Cineon relation as:

```text
printing density = 0.002 × code value
```

with laboratory calibration aims such as D-min code 95 and LAD/midscale code
445. Kodak's scanner-calibration patent is still more explicit: data-telecine
RGB codes should represent printing densities computed from film spectral
transmittance, printer-lamp spectrum and the target print material's spectral
sensitivity. It also warns that this log data is not directly suitable for an
ordinary monitor without a film-calibrated display transform.

Primary sources:

- [Kodak H-387: Digital LAD, recorder calibration and aims](https://www.kodak.com/content/products-brochures/Film/Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf)
- [Kodak EP1309188A2: calibration of a film scanner to printing density](https://patents.google.com/patent/EP1309188A2/en)
- [DFT Spirit 2K data sheet](https://www.dft-film.com/downloads/datasheets/DFT-Spirit-2K-datasheet-11-09.pdf)

The Spirit sheet establishes the period device class—xenon illumination, RGB
beam splitter, line CCDs, optical matching filters, log masking, RGB matching,
AutoDmin and 10-bit log output—but does not publish the proprietary spectral
responses needed to identify a particular scanner exactly.

## Implemented equation

For formed negative record density \(D_{5279}\), the V66 scanner coordinate is:

```text
Dscan,V66(D5279) = Dprinter,active(D5279)
                   − Dprinter,active(Dmin,5279)
```

`Dprinter,active` is the same active 5279 spectral-mask / 2383 record-sensitivity
integration used by the optical-print branch. Microscopic base/fog residuals
below the field-average D-min remain signed; the mean base is subtracted once.
The existing Cineon encoder then retains:

```text
code = 95 + Dscan / 0.002
```

plus the existing neutral-LAD scale calibration to code 445. No negative
formation, multilayer development, DIR, MTF, finite-site grain, 2383 H-D curve,
Cineon code spacing or delivery transfer was changed.

## Single-variable audit

The audit compared five endpoints on a 17³ cube of formed negative record
density against the active printing-density target:

| Endpoint | RMS error (D) | P95 absolute error (D) | Maximum (D) |
| --- | ---: | ---: | ---: |
| V64: 82% toward Status-M | 0.165109 | 0.376830 | 0.847938 |
| Raw period receiver prior | 0.371845 | 0.891076 | 1.585676 |
| Full independent Status-M | 0.217660 | 0.512587 | 1.093942 |
| 82% toward printing density | 0.070726 | 0.169416 | 0.307223 |
| V66 full printing density | 0 | 0 | 0 |

The zero is by coordinate definition, not a claim of empirical scanner colour
accuracy. A partial blend was rejected because it would knowingly retain the
wrong data coordinate merely to make the image change smaller.

On T020 frame 0 at 1440×1080, V66 versus V64 produced:

- linear RGB MAE: `0.00260429`
- linear RGB P95/P99 absolute difference: `0.0121052 / 0.0250539`
- OKLab median/P95/P99 delta: `0.00405754 / 0.0179959 / 0.0245057`
- changed 12-bit components: `83.8239%`
- median linear luma: `0.0451907 → 0.0434754`
- P99 linear luma: `0.503403 → 0.502988`
- Cineon range: `95…704.345 → 95…697.536`, with no 0/1023 clipping

These numbers show a broad but modest coordinate correction, not a new contrast
curve or a highlight/black-level rewrite.

## What the colour chart can and cannot decide

T003's outdoor DGK chart is useful as an alarm, but its scene illuminant SPD,
manufacturer reference illuminant and observer are not identified. Therefore
it cannot fit or certify the scanner matrix. Under the same provisional
D50/Bradford diagnostic:

- natural-patch median hue error changed `11.71° → 9.72°`;
- natural-patch maximum hue error changed `23.27° → 19.18°`;
- primary-patch median hue error changed `8.02° → 7.19°`;
- primary-patch maximum worsened `11.89° → 16.54°`.

The mixed result is exactly why the chart was not used as an optimization
target. It neither disproves the coordinate correction nor identifies missing
device spectra.

## Projection consequence

V65 established that the delivered projection branch currently takes physical
2383 lightness/structure but inherits low-frequency OKLab hue/chroma from the
scan branch. Therefore a corrected scan coordinate must also change the
projection delivery. V66 owns a new 193³ projection-observer lattice with SHA:

```text
03ce9d14a785776121cd33ad76fe7efef222c08a0aee14611f04d10fdb1049ad
```

This is not a second projection correction; it prevents mean projected density
and microscopic density deltas from being evaluated through two different
profile versions.

## Evidence boundary and remaining work

V66 is more internally and standards consistent. It is not a measured clone of
a specific Spirit session or a period Blu-ray master. Still unknown are:

- exact Spirit xenon/filter/CCD spectral response and proprietary calibration;
- exact laboratory printer-lamp SPD and 2383 batch/process variation;
- the period scanner aperture-correction setting and later DI sharpening;
- the creative scene grade;
- the current scan display choices (`0.90` peak placement and the `1.20`
  low-scale Blu-ray finish), which are viewing/finishing policies rather than
  Cineon standards.

The next audit should isolate that last display layer. Open Cineon data,
calibrated viewing and a Blu-ray-style finish must be exposed as separate
contracts instead of letting a provisional finish masquerade as film response.

## Reproducibility

- Audit implementation: `src/audit_v66_scanner_printing_density.py`
- T020 audit: `research_runs/v66_scanner_printing_density_audit.json`
- T003 audit: `research_runs/v66_scanner_printing_density_t003_audit.json`
- Profile: `src/v66_profile.py`
- Lattice builder: `src/build_v66_print_lut.py`

The V64 archive target is restored explicitly whenever an older profile is
applied. Reference and accelerated V66 scanner paths were verified bit-exact.

## Native release verification

T020 frame 0 was rendered through the Production Metal graph at the original
5760×4320 resolution. Total image-pipeline time was `30.842 s/frame`
(`14.128 s` negative formation, `16.254 s` two observers, `0.460 s` delivery
encoding); complete wall time including masters and review derivatives was
`41.857 s`.

Both projection and scan masters are one-frame ProRes 4444 XQ,
`yuv444p12le`, 12-bit, 5760×4320 with Rec.709 colour tags. Their decoded frame
MD5 values are respectively:

```text
projection  d77e31f7cf9c207273da2f34949047ef
scan        d43af174bd6859ff5be73b7a1ad34de8
```

Both differ from V64, as required by the scan-coordinate correction. All
54 regression tests passed. The native delivered colour-tail audit also passed
both branches: no isolated impulses above `0.08`, and the existing opponent
tail, median and sparse-impulse bounds all remained closed. Its machine-readable
record is `research_runs/v66_native_colour_grain_gate.json`.
