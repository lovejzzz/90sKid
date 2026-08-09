# Kodak VISION 500T 5279 - 35 mm calibration notes

Source: Kodak publication H-1-5279t (March 2003). Values below are approximate
visual readings of the published plots, not laboratory measurements.

## MTF target

The 5279 chart shows strong developer-adjacency acutance in the blue and green
records around 10-20 cycles/mm, followed by a high-frequency roll-off. The model
uses a narrow Gaussian core plus a difference-of-Gaussians adjacency band.

Approximate implemented response at an assumed 24.9 mm image width:

| cycles/mm | Red | Green | Blue |
|---:|---:|---:|---:|
| 5 | 101% | 106% | 108% |
| 10 | 102% | 113% | 120% |
| 15 | 100% | 113% | 120% |
| 20 | 94% | 107% | 114% |
| 30 | 81% | 93% | 98% |
| 50 | 52% | 67% | 73% |
| 80 | 18% | 35% | 43% |

The ordering and overall curve shapes follow the data sheet, while exact peak
heights are intentionally conservative because the source chart is small.

## V14 granularity target and finite-layer decomposition

The published diffuse RMS granularity plot uses a 48 micrometre aperture. V14
digitizes it as density standard deviation rather than treating it as an arbitrary
display-noise strength. Blue is highest, green intermediate and red lowest. Each
record rises to a low/mid-exposure maximum and then falls with increasing exposure.
Uniform-patch Monte Carlo checks use the same circular 48 micrometre aperture.

| log exposure | Red target/measured | Green target/measured | Blue target/measured |
|---:|---:|---:|---:|
| -4.0 | .0060 / .0060 | .0110 / .0110 | .0240 / .0241 |
| -3.5 | .0070 / .0071 | .0120 / .0121 | .0260 / .0263 |
| -3.0 | .0140 / .0140 | .0180 / .0180 | .0340 / .0345 |
| -2.5 | .0090 / .0090 | .0140 / .0140 | .0430 / .0432 |
| -2.0 | .0063 / .0063 | .0100 / .0100 | .0380 / .0382 |
| -1.0 | .0060 / .0060 | .0070 / .0070 | .0240 / .0239 |
| 0.0 | .0055 / .0055 | .0055 / .0055 | .0150 / .0149 |

Kodak's filmmaker guide states that one colour record can contain fast, medium
and slow layers and that the fastest grains are generally the largest. A Kodak
multilayer colour-negative patent filed in 1992 provides a representative
architecture: medium is about 0.5 logE slower than fast, slow another 0.8 logE
slower, and their tabular-grain ECDs are 1.24, 0.82 and 0.60 micrometre. The model
uses those ratios and speed separations only to decompose the 5279 totals; it does
not claim that the patent's worked example is the undisclosed 5279 recipe.

Each finite site population is sampled with binomial statistics. Its local
variance is proportional to `p(1-p)`: nearly zero when unexposed, maximal while
the population is transitioning, and low again when saturated. This fixes a
fundamental error in a perpetual-Poisson model, which would continue producing
variance even after all available grains had developed.

For the green record, the resulting share of pre-aperture population variance is:

| log exposure | Fast activation | Medium activation | Slow activation | Fast/medium/slow variance share |
|---:|---:|---:|---:|---:|
| -4 | .030 | .013 | .003 | 80% / 16% / 4% |
| -3 | .152 | .070 | .018 | 77% / 18% / 5% |
| -2 | .508 | .301 | .096 | 64% / 26% / 10% |
| -1 | .856 | .712 | .379 | 38% / 30% / 33% |
| 0 | .971 | .934 | .778 | 20% / 21% / 58% |
| +1 | .995 | .988 | .953 | 16% / 18% / 66% |

Thus “shadows are coarse, highlights are fine” is directionally correct but
incomplete. The fast population still contributes mean density and residual
structure in highlights; it simply ceases to be the main source of *new random
variation*. The slow population eventually saturates too, producing the falling
high-exposure RMS seen in 5279's actual graph.

Relative to the v4 proof of concept, the 35 mm profile:

- reduces physical dye-cloud radii from roughly 2-4 native pixels to 0.7-1.8;
- reduces observation blur from roughly 2-3 native pixels to 0.5-0.8;
- increases effective developed-cloud counts by about five times;
- separates the noise-power kernel from the measured RGB MTF;
- keeps dye-record formation independent, then lets the physical print or scan
  chain determine the visible chromatic grain rather than imposing correlation.

The early v6 exposure model approximated three regimes:

- positive shadows select sparse, large, fast grains and therefore have strong
  relative variation and irregular local detail;
- low/middle exposure carries the broad granularity maximum shown by Kodak;
- highlights select small, dense, overlapping slow grains while the negative
  shoulder reduces their visible density variation.

The v8 normal-process 35 mm refinement reduces native cloud radii to
1.28/0.78/0.50 pixels and raises effective centre densities to 18/50/140. It
also narrows the shadow density-ratio excursion. This preserves exposure-specific
grain structure while moving the visible texture away from the pushed-16 mm
character of v6/v7.

## Optical response and high exposure

The stochastic density field and image sharpness remain coupled through the
stock-scale MTF. V6 also models a small amount of long-range red-layer scatter
from very high exposure. This is intentionally restrained: camera negative has
anti-halation protection, so residual halation should affect bright boundaries
without becoming a general red glow.

The source RAW remains linear until virtual film exposure. In v9 the three
published record curves, rather than a shared luminance function, create the toe
and high-exposure shoulder. Out-of-gamut dye chroma is compressed around
luminance instead of independently clipping RGB.

## V9 sensitometry and spectral dyes

V9 visually digitizes separate red, green and blue Status-M curves across
log-exposure -4 to +1. The plotted D-min offsets are retained during curve
formation and subtracted before viewing. Neutral 18% exposure is placed near
log exposure -1.745, while a scene-linear value of 10 reaches log exposure 0,
matching the +6-stop end of the published camera-stop axis.

Red-, green- and blue-sensitive records form cyan, magenta and yellow dye
changes. The 5279 graph labels its separation curves `D-mins subtracted`, so
they must be interpreted as signed *net* density spectra of the processed,
colour-masked stock—not as isolated positive dye absorptions. Each curve already
contains newly formed dye plus the loss of yellowish/reddish masking coupler.
V12 replaces the former all-positive 3x3 approximation with a 21-sample spectral
LUT; the tiny negative lobes and remaining positive residuals are preserved.

V14 supersedes V9's correlated record shortcut. Each record now owns three finite
populations in negative density space, and no synthetic ±6% chroma clamp is used.
This preserves the measured B > G > R separation while allowing the downstream
spectral print or diffuse 2K scan to integrate it in the historically relevant way.

## Panasonic RAW and viewing branches

Apple's extended-linear BT.2020 output is converted through XYZ D65 to the exact
V-Gamut matrices published by Panasonic. The standard V-Log formula is retained
as an exposure diagnostic and gives 0.4233 at 18% gray; it is not incorrectly
applied to Bayer samples as a decode curve.

`negative_scan` and `print` use the same virtual camera negative. The first caps
the neutral high reference near 0.72 display-linear for grading latitude; the
second uses channel peaks of 0.96/0.95/0.93 for a denser positive interpretation.

## V16 calibrated 2383 print chain

V10 added Kodak VISION Color Print Film 2383 as a real second sensitometric
stage. The optical-printer path differs from scanner inversion in one essential
respect: the 5279 Status-M minimum densities (approximately R 0.15, G 0.58,
B 0.90) remain in the light path as the negative's orange mask. Per-channel
printer-light trims compensate those unequal minima and place a neutral 18%
camera exposure at the 2383 LAD aim of visual density 1.0.

The first implementation treated the net spectral changes as a generic positive
dye-overlap matrix. That discards the sign of coloured-coupler compensation and
can restore unwanted absorption that the stock's orange mask was designed to
cancel. V12 maps each record through the signed, D-min-subtracted 5279 spectral
curves. Scanner inversion removes D-min; V15 optical printing instead integrates
the complete wavelength-dependent D-min/orange-mask curve under a 3200 K lamp
against the three broad 2383 record sensitivities. Neutral printer lights then
compensate the resulting record exposures.

The 2383 red-, green- and blue-sensitive characteristic curves are visually
sampled from log exposure -1.0 to +2.3, with a common maximum density near 4.1.
They are deliberately much steeper than the 5279 negative curves. This produces
the projection-print black separation and midtone snap while the camera negative
still determines highlight latitude.

The print's CMY dyes are sampled at 21 wavelengths from 380 to 780 nm. V15 keeps
their published relative peak heights instead of applying a second empirical
per-dye rescale. Neutral printer lights and projected gray-strip calibration set
balance at their physically appropriate stages.
V13 visually digitizes the non-Planck xenon spectral structure in Kodak's
reference guide rather than using a smooth 5600 K blackbody. A CIE observer
integration converts transmitted light to XYZ and then Rec.709. This can model
spectral dye cross-talk and non-linear saturation, but it cannot reconstruct
scene spectra lost when ProRes RAW is rendered to three RGB channels.

FilmLight documents a subtle print-stock Callier effect and separate
scatter-corrected xenon calibrations. The conservative 1.0-1.4 percent
density-domain correction to 2383 remains. V16 exposes both meanings explicitly:
`2383_projection_clean` is flare-free film transmission; the default
`2383_projection` represents the typical 16-foot-lambert cinema reference with
one-percent projection flare. The flare floor is a lower gamut boundary during
colour calibration, so no channel can be corrected below the scattered light.

Because both sensitometric plots and spectral-dye plots are visual readings,
small slope errors become obvious on 2383's steep scale. Kodak H-61 requires the
LAD patch and every step of a six-step gray scale to remain neutral; a neutral
midtone with pink highlights or tinted shadows indicates contrast mismatch. V11
therefore fits per-record gray-scale shapers before projection and a second
luminance-dependent neutral shaper after print/lamp/observer integration. These
corrections do not collapse non-neutral record differences.

Kodak H-61 also requires correctly displayed red, green and blue patches. V15
therefore adds a stored H-61/TAF-style three-dimensional separation calibration.
Until a real 5279 negative target printed to 2383 is measured, the normal-colour
Spirit optical-film-match branch supplies the provisional patch reference. This
corrects the former red-to-magenta and green-to-yellow hue rotations without
replacing 2383's density, luminance, MTF or grain response.

V16 replaces the final RGB luma-axis gamut compressor with constant-lightness,
constant-hue OKLab chroma reduction. Its neutral protection is based on relative
rather than absolute chroma, allowing very dark saturated reds to receive the
H-61 correction. Clean-frame tests place the median projection/scan hue
difference near 1-2 degrees instead of the V15 dark-red error of roughly 47
degrees.

The physical print stage also adds a small channel-specific MTF contribution
(green > red > blue at high frequency) and a high-count sub-pixel Poisson grain
population. Print grain remains subordinate to the 5279 negative grain.

## Cineon / Spirit 2K scan branch

`cineon_scan` models the historically distinct path used for digital
intermediates, HD transfers and many early Blu-ray masters. Scanner density first
passes through a restrained model of the Spirit's documented optical film
matching and RGB primary correction. The negative base is then removed, and
Spirit-like AutoDmin/RGB negative matching places D-min at Cineon reference
black 95 and neutral 18% gray at code 445.
Density is quantized at the conventional 10-bit 0.002 density per code value.
Code 95 is not treated as the file minimum: a smooth density toe retains the
small distinctions represented by codes 0-94.

The scan is subsequently sampled through a 2048-pixel RGB aperture and given a
small, restrained aperture correction before Rec.709 display rendering. This is
inspired by the Spirit 2K's diffuse xenon source, three 2048-pixel RGB CCD line
arrays, 16-bit internal RGB path and 10-bit logarithmic output. Optional temporal
grain management is disabled because its use varied by title and restoration.

The open result remains available as `cineon_scan_open`. V16's
`cineon_bluray` branch adds a restrained SDR completion stage after the scan: a
1.20 lower-scale gamma is anchored at 18 percent and fades out above mid-gray.
This creates a deliberate display black/contrast decision without turning the
scan into a simulated 2383 print.

Both V16 masters use the Rec.709 OETF declared by their 1-1-1 metadata. Review
JPEGs are converted separately to sRGB, avoiding the former sRGB-encoded/
Rec.709-tagged mismatch that lifted decoded shadows.

## Remaining empirical calibration

The model structure now includes negative, printer and projection stages, but a
controlled real 5279 step-wedge printed onto 2383 is still required to replace
visual graph readings with fitted H-D samples, measured noise-power spectra,
laboratory printer-light settings and an actual projection/scanner spectral
response.

## Finished-feature reference: *Charlie's Angels: Full Throttle*

The local 1080p release is used only as a reference for a historically finished
2K-DI/Blu-ray viewing state. Technical listings identify a 35 mm 5279 negative,
a 2K digital intermediate and 2383 release prints. The available file is a
1920x800, 23.976 fps, 8-bit H.264 4:2:0 encode at roughly 9 Mbit/s video. Its
container does not declare primaries, transfer, matrix or range, so the analysis
assumes the normal Rec.709 limited-range interpretation for an HD Blu-ray encode.

A 20-second whole-feature sample (excluding the first two and final three
minutes) produced 293 usable frames after rejecting near-black transitions. The
numbers below are nonlinear Rec.709/sRGB-like display values, summarized across
frames rather than pooled across all pixels:

| measurement per frame | 10th percentile | median | 90th percentile |
|---|---:|---:|---:|
| pixel 1st-percentile luminance | 0.0000 | 0.0017 | 0.0664 |
| pixel 5th-percentile luminance | 0.0000 | 0.0175 | 0.1172 |
| median luminance | 0.0928 | 0.2317 | 0.6124 |
| pixel 95th-percentile luminance | 0.4923 | 0.7753 | 0.9371 |
| pixel 99th-percentile luminance | 0.6933 | 0.9129 | 0.9907 |
| 95th minus 5th percentile contrast | 0.4704 | 0.7264 | 0.8753 |
| mid-scale OKLab chroma median | 0.0321 | 0.0619 | 0.0990 |
| mid-scale OKLab chroma 90th percentile | 0.0731 | 0.1091 | 0.1543 |

The important calibration conclusion is not one global curve. Deep interiors
frequently reach reference black, while haze, dust, backlight and bright
exteriors legitimately carry elevated scene blacks. Colour ranges from muted to
very rich on a shot-by-shot basis. Therefore this title supports a finished-scan
branch with a real black anchor and preserved highlight range, but it does not
support forcing every frame to a low black or applying a global saturation gain.

The encode retains visible fine, frame-varying texture, but its chroma
subsampling and temporal compression make that texture substantially more
luminance-like. It is useful as an upper bound on *visible Blu-ray chroma grain*,
not as a measurement of the 5279 dye-cloud sizes or independent record
granularity. Direct stable-region comparisons show that the current V16 scan can
expose more independent blue-channel fluctuation than this delivery encode.
Any future Blu-ray finishing option may suppress only high-frequency chroma
grain after the physical scan; the underlying three-record emulsion model should
remain tied to Kodak's granularity data.

## V17 transmission-domain Spirit scan and Blu-ray grain finish

V16 applied the 2048-pixel scan aperture after the stochastic density had
already been converted to display-linear RGB and bounded at display black. That
ordering was not physically correct: a Spirit line-array integrates diffuse
light transmitted through the negative, not a finished positive image. Negative
grain excursions that met the zero-light display boundary became one-sided, and
the subsequent display-space blur spread that positive error into neighboring
pixels. This explains the apparently floating black that remained even though
the clean Cineon transform already reached reference black.

V17 converts the three optically matched scanner densities back to transmission,
area-integrates them at the native 2048-pixel aperture, returns the samples to
log density and only then applies restrained aperture correction, AutoDmin,
Cineon quantization and display rendering. On the native GH7 test frame, the
finished emulsion result's nonlinear luminance percentiles change from V16
`P1=0.0098, P5=0.0269` to V17 `P1=0.0020, P5=0.0101`; the V17 clean reference is
`P1=0.0020, P5=0.0107`. Thus stochastic texture no longer raises the black floor
above its deterministic scan.

The physical `cineon_scan_open` branch retains all three-record texture after
this corrected scan. Only `cineon_bluray` receives a finishing-stage grain
decision constrained by the 2K-DI feature reference: luminance texture is kept,
the highest-frequency opponent-colour component is integrated with a 0.55-pixel
2K kernel while retaining 55 percent of its residual, and grain visibility fades
only into the final reference-black boundary. This does not change the Kodak RMS
targets, sub-emulsion populations, mean colour, sensitometry or highlight curve.

## V18 projection viewing-condition split and sensor-noise separation

The V16 physical projection was internally neutral on gray patches, yet a
native-frame comparison showed a clear viewing mismatch against the finished
Spirit branch. Its midscale effective gamma was about 1.72 versus 0.78 for the
Blu-ray scan. More importantly, 2383 compressed green and yellow chroma more
than blue and cyan; mean B/G therefore rose by roughly 19 percent even though
median hue displacement was only about 1.7 degrees. The perceived blue cast was
mainly a nonlinear contrast/chroma-ratio problem, not an error that could be
fixed safely with global white balance.

V18 preserves that result as `2383_projection_physical` and adds
`2383_projection_monitor`. A 25-cube profile is calculated over the same three
5279 record-density axes. For each point it compares the physical 2383/xenon
render with the calibrated finished Spirit/Cineon render in OKLab. Monitor
lightness is their geometric perceptual blend with 50 percent physical-print
weight. Hue direction uses 25 percent physical weight and saturation uses 17.5
percent, retaining a subordinate print contribution without repeating the
selective warm/green loss. Near-neutral points inherit the physical print's
neutral axis to prevent coloured 3-D lattice corners from contaminating gray.

Nine neutral scene exposures from -4 to +4 stops produce monitor-rendered
linear luminances of approximately `0.0032, 0.0101, 0.0237, 0.0645, 0.1800,
0.3676, 0.5404, 0.6741, 0.7820`. The effective -1 to +1 stop gamma is 1.26.
Thus V18 is deliberately neither the open scan nor literal theatre projection:
it is the 2383 print translated into the Rec.709 viewing condition in which the
master will actually be judged.

The same version inserts an edge-aware scene-linear sensor-noise separation
before exposure reaches the virtual negative. In locally flat regions, the
high-frequency chroma residual is integrated more strongly than the luma
residual; edge and high-signal masks reduce the operation around real detail.
Mean RGB exposure is not intentionally shifted. This prevents static GH7 sensor
noise—especially shadow colour noise—from being counted again as independent
5279 and 2383 stochastic populations. `photochemical` is the default treatment;
`preserve` bypasses it for measurement and A/B tests.

A second V18 calibration treats the stochastic mean itself. Although the
formed record-density deviation is zero-mean, the steep 2383 transmission,
final gamut boundary and perceptual display encoding are nonlinear. Jensen's
inequality therefore produces a non-zero visible mean, and the larger blue
record variance made the representative frame's B/G mean ratio rise from about
0.714 without grain to 0.788 with grain. A 96-bin square-root tonal estimator
now measures the final per-channel conditional bias after those nonlinear
stages. Two iterations remove only that mean in perceptual display space; the
spatial random field, channel independence and noise-power spectrum do not
change. The corrected emulsion frame measures B/G 0.713 and median luminance
0.2161 versus 0.714 and 0.2166 for its deterministic display reference.

## V19 neutral-tone projection colour adaptation

V18's strict neutral patches were balanced, but whole-frame analysis still
found a deterministic colour imbalance: relative to the finished scan, linear
mean B/G rose about 13 percent. The cause was not a global white balance.
Physical 2383 lightness was blended independently at every coloured density
triplet, so green/yellow regions were reweighted against blue/cyan regions; the
one-percent physical flare also desaturated coloured shadows toward projector
white. Median coloured-pixel hue differed by 2.6 degrees and the 90th percentile
by 8.6 degrees, while red and green/cyan perceptual saturation fell to roughly
71 and 77 percent of the scan reference.

V19 separates tone from colour. A monotone eleven-point neutral curve maps the
finished scan luminances `0, .00087, .00863, .03523, .09330, .18, .27646,
.38707, .51532, .66216, 1` to the calibrated monitor-projection luminances `0,
.00320, .01010, .02374, .06445, .17997, .36756, .54039, .67413, .78203,
.97460`. It therefore retains a projection-like effective midscale gamma near
1.24 without allowing hue-dependent print lightness to become a monitor cast.
The scan chromaticity is scaled through that tone curve. Physical 2383 colour is
then limited to at most 8 percent hue direction and 6 percent saturation, gated
to strong-colour midtones; its contribution is zero in shadows, highlights,
neutrals and low-saturation material.

The monitor transform is evaluated directly in 96-row stripes from every 5279
record-density triplet through both the physical 2383 and Cineon reference
branches. This replaces the coarse 3-D delta interpolation and its physical
neutral guard. The native representative frame brings near-neutral residuals
back to essentially zero and restores perceptual saturation from 0.94 to about
0.985 of the scan reference. The remaining whole-frame B/G difference is mostly
the neutral tone curve reweighting differently exposed scene regions, not a
local hue rotation.

## V19 polydisperse grain morphology and frame-to-frame boil

Kodak distinguishes subjective graininess from objective granularity. The 5279
sheet supplies the latter as per-record density standard deviation measured
through a 48 micrometre aperture and calls the result very low. The filmmaker
guide supplies the missing structural constraints: silver-halide grains are
randomly distributed; large sensitive grains preferentially describe shadows;
small insensitive grains describe bright highlights; colour processing removes
the silver and leaves dye clouds at those sites; and there is little migration
or joining of individual grains. It also explains that projected detail is the
cumulative perceptual result of a different grain mosaic in successive frames.

V19 therefore does not add a broad grain cluster or a temporally animated noise
overlay. Each of the nine finite populations is divided into three independently
activated size classes. Their 30/53/17 percent site fractions and
0.70/1.00/1.42 radius factors approximate a continuous coating distribution
while keeping a sparse large tail. Optical spreading varies more narrowly by
0.82/1.00/1.20, and the cloud centres receive a 0.38-pixel sub-pixel phase at a
5760-pixel scan. The phase angle and all binomial activation are resampled for
every frame and population, producing stochastic boil without translating one
fixed texture plate.

The effective correlation radii are reduced by 12 percent relative to V18. This
moves the same measured density variance toward a finer 35 mm texture, while the
existing stock MTF continues to limit deterministic detail at the matching
scale. Variance propagation includes every class kernel and its interpolation;
the final local normalization remains Kodak's exposure-dependent red, green and
blue 48-micrometre RMS target. Mean density, neutral colour, H-D curves, DIR,
scanner aperture and print-grain stages are unchanged.

## V20 marginal-activation dye contribution

The V14–V19 decomposition used fast, medium and slow populations to decide mean
density, variance and spatial morphology, but all three populations then entered
one shared dye record. V20 lets marginal activation select one of three restrained
record-contribution matrices. Each matrix is column-normalized, and it operates
only on the coloured departure from a same-exposure neutral negative. Therefore
the official 5279 neutral sensitometric curves remain exact by construction.

The estimated neighbouring-record shares are approximately three percent for
the fast population, one to two percent for medium, and below one percent for
slow. Across representative red, skin, green, cyan and blue patches, the density
departure from the neutral axis is reduced by about 2–3 percent in the thin and
midscale negative, tapering toward 1–2 percent as the slow layer takes over.
Neutral step-wedge deviation from V19 is exactly zero at float precision.

Every independently sampled population deviation is passed through the same
matrix before summation. Its squared coefficients are included in the predicted
48 um aperture variance, after which each destination record is normalized to
the published 5279 RMS curve. Thus the new colour correlation cannot silently
raise red, green or blue granularity.

The Spirit primary correction retains its calibrated 0.82 strength through the
toe and midscale, then releases smoothly by no more than 0.04 between 1.10 and
1.85 mean net negative density. This is deliberately too small to manufacture a
new highlight look; it only avoids erasing all nonlinear spectral crossover at
the scanner shoulder. VERITA 200D parameters and its reported magenta high-density
scan bias are not used.

## V21 development-domain DIR, record morphology and observer separation

V20's two final screenshots did not express the full physical difference between
the print and scan chains. The monitor-projection transform retained only eight
percent of physical-print hue and six percent of physical-print saturation,
therefore inheriting approximately 92 and 94 percent respectively from the
finished scan. The user's observation that the Blu-ray black was deeper while
most other differences were hard to see was correct. That was a display-adaptation
error, not evidence that a 5279-to-2383 print and a period telecine should be
chromatically identical.

V21 retains the scan branch as a neutral-lightness reference but rebuilds the
projection chromatic adaptation. The provisional H-61 stage now retains 87
percent of the bounded physical-print hue and 40 percent of its saturation; the
final monitor stage keeps the physical hue direction, blends 60 percent of its
saturation, and uses the scan only as a fallback near black, near white and near
neutral. On the representative native frame, projection versus scan measures a
median absolute OKLab hue difference of about 4.80 degrees (90th percentile
10.55 degrees) and a median chroma ratio of about 0.821. This is a controlled
print/scan distinction without restoring the earlier global purple or blue cast.

DIR/interimage coupling now occurs before the nine fast/medium/slow populations
are summed. Each population releases a lateral difference field at its own
diffusion scale; a bounded release/transport/receiver model couples that field
to other populations and records. The same transport also couples stochastic
dye-cloud deviations before record mixing. Because the local operator is a
blurred field minus the original field, it is exactly zero for uniform exposure.
Neutral H-D validation over the tested range gives a maximum absolute error of
`2.3841858e-7 D`.

The representative morphology is now record-specific rather than universal.
Fast/medium/slow effective cloud diameters are `1.28/0.83/0.58 um` for the
cyan-forming record, `1.36/0.79/0.52 um` for magenta-forming, and
`1.14/0.88/0.68 um` for yellow-forming. These values are bounded structural
estimates, not a claim about Kodak's undisclosed 5279 coating formula. Every
record is still normalized to the stock-specific 48 um diffuse-aperture RMS
curves; synthetic validation across log exposures from -3.2 to -0.5 stays within
approximately zero to 1.5 percent of target.

Finally, V21 separates three spectral observers. Narrow Status-M-like weights
are used only to solve the published measurement axes. The period telecine path
uses broad approximate response functions centred near 620, 540 and 470 nm,
followed by the calibrated partial primary correction, transmission-domain 2K
aperture and Cineon finish. The optical-print path continues to use full 5279
transmission, a 3200 K printer source, 2383 sensitivity/development and xenon/CIE
observation. Exact period-scanner filter spectra remain unavailable, so this
separation is physically better founded but not uniquely identified.
