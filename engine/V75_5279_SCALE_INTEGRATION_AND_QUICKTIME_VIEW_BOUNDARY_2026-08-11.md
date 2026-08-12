# V75 5279 scale integration and QuickTime view boundary — 2026-08-11

## Decision

V75 is research-only. It changes no image pixels; V72 remains the current image
profile.

V44 was correct to separate a native 5760×4320 master from a declared
1920×1440 scale-integrated review. V75 now verifies that decision against the
actual encoded V72 projection and scan files and connects it to V74's native
grain result.

The important correction is one of authority. The 1920 review accurately owns
the **viewing aperture and raster geometry**, but its final ProRes XQ encode is
not a mathematically lossless noise-power-spectrum authority. Conversely, the
5760 sRGB companion preserves the native encoded picture well, but an unknown
QuickTime window resize does not own a declared viewing aperture. Neither
delivery effect may be corrected by retuning the negative.

## What was revisited

V74 found that the active 5760-wide model contains about `5.1–7.0×` more
single-pixel negative-density RMS than remains through Kodak's 48 µm
microdensitometer aperture. That is not yet display noise; negative MTF, the
film observer and viewing integration still follow. It does mean that a display
resize is part of the measured question rather than a neutral convenience.

V44 had already observed that a sharp resize made the native result look coarse
or cheap and introduced linear-light pixel-area integration. V75 reopens that
work because three different operations had still been discussed too loosely:

1. optical/sample-area integration;
2. resampling to a smaller raster;
3. encoding and decoding that smaller raster.

They are now measured separately.

## Declared scale integration

For this exact 5760-to-1920 case, every review pixel owns a 3×3 source-pixel
area. If `L` is observer-linear RGB light, the declared review sample is

\[
L_{review}(i,j)=\frac{1}{9}\sum_{a=0}^{2}\sum_{b=0}^{2}
L_{master}(3i+a,3j+b).
\]

sRGB encoding is applied **after** this integration. Applying a nonlinear
transfer first and averaging code values would answer a different physical
question.

The engine currently implements the operation with OpenCV `INTER_AREA`. V75
compares it to an independent explicit 3×3 mean over the complete T020 frame.
For both projection and scan:

- maximum linear-light difference: `1.1921e-7`;
- mean difference: `3.17–3.73e-9`;
- exact-within-float32 gate: pass.

Thus there is no hidden kernel or off-by-one error in the accepted integer-scale
integration.

## Sharp resize ablation on the real frame

The same master frame was resized in linear light with Lanczos and compared to
the exact area result. This does not claim that QuickTime uses Lanczos; it is a
controlled demonstration of what a sharp point-reconstruction policy can do to
the native high-frequency reservoir.

| Branch | Lanczos / area high-pass luma RMS | Lanczos / area opponent RMS |
|---|---:|---:|
| 5279 → 2383 projection | 1.756× | 1.435× |
| period scan | 1.158× | 1.148× |

The projection difference is larger because that branch owns more high-frequency
picture and grain energy before display integration. The two branches therefore
need not suffer the same visible resize error even when the player uses the same
algorithm.

## Uniform grain-only ablation

A new 5760×192 logE `−3` stochastic negative strip removes scene edges and
compares only the formed density residual. Its exact 3×3 area RMS is

`0.03814 / 0.05293 / 0.11241 D` for R/G/B.

Lanczos produces

`0.07347 / 0.09940 / 0.22473 D`,

or `1.926 / 1.878 / 1.999×` the area-integrated RMS. The result demonstrates a
large observation-path effect without changing one emulsion parameter. It also
explains why a geometrically fine native NPS can look more like 8 mm/16 mm when
its high frequencies are retained or folded into a smaller display raster.

This is not proof of the private QuickTime compositor. It is a bound from a
declared sharp diagnostic. QuickTime window size, Retina backing scale, system
scaling and display sharpening must be treated as unknown unless the final
display samples are captured or the resize policy is controlled.

## The ProRes boundary found by V75

The audit also decodes the completed 1920 ProRes XQ review and compares it with
the pre-encode exact integration reconstructed directly from the encoded native
master.

| Branch | Review luma retention | Review opponent retention |
|---|---:|---:|
| projection | 94.82% | 89.90% |
| period scan | 92.51% | 85.14% |

The corresponding operation—decode the native sRGB companion and then apply
the same exact area integration—retains more:

| Branch | Integrated native luma | Integrated native opponent |
|---|---:|---:|
| projection | 98.82% | 97.60% |
| period scan | 99.44% | 98.69% |

This does not make the 1920 review wrong. Apple describes ProRes 4444/XQ as
“virtually lossless,” not mathematically lossless. The empirical result says
that encoding already-integrated, low-amplitude stochastic structure at the
smaller raster attenuates some measured high-pass energy. Encoding it at native
resolution and integrating afterwards averages much of the codec error, but
leaves the viewing resize unspecified in an ordinary player.

Therefore:

- `05_emulsion_master_prores4444.mov` remains the native 5760×4320 12-bit
  picture authority;
- `06_quicktime_preview_srgb_prores4444.mov` is the native-resolution sRGB
  transfer, not a 2K observation policy;
- `07_scale_integrated_review_srgb_prores4444.mov` remains the best supplied
  QuickTime file for judging **2K-scale grain geometry**, but not for claiming
  an exact post-codec NPS amplitude.

The next delivery experiment should compare the same exact integrated float
frame through the current `prores_ks` XQ encoder, Apple's VideoToolbox ProRes
encoder and a lossless reference. That is a delivery audit, not a reason to
weaken or strengthen the emulsion.

## Consequence for the “grain is the image” model

The statement remains correct in the model's intended sense: stochastic
exposure/development events form local dye density before the observers; grain
is not added to finished RGB. But that does not make grain scale-free.

The complete observation is

\[
\text{visible structure} =
\mathcal{D}\!\left(
\mathcal{A}_{view}
\left[
\mathcal{O}_{film}(D_{formed})
\right]
\right),
\]

where `O_film` is the print/scan observer, `A_view` is the declared spatial
aperture and `D` is delivery encoding/decoding. The emulsion owns the native
density field; it does not own an arbitrary player's resampling kernel.

This also sharpens the V74 accuracy boundary. Kodak's 48 µm RMS constrains one
physical aperture, the V24 morphology hypothesizes a native NPS, and V75
declares one display aperture. None of the three alone identifies the other two.

## Reproducible artifacts

- audit code: `src/audit_v75_scale_integrated_delivery.py`
- machine-readable result:
  `research_runs/v75_scale_integrated_delivery_audit.json`
- audited sample: V72 T020 projection and scan, frame 0
- image profile: unchanged V72

## Primary sources

1. Eastman Kodak Company, [*The Essential Reference Guide for Filmmakers*](https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf), on random dye-cloud image formation, 48 µm RMS granularity, projection and temporal perception.
2. R. M. Pointer, Kodak Limited Research Division, [“A Study of Colour-Film Granularity and Print-Image Graininess,” *Journal of Photographic Science* 41(2) (1993)](https://doi.org/10.1080/00223638.1993.11738479), on negative Wiener spectra, print-image granularity and defined magnification.
3. J. H. Altman, Kodak Research Laboratories, [“The Measurement of rms Granularity,” *Applied Optics* 3(1), 35–38 (1964)](https://doi.org/10.1364/AO.3.000035), on aperture-dependent RMS measurement.
4. Apple, [*About Apple ProRes*](https://support.apple.com/en-ca/102207), describing ProRes 4444 and 4444 XQ as virtually lossless exchange codecs.
