# 2026-08-03 research run: bounded 2383 Status-A neutral trajectory

## Outcome

The analytical-dye-amount hypothesis was **internally confirmed but failed the
independent-evidence and visual release gates**.  Kodak's 2383 analytical-dye
matrix supplies a physically meaningful coordinate system in which a neutral
tone trajectory can preserve the official `1.09 / 1.06 / 1.03` Status-A LAD
vector.  In a controlled implementation, that trajectory reduced the shaped
LAD error to `2.38e-7 D` and made the three LAD-normalized analytical dye
amounts nearly identical across six representative neutral probes.

However, those two successes are circular: the candidate was constructed from
the matrix and assessed against the same matrix.  No measured 5279-to-2383
six-step target was found.  The camera-frame change was concentrated in dark
regions, lowered the 1st-percentile luminance by about 40 percent, and had no
stable visible advantage at normal viewing size.  No V22 was created.  V21
remains the production baseline and the private site remains at version 2.

## Safety and prior-state audit

- No emulsion renderer, encoder, site build or deployment process was active at
  the start of the run.  Unrelated development processes belonged to other
  projects and were not touched.
- The previous-task listing service timed out twice, but the process table,
  repository timestamps and clean site worktree showed no unfinished Lens
  writer.  The run proceeded only after those local checks remained stable.
- The original source was present at
  `/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV`.
- V21 was still the highest formal version.  Both 13-frame, native-resolution
  12-bit ProRes 4444 masters and manifests were present.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`.  Sites reported private production
  version 2 at <https://emulsion-5279.skylab.chatgpt.site>.
- No file under `sources/` was changed.

## Falsifiable question

Can a bounded neutral Status-A trajectory preserve Kodak's documented
`1.09 / 1.06 / 1.03` 2383 LAD vector and the six-neutral-patch principle more
defensibly than V21's equal-density shaper, without creating a shadow cast,
black-level regression, colour-patch regression or scan-branch leakage?

The four controlled variants were:

1. current V21: equal `1.00 / 1.00 / 1.00` LAD plus equal-density shaper;
2. official LAD plus the same equal-density shaper;
3. official LAD plus a channel-independent analytical-dye-amount trajectory;
4. official LAD with no additional print-density shaper.

## Sources and evidence boundaries

### New primary evidence

1. **Eastman Kodak, US20020163657A1, _Method of digital processing for
   digital cinema projection of tone scale and color_, paragraphs 40 and
   46–48, Figures 2–4.**  The worked 2383 example describes a control neutral
   DLE step series, performs tone-scale operations in analytical dye amount
   space, gives an explicit Status-A-to-analytical-dye 3×3 matrix, and converts
   the `1.09 / 1.06 / 1.03` LAD vector into that space before adjustment.
   Source: <https://patents.google.com/patent/US20020163657A1/en>.
2. **Eastman Kodak, US20060181721A1, _Motion picture content preview_,
   paragraphs 41–49.**  Its 2383 display construction anchors DPX 445 at green
   Status-A `1.06`; one implementation derives three identical TRCs from the
   green curve, while the patent explicitly notes that three separate RGB TRCs
   may instead be used but require gray-balance compensation.  This is direct
   evidence that the LAD anchor alone does not uniquely select an off-LAD
   trajectory.  Source:
   <https://patents.google.com/patent/US20060181721A1/en>.
3. **Eastman Kodak, US5888706A, _Color motion picture print film_, paragraphs
   72–75.**  Equivalent Neutral Density is the axis used to define overall,
   mid-scale and upper-scale print contrast around the 1.0 END point.  Typical
   red and blue mid-scale contrasts are described as within about ±10 percent
   of green, which is a useful bound but does not provide stock-specific 2383
   six-patch target values.  Source:
   <https://patents.google.com/patent/US5888706A/en>.

### Rechecked official control target

- **Kodak H-61B, page 1.**  The 2383 Status-A LAD aim is
  `1.09 R / 1.06 G / 1.03 B`, the six gray patches should appear neutral, and
  pink highlights with green shadows indicate contrast mismatch.  It does not
  list numeric Status-A values for those six patches.  Source:
  <https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf>.

### Fact, inference and unknown

- **Fact:** Kodak used a 2383-specific mapping from Status-A density to
  analytical dye amounts for a print-film digital model, and adjusted the DLE
  neutral series after converting the LAD vector into that space.
- **Fact:** a separate Kodak patent documents both a common-green-TRC option
  and a three-TRC option requiring gray-balance compensation.  Therefore the
  single LAD anchor does not uniquely determine the trajectory.
- **Model inference tested here:** divide analytical dye amounts by the amounts
  of the official LAD vector, take their common mean, and constrain all three
  normalized amounts to that mean at every neutral exposure.  This is bounded
  and passes exactly through LAD, but Kodak does not state that this was the
  laboratory trajectory for a 5279 negative printed to 2383.
- **Unknown:** measured Status-A or END values for the six H-61 gray patches
  from a period 5279-to-2383 laboratory print, including the printer spectrum,
  processing batch and densitometer calibration.

## Controlled experiment

### Matrix candidate

The 2383 example matrix was used exactly as published:

```text
[R_AD]   [ 0.3260  -0.0402  -0.0287 ] [R_Status-A]
[G_AD] = [-0.3380   0.3859   0.3166 ] [G_Status-A]
[B_AD]   [-0.0017  -0.0361   0.3677 ] [B_Status-A]
```

For a neutral sample with analytical dye vector `a` and LAD vector `a_LAD`,
the research candidate used

```text
t = mean(a / a_LAD)
a_neutral = t · a_LAD
D_Status-A,neutral = M^-1 · a_neutral
```

This is deliberately labeled a model assumption.  It changes neither the
digitized 2383 characteristic curves nor their spectral dyes; it only replaces
the later per-record neutral shaper.

### Invariants

- original 12-bit ProRes RAW decode as extended-linear BT.2020 float32;
- Panasonic official colour conversion and `+0.45` stop exposure;
- 5279 H-D, three speed populations, morphology, DIR, dye/mask spectra and seed;
- full 5279 transmission, 3200 K printer lamp and 2383 record sensitivities;
- 2383 sensitometric and spectral dye curves, Callier term and xenon projection;
- final projected-gray correction, H-61 colour guard and monitor adaptation;
- period Spirit/Cineon/Blu-ray branch and all scan parameters.

### Neutral-density gate

The six probes were scene-neutral levels at `-3, -2, -1, 0, +1, +2` stops
around 18 percent.  They are controlled probes, **not claimed to be the H-61
patch exposures**.

| variant | shaped LAD (R/G/B) | LAD RMS error | mean / max normalized-AD channel span |
|---|---|---:|---:|
| V21 equal | 1.000 / 1.000 / 1.000 | 0.06481 D | 0.13866 / 0.29470 |
| Kodak aim + equal shaper | 1.060 / 1.060 / 1.060 | 0.02449 D | 0.14274 / 0.29823 |
| Kodak aim + analytical dye | 1.090 / 1.060 / 1.030 | 0.000000238 D | 0.000000121 / 0.000000476 |
| Kodak aim + no shaper | 1.090 / 1.060 / 1.030 | 0.000000344 D | 0.10362 / 0.20581 |

The analytical-dye candidate is internally consistent and demonstrably better
than an equal-density target in its specified coordinate system.  It is not an
independent validation because the same matrix defines both the candidate and
the error metric.

### Six-colour directional check

Relative to the unchanged provisional period-scan patch reference, mean
projection/scan OKLab error over red, green, blue, yellow, magenta and cyan was:

- V21: `0.032048`;
- official LAD + equal shaper: `0.031866`;
- official LAD + analytical dye: `0.031852`;
- official LAD + no shaper: `0.031686`.

Mean absolute hue error changed from `4.0399°` in V21 to `3.9598°` for the
analytical-dye candidate.  This tiny improvement is not a release-quality
measurement: the scan reference is itself provisional, and the unshaped model
scores slightly better despite its larger off-LAD analytical-dye error.

## Controlled RAW-frame A/B

Frame 12 was decoded from the original GH7 12-bit ProRes RAW and area-reduced
in linear light to 1440×1080.  Every variant used the same stochastic seed.

For the analytical-dye candidate versus V21:

- linear RGB MAE `0.00096414`, PSNR `56.16 dB`;
- OKLab delta-E median / P95 / P99
  `0.00181 / 0.02260 / 0.04997`;
- P95 absolute luminance delta `0.002177`;
- luminance P1 `0.00003097 -> 0.00001869` (about 40 percent lower);
- luminance P99 `0.843238 -> 0.843234`;
- values at or above 1.0: `0.0%`; at or below 0.0: `0.0%`;
- pixels changed after 8-bit sRGB review conversion: `81.14%`.

Manual review at normal size found the pair very similar overall.  The
amplified difference map located the larger high-percentile changes in dark
foliage, the background and colour edges.  The candidate produced a subtle
green/cyan redistribution and deeper low tail, not a stable correction that
could be attributed to 5279/2383 evidence.  Grain scale and highlight placement
remained coherent.  The no-shaper version changed more strongly and likewise
showed no stable advantage.

The scan/Blu-ray isolation render was bit-identical: linear MAE and maximum
absolute delta were `0.0`, and the baseline/candidate PNG SHA-256 values match.

## Reproducible artifacts

- `research_runs/2026-08-03_status_a_trajectory/run_ab.py`
- `research_runs/2026-08-03_status_a_trajectory/metrics.json`
- `baseline_v21_equal.png`
- `candidate_kodak_equal.png`
- `candidate_kodak_analytical_dye.png`
- `candidate_kodak_unshaped.png`
- corresponding A/B and `difference_x12` PNGs;
- scan-isolation baseline/candidate, A/B and difference PNGs.

All stills are 1440×1080 8-bit sRGB; A/B images are 2880×1080.  They are
research review artifacts, not release screenshots.

## Release decision

No production source, calibration baseline, formal master, release screenshot,
site source, Git commit, saved Sites version or deployment was changed.  V21
remains current.

The hypothesis is not disproved as a mathematical neutral model.  It is
**disproved as a release-ready improvement** because:

1. its strongest quantitative gate is self-referential;
2. no numeric off-LAD 5279/2383 target was found;
3. the provisional colour-patch advantage is tiny and non-unique;
4. the RAW-frame result deepens the low tail and redistributes dark colour
   without a stable visible correction.

## Next priority

Before revisiting the Status-A shaper, obtain an independent off-LAD target:
the original Pytlak LAD paper, a Kodak TAF/DLE step-series table, or measured
2383 neutral-scale Status-A/END data.  If that remains inaccessible, the next
highest-value falsifiable problem is the **later projected-gray calibration**:
test whether V21's equal-density `1.0 / 1.0 / 1.0` viewing anchor is inconsistent
with the official LAD vector and whether an analytical-dye or spectral neutral
anchor can replace it without double-neutralizing the print branch.
