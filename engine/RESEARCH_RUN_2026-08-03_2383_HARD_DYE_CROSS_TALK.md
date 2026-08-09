# 2026-08-03 research run: 2383 hard-dye cross-talk from separated curves

## Outcome

The physical shortcut was **falsified**.  Kodak's published 2383 hard-dye
matrix cannot, by itself, turn the archived separated-light sensitometric
curves into the simultaneous control-neutral DLE trajectory shown in
US 6,987,586 Figure 3.  The parameter-free model predicts the red-minus-blue
crossing in the opposite direction over most of the tested scale.  Its blind
odd-step RGB RMSE is `0.10932 D`, compared with `0.02287 D` for the preceding
free full-RGB interpolation.

A single bounded cross-talk-strength parameter fitted only on even steps
reduces the blind RMSE to `0.06877 D`, but remains about three times worse than
the preceding holdout and still predicts the wrong red/blue sign at patent
steps 2, 3, 4, 6, 7 and 8.  The controlled RAW-frame A/B has no stable visual
advantage, slightly reduces exact display-black pixels, and makes the
six-colour evidence mixed.  V21 remains current.  No V22, formal master,
release screenshot, website change, Git commit, saved Sites version or
deployment was created.

## Safety and prior-state audit

- The preceding RGB DLE-trace run had finished at 11:08 EDT.  No Lens renderer,
  encoder, site build or deployment process was active.
- The original source remained present at 2,007,616,000 bytes: 5760 x 4320,
  165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ with linear transfer.
- V21 remained the highest formal version.  Its projection and scan/Blu-ray
  masters, manifests and SHA-256 hashes were unchanged.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.
- Sites project `appgprj_6a702784adc88191ab6e183be09436b5` remained active,
  owner-only, at <https://emulsion-5279.skylab.chatgpt.site>; production still
  corresponded to saved version 2 and the V21 commit.
- No file under `sources/` was changed.

## Falsifiable question

Can the published 2383 Status-A-to-analytical-dye matrix and dye cross-talk
combine the period separated-light R/G/B characteristic curves into a
simultaneous-neutral trajectory that:

1. predicts patent steps 3/5/7 after calibration only on 2/4/6/8;
2. beats the preceding `0.02287 D` blind RGB holdout;
3. preserves neutral viewing, six-colour direction and exact black; and
4. leaves the independent Spirit/Cineon/Blu-ray branch bit-identical?

Failure of the first two density gates was sufficient to reject release, but a
single original-RAW frame was still rendered to test the visible and branch
consequences rather than relying on synthetic curves alone.

## Sources and evidence boundary

### 1. Kodak/IMAX US 6,987,586 B2, Figures 2-4 and columns 7-8

The patent identifies Figure 3 as a 21-step control-neutral DLE series for
Kodak VISION Color Print Film 2383.  It states that Status-A data are converted
to analytical dye amounts by a hard dye match and publishes the 3x3 example
matrix used here.  It also gives the 2383 LAD point as Status-A
`1.09 / 1.06 / 1.03` for a projected visual neutral density of 1.0.  The patent
explicitly calls the linear matrix a practical approximation rather than an
exact conversion.  Source: <https://patents.google.com/patent/US6987586B2/en>,
especially Figure 3 and text around the hard-dye conversion example.

### 2. Archived Kodak H-1-2383t, revised March 2005, page 5

The National Archives PDF supplies vector red-, green- and blue-exposure
sensitometric curves for period 2383/ECP-2D, exposed for 1/500 second under
tungsten through Kodak Heat Absorbing Glass No. 2043 and a Series 1700 filter,
then measured in Status A.  These are separated-light curves, not a simultaneous
neutral control strip.  Source:
<https://www.archives.gov/files/preservation/products/resources/2383-TI.pdf>,
page 5, figure `F002_1254AC`.

### 3. Kodak H-1-2383, March 2026, pages 4-5

The current sheet provides representative Status-A sensitometry and spectral
dye-density plots, not product specifications or densitometer spectral response
functions.  The dye plot therefore cannot independently reconstruct the
Status-A cross-density matrix.  It remains useful as a physical dye-absorption
shape check, while the patent matrix is the only quantitative hard-dye match
used here.  Source:
<https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf>,
pages 4-5.

## Fact, inference and unknown

- **Fact:** the patent supplies both a 2383 hard-dye matrix and a simultaneous
  control-neutral DLE figure.
- **Fact:** the archived sheet supplies only each separated exposure's principal
  Status-A curve; it does not publish all three Status-A readings for every
  separated exposure.
- **Fact:** the model predicts a red/blue crossover with the opposite sign from
  the patent target through most of the tested scale.
- **Model inference tested:** after subtracting each separated curve's D-min,
  its principal density can be normalized at LAD and treated as the amount of
  the corresponding analytical dye; the inverse patent matrix then supplies
  cross-densities.
- **Empirical parameter tested:** one strength `alpha` between zero and the full
  matrix-predicted chromatic departure, fitted only on even patent steps.
- **Unknown:** the full three-channel cross-density response of the archived
  separated exposures; the exact Status-A densitometer spectral responses;
  the exposure construction and processing state of the patent DLE strip; and
  a measured 5279 negative gray scale printed onto period 2383.

## Model and blind holdout

For channel `c`, archived principal density `D_c(e)`, D-min `Dmin_c`, LAD
density `Dlad_c`, published LAD analytical dye amount `A_lad,c`, and published
hard-dye matrix `M`:

```text
q_c(e) = (D_c(e) - Dmin_c) / (Dlad_c - Dmin_c)
A_c(e) = q_c(e) * A_lad,c
D_Status-A(e) = M^-1 * A(e)
```

The three curves were horizontally aligned at their official LAD densities.
Model and patent samples were then compared at matched mean Status-A density,
so overall tone-scale placement could not conceal colour-trajectory error.

The calibrated variant preserved mean density and used only:

```text
D_calibrated = mean(D) + alpha * (D_model - mean(D_model))
alpha = 0.44377
```

`alpha` was fitted on patent steps 2/4/6/8.  Steps 3/5/7 stayed blind.

| mode | all-point RGB RMSE | even-step fit RMSE | blind 3/5/7 RMSE | blind max error |
|---|---:|---:|---:|---:|
| parameter-free hard dye | 0.10433 D | 0.10042 D | 0.10932 D | 0.20712 D |
| even-step strength fit | 0.05982 D | 0.05212 D | 0.06877 D | 0.11696 D |
| preceding full-RGB interpolation | 0.01706 D | 0.01081 D | **0.02287 D** | 0.03842 D |

At patent step 7 the target is `R-B = -0.07322 D`; the full hard-dye model
predicts `+0.10707 D`, and the even-fit variant still predicts `+0.04751 D`.
This is a structural sign failure, not a small digitization residual.

## Controlled original-RAW A/B

Frame 144 was selected because the preceding sparse inventory found the largest
mean print density there.  It was decoded from the original 12-bit ProRes RAW as
extended-linear BT.2020 float32 and area-reduced in linear light to 1440 x 1080.
The V21 baseline and even-fit candidate shared Panasonic conversion, `+0.45`
stop exposure, frame-index seed, 5279 nine-population dye-cloud formation, DIR,
grain, printer lamp, 2383 base curves/dyes, Callier term, xenon observer, H-61
guard, monitor adaptation and output conversion.  Only the 2383 neutral
Status-A trajectory and matching projected-neutral table changed.

Candidate versus V21:

- linear RGB MAE `0.00084977`, PSNR `56.78 dB`;
- OKLab delta-E median / P95 / P99
  `0.001627 / 0.026267 / 0.058639`;
- P95 absolute luminance delta `0.002105`;
- linear luminance P1 `6.6e-9 -> 3.23e-5`;
- linear luminance P99 `0.823076 -> 0.823053`;
- exact-black 8-bit pixels `1.20486% -> 1.02154%`;
- values at or above 1.0: `0.000279%` of channel samples;
- changed 8-bit pixels: `74.13%`.

Manual review found the normal-size A/B nearly indistinguishable.  The 12x
difference map reveals small cyan/magenta redistribution in foliage, walls and
edges, consistent with the model variable.  There is no obvious global purple
or blue cast, no coarse 8/16 mm-like grain and no spatially broad highlight
clipping.  There is also no stable correction that makes the candidate
preferable, while the exact-black regression is consistent and measurable.

## Neutral, colour and branch checks

- Six neutral probes have corrected OKLab chroma mean/max
  `7.47e-7 / 1.65e-6`; this is an internal consistency check because the
  candidate trajectory also builds its projected-neutral table.
- Six-colour projection-versus-scan mean delta-E is `0.050384`, slightly worse
  than V21's preceding-run value `0.050312`; mean absolute hue error is
  `4.362 degrees`, better than V21's `4.546 degrees`.  Evidence is mixed and the
  scan colour reference remains provisional.
- The scan/Blu-ray isolation A/B is bit-identical: linear MAE and maximum error
  are zero, and no 8-bit pixel changes.

## Reproducible artifacts

- `research_runs/2026-08-03_2383_hard_dye_cross_talk/run_ab.py`
- `research_runs/2026-08-03_2383_hard_dye_cross_talk/metrics.json`
- `research_runs/2026-08-03_2383_hard_dye_cross_talk/hard_dye_holdout.png`
- baseline, candidate, A/B and 12x difference PNGs for frame 144;
- bit-identical scan-isolation PNGs.

All single review stills are 1440 x 1080 8-bit sRGB; A/B stills are
2880 x 1080.  They are research artifacts, not release screenshots.

## Technical validation

- The research script passes Python bytecode compilation and strict JSON
  validation, then completes from the original RAW decoder.
- Source probe: 5760 x 4320, 165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ,
  linear transfer metadata.
- Existing V21 projection SHA-256:
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Existing V21 scan/Blu-ray SHA-256:
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- Site source remained clean and no file under `sources/` changed.

## Release decision

No release.  The candidate fails the independent density holdout by a large
margin, predicts the central R/B sign change incorrectly, slightly worsens the
six-colour delta-E, has no stable visible advantage and reduces exact-black
pixels.  Production `src/emulsion_experiment.py`, `CALIBRATION_5279.md`, formal
outputs, site source, Git history and Sites production remain unchanged.  V21
is still current.

## Next priority

Do not add more free trajectory parameters.  The highest-value next test is to
recover the **full separated-exposure cross-density data** or the Status-A
spectral response functions used for the 2383 hard-dye match.  Search Kodak
patents and SMPTE/lab literature for a TAF/DLE matrix, densitometer response or
three-channel measurements of each red/green/blue separation.  Without those,
the archived principal curves are mathematically insufficient to predict the
simultaneous neutral series, and further fitting would only reproduce the
patent target rather than independently explain it.
