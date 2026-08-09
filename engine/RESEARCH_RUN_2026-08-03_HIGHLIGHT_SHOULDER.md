# 2026-08-03 research run: 5279 high-exposure shoulder and Cineon headroom

## Outcome

The hypothesis was **not supported**, so V21 remains the baseline and no V22
was created. Across all 165 source frames, no area-reduced sample reached the
V21 `logE=+0.5` control point, and no channel approached 10-bit Cineon code
1023. A deliberately severe diagnostic candidate that held all three 5279
records flat above the data sheet's `logE=0` endpoint changed only tiny
specular regions materially and did not provide a defensible visual
improvement.

## Safety and prior-state audit

- No process was writing in `experiments/emulsion_reconstruction`.
- The raw source was present: one 1.9 GB, 5760 x 4320, 23.976 fps, 165-frame,
  12-bit ProRes RAW HQ clip.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.
- Sites project `appgprj_6a702784adc88191ab6e183be09436b5` was active,
  owner-only custom access, with saved production version 2 sourced from that
  exact commit and live at <https://emulsion-5279.skylab.chatgpt.site>.
- The preceding toe-slope run was complete and had explicitly selected this
  high-exposure inventory as the next priority.

## Falsifiable question

Do V21's unmeasured `logE=+0.5/+1.0` shoulder samples affect any frame in the
available GH7 source enough to clip a conventional 10-bit Cineon scan or to
alter highlight rendering in a way that warrants a new curve model?

The hypothesis predicted that at least one source frame would enter the
extrapolated high-exposure region and that its scanner density would approach
code 1023. A severe flat-shoulder bound should then recover stable highlight
detail or colour if V21's extrapolation was excessive.

## Sources and evidence boundaries

### Stock-specific fact

1. **Kodak H-1-5279t, page 3, sensitometric curves.** The graph covers printed
   log exposure from -4 to 0 for 3200 K exposure, ECN-2 processing and Status-M
   densitometry. It does not publish measurements at +0.5 or +1.0. Local file:
   `references/kodak_5279_H-1-5279t.pdf`; archival mirror:
   <https://125px.com/docs/motionpicture/kodak/5279.pdf>.
2. **Kodak H-1-5279t, page 4.** The sensitometric and diffuse RMS granularity
   curves were made on different equipment, so the shoulder cannot be inferred
   by forcing the granularity graph to match the H-D graph point by point.

### Scanner-chain fact, not a 5279 coating measurement

3. **Eastman Kodak, _Scanning Recommendations for Extended Dynamic Range
   Camera Films_, pages 1 and 3.** Conventional 10-bit scanning uses 1023 code
   values, typically 0.002 density per code value, with D-min traditionally at
   code 95. Kodak also states that not every scene clips and that even some
   clipping may be visually negligible. Official PDF:
   <https://www.kodak.com/content/products-brochures/Film/Scanning-Recommendations-for-Extended-Dynamic-Range-Camera-Films-EN.pdf>.
   This document is about later VISION3 stocks. It supports the encoding and
   test method, not 5279 shoulder densities.
4. **Eastman Kodak, _Cineon File Format Description_, pages 1-3.** The format
   stores per-channel minimum/maximum data values and represented quantities,
   with linear interpolation between them. This confirms that code range and
   density meaning must be evaluated separately rather than treating 1023 as a
   generic display white. Official PDF:
   <https://www.kodak.com/content/products-brochures/Film/Cineon-File-Format-Description.pdf>.
   This was the new primary source added in this run; it is a file-format
   specification, not evidence for a particular scanner's spectral response.

## All-frame raw inventory

Every one of the 165 frames was decoded directly through AVFoundation as
extended-linear BT.2020 float32 from the original 12-bit ProRes RAW. Each frame
was area-reduced in extended-linear light to 720 x 540, then passed through the
unchanged Panasonic official camera LUT, photochemical sensor-noise separation,
`+0.45` stop virtual exposure, V-Gamut conversion, 5279 record sensitivities,
V21 development-domain DIR, broad period-telecine observer and Cineon density
matching.

The area reduction makes this an all-frame coverage inventory, not a full-pixel
laboratory measurement. The most extreme selected frame was subsequently
decoded again and tested at 1440 x 1080.

| record | maximum logE | frame | largest frame share above 0 | frames above +0.5 | maximum pre-clip Cineon code | frames clipped at 1023 |
|---|---:|---:|---:|---:|---:|---:|
| R | +0.12394 | 75 | 0.03755% | 0 / 165 | 869.76 | 0 / 165 |
| G | +0.09670 | 137 | 0.00977% | 0 / 165 | 866.16 | 0 / 165 |
| B | +0.21725 | 97 | 0.00412% | 0 / 165 | 858.10 | 0 / 165 |

Thus the `+1.0` point is completely inactive, the `+0.5` point is never reached,
and even the interpolation segment from 0 to +0.5 is touched by at most a few
hundredths of one percent of a frame. The highest measured scanner code retains
more than 153 code values of headroom.

Reproducible artifacts:

- `research_runs/2026-08-03_highlight_inventory/run_inventory.py`
- `research_runs/2026-08-03_highlight_inventory/frame_metrics.csv`
- `research_runs/2026-08-03_highlight_inventory/inventory_summary.json`

## Controlled extreme-frame A/B

Frame 97 was selected because the inventory found the largest high-exposure
excursion in its blue-sensitive record. It was decoded again from RAW and
area-reduced in extended-linear light to 1440 x 1080. This higher-resolution
test found maxima of `R/G/B = +0.11922/+0.11747/+0.35239 logE`; no sample
reached +0.5.

The candidate changed only the two unmeasured H-D samples:

| record | V21 density at logE 0 / +0.5 / +1.0 | diagnostic flat bound |
|---|---|---|
| R | 1.58 / 1.72 / 1.80 | 1.58 / 1.58 / 1.58 |
| G | 2.23 / 2.39 / 2.48 | 2.23 / 2.23 / 2.23 |
| B | 2.55 / 2.67 / 2.73 | 2.55 / 2.55 / 2.55 |

This is intentionally a severe lower bound, not a proposed physical curve.
Decode, exposure, random seed, dye-cloud populations, grain morphology,
development-domain DIR, spectral observers, 2383 chain, Cineon quantization and
both display finishes remained identical.

### 2383 projection-monitor branch

- linear RGB MAE: `0.00054147`
- PSNR: `60.18 dB`
- OKLab delta E: median `0.000916`, P95 `0.002889`, P99 `0.003731`
- absolute luma delta P95: `0.002167`
- luma P99: `0.84220 -> 0.84226`
- maximum luma: `0.98213 -> 0.97286`
- changed after 8-bit sRGB still conversion: `49.64%` of pixels

The large 8-bit changed-pixel count is dominated by tiny, spatially distributed
differences from recalibrating the physical projection-monitor mapping after the
curve change. Side-by-side review is not stably distinguishable. The amplified
difference map shows that the only large local changes occur in bright leaf and
specular details; the candidate lowers peaks but does not reveal new structure.

### Cineon / Spirit 2K / Blu-ray branch

- linear RGB MAE: `0.00001600`
- PSNR: `70.53 dB`
- OKLab delta E: median `0.0000022`, P95 `0.0001369`, P99 `0.0008300`
- absolute luma delta P95: `0.00001314`
- luma P99 unchanged to reported precision: `0.767774 -> 0.767774`
- maximum luma: `0.99911 -> 0.97433`
- changed after 8-bit sRGB still conversion: `1.90%` of pixels

The scan difference is localized to a handful of bright specular pixels. The
flat candidate reduces their peaks but supplies no evidence that the lower
values are more faithful to 5279. It does not recover clipped Cineon data,
because the baseline never clipped.

Controlled artifacts:

- `research_runs/2026-08-03_highlight_inventory/run_shoulder_ab.py`
- `research_runs/2026-08-03_highlight_inventory/shoulder_ab_metrics.json`
- `research_runs/2026-08-03_highlight_inventory/ab_projection.png`
- `research_runs/2026-08-03_highlight_inventory/ab_scan.png`
- `research_runs/2026-08-03_highlight_inventory/difference_x24_projection.png`
- `research_runs/2026-08-03_highlight_inventory/difference_x24_scan.png`

## Technical validation

- The original input remains 5760 x 4320, 165 frames, 24000/1001 fps, 12-bit
  ProRes RAW HQ with linear transfer metadata.
- All 165 inventory frames decoded successfully through the extended-linear
  AVFoundation path.
- No inventory sample clipped conventional 10-bit Cineon code 1023.
- The current V21 masters remain intact and independently signalled as
  5760 x 4320, 12-bit `yuv444p12le`, ProRes 4444, 24000/1001 fps, 13 frames,
  Rec.709 primaries/transfer/matrix.
- Projection master SHA-256:
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Scan/Blu-ray master SHA-256:
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- The existing neutral calibration diagnostic still places V-Log 18% at
  `0.423311`, 2383 LAD at density `1.0`, Cineon neutral gray at code 445, and
  the +6-stop synthetic neutral below display clipping in both branches.
- Manual review found no new purple/blue cast, lifted black, branch leakage or
  coarse 8/16 mm-like grain. The candidate's only obvious local effect is lower
  specular brightness.

## Conclusion: falsified / no release

### Confirmed

- The available source does not exercise the V21 `+0.5/+1.0` shoulder control
  points; only the first fraction of the 0 to +0.5 segment is sampled.
- The modeled conventional Cineon scan has ample headroom for every source
  frame under the present `+0.45` stop virtual exposure.
- Scanner code saturation, negative shoulder density and display highlight
  placement are separate questions. No display preference can replace a
  missing 5279 step-wedge measurement.

### Falsified

- The source does not contain a frame whose modeled 5279 density approaches
  Cineon code 1023.
- Removing all post-0 density growth does not recover hidden highlight detail
  or produce a stable visual-consistency advantage over V21.
- There is no evidence for replacing V21's extrapolation with the flat bound.

### Unknown

- The real 5279 H-D shoulder above the plotted `logE=0` endpoint remains
  unpublished in the available data sheet.
- A hotter source clip, measured 5279 step wedge or period scanner capture could
  still exercise this region and change the conclusion.
- The all-frame inventory was area-reduced; isolated subpixel RAW peaks may be
  higher, but the 1440 x 1080 extreme-frame retest and large Cineon headroom
  make a hidden material clipping event unlikely in this clip.
- The Kodak extended-range scanning paper concerns VISION3, so its later-stock
  clipping examples cannot be imported as 5279 behavior.

## Release decision and next priority

No algorithm file, calibration baseline, formal output master, release
screenshot, site source, Git commit, saved Sites version or production
deployment was changed. V21 remains current; the private production site stays
on version 2.

The next highest-priority falsifiable question is the period Spirit/telecine
observer itself: test whether V21's provisional broad RGB response centres and
widths produce a stable, physically plausible matrix relative to Status-M and
the DFT Spirit 2K documentation, or whether one bounded spectral-response
family measurably improves six-colour separations without disturbing neutral
density and the 2383 branch.
