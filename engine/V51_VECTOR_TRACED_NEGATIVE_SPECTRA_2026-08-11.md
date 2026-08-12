# V51: vector-traced 5279 negative spectra

Date: 2026-08-11
Status: implemented evidence correction; one-frame native validation passed

## Trigger

After recovering Kodak's granularity paths for V50, the same audit was extended
to every other graph-backed 5279 array. The existing characteristic curves were
reasonably close inside Kodak's plotted interval, but the visually transcribed
net-dye and minimum-density spectra were not.

This is important because the spectral table is used twice:

1. a period telecine integrates the D-min-subtracted net dye/masking-coupler
   curves and applies an explicit, incomplete optical-film-match correction;
2. an optical printer integrates the complete negative transmission—the
   separate orange-mask/D-min spectrum plus the net dye changes—against the
   three 2383 record sensitivities under a 3200 K printer lamp.

An error here can rotate hue or alter saturation even when H-D, white balance,
black, gamma and grain are unchanged.

## Source interpretation

Primary source: Kodak H-1-5279t, March 2003, *Spectral Dye Density Curves*:
<https://static1.squarespace.com/static/5790488dbe65943e37169f37/t/57ab931e29687fe82091402d/1470862111007/KODAK%2B500T.pdf>

Retrieved SHA-256:
`f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8`.

The graph states `Process: ECN-2; D-mins subtracted` and identifies the three
separation curves as peak-normalized. Consequently:

- cyan, magenta and yellow are **net density changes**, including the opposite
  change caused by consumed coloured masking couplers;
- small negative lobes are valid and must not be clipped; and
- the dashed Minimum Density curve is a separate wavelength-dependent orange
  mask/base term, included for optical printing but removed by scanner D-min
  calibration.

V51 retains exactly that interpretation. It does not treat the curves as pure,
all-positive analytical dye spectra and does not add the mask twice.

## Vector recovery

The PDF contains five independent paths across 350–800 nm: cyan, magenta,
yellow, Midscale Neutral and dashed Minimum Density. Horizontal coordinates
were calibrated to the eleven printed 50 nm ticks; vertical coordinates were
calibrated to the printed `-0.20..1.80` density axis. V51 samples the three net
paths and the dashed D-min path on the engine's existing 380–780 nm, 20 nm
grid. The recovered values, including the unused Midscale Neutral witness, are
versioned in
[`data/5279_spectral_trace_2003.csv`](data/5279_spectral_trace_2003.csv).

Path identity is unambiguous from peak wavelength:

- yellow peaks near 440 nm;
- magenta peaks near 540 nm;
- cyan peaks near 680 nm; and
- Minimum Density is the dashed path.

## Demonstrated archive errors

Against the vector paths, the archive net-dye table's maximum absolute density
errors were:

| path | max abs error | RMS error |
|---|---:|---:|
| cyan net change | 0.1331 D | 0.0640 D |
| magenta net change | 0.2280 D | 0.1011 D |
| yellow net change | 0.0766 D | 0.0343 D |
| Minimum Density | 0.5708 D | 0.1748 D |

The clearest error was short-wavelength magenta: at 380 nm the archive used
approximately 0.27 D while the vector path is 0.0837 D. The Minimum Density
array was also misaligned at its short-wavelength end: at 380 nm the vector
path is approximately 0.8508 D, not 0.28 D.

Before downstream calibration, replacing the curves changes the complete 29³
period-scan density LUT by 0.1928 D RMS and the negative-to-2383 printer-density
LUT by 0.1725 D RMS. These large internal differences are expected to be
reduced—but not erased—by AutoDmin, optical-film matching, neutral printer-light
placement and the evidence-bounded monitor observer.

## Isolated V51 change

V51 inherits V50 and changes only:

- `NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY`; and
- `NEGATIVE_5279_DMIN_SPECTRAL_DENSITY`.

Profile switching explicitly restores the archive arrays and invalidates every
dependent LUT, neutral shaper and scanner reference. A new 193³ monitor-output
lattice was generated from the corrected analytical path:

`7f4cd389d5a329f3582603c49d3bd16cadbdb7fff50639c1365c0a0c6a00cd25`

Unit conformance proves that V51 leaves the H-D table, V50 granularity table,
DIR transport and negative MTF arrays unchanged.

## Native T020 validation

One frame was rendered at 5760 × 4320 from the same decoded GH7 ProRes RAW
source, absolute frame identity, exposure, V50 grain field and 12-bit delivery
contract. Both masters are ProRes 4444 XQ `yuv444p12le`, 12-bit, with Rec.709
primaries, transfer and matrix signalling.

On the 1920-pixel linear-light-integrated sRGB reviews, V50 → V51 measured:

| observer | RGB RMS code delta | all-channel RMS | PSNR |
|---|---|---:|---:|
| projection | 0.00240 / 0.00199 / 0.00319 | 0.00258 | 51.78 dB |
| scan | 0.00289 / 0.00206 / 0.00396 | 0.00307 | 50.26 dB |

Mean encoded blue rose by 0.00135 in projection and 0.00149 in scan; mean red
and green moved by less than 0.00024. The change is subtle in the T020 frame,
but local saturated regions reach larger differences (99th-percentile absolute
code delta 0.00748 projection, 0.00951 scan). This agrees with the mechanism:
neutral calibration removes most uniform displacement, while chromatic
separations retain the corrected spectral crossover.

Engine time was 44.4 seconds for the native frame and total wall time was 58.0
seconds. The speed change from V50 is machine-load variation; V51 replaces LUT
values and does not alter full-frame algorithmic complexity.

## H-D audit and withheld change

The three characteristic paths were also recovered. Inside the official
internal `-4..0` graph interval, the archive interpolation differs by mostly
0.5–3%, with a worst relative difference of about 6.6% in the red-record toe.
That is much smaller than the spectral error, but still worth correcting.

The archive H-D arrays also contain two shoulder samples at internal logE
`+0.5` and `+1.0`, beyond Kodak's printed domain. V51 deliberately does not
change them: replacing a plausible continuation with a hard endpoint hold would
be a new highlight assumption, not a direct graph correction. A future H-D
revision must separate exact in-domain vector recovery from the explicitly
inferred out-of-domain shoulder, then test highlight continuity independently.

## 2383 audit boundary

Kodak's current official 2383 technical PDF was also checked:
<https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf>

Its retrieved SHA-256 was
`210d5e8ec1ea3a23a003b0c95b66c3688a29088b351124470638de35062a7565`.
Unlike the 5279 archive, its plots are embedded raster artwork rather than
recoverable vector paths. Therefore no 2383 table was silently replaced in
V51; a calibrated raster extraction with uncertainty estimates is a separate
research task.

## Decision

V51 is more accurate than V50 in the narrow, testable sense that its negative
spectral data now reproduce Kodak's actual embedded paths instead of a coarse,
partly misaligned transcription. It does not prove a proprietary scanner
matrix, 5279 analytical dye chemistry or exact release-print timing. Those
boundaries remain explicit.
