# 2026-08-03 research run: 2383 LAD Status-A aim

## Outcome

The hypothesis was **partly confirmed at the density-calibration stage but did
not pass the release gate**.  V21 places an 18 percent negative at equal
`1.00/1.00/1.00` Status-A densities on 2383.  Kodak H-61B instead specifies
`1.09 red / 1.06 green / 1.03 blue` to obtain a visual neutral density of 1.0.
A controlled candidate hit those three raw print densities to within
`4.8e-7 D`, but V21's later gray-scale shaper reduced the candidate to equal
`1.06/1.06/1.06`, partially erasing the official channel-specific aim.

The candidate caused only a very small projection change, produced mixed
six-colour results, and had no stable visible advantage in the RAW-frame A/B.
No V22 was created.  V21 remains the current production baseline.

## Safety and prior-state audit

- No emulsion renderer, encoder, site build or deployment process was active at
  the start of the run.
- The source clip was present and unchanged: 2,007,616,000 bytes, 5760 x 4320,
  165 frames, 24000/1001 fps, 12-bit ProRes RAW HQ.
- V21 was the highest formal version.  Its projection and scan manifests and
  two 13-frame 12-bit ProRes 4444 masters were present.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`; its published content still
  identifies V21 as the baseline.
- The site repository has no persistent `origin` remote.  This was noted but
  was not a release blocker because the research gate failed before any build,
  commit or deployment was authorized.
- No file under `sources/` was changed.

## Falsifiable question

Does replacing V21's equal `1.00/1.00/1.00` 2383 Status-A LAD exposure aim
with Kodak's `1.09/1.06/1.03` aim improve the documented density constraint
while preserving neutral and six-colour behavior, projection/scan separation,
and visual consistency on the original GH7 RAW frame?

The release hypothesis required:

1. a primary Kodak source must specify the candidate densities for 2383;
2. the candidate must reduce error against that density aim without breaking
   the six-step-neutral principle;
3. the projection RAW-frame A/B must show a stable consistency advantage with
   no clipping, cast, coarse grain or scan-branch leakage.

## Sources and evidence boundaries

### New and rechecked primary sources

1. **Eastman Kodak, H-61B, _LAD for KODAK VISION Color Print Film_, page 1.**
   The LAD patch is a visual neutral density of 1.0, but the corresponding
   2383/3383 Status-A aim is `1.09 R / 1.06 G / 1.03 B`.  The same page says
   the six gray patches should appear neutral, that pink highlights and green
   shadows reveal contrast mismatch, and that a 0.025 log-exposure printer
   trim changes 2383 density by about 0.07.  Source:
   <https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf>.
2. **Eastman Kodak, H-387, _KODAK Digital LAD Test Image / Digital Recorder
   Calibration and Aims_, page 5.**  It independently gives suitable 2383
   Status-A print densities of `1.09/1.06/1.03` and distinguishes equal digital
   printing-density code values from Status-M densities and final Status-A
   print aims.  Source:
   <https://www.kodak.com/content/products-brochures/Film/Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf>.
3. **Eastman Kodak, EP1309188A2, _Method for calibrating a film scanner_,
   Figure 3 and the Integral Transmittance description.**  Printing density is
   computed separately for each colour from the wavelength-by-wavelength
   product of film spectral transmittance, printer-light SPD and the target
   print material's spectral sensitivity.  It explicitly warns that the same
   Status-M density can imply many printing densities depending on lamp house
   and print stock.  Source:
   <https://patents.google.com/patent/EP1309188A2/en>.
4. **Eastman Kodak, H-1-2383, revised March 2026, pages 2-5.**  Page 2 states
   that 2383 is balanced for colour negatives and that the red-, green- and
   blue-sensitive layers form cyan, magenta and yellow dyes.  Page 3 routes
   timing and curve placement to H-61 LAD control.  Pages 4-5 describe the
   characteristic, spectral-sensitivity and peak-normalized dye curves and
   warn that plotted values are representative production data rather than a
   specification for a particular roll.  Source:
   <https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf>.

### Fact, model assumption and unknown

- **Fact:** `1.09/1.06/1.03` Status-A, not three equal 1.00 densities, is
  Kodak's documented 2383 LAD aim for a visual neutral density of 1.0.
- **Fact:** printing density is a spectral integral tied to the negative,
  printer lamp and target print stock; it is not identical to Status-M.
- **Confirmed implementation fact:** V21 already computes the 5279-to-2383
  effective printer density using full negative transmission, a 3200 K printer
  lamp and the three 2383 spectral-sensitivity records.  The new inconsistency
  is the later print-exposure anchor, not the integral itself.
- **Model assumption:** V21's visually digitized 2383 curves, spectral
  sensitivities and dye curves approximate one representative coating and
  process.  They are not measurements of the original 2003 release-print lot.
- **Unknown:** the Status-A density trajectories corresponding to all six
  neutral patches, and the exact 5279 negative/2383 print target measured in a
  period laboratory.  H-61B supplies an exact LAD anchor and a visual
  neutrality requirement, not a complete three-channel density curve at every
  gray level.

## Controlled experiment

### Candidate and invariants

The production source was not edited.  A research-only monkeypatch changed the
three 2383 printer-light exposure aims from `1.00/1.00/1.00` to
`1.09/1.06/1.03`.  All of the following remained fixed:

- original 12-bit ProRes RAW decode and Panasonic colour transform;
- +0.45-stop virtual exposure;
- 5279 H-D curves, fast/medium/slow populations, DIR, morphology and seed;
- signed 5279 dye/mask spectra and full D-min spectrum;
- 3200 K printer lamp and 2383 spectral sensitivities/characteristic curves;
- gray-scale shapers, Callier correction, xenon projection, H-61 hue guard and
  monitor adaptation;
- Spirit/Cineon/Blu-ray branch and every scan parameter.

### Density gate

For the 18 percent neutral negative, V21's full spectral integration produced
effective 2383-record printer densities of
`1.08055 / 1.54538 / 1.55008 D`.  Applying the baseline and candidate printer
lights gave:

| metric | V21 baseline | Kodak-aim candidate |
|---|---:|---:|
| raw 2383 Status-A density | 1.00000 / 1.00000 / 1.00000 | 1.09000 / 1.06000 / 1.03000 |
| RMS error from H-61B aim | 0.06481 D | 0.00000034 D |
| after V21 gray shaper | 1.00000 / 1.00000 / 1.00000 | 1.06000 / 1.06000 / 1.06000 |
| post-shaper RMS error | 0.06481 D | 0.02449 D |

The official aim therefore fixes a real exposure-anchor error, but the current
shaper overwrites two-thirds of the channel-specific relationship.  Removing
or redesigning that shaper cannot be justified from the single LAD point
alone; doing so would invent the rest of the neutral scale.

### Neutral and six-colour gate

The finished neutral patch remained numerically neutral in both cases
(`RGB span 4.47e-8`) because the later projected-gray calibration explicitly
protects the neutral axis.  Relative to V21's provisional Spirit colour
reference, the mean six-colour OKLab difference changed only from `0.03205` to
`0.03187`, and mean absolute hue difference from `4.040°` to `3.961°`.

That small average is not a uniform improvement: green, yellow and magenta
moved closer, while red, blue and cyan moved farther away.  The reference is
also a modelled Spirit path, not a measured 5279/2383 TAF result.  The six-colour
gate is therefore mixed, not passed.

## Controlled RAW-frame A/B

Frame 12 was decoded from the original 12-bit ProRes RAW through AVFoundation
as extended-linear BT.2020 float32 and area-reduced in linear light to
1440 x 1080.  Baseline and candidate used the same stochastic seed.

- linear RGB MAE: `0.00068660`;
- PSNR: `58.53 dB`;
- OKLab delta E: median `0.00130`, P95 `0.00381`, P99 `0.01019`;
- absolute luma delta P95: `0.002178`;
- luma P1: `0.00003097 -> 0.00003237`;
- luma P99: `0.843238 -> 0.843232`;
- candidate values at or above 1.0: `0.0%`; at or below 0.0: `0.0%`;
- pixels changed after 8-bit sRGB review conversion: `65.50%`.

The changed-pixel percentage reflects tiny distributed record-balance changes.
Manual side-by-side review found the images effectively indistinguishable at
normal viewing size.  The amplified difference map shows content-dependent
edge and hue changes, but no stable correction of a visible cast.  Grain size,
black floor and highlight placement remain coherent.

The scan/Blu-ray branch was rendered before and after the candidate as an
isolation check.  Its linear MAE and maximum absolute delta were both exactly
`0.0`; its review PNG hashes are identical.  The print calibration therefore
did not leak into the scan branch.

Reproducible artifacts:

- `research_runs/2026-08-03_print_lad_status_a/run_ab.py`
- `research_runs/2026-08-03_print_lad_status_a/metrics.json`
- `research_runs/2026-08-03_print_lad_status_a/baseline_projection.png`
- `research_runs/2026-08-03_print_lad_status_a/candidate_projection.png`
- `research_runs/2026-08-03_print_lad_status_a/ab_projection.png`
- `research_runs/2026-08-03_print_lad_status_a/difference_x16_projection.png`
- corresponding baseline/candidate/A-B/difference scan-isolation PNGs.

## Technical validation

- The research script compiles and completes deterministically.
- Review stills are 1440 x 1080 8-bit sRGB PNGs; A/B stills are 2880 x 1080.
- No formal master was rendered because the visual and six-colour release gates
  failed.
- Existing V21 masters remain 5760 x 4320, 13 frames, 24000/1001 fps,
  12-bit `yuv444p12le` ProRes 4444 with Rec.709 1-1-1 signalling.
- Projection SHA-256 remains
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Scan/Blu-ray SHA-256 remains
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- No clipping increase, black-floor discontinuity, purple/blue global drift,
  coarse 8/16 mm-like grain or branch cross-contamination was observed.

## Conclusion and next priority

### Confirmed

- V21 uses the wrong per-channel Status-A LAD exposure anchor for 2383.
- The Kodak aim corrects that raw print-density anchor almost exactly.
- V21's spectral printing-density integration already follows the documented
  printer-lamp/target-stock method and should not be replaced by a
  channel-independent Status-M approximation.
- The scan branch remains physically and numerically independent.

### Not established

- The current gray shaper cannot simply be removed: H-61B requires six neutral
  patches, while only the central Status-A anchor is presently known exactly.
- The tiny mixed patch changes and visually indistinguishable RAW A/B do not
  establish a finished-image improvement.
- Charlie's Angels cannot resolve this calibration because its creative grade,
  DI, recorder/print and home-video transfer are not separable measurements.

### Release decision

No production algorithm, calibration baseline, formal output, release
screenshot, site source, Git commit, saved Sites version or deployment was
changed.  V21 remains current; the private site remains production version 2 at
<https://emulsion-5279.skylab.chatgpt.site>.

The next highest-priority falsifiable problem is to derive a **bounded neutral
Status-A trajectory** that preserves the official `1.09/1.06/1.03` LAD anchor
and H-61B's six-neutral-patch requirement without inventing fixed density
offsets.  The first test should compare (a) V21's equal-density shaper, (b) a
spectrally derived equivalent-neutral-density mapping constrained at LAD, and
(c) no additional shaper, using neutral-scale error, six-colour patches and a
RAW-frame A/B.  No production change should be made without a measured or
otherwise independently defensible off-LAD target.
