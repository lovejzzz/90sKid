# 2026-08-03 research run: 2383 projected-gray anchor

## Outcome

The hypothesis was **internally supported but failed the independent-evidence
and visual-improvement release gates**. Kodak's documented 2383 LAD vector of
`1.09 / 1.06 / 1.03` Status-A does not remain neutral when V21's later view
correction is calibrated on equal Status-A density triplets. A research
candidate that calibrated the view correction on scalar multiples of the
official LAD vector reduced the LAD OKLab chroma from `0.0034974` to
`0.000000597` and kept six synthetic neutral probes similarly close to gray.

That result is circular: the same inferred LAD-proportional trajectory defines
both the candidate and the neutrality metric. No measured off-LAD 2383 neutral
scale was found, the six-colour directional check was mixed, and the RAW-frame
A/B did not show a stable visible correction. V21 remains the baseline; no V22,
formal master, website change, commit, saved Sites version or deployment was
created.

## Safety and prior-state audit

- The prior Status-A trajectory run completed at 07:56 EDT, wrote a complete
  negative result and left production unchanged. No prior emulsion process was
  active.
- The raw source remained present and unchanged: 2,007,616,000 bytes,
  5760 x 4320, 165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ.
- V21 remained the highest formal version. Both 13-frame native 5.7K,
  12-bit ProRes 4444 masters and their manifests were present.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.
- Sites production version 2 was sourced from that exact commit, remained
  owner-only, and was live at <https://emulsion-5279.skylab.chatgpt.site>.
- No file under `sources/` was changed.

## Falsifiable question

After adopting Kodak's official 2383 LAD vector and the preceding run's
proportional analytical-dye neutral trajectory, should the post-spectral
projected-gray correction be calibrated on V21's equal Status-A density axis,
omitted, or recalibrated on scalar multiples of the official LAD vector?

The release hypothesis required the LAD-aware view correction to:

1. preserve Kodak's documented visual-neutral LAD relationship;
2. reduce gray-scale chroma using evidence independent of its own construction;
3. avoid black-level, highlight, six-colour or scan-branch regressions; and
4. provide a stable visible improvement on the original RAW frame.

## Sources and evidence boundaries

### Newly added primary evidence

1. **Eastman Kodak, US 6,372,418 B1, lines 247 and 264 / print-film
   sensitometry definitions.** Equivalent Neutral Density is a *visual*
   density obtained when the other dye records are added in the quantities
   needed for neutral gray. It is not an equal-RGB Status-A triplet. The patent
   also defines print-film contrast on END-versus-log-exposure curves. Source:
   <https://patents.google.com/patent/US6372418B1/en>.
2. **Eastman Kodak, US 6,987,586 B2, claims 19-20 and 27-30.** A print-film
   appearance transform converts density-log-exposure curves to analytical dye
   amounts, applies viewing-condition corrections including neutrality, and
   then converts through a perceptual colour space under a chosen illuminant to
   the display device. Source:
   <https://patents.google.com/patent/US6987586/en>.

### Rechecked primary constraints

3. **Kodak H-61B, page 1.** For 2383/3383, `1.09 R / 1.06 G / 1.03 B`
   Status-A is the aim that produces visual neutral density 1.0. Six gray
   patches should appear neutral; pink highlights and green shadows indicate
   contrast mismatch. Source:
   <https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf>.
4. **Eastman Kodak, US 2002/0163657 A1, paragraphs 46-48.** The 2383 example
   converts Status-A densities into analytical dye amounts with a published
   3x3 approximation, states that the exact transform depends on dye set and
   viewing light, and converts the official LAD vector before adjustment.
   Source: <https://patents.google.com/patent/US20020163657A1/en>.

### Fact, inference and unknown

- **Fact:** Equal Status-A densities are not the documented 2383 visual-neutral
  LAD aim.
- **Fact:** Kodak's digital print-film model places viewing-light/perceptual
  conversion after analytical dye amount and allows a distinct neutrality
  correction at that stage.
- **Implementation fact:** V21's `neutralize_2383_projected_gray_scale()` builds
  its correction table from equal Status-A triplets, despite V21's preceding
  spectral integration of 2383 dyes under a xenon SPD.
- **Model inference tested:** scalar multiples of `1.09 / 1.06 / 1.03` form the
  complete off-LAD visual-neutral trajectory. The public sources do not state
  that this was the laboratory trajectory for a 5279 negative printed to 2383.
- **Unknown:** measured Status-A or END values for the six H-61 gray patches,
  including period printer spectrum, processing batch, densitometer and
  projection calibration.

## Controlled experiment

### Four variants

1. `v21_equal`: equal `1.00 / 1.00 / 1.00` print aim and V21's equal-density
   projected-gray correction;
2. `kodak_ad_v21_view`: official LAD, proportional analytical-dye print
   trajectory and V21's equal-density projected-gray correction;
3. `kodak_ad_no_view`: official LAD trajectory with no post-spectral gray
   correction;
4. `kodak_ad_lad_view`: official LAD trajectory with the projected-gray table
   built from scalar multiples of the LAD vector.

Within variants 2-4, only the projected-gray correction changed. Relative to
V21, all three also include the previous run's research-only official-LAD print
trajectory. The original 12-bit RAW decode, Panasonic transform, `+0.45` stop
exposure, 5279 H-D/chemistry/DIR/morphology and seed, 3200 K printer model,
2383 curves and dyes, Callier term, xenon SPD, H-61 colour guard, monitor
adaptation and scan branch were held fixed.

### Synthetic neutral gate

The six probes are scene-neutral levels at `-3, -2, -1, 0, +1, +2` stops
around 18 percent. They are not claimed to be the H-61 patch exposures.

| variant | shaped LAD Status-A | LAD corrected OKLab chroma | six-probe mean / max chroma |
|---|---|---:|---:|
| V21 equal | 1.000 / 1.000 / 1.000 | 0.00000463 | 0.0000348 / 0.0001947 |
| Kodak AD + V21 view | 1.090 / 1.060 / 1.030 | 0.00349743 | 0.0027757 / 0.0037119 |
| Kodak AD + no view correction | 1.090 / 1.060 / 1.030 | 0.00892046 | 0.0130317 / 0.0238728 |
| Kodak AD + LAD-aware view | 1.090 / 1.060 / 1.030 | 0.000000597 | 0.0000368 / 0.0001224 |

This confirms that V21's equal-density table is coordinate-inconsistent with
the official LAD candidate, and that simply removing the final correction is
worse. It does **not** independently validate the LAD-proportional correction,
because its own trajectory defines the gray target.

### Six-colour directional check

Relative to the unchanged provisional Spirit/Cineon patch reference:

- V21 mean colour delta-E / mean absolute hue error:
  `0.0503121 / 4.5461 degrees`;
- official LAD plus V21 view:
  `0.0503590 / 4.3299 degrees`;
- official LAD with no view correction:
  `0.0503379 / 4.3343 degrees`;
- official LAD plus LAD-aware view:
  `0.0503371 / 4.3591 degrees`.

The candidate slightly improves the provisional hue metric while slightly
worsening delta-E. The differences are small, mixed, and not independent of
the model's existing scan-derived H-61 guard.

## Controlled RAW-frame A/B

Frame 12 was decoded from the original ProRes RAW as extended-linear BT.2020
float32 and area-reduced in linear light to 1440 x 1080. Every variant used the
same stochastic seed.

For the full LAD-aware candidate versus V21:

- linear RGB MAE `0.00069865`, PSNR `58.56 dB`;
- OKLab delta-E median / P95 / P99
  `0.001345 / 0.005908 / 0.015386`;
- P95 absolute luminance delta `0.002179`;
- luminance P1 `0.00003097 -> 0.00002893`;
- luminance P99 `0.843238 -> 0.843156`;
- values at or above 1.0: `0.0%`; values at or below 0.0: `0.0%`;
- pixels changed after 8-bit sRGB review conversion: `68.57%`.

Manual review at native review size found the pair nearly indistinguishable.
The 12x difference map showed low-amplitude opponent changes concentrated on
dark foliage, coloured edges and fine texture. There was no new purple/blue
cast, lifted black, highlight clipping, branch leakage or coarse 8/16 mm-like
grain, but also no stable correction attributable to independent 2383 evidence.
The no-view variant produced larger chroma and shadow changes and was rejected.

The scan/Blu-ray isolation render was bit-identical: linear MAE, maximum
absolute delta and changed 8-bit pixels were all `0.0`.

## Reproducible artifacts

- `research_runs/2026-08-03_projected_gray_anchor/run_ab.py`
- `research_runs/2026-08-03_projected_gray_anchor/metrics.json`
- `baseline_v21_equal.png`
- `candidate_kodak_ad_v21_view.png`
- `candidate_kodak_ad_no_view.png`
- `candidate_kodak_ad_lad_view.png`
- corresponding A/B and `difference_x12` images;
- view-stage-isolation and scan-isolation images.

All single stills are 1440 x 1080 8-bit sRGB; A/B images are 2880 x 1080.
They are research review artifacts, not release screenshots.

## Technical validation

- The research script passed Python bytecode compilation and completed from the
  original RAW decoder.
- The source probe remained 5760 x 4320, 165 frames, 24000/1001 fps, 12-bit
  ProRes RAW HQ with linear transfer metadata.
- The existing V21 masters remained 5760 x 4320, 12-bit `yuv444p12le`, ProRes
  4444, 24000/1001 fps, 13 frames, with Rec.709 primaries/transfer/matrix.
- Projection master SHA-256:
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Scan/Blu-ray master SHA-256:
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- The site repository remained clean and no `sources/` file changed.

## Release decision

No release. The LAD-aware view correction is more coherent than applying an
equal-Status-A table to an unequal official LAD vector, but it fails two
required gates:

1. the off-LAD trajectory and its validation target are the same inference;
2. the representative RAW A/B and provisional six-colour check do not show a
   stable independent advantage.

V21 remains current. No new video, formal screenshot, Changelog entry, site
build, Git commit, Sites version or deployment was made. The private production
site remains on version 2.

## Next priority

Obtain an independent neutral-scale target before revisiting the code: the
1976 Pytlak et al. LAD control paper, the cited END densitometer-calibration
procedure, a Kodak TAF/DLE step-series table, or measured 2383 six-patch
Status-A/END values. The next falsifiable test should compare V21 and the
LAD-aware candidate against that independent trajectory; absent such data,
further gray-table changes would be subjective drift.
