# Multiple-aperture RMS still does not nonparametrically identify 5279's NPS

- Note ID: `20260804T005816Z_48um_rms_does_not_identify_nps`
- Research time: 2026-08-04T00:58:16Z
- Access date for web sources: 2026-08-03/04 (America/New_York / UTC boundary)
- Scope: research and evidence organization only
- Result type: refinement of an existing boundary with a stricter minimum-evidence design

## Research question

The V24 research-run README already states correctly that Kodak VISION 500T
5279's single 48-micrometre RMS observation is not a complete noise-power
spectrum. Would adding RMS measurements at a finite set of other aperture sizes
be enough to recover the spectrum uniquely without a morphology prior, or is a
frequency-resolved scan still required?

## Why this remained unresolved

`research_runs/2026-08-03_v24_35mm_separation/README.md`, lines 12-17, had
already established the qualitative boundary: a single-aperture RMS is an
amplitude constraint rather than a complete Wiener/noise-power spectrum. The
existing calibration also says measured noise-power spectra are still required.

What remained insufficiently evidenced was the next measurement-design step.
The V24 README did not establish whether a small multi-aperture series could by
itself identify the spectrum, how the aperture response enters the observation,
or which primary method treats granularity transfer in frequency space.

This note does not claim the single-aperture boundary as a new discovery. It
tests only the stricter question above and does not estimate a 5279 noise
spectrum or choose new morphology parameters.

## Search method and keywords

The local 5279 sheet and Kodak filmmaker guide were checked page by page,
including visual inspection of the relevant graph pages. External searches then
targeted the measurement standard and primary photographic-science literature:

- `5279 48 micrometer aperture diffuse rms granularity`
- `photographic rms granularity aperture Wiener spectrum`
- `ISO 10505 noise power spectrum excluded`
- `Kodak Research Laboratories rms granularity aperture`
- `photographic granularity power spectrum scanning aperture response`

The positive-identification criterion was strict: a source had to provide either
a 5279-specific Wiener/noise-power spectrum, a spatial autocorrelation function,
or a demonstrated unique inversion from a finite multi-aperture series without
an assumed spectrum family. A single RMS value, several unvalidated aperture
integrals, or an MTF curve did not qualify.

No attachment was downloaded. Stable local copies of the Kodak publications
already exist, and the remaining sources have stable publisher or DOI pages.

## Sources

### S1 - Kodak 5279 technical data

- Eastman Kodak Company, *KODAK VISION 500T Color Negative Film / 5279,
  7279*, H-1-5279t, revised March 2003.
- Local PDF: `experiments/emulsion_reconstruction/references/kodak_5279_H-1-5279t.pdf`
- Relevant PDF pages: 3-4; MTF graph `F002_0267AC`; diffuse RMS granularity
  graph `F002_0269AC`; footnote 4.
- Full relevant pages and graph labels were accessible and visually inspected.

### S2 - Kodak's general motion-picture image-structure explanation

- Eastman Kodak Company, *The Essential Reference Guide for Filmmakers*,
  2007 PDF edition.
- Official PDF: <https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf>
- Local PDF: `experiments/emulsion_reconstruction/references/kodak_essential_reference_guide.pdf`
- Relevant PDF pages 55-57 (printed pages 54-56), especially "Graininess and
  Granularity", "Diffuse rms Granularity", and "Sharpness and
  Modulation-Transfer Curve".
- Full relevant text was accessible; the 5279 product itself is not measured in
  this general guide.

### S3 - ISO RMS-granularity method scope

- ISO 10505:2009, *Photography - Root mean square granularity of photographic
  films - Method of measurement*, ISO/TC 42, published May 2009; confirmed
  current in 2025 according to the official ISO catalog.
- Official catalog entry:
  <https://www.iso.org/cms/live/live/en/sites/isoorg/contents/data/standard/05/07/50747.html>
- Relevant locator: official abstract/scope; the catalog states explicitly that
  estimation of the noise-power (Wiener) spectrum is not covered.
- The complete 24-page standard was not obtained in this run. No clause number
  beyond the public scope is claimed.

### S4 - Kodak Research Laboratories on RMS aperture dependence

- J. H. Altman, "The Measurement of rms Granularity," *Applied Optics* 3(1),
  35-38 (1964), DOI: <https://doi.org/10.1364/AO.3.000035>.
- Publisher page:
  <https://opg.optica.org/ao/abstract.cfm?uri=ao-3-1-35>
- Relevant locator: publisher abstract. It states that the measured value
  depends on the scanner optical aperture and discusses conversion to a diffuse
  basis.
- Only the abstract was accessible without subscription; equations and figure
  details were not used.

### S5 - Primary power-spectrum measurement method

- Shingo Ooue, "Graininess and Granularity of Photographic Materials (I):
  Measurement of Power Spectrum," *Oyo Buturi* 29(3), 169-175 (1960), Fuji
  Photo Film Research Laboratory, DOI:
  <https://doi.org/10.11470/oubutsu1932.29.169>.
- Full-text record:
  <https://www.jstage.jst.go.jp/article/oubutsu1932/29/3/29_3_169/_article/-char/en>
- Relevant pages: 169-171; English abstract; equation (5) and surrounding
  definitions on printed page 171.
- The paper studies uniformly exposed black-and-white Fuji materials, not 5279.
  It is used only for the measurement relationship between a scanning aperture,
  a one-dimensional scan spectrum, and a two-dimensional Wiener spectrum.

### S6 - Kodak Research Laboratories on granularity transfer

- Edward C. Doerner, "Wiener-Spectrum Analysis of Photographic Granularity,"
  *Journal of the Optical Society of America* 52(6), 669-672 (1962), DOI:
  <https://doi.org/10.1364/JOSA.52.000669>.
- Publisher page:
  <https://opg.optica.org/josa/abstract.cfm?uri=josa-52-6-669>
- Relevant locator: publisher abstract. It identifies the Wiener spectrum of
  density fluctuations as the appropriate description for linear transfer of a
  negative's granularity through printing.
- Only the abstract was accessible without subscription; no unavailable formula
  or result is asserted.

## Evidence ledger

### Direct facts

#### F1 - The stock-specific observation is a fixed-aperture standard deviation

S1, PDF page 3, says the red, green, and blue readings use a microdensitometer
with a 48-micrometre aperture. Page 4 plots `Granularity Sigma D` against the
same exposure axis as the characteristic curves and instructs the reader to
multiply the plotted value by 1000. It also says the granularity curve uses
"modified measuring techniques."

The sheet does not publish a scan trace, sampling pitch, two-dimensional
autocorrelation, Wiener spectrum, radial frequency bins, or measurement
repeatability. The MTF graph on page 3 is a separate deterministic response
measurement, not a noise spectrum.

#### F2 - Kodak defines RMS granularity as aperture-scale density variation

S2, PDF page 56 (printed page 55), distinguishes subjective graininess from
objective granularity. It describes a microdensitometer with a small aperture,
usually 48 micrometres, and defines RMS granularity as the standard deviation of
density readings from the average, reported after multiplication by 1000.

The same pages say processed colour-film graininess results from dye formation
where silver-halide particles existed. That mechanism does not supply the
missing 5279 spatial covariance or cloud-size distribution.

#### F3 - The RMS standard explicitly excludes spectrum estimation

S3's official scope covers intrinsic density fluctuations from developed image-
forming centres in continuous-tone monochrome and colour films. It explicitly
lists estimation of the noise-power/Wiener spectrum among measurements not
covered by ISO 10505:2009.

Thus conformance to an RMS-granularity method is not, by the standard's own
scope, a Wiener-spectrum measurement.

#### F4 - RMS depends on the measurement aperture

S4's publisher abstract reports the Kodak Research Laboratories procedure and
states directly that measured RMS granularity depends on the optical aperture
of the scanner. Therefore the 48 um diameter is part of the observation, not an
incidental unit that can be discarded after reading the value.

#### F5 - Spectrum recovery requires frequency-resolved information and an
aperture response

S5, printed pages 169-171, describes a scanning microphotometer plus frequency
analyser. Its equation (5) relates the measured one-dimensional spectrum to the
two-dimensional power spectrum through the squared response of the scanning
aperture. The authors then require additional assumptions and a fitted
multi-component approximation to recover a two-dimensional spectrum.

This is direct evidence about the measurement problem, not about 5279's actual
spectrum. It shows that even a frequency-resolved line scan must account for the
aperture response; one scalar RMS contains still less information.

#### F6 - Granularity transfer is frequency dependent

S6's publisher abstract says the printed-through granularity of a negative is
best analysed with the Wiener spectrum of density fluctuations and presents a
linear transfer treatment through printing. It does not assert that a single RMS
number is sufficient for that transfer.

### Bounded inferences

#### I1 - Each aperture RMS is one weighted total, not a frequency bin

Reasoning chain:

1. RMS granularity is the standard deviation of aperture-averaged density.
2. The aperture has its own spatial response (F4-F5).
3. Spatial variance after each aperture combines contributions from all passed
   frequencies into one scalar.
4. Different non-negative spectra can have the same aperture-weighted total.
5. A finite set of aperture sizes supplies a finite set of such weighted totals,
   not independent values at every spatial frequency.
6. Therefore a finite multi-aperture RMS series does not uniquely recover an
   arbitrary continuous spectrum unless a spectrum family, smoothness rule, or
   other prior is imposed.

In frequency-domain notation, the observable is of the form
`sigma_A^2 = integral N(f) |A(f)|^2 df`, where `A` is the measurement-aperture
response and `N` is the density-noise spectrum. This notation summarizes the
measurement relationship supported by S5; it is not a quoted 5279 formula.

Boundary: every aperture RMS is still a useful constraint on weighted variance.
With an explicitly predeclared low-dimensional spectrum family, enough
well-separated apertures may identify that family's parameters. That is
parametric identification, not a nonparametric recovery of Kodak's spectrum.

#### I2 - Matching both RMS and MTF still does not identify grain morphology

Reasoning chain:

1. S1 publishes MTF and RMS as separate image-structure measurements.
2. MTF describes deterministic contrast transfer of an input pattern; RMS
   describes stochastic density variation after a fixed aperture.
3. Neither supplies the missing stochastic phase, covariance, or spectrum.
4. Several random fields can therefore share the same MTF and 48 um RMS while
   differing visibly in clump size, high-frequency roll-off, and correlation.

Boundary: a future physical model should satisfy both measurements, but doing so
does not prove its fast/medium/slow sizes or cloud radii are Kodak's formula.

#### I3 - A 48 um match cannot validate a 2K scan or 2383 print grain transfer

S6 establishes that granularity transfer through another imaging stage is
frequency dependent. Since S1 does not publish 5279's input spectrum, the
variance surviving a scanner aperture, printer MTF, or projection chain is not
uniquely predicted by the 48 um scalar alone.

Boundary: this does not deny existing restrained scanner/print observers; it
only says their visible texture cannot be claimed as stock-identified from the
published RMS curve.

### Model candidate hypotheses for future testing

1. **Multi-aperture rejection hypothesis:** at each selected exposure and
   record, RMS measured with several calibrated circular apertures can reject
   many candidate spectra that all match the 48 um point, even though it cannot
   uniquely recover an arbitrary spectrum.
2. **Direct-spectrum hypothesis:** a low-dimensional, non-negative spectrum
   family constrained jointly by multi-aperture RMS and direct frequency-resolved
   scans will predict held-out aperture sizes better than a morphology family
   calibrated only at 48 um.
3. **Observer-transfer hypothesis:** a candidate that predicts the directly
   measured 5279 spectrum will also predict the change in variance after known
   2K scanner and print-stage MTFs without a new texture-strength fit.

These are future experiment candidates only. No algorithm, parameter, image, or
output was changed in this run.

### Still unknown

- The two-dimensional red, green, and blue density-noise spectra of processed
  5279 as functions of exposure.
- Cross-spectral density or spatial covariance between the three colour records.
- Whether Kodak's unpublished "modified measuring techniques" for this sheet
  differ materially from the later ISO 10505 method.
- The 5279 sampling pitch, scan length/area, number of readings, aperture shape
  tolerance, spectral densitometry details, and repeat uncertainty behind graph
  `F002_0269AC`.
- Any unique mapping from the published RMS curves to fast/medium/slow grain
  diameters, dye-cloud radii, population fractions, or correlation kernels.
- Whether any practical set of aperture diameters makes a particular declared
  low-dimensional spectrum family well-conditioned for processed 5279.
- A period Spirit/2K or 5279-to-2383 measured transfer spectrum from the same
  processed negative patches.

## Potential relationship to the existing model

This note preserves V24's existing single-aperture conclusion and sharpens its
experimental consequence. The existing per-record, exposure-dependent 48 um
normalization remains justified as a stock-specific variance constraint. A
future multi-aperture series would strengthen rejection power, but without
direct frequency information or a declared parametric family it still would not
authorize promoting one population split, radius sequence, spatial kernel, or
post-scan texture as uniquely measured 5279 structure.

The current morphology should therefore remain labelled a bounded structural
candidate. A future evidence-bearing change requires frequency-resolved
processed-5279 measurements with multi-aperture validation, or an explicitly
declared parametric spectrum family that predicts held-out apertures. Nothing in
this note authorizes an algorithm or parameter change.

## Falsifiable future experiment design - not executed

1. Expose uniform 5279 patches from one documented roll at pre-registered log
   exposures spanning toe, the three RMS maxima, midscale, and shoulder; include
   neutral plus record-isolating exposures where physically achievable.
2. Process randomized replicates in controlled ECN-2 runs and retain H-24
   control-strip data only as process-drift covariates.
3. Measure diffuse Status-M density on the same registered areas with calibrated
   circular apertures such as 6, 12, 24, 48, and 96 um. Exact sizes are a proposed
   design, not a Kodak requirement. Use these first as held-out integral
   constraints, not as a claim of nonparametric spectrum recovery.
4. Acquire high-sampling line scans or two-dimensional microdensitometer maps;
   report sampling pitch, aperture MTF, scan length/area, detrending, windowing,
   and replicate uncertainty.
5. Estimate per-record auto-spectra and cross-spectra with confidence intervals.
   Fit candidate morphology only on a subset of apertures and spatial-frequency
   bands.
6. Hold out at least one aperture, one exposure, and one ECN-2 run. Propagate the
   fitted spectrum through independently measured scanner/print MTFs without a
   new variance rescale.

## Denial conditions

The present stricter identifiability conclusion is falsified if a primary source
or mathematical result demonstrates a unique, stable, assumption-free recovery
of the relevant continuous 5279 spectrum from a finite set of aperture RMS
values. A 5279-specific autocorrelation/Wiener spectrum would resolve the
practical stock unknown but would not by itself prove that finite-aperture RMS
was sufficient to recover it.

A candidate morphology is denied if it matches the 48 um curve but misses any
held-out aperture RMS by more than the predeclared combined measurement
uncertainty, produces systematic residuals across spatial frequency, or requires
a new texture-strength fit after every observer MTF.

Conversely, the simple spectrum-family hypothesis gains support only if one fit
predicts held-out apertures, exposures, runs, and observer transfers within their
predeclared uncertainty.

## Conclusion

### Confirmed

- 5279's stock-specific granularity observation is per-record density standard
  deviation measured through a 48 um aperture as a function of exposure; this
  was already recognized as incomplete spectrum evidence in the V24 README.
- The measurement depends on aperture, and the applicable RMS method does not
  estimate a Wiener/noise-power spectrum.
- A finite multi-aperture series adds useful weighted-integral constraints but
  still does not uniquely identify an arbitrary continuous spectrum without
  further assumptions.
- Frequency-resolved granularity transfer requires a spectrum and the transfer
  response of the observing/printing system.

### Denied

- The claim that merely extending graph `F002_0269AC` to a finite set of aperture
  RMS curves would uniquely recover an assumption-free 5279 noise spectrum,
  dye-cloud radius, or fast/medium/slow morphology.
- The claim that matching both published RMS and MTF alone validates the visible
  grain after a 2K scanner or 2383 print chain.

### Still unknown

- All stock-specific frequency-domain and cross-record quantities listed above;
  the public evidence reviewed here supplies no numerical 5279 NPS.

## Next highest priority

Search Kodak/SMPTE photographic-science proceedings and laboratory archives for
a 5279 or same-batch VISION 500T processed-negative frequency-resolved
microdensitometer scan, autocorrelation plot, or Wiener spectrum. Treat a
multi-aperture table as corroborating integral constraints, not a substitute for
frequency data. Prioritize accession-level records and figures with
instrument/aperture metadata; do not spend the next run re-reading the already
established single-aperture boundary.

## Safety and modification audit

- No algorithm, RAW decoder, ffmpeg process, long computation, renderer, A/B
  test, version, manifest, output, finished image, screenshot, calibration
  baseline, V21 research file, site, Git commit/push, or deployment was created
  or changed.
- `sources/` was not modified.
- No research attachment was downloaded.
- The project mirror is not a Git repository, so Git branch/status could not be
  obtained; conflict checks used process inspection and file timestamps instead.
- No concurrent matching automation or emulsion-reconstruction process was
  found before writing.
- The only project changes from this run are this new note and its one-line
  `research_notes/INDEX.md` entry.
