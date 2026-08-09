# 2026-08-03 research run: period Spirit observer identifiability

## Outcome

The hypothesis was **not sufficiently supported for release**, so V21 remains
the baseline and no V22 was created.  A bounded spectral sweep found a narrower
diagnostic observer that fits an internally generated six-colour separation
target better than V21's provisional Gaussian observer.  However, neither DFT
nor Kodak publishes the Spirit 2K detector response, and the target is derived
from the model's own digitized 5279 spectra rather than a measured Spirit scan.
The candidate therefore demonstrates parameter sensitivity, not historical
identification or visual superiority.

## Safety and prior-state audit

- No emulsion renderer, research script, encoder, site build or deployment was
  writing in `experiments/emulsion_reconstruction` at the start of the run.
- The raw source was present: one 2,007,616,000-byte, 5760 x 4320, 165-frame,
  24000/1001 fps, 12-bit ProRes RAW HQ clip.
- The site subrepository was clean on `main` at
  `c670ea28f47df555ed12fb63519af418ff2c185d`; its last commit remains
  `Publish V21 emulsion reconstruction`.
- V21's projection and scan manifests were intact.  The preceding shoulder run
  had completed and explicitly selected the Spirit observer as this run's next
  priority.
- No file under the synced project `sources/` tree was changed.

## Falsifiable question

Can V21's provisional broad period-telecine observer be replaced by one bounded
spectral-response family that measurably improves six-colour separations and
neutral-density behavior, without changing RAW interpretation, negative
formation, the physical 2383 branch or the finishing chain?

The release hypothesis required all three of the following:

1. primary documentation must bound the candidate as a plausible Spirit/period
   telecine response;
2. a held-out calibration wedge must improve after the documented stock-specific
   masking operation; and
3. a RAW-frame A/B must improve visual consistency without a global cast or
   branch leakage.

## Sources and evidence boundaries

### New primary source

1. **Eastman Kodak, EP1309188A2, _Method for calibrating a film scanner_.**
   Paragraphs corresponding to the detailed description around lines 221-230
   define integral density as the wavelength-by-wavelength product of film
   transmittance, light-source SPD and detector sensitivity.  The calibration
   procedure around lines 250-269 specifies a stock-specific 3 x 3 masking
   matrix to correct dye crosstalk, plus black/white matching, lift, gamma,
   gain, LUTs and offsets, and says that a separate setup can be stored for each
   film type.  Source:
   <https://patents.google.com/patent/EP1309188A2/en>.

### Previously used primary sources, rechecked for this question

2. **DFT, _Spirit 2K Product Data Sheet_, pages 2-5.** Page 2 lists an
   Eastman-Kodak-designed imaging subsystem, diffuse high-power xenon, optical
   film matching, logarithmic masking, RGB negative matching and RGB primary
   correction.  Page 3 describes a broad continuous 700 W xenon spectrum with
   extra blue energy, an integration cylinder, RGB beam splitter and 2K RGB CCD
   line array.  Page 5 states that the three colour paths each use a 2048-pixel
   CCD and produce 10-bit processed output.  It publishes no CCD/dichroic
   spectral response curves.  Source:
   <https://www.dft-film.com/downloads/datasheets/DFT-Spirit-2K-datasheet-11-09.pdf>.
3. **Eastman Kodak, US5500316A, _Color negative film with contrast adjusted for
   electronic scanning_, Figure 1 and detailed description.** Figure 1 plots a
   typical telecine's broad RGB spectral responses; visual readings place the
   peaks near 620/540/470 nm.  The text explains red-channel magenta crosstalk,
   electronic gain and the benefit of bringing the pre-channel-correction
   red/green contrast ratio to at least 0.96.  It is a typical telecine, not a
   Spirit 2K disclosure and not a 5279 coating measurement.  Source:
   <https://patents.google.com/patent/US5500316A/en>.

### Fact, model assumption and unknown

- **Fact:** Spirit 2K uses broad-spectrum xenon, an RGB beam splitter, separate
  2048-pixel CCD paths, stock-dependent optical/electronic matching and a
  16-bit internal RGB path before 10-bit output.
- **Fact:** period telecine calibration can include a stock-specific 3 x 3
  crosstalk/masking matrix and additional one-dimensional and LUT controls.
- **Model assumption:** V21's 620/540/470 nm centres and 52/44/38 nm Gaussian
  sigmas are a compact family consistent with Kodak's generic telecine plot.
  They are not disclosed Spirit sensitivities.
- **Unknown:** the Spirit lamp-after-filter SPD, dichroic curves, CCD quantum
  efficiency, factory film-match filters/matrices and the exact 5279 setup.
- **Unknown:** a measured 5279 separation/gray target scanned on the intended
  Spirit configuration.  Without it, a model-generated target cannot identify
  the real observer.

## Controlled spectral-family experiment

### Design

The test held the digitized 5279 net dye/mask spectra fixed and swept 81 broad
Gaussian observer families:

- centres: each of 620/540/470 nm independently shifted by -10, 0 or +10 nm;
- widths: V21's 52/44/38 nm sigmas multiplied by 0.8, 1.0 or 1.2;
- calibration: a through-origin 3 x 3 masking matrix fitted on cyan, magenta,
  yellow, red, green, blue and neutral directions at five density levels;
- validation: the same seven directions at five disjoint density levels;
- invariant stages: Status-M curve fitting, negative D-min, dye spectra,
  development-domain DIR, grain, Cineon mapping and display finishing.

This calibration intentionally tests the matrix operation documented by Kodak.
It does not model all of the Spirit's additional logarithmic masking, RGB
negative matching, LUT and grading controls.

### Sweep result

| metric | V21 provisional family | lowest synthetic holdout error | full 81-family range |
|---|---:|---:|---:|
| centres R/G/B (nm) | 620 / 540 / 470 | 630 / 550 / 460 | 610-630 / 530-550 / 460-480 |
| sigmas R/G/B (nm) | 52 / 44 / 38 | 41.6 / 35.2 / 30.4 | 0.8-1.2 x V21 |
| held-out RMS density error | 0.15785 D | 0.10753 D | 0.10753-0.18414 D |
| held-out maximum error | 0.64062 D | 0.45129 D | 0.44672-0.75036 D |
| neutral maximum error | 0.33014 D | 0.23057 D | 0.20762-0.43773 D |
| masking-matrix largest singular value | 4.222 | 2.820 | 2.784-7.439 |

The lower-error family sits on three search boundaries: red and green centres
move to their highest tested values, blue to its lowest, and every band narrows
to the minimum tested width.  This is evidence that V21's result is sensitive
to the provisional observer.  It is not evidence that the boundary values are
the Spirit response; extending the unconstrained sweep would simply optimize a
self-generated target.

Reproducible artifacts:

- `research_runs/2026-08-03_spirit_observer/run_observer_sweep.py`
- `research_runs/2026-08-03_spirit_observer/observer_sweep.csv`
- `research_runs/2026-08-03_spirit_observer/observer_sweep_metrics.json`

## Controlled RAW-frame A/B

Frame 12 was decoded from the original 12-bit ProRes RAW through AVFoundation
as extended-linear BT.2020 float32 and area-reduced in linear light to
1440 x 1080.  The A/B changed only the period-telecine spectral family from the
V21 values to the lowest synthetic holdout-error family.  Panasonic colour
conversion, +0.45-stop virtual exposure, random seed, nine-population dye-cloud
formation, DIR, scanner aperture, 10-bit Cineon encoding, Blu-ray finish and all
grain parameters remained identical.

- linear RGB MAE: `0.00080344`;
- PSNR: `57.42 dB`;
- OKLab delta E: median `0.00204`, P95 `0.00531`, P99 `0.00650`;
- absolute luma delta P95: `0.003268`;
- luma P1: `0.00006653 -> 0.00006819`;
- median OKLab shift: `a=-0.00086`, `b=+0.00094`;
- changed after 8-bit sRGB still conversion: `67.92%` of pixels.

The changed-pixel percentage is dominated by small distributed colour changes.
Side-by-side review is close, but the difference map and neutral surfaces show
a coherent green/yellow tendency.  There is no measured Spirit or 5279 target
showing that this direction is more correct, and the finished-feature reference
cannot answer it because its creative grade, DI transforms and Blu-ray master
are inseparable from the stock/scanner response.

Artifacts:

- `research_runs/2026-08-03_spirit_observer/baseline_scan.png`
- `research_runs/2026-08-03_spirit_observer/candidate_scan.png`
- `research_runs/2026-08-03_spirit_observer/ab_scan.png`
- `research_runs/2026-08-03_spirit_observer/difference_x16_scan.png`

The 5279-transmission-to-printer-lamp/2383-record calculation was also sampled
before and after the scanner observer substitution; its maximum density delta
was exactly `0.0`.  This confirms that the physical optical-print integration
is independent.  V21's later, explicitly provisional H-61 hue trim still uses
a Spirit reference, so any future production scanner change must revalidate
that trim or replace it with a measured 5279-to-2383 target.

## Technical validation

- The research script compiles and completes deterministically.
- Baseline and candidate images are 1440 x 1080 8-bit sRGB review PNGs; the
  A/B is 2880 x 1080.  No formal master was rendered because the release gate
  failed.
- Existing projection and scan masters remain 5760 x 4320, 13 frames,
  24000/1001 fps, 12-bit `yuv444p12le` ProRes 4444 with Rec.709 1-1-1
  signalling.
- Projection master SHA-256 remains
  `1782586f32b9d461a022827ab5de13f6cb2edc80fe43f6f12ccbe884492053ed`.
- Scan/Blu-ray master SHA-256 remains
  `86dcc8bc39d8a7ef86ee1d2151f68e18c1612296622860390af6ef68a90c8ac4`.
- Manual review found no clipping, black-floor jump, coarse 8/16 mm-like grain
  or projection/scan data leakage.  The diagnostic candidate's visible concern
  is the coherent green/yellow shift, not an encoding defect.

## Conclusion: useful sensitivity result / no release

### Confirmed

- Status-M, a raw telecine observer and a calibrated Spirit output are three
  different objects; the stock-specific masking and matching stage cannot be
  omitted when judging an observer.
- V21's current period-observer widths and exact centres are underconstrained
  empirical parameters, not official Spirit facts.
- A bounded change can materially reduce an internally defined separation
  error while leaving the physical 2383 integration exactly unchanged.

### Not established

- The lowest-error family is not identified as the real Spirit response.
- Its lower model error does not prove better 5279 colour because the target is
  generated from the same approximate dye spectra used by the model.
- The RAW-frame shift has no stable visual-consistency advantage; its slight
  green/yellow direction is at least as plausibly parameter drift.

### Release decision and next priority

No production algorithm, calibration baseline, formal output master, release
screenshot, site source, Git commit, saved Sites version or production
deployment was changed.  V21 remains current and the private site remains on
production version 2 at <https://emulsion-5279.skylab.chatgpt.site>.

The next highest-priority falsifiable question follows directly from the new
calibration patent: compare V21's present aim of partially recovering
channel-independent negative record densities with Kodak's documented
**printing-density aim** computed from spectral film transmission, printer-lamp
SPD and 2383 record sensitivities.  A controlled wedge must test whether that
aim reduces the large nonlinear masking residual while keeping the scan
encoding and physical projection observer distinct.  It must not be released
without RAW-frame evidence and a neutral/six-colour improvement.
