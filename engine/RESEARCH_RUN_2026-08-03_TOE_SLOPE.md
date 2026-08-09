# 2026-08-03 research run: 5279 toe slope, scan quantization, and black placement

## Outcome

The hypothesis was **not supported**, so V21 remains the baseline and no V22
was created. A higher-density raster reading of the two darkest interior points
does not show a common underestimation of toe slope across the red, green, and
blue records. It mainly moves the onset of the toe upward. In a controlled
representative-frame A/B this produces a measurable but visually ambiguous
shadow lift in both branches, not a demonstrated improvement.

## Safety and prior-state audit

- No process was writing in `experiments/emulsion_reconstruction`.
- Two long-running `npm run dev` processes belonged to
  `/Users/tianxing/CodexProjects/Roundtable`, not this project.
- The raw source was present: one 1.9 GB, 5760 x 4320, 23.976 fps, 12-bit
  ProRes RAW clip.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.
- Sites project `appgprj_6a702784adc88191ab6e183be09436b5` was active,
  private/custom access, with production version 2 sourced from that exact
  commit. This resolved the prior release state before any experiment began.

## Falsifiable question

Does V21's sparse 12-point visual digitization underestimate the local toe
slope of 5279, causing the finished Cineon/Blu-ray black decision and visible
grain suppression to be calibrated against the wrong negative density?

The hypothesis predicted all three records would need a coherently steeper toe
and that the corrected curve would improve shadow separation without lifting
the final black floor.

## Sources and evidence boundaries

### Stock-specific fact

1. **Kodak H-1-5279t, page 3, sensitometric curves.** The graph is explicitly
   for 3200 K tungsten exposure, ECN-2 processing, and Status-M densitometry.
   The plotted domain is log exposure -4 to 0, with camera-stop marks -6 to +6.
   Local file:
   `references/kodak_5279_H-1-5279t.pdf`; public archival mirror:
   <https://125px.com/docs/motionpicture/kodak/5279.pdf>.
2. **Kodak H-1-5279t, page 4.** Kodak states that the sensitometric and diffuse
   RMS granularity curves were produced on different equipment and that a small
   curve-shape variation may be noticed. Therefore the two graphs cannot be
   forced into a false point-for-point coupling.

### Scanner-chain fact, not a 5279 coating measurement

3. **Eastman Kodak, _Scanning Recommendations for Extended Dynamic Range
   Camera Films_, pages 1 and 3-6.** Conventional 10-bit scanning commonly uses
   0.002 density/CV and D-min at code 95. The paper treats density encoding,
   highlight coverage, grain as prequantization dither, and later contrast
   correction as distinct stages. Official PDF:
   <https://www.kodak.com/content/products-brochures/Film/Scanning-Recommendations-for-Extended-Dynamic-Range-Camera-Films-EN.pdf>.
   The document concerns later VISION3 stocks, so it supports stage ordering
   only; it does **not** provide 5279 toe values.
4. **Kodak laboratory tools page.** Kodak lists the scanning paper alongside
   Cineon and Digital LAD materials, supporting its role as scanner setup
   guidance rather than camera-stock sensitometry:
   <https://www.kodak.com/en/motion/page/laboratory-tools-and-techniques/>.

### Rejected lead

Eastman Kodak patent US 5,835,117 has a relevant-sounding title about neutral
toe colour shifts, but its claims concern thermal dye-diffusion printers. It is
not evidence about ECN-2 negative film, Cineon scanning, or 5279 and was excluded
from the model.

## Data-sheet digitization check

Page 3 was rendered at 220 dpi. The graph rectangle was calibrated from its
printed axes: log exposure -4 to 0 and density 0 to 3. Central black-line pixels
were sampled near the existing curve, avoiding labels and axis strokes. This is
still a raster reading of a small published graph, not laboratory measurement.

Only the two interior toe samples were admitted to the candidate so the test
would not silently change midscale, shoulder, D-min, or capacity:

| record | logE | V21 density | raster candidate | delta |
|---|---:|---:|---:|---:|
| R | -3.4 | 0.16000 | 0.17522 | +0.01522 D |
| R | -3.1 | 0.18000 | 0.19646 | +0.01646 D |
| G | -3.4 | 0.59000 | 0.60531 | +0.01531 D |
| G | -3.1 | 0.62000 | 0.63186 | +0.01186 D |
| B | -3.4 | 0.91000 | 0.93451 | +0.02451 D |
| B | -3.1 | 0.94000 | 0.96106 | +0.02106 D |

Between -3.4 and -3.1 logE, V21 slopes are approximately
`R/G/B = 0.0667 / 0.1000 / 0.1000 D per logE`; the candidate slopes are
`0.0708 / 0.0885 / 0.0885`. Only red becomes slightly steeper. Green and blue
become about 11.5% shallower. The candidate therefore does not support the
predicted common underestimation. Its larger effect is an earlier rise away
from D-min between -4 and -3.4.

## Raw-source coverage

Frame 12 was decoded directly through AVFoundation as extended-linear BT.2020
float32 from the original 12-bit ProRes RAW. The Panasonic camera LUT,
photochemical sensor-noise separation, +0.45-stop virtual exposure, V-Gamut to
balanced film conversion, and record sensitivities were kept unchanged.

The resulting log-exposure coverage shows that the question is testable on the
actual frame rather than only on synthetic wedges:

| record | <= -4.0 | <= -3.4 | <= -3.1 | maximum |
|---|---:|---:|---:|---:|
| R | 1.2839% | 2.9391% | 5.7909% | +0.3017 |
| G | 0.0630% | 0.5248% | 2.3811% | +0.2307 |
| B | 0.4449% | 5.5680% | 13.3317% | +0.4917 |

Only 0.0368%, 0.0098%, and 0.0043% of R/G/B samples exceed logE 0, and none
exceeds +0.5. The current +0.5 and +1.0 extrapolation points therefore do not
drive this representative frame; they remain an explicit uncertainty for more
extreme highlights.

## Controlled A/B

The original frame was area-reduced in extended-linear light to 1440 x 1080 for
the controlled test. Baseline and candidate used identical random seed, grain
geometry, development-domain DIR, Status-M/spectral transforms, print chain,
scanner chain, and finishing. Only the six table entries above differed.

Artifacts and the complete reproducible script are in
`research_runs/2026-08-03_toe_slope_ab/`.

### 2383 projection-monitor branch

- linear RGB MAE: `0.00063644`
- PSNR: `59.82 dB`
- OKLab delta E: median `0.00132`, P95 `0.01047`, P99 `0.02881`
- absolute luma delta P95: `0.002176`
- luma P1: `0.00003097 -> 0.00024149`
- luma P5: `0.00239401 -> 0.00280971`
- changed after 8-bit sRGB still conversion: `65.29%` of pixels

The large changed-pixel count comes from small sub-code-value changes spread
across grain and shadow texture; it does not mean a large perceptual change.
Side-by-side review was nearly indistinguishable. The amplified difference map
shows the change is concentrated in low-exposure structure and grain, but the
direction is consistently toward lifted blacks.

### Cineon / Spirit 2K / Blu-ray branch

- linear RGB MAE: `0.00004298`
- PSNR: `77.59 dB`
- OKLab delta E: median `0`, P95 `0.00719`, P99 `0.01400`
- absolute luma delta P95: `0.0001796`
- luma P1: `0.00006653 -> 0.00015950`
- luma P5: `0.00069711 -> 0.00085133`
- changed after 8-bit sRGB still conversion: `20.26%` of pixels

The 10-bit density quantizer and Blu-ray finish strongly reduce the candidate's
effect, but they do not reverse the shadow lift. Grain still enters before
Cineon quantization, consistent with Kodak's scanner-stage description.

## Conclusion: falsified / no release

### Confirmed

- V21's graph digitization is already close to the published curve through the
  useful -4 to 0 domain; the tested interior differences are small density
  offsets rather than a missing common toe slope.
- Negative sensitometry, scanner density quantization, and display black
  placement are separate stages. Moving the negative toe cannot be justified
  merely because a later display black looks preferable.
- Real 5279 grain should remain before Cineon quantization; it is not an
  after-the-fact overlay or a substitute for accurate density encoding.

### Falsified

- The three records do not all require a steeper -3.4 to -3.1 toe.
- The raster candidate does not preserve the existing black floor while
  increasing shadow separation; it measurably lifts both outputs.
- The side-by-side image does not provide a stable visual-consistency advantage
  over V21.

### Unknown

- A small published raster graph cannot establish the true production-coating
  D-min and local slope to better than a few thousandths to hundredths of a
  density unit.
- No measured 5279 step wedge scanned on the target period scanner is available.
- The +0.5 and +1.0 logE extrapolation points remain unmeasured by the shown
  H-1-5279t graph, though they affect essentially none of this frame.
- The Kodak scanning paper is later VISION3 guidance and cannot be used to
  import its extended-range stock behavior into 5279.

## Release decision and next priority

No algorithm file, calibration baseline, output master, screenshot archive,
site source, Git commit, Sites version, or production deployment was changed.
V21 remains current.

The next highest-priority falsifiable question is the unmeasured high-exposure
extension beyond logE 0: test whether the +0.5/+1.0 shoulder extrapolation ever
affects other source frames or clips a historically plausible 10-bit Cineon
scan. That test must inventory all raw frames before proposing any curve change.
