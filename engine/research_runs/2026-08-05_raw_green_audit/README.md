# V32 shared-green RAW decode audit — 2026-08-05

## Question

T007 and T031 appear mildly green in all three V32 branches: Panasonic V-709
camera baseline, 5279 → 2383 projection, and 5279 → period-2K scan. Because all
three branches share the same RAW ingress, this audit tests that ingress before
changing any film parameter or adding a corrective tint.

## RAW metadata recovered from the Bayer decode

Both clips were decoded once as Apple's full-resolution `bp16` Versatile Bayer
buffer, independently of the existing float-RGB renderer. The relevant Core
Video attachments are identical:

- Bayer pattern: RGGB
- black / white levels: 256 / 48113
- gain factor: 8.134586334228516
- as-shot CCT: 5500 K
- red white-balance factor: 2.4228515625
- blue white-balance factor: 1.4375
- camera RGB → CIE XYZ D65 matrix:

  ```text
  0.6641846    0.15942383   0.12670898
  0.25964355   0.8190918   -0.07873535
 -0.037353516 -0.13867188   1.2651367
  ```

The row sums are approximately `(0.95032, 1.00000, 1.08911)`, the normalized
D65 XYZ white. The files therefore contain an internally coherent white point,
white-balance factors and camera matrix; missing RAW colour metadata is ruled
out.

T002, T020 and T032—the three V31 sources—were probed through the same Bayer
path and carry the same CCT, white-balance factors and camera matrix. The
conclusion therefore covers the V31 three-way gallery as well as V32.

The converted float buffers used by V32 independently advertise extended-range
linear BT.2020/D65 through their Core Video attachments. The existing ingress
then performs only a linear primary conversion:

```text
extended-linear BT.2020/D65 → XYZ D65 → Panasonic V-Gamut
```

It does not apply the Panasonic RAW-Gamut camera LUT a second time.

## Independent Apple reference

T031 was imported by reference into a temporary Final Cut Pro library. The
library remained Standard Gamut SDR, no optimized/proxy media, Balance Color,
analysis or creative effect was enabled. The browser playhead was placed at
source frame 144 (`12:28:59:05`), matching the V32 representative frame.

Final Cut Pro's official Standard ProRes RAW preview contains the same mild
green direction visible in the current camera baseline. A structure-aligned
comparison of the FCP viewer capture and the V-709 reference produced:

| observer | neutral-candidate median RGB chromaticity |
|---|---|
| Final Cut Pro Standard RAW | (0.32917, 0.34711, 0.31792) |
| V32 Panasonic V-709 baseline | (0.32540, 0.35000, 0.31731) |

The V-709 observer raises the green chromaticity by about `0.0029` relative to
the Apple reference. That is a small observer difference, not evidence of a
wrong RAW matrix. Omitting the recorded RAW white balance would create a much
larger red/blue deficiency because the recorded factors are 2.42 and 1.44;
neither the FCP preview nor V32 exhibits that failure signature.

Apple's supported-camera table currently lists GH7 ProRes RAW adjustment as
ISO/exposure-offset support, while some other Panasonic models also expose
temperature. The as-shot 5500 K interpretation therefore remains the correct
unmodified reference for this file rather than a freely chosen neutralization.

## Web-video exclusion

The first frames of all six V32 H.264 previews were decoded and compared with
their matched sRGB stills. Median signed RGB error is zero. Green-excess delta
`ΔG - (ΔR + ΔB)/2` ranges from `-0.00096` to `-0.00119`; the web proxy does not
add green and, on average, reduces it by roughly one code value per thousand.
The V31 preview manifest independently records the same explicit sRGB transfer
and matched-master verification for all nine projection/scan/camera previews.

## Conclusion

The green impression is real, but the tested failure hypotheses are rejected:

1. RAW white balance or camera matrix missing — rejected.
2. V-Log code values accidentally treated as linear — rejected.
3. Panasonic RAW-Gamut LUT applied twice — rejected.
4. Website H.264 / sRGB conversion adding green — rejected.
5. Current decoder departing materially from Apple's Standard RAW observer —
   rejected for the matched T031 frame.

The remaining likely causes are the recorded 5500 K as-shot interpretation in
a foliage-dominated environment, green indirect illumination on nominally gray
surfaces, and a small V-709 observer contribution. None should be removed by an
automatic gray-world or per-shot magenta bias: those would be artistic grading
and would damage genuinely green scenes.

## Required falsification capture

The definitive next test is a stationary GH7 / Ninja ProRes RAW shot containing
an illuminated neutral gray card or ColorChecker, recorded alongside the same
scene. Measure the card in Apple's Standard RAW conversion and in the V32
ingress before any film operation. A systematic positive green error on the
card across at least two illuminants would authorize a camera-input correction;
without that measurement, the V31/V32 film baseline remains frozen.

## Primary references

- Apple, [Adjust ProRes RAW camera settings in Final Cut Pro](https://support.apple.com/en-euro/guide/final-cut-pro/ver3eb60032c/mac)
- Apple, [Cameras supported by Final Cut Pro](https://support.apple.com/en-ca/109504)
- Apple Developer, [CVProResRawMetadata](https://developer.apple.com/documentation/corevideo/cvproresrawmetadata)
- Panasonic, [DC-GH7 Operating Instructions](https://www.panasonic.com/content/dam/Panasonic/au/en/PDF/DC-GH7GN-Operating-Instructions-Complete-Guide.pdf)
