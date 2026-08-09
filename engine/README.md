# Virtual-emulsion reconstruction experiment

## Current entry point: V42 research-conformant engine

The validated historical implementation and research record were recovered in
full on 2026-08-08. New work starts through `engine.emulsion5279`. V42 makes
the RAW, 5279 negative, two-observer and single-picture-authority delivery
boundaries explicit. It freezes V41 image formation while enforcing the latest
accepted research in executable code.

Bootstrap the generated 2383 observer cache:

```bash
python3 engine/bootstrap.py
```

Verify that no recovered source or research record has silently disappeared:

```bash
python3 engine/source_integrity.py
```

When an intentional authored-file change is ready for review, regenerate the
versioned inventory with `python3 engine/source_integrity.py --write`. CI checks
the same manifest on every pull request and main-branch push. Generated movie
files remain outside Git; source code, tests and research never belong only in
an ignored experiment directory.

Render one or more native ProRes RAW frames after compiling the AVFoundation
decoder in `engine/src/prores_raw_float_decode.swift`:

```bash
python3 -m engine.emulsion5279 INPUT.mov OUTPUT_DIR \
  --decoder PATH_TO_DECODER --start-frame 0 --frames 1
```

Run the compact regression suite:

```bash
python3 -m unittest -v engine.emulsion5279.test_pipeline
PYTHONPATH=engine/src python3 -m unittest -v \
  engine.src.test_fsd_density \
  engine.src.test_v32_kernels \
  engine.src.test_v41_colour_transport
```

Recovery, reference identity and V42 Production evidence are recorded in
[`V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md`](V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md).

Pipeline engineering notes:

- [V43H exact pipeline optimization and 12-master identity audit](V43H_EXACT_PIPELINE_OPTIMIZATION_2026-08-09.md)
- [V28 ProRes RAW colour-input contract and green-cast correction](V28_COLOUR_INPUT_CONTRACT_2026-08-04.md)
- [V29 evidence-gated full-motion validation](V29_VALIDATION_AND_EVIDENCE_BOUNDARY_2026-08-04.md)
- [M4 Max V27 optimization report](PIPELINE_OPTIMIZATION_2026-08-04.md)
- [OFX / Metal resident-pipeline architecture](OFX_GPU_PIPELINE_ARCHITECTURE.md)
- [Roundtable audit and main-agent decisions](ROUNDTABLE_AUDIT_2026-08-04.md)

This experiment tests one central claim: film grain should participate in image
formation instead of being placed over an already rendered image.

The preferred source path asks macOS AVFoundation for extended-range 32-bit
float RGB directly from GH7 ProRes RAW HQ. It is linear BT.2020 and preserves
values far above 1.0, avoiding the hard highlight clipping found in a ProRes 4444
video intermediate. The original camera file is never modified.

## V28 ProRes RAW input-contract correction

V28 corrects the stage boundary ahead of the otherwise unchanged V27 negative.
The Core Video buffer requested by the decoder identifies itself as extended
linear BT.2020/D65. V27 encoded that already converted buffer as V-Log and fed
it to Panasonic's separate RAW-Gamut-to-V-Gamut Camera LUT. That treated one
camera separation as though it were still unprocessed RAW Gamut and produced a
scene-dependent green veil, most visible in the finished scan.

V28 performs only the required primary conversion: linear BT.2020 to XYZ D65 to
linear V-Gamut. It retains AVFoundation's standard ProRes RAW conversion and
as-shot metadata contract, and does not apply a second white balance. The 5279
sensitometry, spectral dye model, DIR coupling, grain, MTF, Spirit/2383 observers,
black, contrast, gamma and Rec.709 encoding remain V27-identical. This makes V28
a colour-input correction rather than an artistic grade.

## V29 evidence-gated full-motion validation

V29 retains V28 image formation because the remaining public record does not
identify a unique 5279 grain NPS, DIR matrix, sub-emulsion coating formula or
period-scanner spectral match.  It implements the measurable remainder instead:
complete-source rendering, absolute-frame deterministic emulsion seeds across
parallel ranges, two observers from one formed negative, source PCM/timecode
retention, and full-motion black/highlight/temporal/delivery validation.

The formal T002 release processes all 165 source frames at 5760 x 4320 and
24000/1001 fps.  Both masters are 12-bit ProRes 4444 with Rec.709 1-1-1
signalling.  A separately rendered absolute source frame is decoded and compared
bit-for-bit against the same frame in the concatenated master, proving that the
range boundary does not reset or alter the stochastic realization.

## V14 finite multilayer emulsion model

V14 forms the negative in nine microscopic populations: fast, medium and slow
sites inside each of the red-, green- and blue-sensitive records. A site has a
finite chance `p` of becoming developable. Its variance is therefore binomial,
`p(1-p)`, rather than a Poisson texture that keeps growing after a layer is full.
Disk-shaped dye clouds and the observation aperture integrate those discrete
events into continuous optical density.

The populations overlap instead of switching at hard shadow/highlight thresholds.
In deep shadows only a small fraction of the large fast grains responds, so that
population dominates density variation. With rising exposure the fast population
saturates and its variance falls; medium and then small slow grains carry more of
the newly formed density. At the high-exposure shoulder the slow population also
saturates, so absolute RMS granularity falls even though the negative contains
more total dye.

The exact published 5279 red/green/blue H-D curves remain the deterministic mean.
The published 48-micrometre diffuse RMS curves set the stochastic density at every
exposure. Representative same-era Kodak multilayer geometry supplies the otherwise
unpublished internal decomposition: 0/0.5/1.3 log-exposure offsets and approximate
1.24/0.82/0.60 micrometre fast/medium/slow grain ECDs. These values constrain the
texture but are not presented as Kodak's proprietary 5279 coating recipe.

The three dye records are physically distinct stochastic populations. Their
negative-domain RMS follows Kodak's measured blue > green > red behavior; print
stock MTF, printer optics, scanner aperture and spectral visual weighting then
determine how much of that chromatic density variation reaches the final image.
No display-space grain plate is added.

Image MTF is coupled to the same physical scale as the dye clouds. Increasing
grain radius therefore rolls off high-frequency luminance and chroma detail;
coarse grain cannot coexist with untouched digital edges.

## 5279 35 mm calibration

The current profile assumes a 24.9 mm image width sampled at 5760 pixels. The
5279 technical sheet's MTF is approximated per colour record with a narrow
high-frequency core plus a developer-adjacency band around 10–20 cycles/mm.
Poisson cloud counts were raised and cloud radii reduced from the early 8 mm-like
proof of concept toward restrained 35 mm 5279 granularity.

V9 replaces the former shared luminance shoulder and warm colour matrix with a
camera-negative pipeline: separate visually digitized red/green/blue Status-M
H-D curves form cyan/magenta/yellow dye amounts, followed by a non-ideal spectral
dye-density matrix. Off-diagonal absorption tails create stock-like colour
interaction without an arbitrary three-channel LUT.

V14 replaces the earlier correlated-display-grain shortcut with independently
formed dye records. This matters because the data sheet reports separate RMS
curves, while Kodak's print-grain method explicitly says that negative frequency
content, dye spectra, print contrast, print and printer MTF, magnification and
human spectral sensitivity all intervene before the result becomes visible grain.

## RAW, V-Log and highlights

The Atomos file tags the intended intermediate as V-Log/V-Gamut, but ProRes RAW
contains Bayer sensor samples, not a baked V-Log image. A bp16 diagnostic decode
of frame 12 measured only 323 sensels at or above the RAW white level out of
24,883,200 (0.0013%). Apple's extended-linear RGB decode reaches about 10.0,
confirming that the earlier broad clipping was caused by the video intermediate.

The pipeline therefore stays scene-linear through optical scatter and virtual
film exposure. Apple's linear BT.2020 rendering is transformed through CIE XYZ
into Panasonic's published linear V-Gamut primaries. Panasonic V-Log is used as
an exposure reference: its formula places 18% gray at 0.4233. It is not decoded
a second time as if Bayer values were already logarithmic.

Two post-negative branches are available. `negative_scan` keeps a lower-contrast,
open-shadow scan interpretation for grading. `print` maps the same negative to a
denser display-positive result. A restrained red-layer scatter is added only from
exposure near and above diffuse white.

## V17 projector/scanner optics, colour patches and black calibration

`2383_projection` replaces the synthetic positive mapping with a second photographic
stage. Full wavelength-dependent 5279 transmission retains the orange mask/base.
A 3200 K printer lamp is integrated through the three broad 2383 spectral
sensitivities; neutral RGB printer lights then place an 18% negative on Kodak's
LAD density aim of 1.0, and three visually digitized 2383 Status-A curves form a
high-contrast projection print.

The 5279 cyan, magenta and yellow curves are not isolated positive dye spectra.
Kodak labels them `D-mins subtracted`: they are net separation-density changes
measured in the processed masked negative. They therefore include both formed
dye absorption and the opposite change from consumed coloured coupler. V12
digitizes those signed, peak-normalized shapes into a spectral LUT. D-min is
removed for scanning; for optical printing the orange base remains exactly once
and is balanced by printer lights. This replaces V11's all-positive scanner
cross-talk approximation without inventing a second mask.

Two multi-step neutral calibrations remain: one across the 5279-to-2383 gray
scale and one after print/lamp/observer integration. This follows Kodak's
instruction to check all six gray steps for colour crossover, not only LAD.

The resulting cyan, magenta and yellow print densities are not converted with a
generic look matrix. A 25-cube LUT integrates 21 wavelength samples from 380 to 780
nm through approximate Kodak 2383 spectral-dye-density curves and a CIE 1931
observer. V13 replaced the former 5600 K Planck approximation with the structured
xenon spectrum plotted in Kodak's reference guide. V15 retains the plotted
relative dye peaks, removes a duplicated empirical dye scale, and uses Bradford
adaptation from xenon white to the Rec.709 D65 master.

Gray balance is necessary but not sufficient: Kodak H-61 also requires red,
green and blue patches to display correctly. The earlier branch passed the gray
strip while rotating red toward magenta and green toward yellow. V15 stores an
H-61/TAF-style three-dimensional separation profile. Until a measured
5279-to-2383 target is available, the normal-colour Spirit optical-film-match
branch is its provisional RGB reference. The print's density, luminance,
contrast, gamut boundary, MTF and grain remain those of the projection path.

V16 fixes the remaining shadow-colour failure. The former RGB luma-axis gamut
compression rotated very dark reds toward magenta, and an absolute-chroma guard
mistook saturated dark colours for neutrals. Out-of-gamut values now reduce
OKLab chroma at constant lightness and hue; the neutral guard uses relative
chroma. Separate profiles are generated for clean transmission and the final
one-percent-flare viewing state.

The projection branch retains a roughly one-percent 2383 Callier density
correction for collimated projection. `2383_projection_clean` exposes the
flare-free film transmission, while the default `2383_projection` reproduces
FilmLight's typical 16-foot-lambert reference with one-percent projection flare.
The physical flare floor is enforced after constant-hue calibration, so colour
correction cannot create channel values below the light scattered onto screen.

2383 adds its own channel MTF (green finest, red intermediate, blue softest) and
a deliberately subordinate, sub-pixel Poisson print-grain population. The main
visible texture remains the 5279 camera-negative image structure.

`cineon_scan` is a separate historical scan/display branch. V13 now represents
the Spirit's documented optical film matching and RGB primary correction before
AutoDmin/RGB negative matching; an uncorrected CCD dye-overlap signal is not what
the machine normally delivered. The branch removes the orange mask, maps
reference black to Cineon code 95 and neutral 18% gray to code 445, quantizes
negative density at the conventional 0.002 density/code step, and renders a
Rec.709 master. V17 moves the 2048-pixel aperture to its physical position:
diffuse negative transmission is area-integrated before Cineon encoding, then
returned to density for restrained electrical aperture correction. V16 instead
blurred a bounded display image, which could spread one-sided grain excursions
away from black and visibly lift the finished shadow floor. Optional Spirit
hardware grain reduction remains off.
V15 treats 95 as reference black rather than file minimum: codes 0-94 pass
through a smooth density toe instead of all being clipped to the same black.
V16 keeps this as `cineon_scan_open`. `cineon_bluray` adds a restrained SDR
finishing decision: a 1.20 lower-scale gamma anchored at 18% and faded out above
mid-gray. V17 also protects reference black from grain-floor bias and gently
integrates only the highest-frequency opponent-colour grain in this finished
branch, following measurements of a 5279-originated 2K-DI Blu-ray reference.
Luminance texture and the open scan's physical three-record texture remain
unchanged. It grounds dark scene values without giving the scan 2383 projection
contrast or changing its highlights.

Both masters use the actual Rec.709 OETF declared by their 1-1-1 metadata.
Earlier builds encoded sRGB values while tagging them Rec.709, which could make
decoded shadows more than twice as bright. JPEG review stills are separately
converted to sRGB for normal image viewers.

V18 separates two meanings that previous projection renders conflated.
`2383_projection_physical` (and the backward-compatible `2383_projection`)
retains the calibrated 2383/xenon instrument result for a cinema viewing
condition. `2383_projection_monitor` starts from that same physical print but
adapts it for a Rec.709 monitor: print and finished Spirit references are blended
in perceptual lightness, while colour direction and saturation stay primarily
anchored to the calibrated scan. The neutral 18-percent patch remains 0.18. On
the nine-stop diagnostic strip the effective -1 to +1 stop gamma is about 1.26,
between the physical projection's 1.72 and the finished scan's 0.78. This keeps
print snap without reproducing the former excessively black, dense and
relatively blue monitor image.

V18 also adds a restrained pre-exposure sensor-noise separation. In locally
flat areas it integrates more high-frequency chroma than luma noise, protects
edges, and preserves mean scene exposure. The negative's nine stochastic
sub-emulsion populations and the 2383 print population are then generated from
the cleaned scene signal. This follows the useful distinction in Greg Enright's
*The Most Expensive Grain in Movie History Is Invisible*: sensor noise is not
photochemical grain, and stacking both can make an otherwise physical model read
as digital colour noise. `--sensor-noise-treatment preserve` remains available
for controlled comparisons.

The final V18 pass also corrects a subtler stochastic-mean error. A zero-mean
density fluctuation does not remain zero-mean after steep 2383 transmission,
gamut limiting and a perceptual display curve; unequal record variance can
therefore turn grain into a whole-frame hue shift. V18 measures this Jensen bias
by deterministic display level after all nonlinear boundaries and removes only
the conditional mean in perceptual display space. Spatial grain and its
noise-power spectrum are left intact. On the native representative frame the
no-grain and emulsion B/G mean ratios are 0.714 and 0.713, compared with 0.788
before this correction.

V19 removes the remaining display-projection colour drift. V18 blended physical
and scan lightness independently for every colour. Because 2383 compresses
green/yellow and blue/cyan differently, that changed the relative brightness of
large hue regions even when a gray patch remained neutral. V19 derives one
monitor contrast curve only from the calibrated neutral scale, applies it to the
finished scan luminance while preserving local chromaticity, and permits at most
8 percent physical-print hue and 6 percent physical-print saturation only in
strong-colour midtones. Shadows, highlights, neutrals and low-saturation areas
use the scan direction exactly; projector flare contributes tone rather than a
colour wash.

The native monitor projection is now evaluated stripe by stripe against its
exact Cineon reference. The former 25/33-cube colour-delta profile and physical
neutral guard are bypassed, eliminating curved-locus interpolation errors while
keeping native-resolution memory bounded. The physical 2383 projection toggle
remains unchanged.

V19 also refines the negative's microscopic morphology without increasing the
published grain amplitude. Kodak describes graininess as the subjective view of
a randomly distributed silver-halide mosaic; after colour processing the silver
is removed and dye clouds remain at the former grain sites, with little physical
migration or joining of individual grains. The guide further says that large,
fast grains dominate shadows, small, slow grains record highlights, and motion
projection accumulates detail from a newly sampled mosaic in every frame.

Accordingly, every one of the nine fast/medium/slow colour-record populations is
split into three independent size classes (30/53/17 percent site coverage), with
the smallest and middle classes dominant and the largest class deliberately
sparse. Their cloud radii follow 0.70/1.00/1.42 factors around the population's
representative size, with a fresh sub-pixel phase and random activation every
frame. A global 0.88 correlation-radius refinement shifts texture toward the fine
35 mm end. The final density is still renormalized to the same exposure-dependent
5279 48-micrometre RMS curves, so this changes spatial/temporal character—not
grain strength, mean colour, sensitometry or highlight response.

## V20 exposure-dependent sublayer colour and scanner shoulder

V20 removes the remaining assumption that the fast, medium and slow coatings
form spectrally identical dye records. Kodak publishes 5279's total red, green
and blue H-D curves and its processed net dye/masking spectra, but not the
individual coating recipes. The model therefore keeps every published neutral
H-D value exact and introduces only a bounded, column-normalized estimate away
from the neutral exposure axis. Marginal layer activation chooses the estimate:
fast shadow grains share roughly three percent of their effective measured
density with neighbouring records, medium grains about half that amount, and
slow highlight grains remain nearly record-pure.

This produces a physical coupling that V19 lacked. A thin negative no longer
means only lower density plus larger relative RMS grain; its colour-record
separation is also about two to three percent less complete. As exposure rises,
smaller slow grains carry more of the newly formed density and separation
recovers smoothly. There are no luminance thresholds, saturation boosts or
display-space shadow tints. Neutral steps remain numerically identical to V19.

The same population-specific contribution now acts on stochastic dye-cloud
formation. Variance is propagated through every cross-record coefficient before
the final per-record normalization, so the result still matches Kodak's 48 um
red, green and blue RMS curves. The added correlation changes grain colour and
boil character without increasing published grain amplitude.

Finally, the Spirit optical-film-match correction is no longer treated as a
perfectly constant matrix deep into the negative shoulder. Its 0.82 midscale
correction releases by at most 0.04 from 1.10 to 1.85 mean net density. This
keeps normal colour and AutoDmin calibration stable while allowing a small part
of 5279's own high-density spectral crossover to survive. It does not copy
VERITA 200D's documented magenta-highlight behaviour.

## V21 development-domain chemistry and corrected branch comparison

V21 moves DIR/interimage coupling ahead of the fast/medium/slow density sum.
Each of the nine populations produces a scale-dependent lateral inhibitor field;
a bounded transport model feeds it into neighbouring populations and also
couples their stochastic dye-cloud deviations. Uniform exposure remains exactly
unchanged by construction. The neutral H-D validation error is approximately
`2.4e-7 D`.

The three colour records now use separate representative fast/medium/slow cloud
morphologies and site counts, while the final visible variance remains locked to
5279's per-record 48 µm RMS curves. Synthetic aperture tests remain within about
0–1.5 percent of the published target across the tested exposure range.

Status-M is now only a measurement observer. The Cineon branch integrates the
negative through a broader period-telecine response before its partial primary
correction and transmission-domain 2K aperture. The print branch continues to
use the full 5279 spectral transmission, printer light, 2383 exposure/development
and xenon observation.

The monitor-projection comparison is also corrected. V20 inherited nearly all
scan hue and saturation, leaving black level as its dominant visible difference.
V21 shares only the neutral lightness aim and retains bounded physical 2383 hue
and saturation. On the representative frame, projection and scan now differ by
about 4.8 degrees median OKLab hue while avoiding a global purple or blue cast.

## Limits

- The total H-D and 48-micrometre RMS targets are stock-specific, but Kodak did
  not publish 5279's exact internal fast/medium/slow coating recipe. The V14
  decomposition is constrained by a same-era Kodak patent and still requires a
  real 5279 step wedge/noise-power scan for unique identification.
- Source metadata is ISO 500 and 5500 K.
- A real 5279 negative scan at controlled exposures is still needed for exact
  density, spectral and granularity calibration.
- The spectral print model can reproduce nonlinear dye/projection interaction,
  but an RGB RAW decode cannot recover the unique spectrum of the original scene.
- Master output is 12-bit 4:4:4 ProRes; JPEG stills are only viewing aids.
- ProRes masters carry a Rec.709 OETF and complete Rec.709 1-1-1
  primaries/TRC/matrix signalling in
  both the frame header and MOV colour atom. Earlier V13 masters left primaries
  and TRC unspecified, allowing ColorSync/player guesses that could appear
  purple-red even though the neutral projection calibration itself was balanced.

## Run

The M4 Max-specific V27 pipeline optimization report, strict parity gates and
parallel renderer are documented in
[`PIPELINE_OPTIMIZATION_2026-08-04.md`](PIPELINE_OPTIMIZATION_2026-08-04.md).

Compile the native decoder:

```bash
swiftc -O -framework AVFoundation -framework CoreMedia -framework CoreVideo \
  src/prores_raw_float_decode.swift -o /tmp/prores_raw_float_decode
```

Render the physical 5279-to-2383 native-resolution master:

```bash
python3 src/emulsion_experiment.py \
  /path/to/GH7_PRORES_RAW.mov outputs/native_2383_projection \
  --width 5760 --oversample 1 --max-frames 13 --master-only \
  --look 2383_projection --exposure-stops 0.45 \
  --prores-raw-decoder /tmp/prores_raw_float_decode

python3 src/emulsion_experiment.py \
  /path/to/GH7_PRORES_RAW.mov outputs/native_2383_projection_monitor \
  --width 5760 --oversample 1 --max-frames 13 --master-only \
  --look 2383_projection_monitor --exposure-stops 0.45 \
  --sensor-noise-treatment photochemical \
  --prores-raw-decoder /tmp/prores_raw_float_decode

python3 src/emulsion_experiment.py \
  /path/to/GH7_PRORES_RAW.mov outputs/native_cineon_scan \
  --width 5760 --oversample 1 --max-frames 13 --master-only \
  --look cineon_scan --exposure-stops 0.45 \
  --prores-raw-decoder /tmp/prores_raw_float_decode
```

The earlier scan and synthetic-print comparison branches remain available:

```bash
python3 src/emulsion_experiment.py \
  /path/to/GH7_PRORES_RAW.mov outputs/native_print \
  --width 5760 --oversample 1 --max-frames 13 --master-only --look print \
  --exposure-stops 0.45 --prores-raw-decoder /tmp/prores_raw_float_decode

python3 src/emulsion_experiment.py \
  /path/to/GH7_PRORES_RAW.mov outputs/native_negative_scan \
  --width 5760 --oversample 1 --max-frames 13 --master-only --look negative_scan \
  --exposure-stops 0.45 \
  --prores-raw-decoder /tmp/prores_raw_float_decode
```
