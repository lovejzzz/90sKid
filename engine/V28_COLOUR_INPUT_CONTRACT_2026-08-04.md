# V28 ProRes RAW colour-input contract

Date: 2026-08-04
Scope: Panasonic GH7 ProRes RAW decoded by AVFoundation, before the virtual
Kodak VISION 500T 5279 negative.

## Result

The green veil was not a 5279 dye, grain, black-level or gamma characteristic.
It came from applying Panasonic's RAW-Gamut Camera LUT to a buffer that Apple
had already converted to extended-linear BT.2020/D65.

V28 changes only that input boundary. All V27 film and observer parameters are
held fixed so the correction cannot silently become a look or a grade.

## Evidence and official boundary

The decoder requests `kCVPixelFormatType_128RGBAFloat`. The returned Core Video
pixel buffer reports extended-linear transfer, BT.2020 primaries and D65.

Apple describes ProRes RAW conversion and the optional Camera LUT as separate
stages. In a linear/None workflow, RAW conversion produces scene-linear values
and the Camera LUT is not applied. Panasonic describes
`VLog_RAWGamut_to_VLog_VGamut` specifically as a Camera LUT that converts the
ProRes RAW `RAW Gamut` result to V-Log/V-Gamut; Panasonic lists the GH7 as a
compatible camera. These statements do not authorize reapplying that LUT after
the host has supplied a BT.2020-linear RGB buffer.

Sources:

1. Panasonic, *Apple ProRes RAW Output LUT*, official support page:
   https://av.jpn.support.panasonic.com/support/global/cs/dsc/download/lut/s1h_raw_lut/index.html
2. Apple, *Apply built-in camera LUTs in Final Cut Pro for Mac*:
   https://support.apple.com/en-am/guide/final-cut-pro/ver5d55de8fd/mac
3. Apple, *Adjust camera settings in Final Cut Pro for Mac*:
   https://support.apple.com/en-euro/guide/final-cut-pro/ver3eb60032c/mac
4. Apple Developer Documentation, `CVProResRawMetadata`:
   https://developer.apple.com/documentation/corevideo/cvproresrawmetadata

## V27 stage-order error

The V27 path was effectively:

```text
ProRes RAW
  -> AVFoundation standard conversion
  -> extended-linear BT.2020/D65
  -> encode those values as V-Log
  -> apply RAW-Gamut -> V-Gamut Camera LUT
  -> decode V-Log
  -> virtual 5279
```

The camera LUT was therefore asked to interpret BT.2020 primaries as Panasonic
RAW Gamut. Because the LUT is a nonlinear three-dimensional camera separation,
the error is scene-dependent. It cannot be repaired robustly with a global
green-channel multiplier, tint control, saturation adjustment or black shift.

## V28 transform

The corrected path is:

```text
ProRes RAW
  -> AVFoundation standard conversion / as-shot metadata
  -> extended-linear BT.2020/D65
  -> linear BT.2020 -> XYZ D65 -> linear V-Gamut
  -> virtual 5279
```

For a row-vector RGB sample `r`, V28 evaluates:

```text
X = M_2020_to_XYZ * r
v = M_XYZ_to_VGamut * X
```

with the published D65 primary matrices stored in the reconstruction. No
transfer curve occurs between the two matrices. No second white balance is
introduced.

## Controlled A/B observations

Both supplied GH7 shots were rendered from the same frame, exposure, emulsion
seed and observer parameters. Only the input-gamut branch changed.

Near-neutral green/red ratios measured after the final ProRes decode were:

| Source | Observer | V27 | V28 |
|---|---:|---:|---:|
| T020 | Blu-ray/Spirit scan | 1.04294 | 1.02895 |
| T020 | 2383 monitor projection | 1.00234 | 0.99971 |
| T032 | Blu-ray/Spirit scan | 1.06476 | 1.04777 |
| T032 | 2383 monitor projection | 1.03915 | 1.02518 |

The neutral masks are spatially sparse and neither scene contains a chart, so
these values are diagnostic rather than a colorimetric camera calibration.
T032 remains legitimately green because the decoded rainy forest source is
green. V28 removes the extra fluorescent veil without neutralizing the scene.

On T020 the mean encoded V28-minus-V27 change was approximately:

```text
R +0.00277, G -0.01493, B +0.03180
```

That vector is consistent with correcting a misplaced three-dimensional camera
separation, not applying a simple minus-green grade.

## Black, gamma and highlight checks

- The 99th through 99.9th percentile luminance anchors are essentially
  unchanged.
- No new white clipping was observed.
- Median luminance moves slightly lower, rather than creating a lifted black.
- A synthetic uniform gray remains neutral through the complete V28 pipeline.
- V27 Spirit neutral calibration remains enabled; disabling it creates a new
  magenta/green-low gray-axis error and is not a valid fix.

## Acceleration integrity

The 193-cube 2383 monitor lattice is the exact output of the analytical print
builder. V28 stores that immutable result once and verifies its SHA-256 before
loading it, removing a 17.57-second per-process rebuild. A fused signed-density
trilinear kernel then samples the same lattice.

Validation used random signed densities including values below D-min and above
the lattice ceiling. The reference and accelerated float32 arrays were exactly
equal. More importantly, a native 5760 x 4320 frame was encoded through both
implementations and decoded to RGB48: both the projection and scan hashes were
identical. Thus the optimization changes neither delivered pixel values nor
grain realization.

Validated lattice SHA-256:

```text
647ee4b66c17e6267071bf441b69df7084e8256d6c583d1d56f04719a0606bab
```

## Release constraint

V28 is a baseline film reconstruction, not a creative grade. It intentionally
does not normalize foliage, warm skin, alter exposure, compress saturation, or
match a selected feature film. Those decisions belong downstream in the DI or
grading stage.
