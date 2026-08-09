# 2026-08-05 FCP Standard ProRes RAW full-pipeline audit

## Verdict

The GH7 ProRes RAW decode is not the source of the visible green tendency.
Apple's own untouched Final Cut Pro Standard rendering of aligned T031 source
frame 144 carries the same broad direction.  The current V-709 baseline adds a
small observer-dependent green displacement on low-chroma pixels, but the
BT.2020-to-V-Gamut matrix and the Panasonic V-709 LUT remain neutral on a
mathematically neutral input.  This is therefore not an RGB-order, white-balance
or double-camera-matrix error.

The native geometry, frame rate, 12-bit master encoding, legal-range boundary,
Rec.709 signalling, deterministic frame indexing, projection/scan shared
emulsion, and explicit sRGB web conversion all pass.  No production image
parameter was changed during this audit.

Three items remain measurement or product-contract issues rather than decode
failures:

1. `+0.45 stop` is a deliberate virtual exposure calibration used by every
   film branch and by the V-709 comparison.  It is not Final Cut Pro's untouched
   exposure default and must remain an explicit, separately labelled film-EI
   parameter.
2. The finished Blu-ray observer intentionally applies a lower-scale gamma and
   black decision.  On this dark T031 frame, 1.82% of the downsampled pixels are
   at display black.  This is not RAW clipping, but V32's validator did not
   separately gate low-end clipping and should do so in the next release.
3. The full-release remux path is correct for a complete source render.  If it
   is used for an arbitrary subrange while retaining audio, it currently maps
   the whole source audio rather than trimming audio to the selected video
   range.  The planned full-length T002 render is unaffected.

## Independent FCP reference

The reference was created in Final Cut Pro using the original ProRes RAW HQ
file, with no optimized or proxy media and no manual RAW adjustment:

- source: `NJARAW_S001_S001_T031.MOV`;
- source frame: 144, timecode `12:28:59:05`;
- RAW processing: untouched FCP Standard/as-shot state;
- project: Custom `5760 x 4320`, `24000/1001`, Standard Rec.709;
- Color Conform: Automatic, conversion `None`;
- render/export: Apple ProRes 4444, Standard Rec.709;
- duration: 24 frames / 1.001 seconds.

FCP initially classified `5760 x 4320` as non-standard and proposed an
`7680 x 4320` 8K project.  Accepting that default would rescale the image and
change the apparent grain size.  The project was therefore explicitly kept at
the camera's native `5760 x 4320` dimensions.

The resulting reference is
[`fcp_reference/FCP_Standard_T031_frame144_1s.mov`](fcp_reference/FCP_Standard_T031_frame144_1s.mov).

Apple documents that Standard conversion can use the as-shot ISO, exposure and
white-balance metadata, and that Final Cut can automatically pair a
manufacturer RAW-to-log conversion with a built-in camera LUT.  Consequently,
the FCP export is an official viewing reference, not a requirement that a
Panasonic V-709 observer be pixel-identical to FCP's internal display transform.

## RAW decode and metadata

The native Bayer metadata at frame 144 is:

| Field | Value |
|---|---:|
| Bayer pattern | RGGB |
| black level | 256 |
| white level | 48113 |
| gain factor | 8.134586334 |
| as-shot CCT | 5500 K |
| red WB factor | 2.4228515625 |
| blue WB factor | 1.4375 |
| recommended crop | zero on all sides |
| pixel aspect ratio | 1:1 |

The camera RGB-to-XYZ D65 matrix is:

```text
0.6641846    0.15942383   0.12670898
0.25964355   0.8190918   -0.07873535
-0.037353516 -0.13867188  1.2651367
```

Its row sums are `(0.95032, 1.00000, 1.08911)`, the expected D65 white.

The production decoder requests `kCVPixelFormatType_128RGBAFloat`.  Apple
returns a colour-managed pixel buffer explicitly tagged:

```text
Rec. ITU-R BT.2020-1 Linear; extended range
CVImageBufferColorPrimaries = ITU_R_2020
CVImageBufferTransferFunction = Linear
```

This buffer has already passed through Apple's ProRes RAW standard conversion.
The pipeline therefore correctly does **not** reapply the Bayer colour matrix,
black/white normalization or as-shot WB factors.  It only performs a D65
primary conversion from linear BT.2020 to Panasonic V-Gamut.

Native float measurements for frame 144 are stored in
[`raw_float_frame144_metrics.json`](raw_float_frame144_metrics.json).  Important
results:

- all values are finite;
- channel minima are `(-0.01780, -0.00458, -0.00927)`;
- channel maxima are `(0.60242, 0.59853, 0.52900)`;
- 0.026% to 0.258% of samples are negative, depending on channel;
- no sample is above 1.0 and no channel has a 1.0 plateau;
- the exact-zero fraction is only 0.0405% and is equal in all channels.

The retained negative values and absence of a 1.0 plateau reject an early
video-range clamp or baked SDR decode.

## Panasonic V-Log / V-709 boundary

The Panasonic V-Log implementation passes a 1,000-point encode/decode
round-trip with maximum scene-linear error `1.15e-5`.  The colour matrices pass:

- V-Gamut/XYZ inverse error: `8.35e-7`;
- Rec.709/XYZ inverse error: `1.62e-6`;
- BT.2020 neutral white to V-Gamut: `(1.0000007, 0.9999998, 0.9999992)`.

The official LUT in use is
`VLog_to_V709_forV35_ver100.cube`, SHA-256
`f99223675b29933952da2153bdb3137dd749d12964d0753db85e47576ca4578d`.
Panasonic's accompanying readme explicitly says its output is legal range
only.  At V-Log black (`0.125`), the neutral LUT output is approximately
`0.061523`, effectively the 10-bit legal black boundary.  The implementation
normalizes legal `64-940` to full RGB once before ffmpeg converts that RGB to
legal-range ProRes YUV.  A separate ramp test confirms there is no double range
conversion.

A neutral V-Log ramp remains neutral through the 3D LUT; at the 18% gray input,
the maximum channel difference is only `4.4e-5`.  The small real-image green
difference relative to FCP is therefore a difference between two nonlinear
camera/display observers, not a neutral-axis matrix offset.

## Aligned frame comparison

Measurements are in
[`aligned_frame144_metrics.json`](aligned_frame144_metrics.json).  FCP frame 0
and V32 frame 12 both correspond to absolute source frame 144.

| Stage | Laplacian structure correlation to FCP | measured x/y shift at 1440 px | black clip | white clip |
|---|---:|---:|---:|---:|
| FCP Standard | 1.0000 | 0.0000 / 0.0000 | 0% | 0% |
| Panasonic V-709 baseline | 0.9904 | 0.0022 / -0.0007 px | 0% | 0% |
| 5279 -> 2383 projection | 0.7743 | 0.0048 / -0.0058 px | 0.049% | 0% |
| 5279 -> Period 2K/Blu-ray | 0.7371 | 0.0044 / -0.0017 px | 1.819% | 0% |

The essentially zero phase shift rejects a crop, pixel-aspect, rotation,
orientation or lens-geometry discrepancy between AVFoundation and FCP.  Lower
film-stage structure correlations are expected because MTF, scanner aperture
and stochastic emulsion formation alter high-frequency image structure.

On pixels that are low-chroma in both FCP and each compared stage, normalized
RGB chromaticities are:

| Stage | FCP on the same pixels | compared stage |
|---|---|---|
| V-709 | `(0.33098, 0.34432, 0.32470)` | `(0.33112, 0.35195, 0.31694)` |
| projection | `(0.32736, 0.34259, 0.33006)` | `(0.32862, 0.34908, 0.32229)` |
| scan | `(0.32739, 0.34194, 0.33067)` | `(0.32882, 0.34584, 0.32534)` |

This confirms a small additional green displacement, largest in V-709 and
smallest in the scan observer.  It does not support a large common green cast
introduced by the decoder.

Tone is intentionally not identical.  Linear-luma median / 99th percentile:

| Stage | median | p99 |
|---|---:|---:|
| FCP Standard | 0.05454 | 0.22241 |
| V-709 at +0.45 stop | 0.06370 | 0.31916 |
| projection | 0.03664 | 0.34674 |
| scan | 0.05207 | 0.26427 |

The V-709 difference includes the explicit `+0.45 stop`; projection and scan
include their physically modelled/finished observer curves.  These values must
not be interpreted as RAW exposure errors.

## 5279, projection and scan stages

The current release still satisfies the intended stage ordering:

1. Apple extended-linear BT.2020 ProRes RAW conversion;
2. D65 BT.2020 to V-Gamut primary conversion;
3. explicit virtual exposure and restrained sensor-noise separation;
4. 5279 film-record exposure, H-D curves, multilayer populations, DIR,
   net-dye/masking-coupler spectra, MTF and frame-unique grain;
5. one shared developed emulsion realization feeding both observers;
6. 2383/LAD/xenon projection observer or Period 2K/Cineon/Blu-ray observer;
7. Rec.709 signal encoding and 12-bit ProRes interchange.

The V30 analytical 2383 lattice SHA-256 is
`5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c`,
matching the renderer lock.  V31's released normal-process adapter is also
correctly documented as a final display-boundary operation: it keeps the
projection's exact linear luma and high-frequency opponent residual while using
the scan observer's low-frequency dye colour.  It does not recompute RAW,
negative density, grain, DIR, MTF, gamma or black.

The public data does not uniquely identify the camera's sensor spectral
sensitivities, historical scanner proprietary negative-match matrix, complete
5279 layer recipe, or exact DIR coefficients.  Those parts remain
evidence-constrained models, not manufacturer-certified reconstructions.  The
audit found no accidental transform duplication or code-path regression, but
cannot turn those underdetermined parameters into measured facts.

## Master and web delivery

FCP and all three V32 masters agree on:

- `5760 x 4320` native raster;
- `24000/1001` and 24 frames;
- Apple ProRes 4444;
- 12-bit component depth;
- TV/legal range;
- Rec.709 primaries, transfer and matrix (`1-1-1`).

FCP includes an opaque alpha plane (`yuva444p12le`); the project masters omit
the redundant alpha plane (`yuv444p12le`).  This has no appearance impact.

The synthetic ramp round-trip in
[`prores_roundtrip/prores_roundtrip_metrics.json`](prores_roundtrip/prores_roundtrip_metrics.json)
measured:

- mean absolute signal error: `0.000306`;
- p99 absolute signal error: `0.000672`;
- maximum absolute signal error: `0.000724`;
- decoded black: `0.0`;
- decoded white: `0.99956`.

This is normal 12-bit ProRes/YUV quantization and confirms one legal-range
conversion, not two.

V32 web proxies are `1920 x 1440`, 24 frames, H.264 High, YUV 4:2:0, TV range,
Rec.709 primaries/matrix and explicit sRGB transfer.  Their build path decodes
the Rec.709 OETF to light and then applies the sRGB transfer.  The recorded
first-frame channel MAE is approximately `0.006-0.013`, explained by 5.7K to
1920 downsampling, 4:2:0 chroma subsampling and H.264 compression; the earlier
green audit found no web-only green addition.

## Next-release gates

The next release should add the following tests before changing appearance:

1. preserve this FCP frame-144 reference as an immutable decoder/display
   witness;
2. report camera-baseline results at both 0.0 and +0.45 stop so film EI is not
   confused with untouched camera exposure;
3. add low-end clip fraction and sub-reference toe occupancy to the validator,
   separately for projection and finished scan;
4. retain the pure-neutral V-709 test to prevent an actual matrix/LUT-axis green
   regression;
5. trim/remap audio time for any future partial-range deliverable that requests
   source audio;
6. keep native `5760 x 4320` instead of accepting FCP's automatic 8K proposal.

## Sources

- [Apple: Adjust ProRes RAW camera settings in Final Cut Pro](https://support.apple.com/en-euro/guide/final-cut-pro/ver3eb60032c/mac)
- [Apple: Use built-in camera LUTs with ProRes RAW](https://support.apple.com/en-am/guide/final-cut-pro/ver5d55de8fd/mac)
- [Apple: Automatic color management and Color Conform](https://support.apple.com/en-euro/guide/final-cut-pro/ver808063493/mac)
- [Panasonic: V-Log/V-Gamut Reference Manual](https://pro-av.panasonic.net/en/cinema_camera_varicam_eva/support/pdf/VARICAM_V-Log_V-Gamut.pdf)
- Local Panasonic V-709 LUT readme and checksum-locked `.cube`
- Local Kodak 5279, 2383, ECN-2, ECP-2 and scanner references recorded by the
  main project research log
