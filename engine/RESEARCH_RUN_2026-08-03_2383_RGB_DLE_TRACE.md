# 2026-08-03 research run: 2383 red/blue DLE trace and archived curve cross-check

## Outcome

The line-identification hypothesis was **supported**, but the release hypothesis
failed.  The red solid and blue dotted curves in Kodak/IMAX US 6,987,586 B2
Figure 3 can be separated reproducibly through the dense half of the 2383
control-neutral DLE series.  At patent step 7 their Status-A densities differ by
about `0.0732 D`, well above the conservative `0.0125 D` single-line reading
uncertainty.

A full-RGB research candidate trained only on steps 2/4/6/8 reduced the blind
3/5/7 all-channel RMSE from V21's `0.10346 D` and the preceding green-only
candidate's `0.07830 D` to `0.02287 D`.  It still did not earn V22.  The
six-colour directional metric became slightly worse than the preceding
candidate, the visible A/B had no stable advantage, and exact display-black
pixels fell consistently on all three high-print-density RAW frames.  V21
remains the production baseline.  No formal master, release screenshot, website
change, Git commit, saved Sites version or deployment was made.

## Safety and prior-state audit

- The preceding 2383 DLE holdout run finished at 10:03 EDT and left production
  unchanged.  No Lens emulsion renderer, encoder, site build or deployment
  process was active at the start of this run.
- The original source remained present: 2,007,616,000 bytes, 5760 x 4320,
  165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ with linear transfer metadata.
- V21 remained the highest formal version.  Both native 5.7K, 13-frame, 12-bit
  ProRes 4444 masters and their manifests were intact.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`; its published content still names
  V21 as current.  The private production site was not changed.
- No file under the synced `sources/` tree was changed.

## Falsifiable question

Can the patent's red solid and blue dotted 2383 control-neutral DLE traces be
separated reproducibly, and does the resulting full-RGB neutral trajectory:

1. predict unseen odd-numbered patent steps better than V21 and the preceding
   green-only candidate;
2. preserve neutral viewing and strict scan-branch isolation; and
3. improve several original RAW frames without clipping, black lift, a global
   cast, coarse grain or projection/scan leakage?

The candidate could advance only if all three gates passed.

## New primary evidence

### 1. Archived Kodak H-1-2383t, revised March 2005, page 5

The U.S. National Archives preserves an original Kodak technical sheet whose
PDF metadata has a December 1997 creation date and a May 2005 modification date.
Page 5 contains vector, rather than raster-only, sensitometric paths identified
as figure `F002_1254AC`.  The exposure is 1/500 second tungsten through Kodak
Heat Absorbing Glass No. 2043 plus Series 1700 filter; processing is ECP-2D and
densitometry is Status A.  The graph labels the blue-, green- and red-exposure
curves separately.  Source:
<https://www.archives.gov/files/preservation/products/resources/2383-TI.pdf>,
page 5.

This is a stock/process-era cross-check, not a neutral control-strip trajectory.
Its three curves are separate coloured-light sensitometric exposures.  They
cannot be treated as simultaneous neutral RGB Status-A output without also
modeling dye cross-talk and the exposure construction of the neutral strip.

### 2. Kodak/IMAX US 6,987,586 B2, Figure 3 and columns 7-8

The patent identifies Figure 3 as a 21-step control-neutral DLE series for Kodak
VISION Color Print Film 2383, measured in red, green and blue Status-A density.
Its legend identifies red as solid, green as dashed and blue as dotted.  The
series was used as physical target tone-scale data for a digital-cinema print
model.  Source: <https://patents.google.com/patent/US6987586B2/en>, Figure 3 and
the description corresponding to public text lines 334-343.

### Fact, model inference and unknown

- **Fact:** the patent red and blue paths are distinct at several steps; the
  separation changes sign across the tested scale.
- **Fact:** the archived sheet supplies independently labelled vector R/G/B
  sensitometric curves for period 2383/ECP-2D.
- **Inference tested:** an even-step, mean-preserving interpolation of the full
  patent RGB departure can represent the intervening odd steps.
- **Unknown:** the exact simultaneous exposure construction, batch, control-strip
  calibration and post-DLE neutrality operations behind Figure 3.
- **Unknown:** how the archived separated-light sensitometric curves combine
  through dye cross-talk into a control-neutral RGB density series.
- **Unknown:** a measured 5279 negative gray strip printed onto period 2383.

## Reproducible red/blue separation

The patent raster was thresholded once.  The continuous red solid curve joins
the graph boundary and therefore belongs to the large plot component containing
the step-2 red seed.  Row centres were restricted to a bounded neighborhood of
the already recorded red/blue midpoint, then stabilized by a 31-row median and
a 101-row cubic Savitzky-Golay fit.  Blue was reflected across the preceding
run's independently recorded red/blue midpoint.  Seven isolated dotted
components independently verify that the blue path crosses from the lower-
density side of red to the higher-density side.

| patent step | red D | green D | blue D | red - blue D |
|---:|---:|---:|---:|---:|
| 2 | 4.0783 | 4.0150 | 4.0768 | +0.0016 |
| 3 | 3.9474 | 3.8288 | 3.9198 | +0.0276 |
| 4 | 3.7260 | 3.5080 | 3.7312 | -0.0052 |
| 5 | 3.3085 | 3.0183 | 3.3132 | -0.0048 |
| 6 | 2.6886 | 2.4206 | 2.7033 | -0.0148 |
| 7 | 1.8958 | 1.7243 | 1.9690 | -0.0732 |
| 8 | 1.1806 | 1.1375 | 1.2165 | -0.0360 |

Artifacts:

- `research_runs/2026-08-03_2383_rgb_dle_trace/run_ab.py`
- `research_runs/2026-08-03_2383_rgb_dle_trace/digitized_dle_rgb.csv`
- `research_runs/2026-08-03_2383_rgb_dle_trace/metrics.json`

## Blind full-RGB trajectory holdout

Only steps 2/4/6/8, the official `1.09/1.06/1.03` LAD vector and conservative
zero-departure endpoints were supplied to the candidate.  Steps 3/5/7 remained
blind.  Every target preserves mean Status-A density; only the R/G/B departure
from that mean is fitted.

| mode | all-point RGB RMSE | blind 3/5/7 RGB RMSE | blind max error |
|---|---:|---:|---:|
| V21 equal | 0.09391 D | 0.10346 D | 0.19506 D |
| preceding green-only DLE candidate | 0.07622 D | 0.07830 D | 0.10964 D |
| full-RGB DLE candidate | **0.01706 D** | **0.02287 D** | **0.03842 D** |

The full-RGB interpolation therefore predicts the withheld patent steps much
better than both prior modes.  Its blind per-channel RMSE is approximately
`R 0.01271 / G 0.02650 / B 0.02656 D`.  The residual is still two to three
times the single-curve raster reading uncertainty.

## Archived sensitometric-curve comparison

The 2005 sheet's vector paths were extracted directly.  Each was aligned at the
official LAD density and sampled at a common relative log exposure whose mean
density matched each patent step.  The result is directionally useful but not a
neutral-trajectory replacement:

- all-channel RMSE against patent Figure 3: `0.06105 D`;
- channel RMSE: `R 0.03486 / G 0.05518 / B 0.08320 D`;
- maximum error: `0.15277 D`;
- red-minus-blue RMSE: `0.11502 D`.

Most importantly, the aligned separated-light curves predict positive red-minus-
blue density through the tested scale, reaching about `+0.1541 D` at step 7,
where the simultaneous neutral patent series measures about `-0.0732 D`.
Therefore the archived graph confirms the historical stock and characteristic-
curve scale but falsifies the shortcut of transplanting its separated-light
paths directly into a neutral shaper.

Artifacts:

- `research_runs/2026-08-03_2383_rgb_dle_trace/kodak_2383_H-1-2383t_2005.pdf`
- `research_runs/2026-08-03_2383_rgb_dle_trace/kodak_2383_H-1-2383t_2005_page5.png`
- `research_runs/2026-08-03_2383_rgb_dle_trace/extract_archived_curves.py`
- `research_runs/2026-08-03_2383_rgb_dle_trace/archived_2005_2383_curves.csv`
- `research_runs/2026-08-03_2383_rgb_dle_trace/archived_curve_comparison.json`

## Controlled multi-frame RAW A/B

A sparse 15-frame inventory selected three high-print-density frames from the
original source: frame 120 had the largest fraction above mean 2383 density
2.5, frame 144 the highest mean print density, and frame 164 the largest
fraction above density 3.0.  Each was decoded from the original 12-bit ProRes
RAW as extended-linear BT.2020 float32 and area-reduced in linear light to
1440 x 1080.

Within every A/B, Panasonic conversion, +0.45-stop virtual exposure, frame-index
seed, 5279 nine-population dye-cloud formation, development-domain DIR, grain,
printer lamp, 2383 base curves/dyes, Callier term, xenon observer, H-61 guard,
monitor adaptation and output encoding were fixed.  Only the 2383 neutral
Status-A shaper and its matching post-spectral neutral table changed.

| frame | linear MAE | PSNR | median / P95 OKLab dE | exact black V21 -> candidate |
|---:|---:|---:|---:|---:|
| 120 | 0.0010103 | 55.03 dB | 0.00186 / 0.02555 | 1.2282% -> 1.0509% |
| 144 | 0.0010109 | 55.02 dB | 0.00187 / 0.02630 | 1.2049% -> 1.0214% |
| 164 | 0.0010119 | 55.01 dB | 0.00186 / 0.02530 | 1.1813% -> 1.0052% |

P95 absolute luminance changes stay near `0.0021`; no meaningful highlight
clipping occurred.  The scan/Blu-ray branch was bit-identical at frame 144:
linear MAE and maximum error were zero and no 8-bit pixel changed.

Six-colour projection-versus-scan mean delta-E changed from V21 `0.050312` to
the green-only candidate `0.050324` and the RGB candidate `0.050343`.  Mean
absolute hue error changed `4.546 -> 4.364 -> 4.370 degrees`.  Thus the RGB
candidate improves over V21's hue direction but is slightly worse than the
preceding candidate on both colour metrics.

Manual side-by-side review found no clipping, global purple/blue cast, coarse
8/16 mm-like grain or branch leakage.  The normal-size A/B is nearly
indistinguishable; the 12x difference shows distributed cyan/magenta
redistribution around foliage and density boundaries, not a stable visual
correction.  The exact-black reduction is small but consistent and moves in the
wrong direction for the established black discipline.

Representative artifacts:

- `research_runs/2026-08-03_2383_rgb_dle_trace/ab_rgb_dle_frame144.png`
- `research_runs/2026-08-03_2383_rgb_dle_trace/difference_x12_rgb_dle_frame144.png`
- corresponding frame-120 and frame-164 A/B files;
- bit-identical frame-144 scan-isolation images.

## Technical validation

- Both research scripts pass Python bytecode compilation; both JSON artifacts
  parse in strict mode.
- The patent source raster hash remains
  `9325994fead512abcc6f037d6915a533cf8993daae797bd9a255a9d72076574e`.
- The archived Kodak PDF hash is
  `76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156`.
- All review stills are 1440 x 1080 8-bit sRGB; side-by-side files are
  2880 x 1080.  They are research artifacts, not release screenshots.
- Existing V21 projection SHA-256 remains
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Existing V21 scan/Blu-ray SHA-256 remains
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- Site source remained clean and no file under `sources/` changed.

## Release decision

No release.  The run converts an ambiguity into useful three-channel evidence
and the blind density holdout is materially better, but it still fails the
complete release gate:

1. the patent series is representative and lacks its exact control-strip setup;
2. the archived separated-light curves cannot reproduce the neutral R/B sign
   change and cannot supply independent confirmation;
3. six-colour evidence is slightly worse than the preceding candidate;
4. three RAW frames show no stable visible advantage; and
5. exact-black population decreases consistently.

Production `src/emulsion_experiment.py`, `CALIBRATION_5279.md`, formal outputs,
site source, Git history and Sites production all remain unchanged.  V21 is
still current.

## Next priority

Test whether the published 2383 Status-A-to-analytical-dye matrix and spectral
dye curves can combine the archived separated-light sensitometric paths into a
**simultaneous neutral-exposure** DLE series that predicts the patent's red/blue
sign reversal.  This must be an exposure/dye-cross-talk calculation, not another
free RGB interpolation.  Use patent steps 2/4/6/8 for calibration and 3/5/7 as
blind holdout; reject the hypothesis if it cannot beat the present `0.02287 D`
RGB holdout without raising display black or worsening six-colour direction.
