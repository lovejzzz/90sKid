# 2026-08-03 research run: independent 2383 DLE holdout

## Outcome

The research hypothesis was **supported by an independent holdout**, but the
release hypothesis failed.  A previously overlooked primary figure supplies a
real Kodak VISION 2383 control-neutral Density Log Exposure series rather than
an inferred scalar trajectory.  Its green Status-A curve departs materially
from the red/blue midpoint through the dense half of the print scale.  This
falsifies both V21's equal-density trajectory and the recent hypothesis that
every off-LAD neutral is a scalar multiple of `1.09 / 1.06 / 1.03`.

A research-only density-dependent green-crossover candidate reduced the blind
three-step holdout RMSE from about `0.216 D` to `0.040 D`.  It did not earn a
release: red and blue cannot yet be separated reliably from the plotted line
styles, six-colour evidence remained mixed, the RAW-frame difference was not a
stable visible improvement, and the candidate slightly reduced the population
of exact display-black pixels.  V21 remains current.  No V22, formal master,
website change, commit, saved Sites version or deployment was created.

## Safety and prior-state audit

- The projected-gray-anchor run had finished at 08:56 EDT and left production
  unchanged.  No Lens emulsion, encoder, build or deployment process was
  active.  The app task-list query timed out and was terminated safely; process,
  output-timestamp and clean-worktree checks showed no residual writer.
- The original source remained present: 2,007,616,000 bytes, 5760 x 4320,
  165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ with linear transfer.
- V21 remained the highest formal version.  Its projection and scan masters,
  manifests and hashes were unchanged.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.
- Sites project `appgprj_6a702784adc88191ab6e183be09436b5` remained active,
  owner-only, and live at <https://emulsion-5279.skylab.chatgpt.site>.  Production
  remained saved version 2 from the exact site commit above.
- No file under `sources/` was changed.

## Falsifiable question

Does an independent Kodak 2383 neutral DLE series support:

1. V21's equal Status-A neutral trajectory;
2. scalar multiples of the official `1.09 / 1.06 / 1.03` LAD vector; or
3. a density-dependent, non-achromatic Status-A trajectory?

The candidate could advance only if an unseen subset of the independent figure
was predicted better, neutral viewing and branch isolation remained valid, and
the original RAW frame showed a stable improvement without clipping, cast,
black lift or grain regression.

## New primary evidence

### 1. Kodak / IMAX US 6,987,586 B2, Figure 3 and columns 7-8

Figure 3 is explicitly described as the control-neutral DLE step series for
Kodak VISION Color Print Film 2383.  It contains 21 patch steps measured as red,
green and blue Status-A densities.  The text says that the series spans print
D-max to D-min, is converted to analytical dye amount, and is anchored at the
2383 LAD vector before optional flare, gamma, contrast and neutrality work.
Source: <https://patents.google.com/patent/US6987586B2/en>, especially Figure 3
and the description corresponding to lines 335-351 in the public text view.

The figure's red solid and blue dotted curves nearly overlap in places, but the
green dashed curve is unambiguous.  Between patent patch steps 2 and 8 its
Status-A density is about `0.06–0.29 D` below the red/blue midpoint.  Therefore
the documented control-neutral scale is not equal Status-A and is not a fixed
scalar multiple of the LAD vector.

### 2. Pytlak and Fleischer, SMPTE Journal 85(10), 1976

The accessible abstract confirms that LAD is a single standard patch placed
near the centre of each duplicating stock's useful straight-line region.  It
does not publish a 2383 six-step off-LAD trajectory in the available abstract.
Source: John P. Pytlak and Alfred W. Fleischer, “A Simplified Motion-Picture
Laboratory Control Method for Improved Color Duplication,” DOI
<https://doi.org/10.5594/J07544>, pp. 781-786.  The full article remains behind
the SMPTE member access boundary, so no inaccessible table is claimed here.

### 3. US 2006/0181721 A1 and current H-1-2383

The Kodak patent maps Cineon/DPX 445 to visual density 1.0 and green Status-A
`1.06`; for its 2383 example the reference relative log exposure is `0.714`, and
the sampled curve spans about `0.0587–3.979 D`.  It also warns that separate RGB
TRCs require gray-balance compensation.  Source:
<https://patents.google.com/patent/US20060181721A1/en>, paragraphs corresponding
to public text lines 338-347.

The current Kodak sheet calls its sensitometric curves representative
production data rather than product specifications.  That boundary applies
equally to the patent figure: it is strong evidence for curve *shape*, not a
batch-accurate 5279-to-2383 lab measurement.  Source: Kodak H-1-2383, March
2026, page 5:
<https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf>.

## Fact, inference and unknown

- **Fact:** Figure 3 is identified as a 2383 control-neutral DLE series measured
  in three Status-A channels.
- **Fact:** the dense-scale green curve is not the red/blue midpoint.
- **Fact:** V21's equal-density shaper and the recent LAD-proportional shaper
  both force `G - (R+B)/2` essentially to zero.
- **Model inference tested:** the visible green separation can be represented by
  a smooth correction against mean Status-A density while preserving mean print
  density and the official LAD anchor.
- **Unknown:** exact red-versus-blue samples where solid and dotted strokes
  overlap; the exact exposure, processing batch, densitometer, illuminant and
  post-DLE neutrality configuration used for the plotted series; and an actual
  5279 negative six-step strip printed onto period 2383.

## Digitization and blind holdout

The archived full-resolution Figure 3 raster was saved with SHA-256
`9325994fead512abcc6f037d6915a533cf8993daae797bd9a255a9d72076574e`.
The plot axis was calibrated from `4.5 D` at pixel x=125 to `0.0 D` at x=1563.
Line-stroke centres carry a conservative `+/-4 px`, or about `+/-0.0125 D`,
single-curve reading uncertainty.

Only the green curve minus the red/blue midpoint was used.  Patches 2, 4, 6 and
8 were fitting anchors.  Patches 3, 5 and 7 were not supplied to the candidate
and formed the blind holdout.

| mode | all 7 RMSE | fit RMSE | blind 3/5/7 RMSE | blind max error |
|---|---:|---:|---:|---:|
| V21 equal | 0.1971 D | 0.1818 D | 0.2160 D | 0.2926 D |
| LAD-proportional | 0.1971 D | 0.1818 D | 0.2160 D | 0.2926 D |
| official LAD, unshaped | 0.2888 D | 0.2698 D | 0.3124 D | 0.4507 D |
| patent-DLE candidate | **0.0311 D** | **0.0225 D** | **0.0398 D** | **0.0490 D** |

The unshaped current H-1 curve model crosses in the opposite direction and is
independently rejected.  The patent-DLE candidate predicts the withheld points
far better, but its residual remains larger than line-reading uncertainty and
does not resolve the missing red/blue trajectories.

## Research-only algorithm change

The candidate begins with the official LAD-proportional analytical-dye target.
Let `m` be its mean Status-A density and let `delta_g(m)` be the fitted green
departure from the red/blue midpoint.  The update preserves mean density:

```text
R' = R - correction / 3
G' = G + 2 * correction / 3
B' = B - correction / 3

correction = delta_g(m) - (G - (R+B)/2)
```

`delta_g` is piecewise linear through patches 2/4/6/8, the official LAD point
and conservative zero endpoints.  A post-spectral neutral table is then built
on the same DLE trajectory.  This second table is not counted as independent
evidence; independence comes only from the withheld patent points.

Production `src/emulsion_experiment.py` was not changed.

## Controlled RAW-frame A/B

Frame 12 was decoded from the original 12-bit ProRes RAW as extended-linear
BT.2020 float32 and area-reduced in linear light to 1440 x 1080.  The V21 frame
and candidate used the same `+0.45` stop exposure and deterministic stochastic
seed.  Only the 2383 neutral DLE shaper and matching projected-neutral table
changed.

Candidate versus V21:

- linear RGB MAE `0.00090897`, PSNR `56.33 dB`;
- OKLab delta-E median / P95 / P99
  `0.001737 / 0.024481 / 0.057477`;
- P95 absolute luminance delta `0.002185`;
- linear luminance P1 `0.00003097 -> 0.00007343`;
- linear luminance P99 `0.843238 -> 0.843294`;
- values at or above 1.0: `0.0%`; values at or below 0.0: `0.0%`;
- pixels changed after 8-bit sRGB review conversion: `77.33%`.

The 8-bit review still's exact-black population changed from `1.05%` to
`0.89%`, and its P1 luminance changed from zero to about `0.00083`.  This is
small but points in the wrong direction for the established scan/print black
discipline.

Manual review found the A/B nearly indistinguishable at normal size.  The 12x
difference map showed red/blue redistribution in high-density foliage, dark
edges and highlights, consistent with the intended green crossover.  There was
no new global purple/blue cast, highlight clipping, branch leakage or coarse
8/16 mm-like grain.  There was also no independently grounded visual reference
that made the candidate preferable.

## Neutral, colour and branch checks

- Six synthetic neutral probes had mean/max corrected OKLab chroma
  `0.0000203 / 0.0001090`, versus V21
  `0.0000348 / 0.0001947`.  This is an internal consistency check because the
  candidate's own DLE trajectory builds the viewing table.
- Six-colour provisional scan-reference mean delta-E changed
  `0.050312 -> 0.050324` (slightly worse), while mean absolute hue error changed
  `4.546 degrees -> 4.364 degrees` (slightly better).  The evidence is mixed.
- The scan/Blu-ray isolation render was bit-identical: linear MAE, maximum
  delta and changed 8-bit pixels were all zero.

## Reproducible artifacts

- `research_runs/2026-08-03_2383_dle_holdout/run_ab.py`
- `research_runs/2026-08-03_2383_dle_holdout/metrics.json`
- `research_runs/2026-08-03_2383_dle_holdout/US6987586B2_figure_3.png`
- `research_runs/2026-08-03_2383_dle_holdout/digitized_dle_green_crossover.csv`
- `research_runs/2026-08-03_2383_dle_holdout/dle_holdout_validation.png`
- baseline, candidate, A/B and 12x difference PNGs for projection and exact
  scan-branch isolation.

All single review stills are 1440 x 1080 8-bit sRGB; A/B stills are
2880 x 1080.  They are research artifacts, not release screenshots.

## Technical validation

- The research script passed Python bytecode compilation and strict JSON
  validation, then completed from the original RAW decoder.
- The source probe remained 5760 x 4320, 165 frames, 24000/1001 fps, 12-bit
  ProRes RAW HQ with linear transfer metadata.
- Existing V21 projection SHA-256:
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Existing V21 scan/Blu-ray SHA-256:
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- Site repository remained clean; no file under `sources/` changed.

## Release decision

No release.  The independent figure establishes that V21's equal Status-A
trajectory is structurally incomplete, and the holdout establishes that a
density-dependent green crossover is testable.  The current candidate still
fails the full release gate because:

1. it does not identify red and blue independently;
2. its figure is representative rather than a batch/process specification;
3. the six-colour test is mixed and the representative frame has no stable
   visible advantage;
4. display black moves slightly upward; and
5. no real 5279-to-2383 off-LAD measurement yet confirms that the patent DLE
   series should be transplanted unchanged into this exact negative/print chain.

V21 remains current.  No new video, formal screenshot, Changelog entry, site
build, Git commit, Sites version or production deployment was made.

## Next priority

Recover an archived 1998-2002 H-1-2383 curve or higher-fidelity patent/vector
figure and separate the red solid from blue dotted trace.  Then compare all
three Status-A channels against the contemporary print-stock curve at matched
relative log exposure, not only against mean density.  If that resolves the
red/blue ambiguity, repeat the holdout on several RAW frames selected for dense
print regions and require exact-black retention before considering V22.
