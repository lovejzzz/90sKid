# ECN-2 process-control limits are not 5279 interimage uncertainty bounds

- Note ID: `20260803T235532Z_ecn2_control_limits_not_interimage_uncertainty`
- Research time: 2026-08-03T23:55:32Z
- Access date for web sources: 2026-08-03
- Scope: research and evidence organization only
- Result type: negative result with a newly established measurement boundary

## Research question

Can Kodak H-24 ECN-2 process-control tolerances be used as numerical uncertainty
bounds for a future Kodak VISION 500T 5279 neutral-versus-single-colour
separation experiment, or do they measure a different object?

## Why this remained unresolved

The preceding note established that a green-only exposure can be a causal
exclusion control, but the available Kodak example reported only speed changes,
not full three-channel density curves or repeat uncertainty. The next required
piece was therefore an ECN-2 uncertainty model. Kodak H-24 publishes numerical
action and control limits, so it was necessary to determine whether those limits
could legitimately supply the missing error bars.

This is narrower than asking for the magnitude of 5279 interimage itself. It
asks only what H-24's numerical tolerances mean and whether they can be
transferred to that measurement.

## Search method and keywords

Sources searched were Kodak's official H-24 processing-manual collection,
individual H-24 Modules 1 and 8, and Kodak-assigned patent literature found with
queries combining:

- `ECN-2 process control tolerance D-min LD MD HD`
- `ECN-2 full characteristic curve control strip repeatability`
- `ECN-2 separation exposure interimage neutral exposure`
- `Kodak patent Gsep Gneut ECN-2`
- `motion picture color negative interimage gamma separation neutral`

The acceptance test for a positive result was strict: a source had to publish
neutral and single-colour separation data, all relevant density channels across
exposure, and replicate or statistical uncertainty under ECN-2. A laboratory
alarm band, a qualitative trend chart, one density difference, or an ECN-2
applicability assertion without the underlying ECN-2 data did not qualify.

No attachment was downloaded. Both Kodak manuals are available at stable public
Kodak URLs and the patent record is publicly accessible; retaining another full
copy was unnecessary for this note.

## Sources

### S1 — Kodak H-24 Module 1

- Eastman Kodak Company, *Processing KODAK Motion Picture Films, Module 1:
  Process Control*, publication H-24.01, copyright 1999.
- Official PDF:
  <https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-1.pdf>
- Relevant pages: title page; 1-6 to 1-7; 1-10; 1-14 to 1-16; Table 1-5;
  Figure 1-8.
- Full text and page numbering were accessible.

### S2 — Kodak H-24 Module 8

- Eastman Kodak Company, *Processing KODAK Motion Picture Films, Module 8:
  Effects of Mechanical & Chemical Variations in Process ECN-2*, copyright
  2011.
- Official PDF:
  <https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-8.pdf>
- Relevant pages: title page; 8-5 to 8-6.
- Full text and page numbering were accessible.

### S3 — Kodak patent example and its ECN-2 applicability statement

- Eastman Kodak Company, EP 1 016 912 A2, *Photographic recording material for
  accelerated development*, published 2000-07-05.
- Public patent record:
  <https://patents.google.com/patent/EP1016912A2/en>
- Relevant paragraphs in the Google Patents text: `Processing and Measurements`
  under Example 1, especially the definitions of `Gsep-Gneut`, followed by the
  statement that similar findings result with ECN-2. In the accessible text
  these appear around lines 933-942; the publication does not expose numbered
  patent paragraphs for this passage.
- This is a worked multilayer patent example, not a 5279 product disclosure.

## Evidence ledger

### Direct facts

#### F1 — The ECN-2 control strip is a 21-step gray-scale process monitor

S1, pages 1-6 to 1-7, says process-control strips are exposed with a consistent
light source through an unchanging standard attenuator. ECN-2 strips contain 21
gray-scale positions: 20 exposed steps at 0.20 log H intervals plus minimum
density. A reference strip from the same batch is processed under specified,
well-controlled conditions.

This is a stepped gray-scale comparison against a batch reference. It is not a
published set of red-only, green-only, and blue-only separation wedges.

#### F2 — Routine ECN-2 limits monitor selected points, not an interimage curve

S1, pages 1-10 and 1-14, defines routine ECN-2 readings at D-min, LD, MD, HD,
and the HD-minus-LD contrast parameter, using Status-M densitometry. Table 1-5
gives the following recommended density departures from the laboratory aim:

| quantity | action limit | control limit |
|---|---:|---:|
| D-min | +0.03 D | +0.05 D |
| LD | +/-0.03 D | +/-0.05 D |
| MD | +/-0.05 D | +/-0.07 D |
| HD | +/-0.06 D | +/-0.08 D |
| HD - LD | +/-0.05 D | +/-0.07 D |

The same table separately gives colour-balance spread limits. These numbers are
operational deviations from an aim value at selected control-strip points; the
table does not define uncertainty for a difference between neutral and
single-colour separation curves.

#### F3 — Kodak explicitly does not define those limits as universal error bars

S1, page 1-14, says precise limits for a laboratory depend on statistical
considerations, customer quality requirements, and reasonable cost. It calls
the recommended limits arbitrary and says they can change with anticipated
trends or experience. The same page attributes unavoidable plotted variation to
the combined process and control system, including strips and densitometry.

Therefore the published bands combine several operational sources of variation.
They are not presented as a standard deviation, confidence interval, repeatability
coefficient, or instrument-only uncertainty.

#### F4 — H-24 permits full gray-scale curve comparison but still does not
isolate interimage

S1, pages 1-15 to 1-16, recommends periodically plotting all 11 or 21 control
steps against the corrected reference curve. Kodak says the full plot gives a
truer view of speed, density, colour balance, and contrast than the four routine
points.

This establishes that H-24 can monitor a full characteristic curve. It does not
turn the gray-scale exposure into a set of colour separations: the other records
are still simultaneously active, so the comparison cannot isolate causer-to-
receiver interimage terms.

#### F5 — The later H-24 ECN-2 examples are not 5279 measurements

S2, pages 8-5 to 8-6, identifies the supplied camera-negative ECN-2 control
strip as KODAK VISION3 200T 5213 with 21 gray-scale steps. Its mechanical and
chemical variation plots cover 5213, intermediate films 5254 and 5242. Kodak
explicitly says those plots are qualitative rather than quantitative, are not
process-control limits, and are only representative trend guides from small
laboratory machines.

Thus neither the stock identity nor the declared evidentiary use supports
transferring these plots to 5279 interimage uncertainty.

#### F6 — A nearby patent lead still supplies only a single C-41 difference

S3's Example 1 defines a green-separation exposure using 5500 K light plus a
WRATTEN 99 filter. It evaluates `Gsep-Gneut` at one position, 1.5 log E from a
speed point. The actual example samples were developed in the cited C-41
process. The patent then states that similar findings result when such films are
processed in ECN-2.

The publication does not provide the underlying ECN-2 curve, ECN-2 replicate
count, uncertainty, or a 5279 sample. The applicability statement therefore
cannot be promoted into numerical 5279/ECN-2 evidence.

### Bounded inferences

#### I1 — H-24 control data are useful as a drift gate, not as the error model

Reasoning chain:

1. H-24 control strips quantify whether a lab process stays near a batch-adjusted
   process aim.
2. Their limits combine film-batch, exposure, processing, densitometer, quality,
   and economic considerations.
3. A neutral-minus-separation interimage measurement is a different statistic
   and contains paired-exposure and paired-density covariance absent from the
   H-24 table.
4. Therefore H-24 data could accept, reject, or stratify a future ECN-2 run for
   process drift, but the experiment must estimate its own uncertainty from
   repeated 5279 wedges.

Boundary: this inference concerns measurement design. It does not say that an
in-control ECN-2 process is irrelevant, nor that its variability is zero.

#### I2 — A full neutral control curve cannot identify off-diagonal coupling

At each exposure, a neutral wedge activates multiple colour records together.
Even if all 21 red, green, and blue Status-M readings are retained, they reveal
only the combined neutral response. Without independent colour-separation
exposures, multiple causer-to-receiver coupling patterns can produce the same
neutral curves.

Boundary: this is an identifiability statement, not a claim that the neutral
curve contains no interimage effect.

### Candidate model hypothesis for a future experiment

Treat contemporaneous H-24 control-strip departures as nuisance covariates and
run-validity gates, not as priors for a fixed 5279 DIR/interimage matrix. Estimate
the neutral-minus-separation response and its covariance only from randomized,
paired, repeated 5279 wedges processed in the same ECN-2 runs.

This is a candidate protocol, not an algorithm change and not a conclusion that
5279 follows any H-24 example stock.

### Still unknown

- No searched source supplied full 5279 neutral and red/green/blue separation
  density curves under ECN-2.
- No searched source supplied replicate uncertainty or covariance for such a
  5279 experiment.
- The exact exposure spectrum of historical 5279 control strips and their
  batch-specific aim sheets was not found.
- The magnitude, sign, exposure dependence, spatial scale, layer dependence,
  and ECN-2 process sensitivity of 5279 interimage remain unknown.
- Whether unpublished Kodak or laboratory archives retain separation wedges for
  5279 remains unknown.

## What was supported, rejected, and left unchanged

### Supported

- H-24 is an appropriate way to monitor whether an ECN-2 laboratory process is
  stable enough to interpret a separate sensitometric experiment.
- Full 21-step control-strip curves are more informative about process drift
  than only D-min/LD/MD/HD.

### Rejected

- Using H-24 Table 1-5's +/-0.03 to +/-0.08 D action/control bands as 5279
  interimage error bars.
- Treating the H-24 Module 8 trend plots as quantitative 5279 response data.
- Treating S3's unreported “similar” ECN-2 result as though it were a published
  ECN-2 curve or a 5279 measurement.

### Existing conclusion that should not change

The prior conclusion remains intact: a separation exposure can be a useful
causal control, but no numerical 5279 cross-record coefficient is identified by
the public evidence found so far.

## Potential relationship to the existing model

Any existing fixed 3-by-3 coupling matrix or population-dependent transport
term remains a bounded modeling assumption. H-24 tolerances cannot calibrate its
coefficients, provide confidence intervals, or validate its exposure dependence.
At most, H-24 supplies a future laboratory quality-control layer around the
measurement used to fit or falsify such a model.

No current model parameter should change because of this note.

## Falsifiable future experiment design — not executed

1. Cut 5279 from one documented roll and prepare matched neutral, red-only,
   green-only, and blue-only 21-step wedges with recorded source spectra and
   0.20 log H spacing.
2. Randomize wedge order and process at least five matched sets in each of at
   least three independent ECN-2 runs. These counts are a proposed starting
   design, not a Kodak requirement.
3. Run the laboratory's appropriate Kodak control strip before, during, and
   after each batch; retain all 21 Status-M readings plus chemistry, temperature,
   time, replenishment, and densitometer check-plaque records.
4. Predefine a run-rejection or stratification rule from that laboratory's H-24
   process-control practice. Do not substitute the generic Table 1-5 bands for
   the replicate covariance of the 5279 wedges.
5. Read R/G/B Status-M densities for every wedge step without moving the strip
   between channel reads. Estimate paired neutral-minus-separation curves and a
   full covariance across exposure, receiver channel, run, and strip.
6. Hold out one complete ECN-2 run. A candidate coupling model must predict all
   held-out receiver-channel curves within their predeclared intervals and must
   outperform a diagonal/no-cross-record alternative.

## Denial conditions

The present negative conclusion is falsified if any of the following is found:

- a Kodak or laboratory primary record publishes 5279 neutral and colour-
  separation ECN-2 curves with replicate uncertainty;
- an H-24 companion document explicitly defines a published tolerance as a
  statistical interval for the paired neutral-minus-separation statistic; or
- repeated 5279 testing demonstrates that a predeclared transform from H-24
  control-strip residuals predicts interimage measurement covariance on held-out
  ECN-2 runs.

Conversely, a proposed 5279 coupling model is denied if it cannot predict the
sign and magnitude of held-out receiver-channel changes across exposure, or if
its apparent effect disappears after accounting for run and densitometer drift.

## Next highest priority

Search laboratory and Kodak archive records for historical 5279 control-strip
instruction sheets, sensitometric test reports, or colour-separation wedge plots
that retain all three Status-M readings. Prioritize accession-level finding aids,
SMPTE supplementary figures, and Kodak technical-paper appendices; do not spend
another run on generic H-24 control limits or a patent that reports only one
`Gsep-Gneut` point.

## Safety and modification audit

- No algorithm, renderer, RAW decoder, ffmpeg process, A/B test, version,
  manifest, output, screenshot, calibration baseline, site, Git commit/push, or
  deployment was created or changed.
- `sources/` was not modified.
- No research attachment was downloaded.
- The only project changes from this run are this new note and its one-line
  `research_notes/INDEX.md` entry.
