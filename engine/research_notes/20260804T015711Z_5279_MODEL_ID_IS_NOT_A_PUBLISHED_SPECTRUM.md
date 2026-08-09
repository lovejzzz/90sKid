# A 5279 grain-model identifier is not a published 5279 spectrum

- Note ID: `20260804T015711Z_5279_model_id_is_not_a_published_spectrum`
- Research time: 2026-08-04T01:57:11Z
- Web-source access date: 2026-08-04
- Scope: research and evidence organization only
- Result type: negative result with one new stock-specific documentary lead

## Research question

Does a period primary source publish a frequency-resolved microdensitometer
trace, autocorrelation, Wiener/noise-power spectrum, or numerical spatial model
for Kodak VISION 500T 5279? In particular, does the 5279 model identifier in a
2003-priority film-grain-coding patent disclose the missing stock-specific
spatial data, or only name a lookup-table key whose contents remain unpublished?

## Why this remained unresolved

The preceding note established that a finite set of aperture RMS measurements
cannot nonparametrically recover an arbitrary continuous spectrum. The next
priority was therefore to seek actual frequency-resolved 5279 evidence.

Kodak H-1-5279t remains the only stock-specific image-structure source already
verified locally. It publishes MTF and exposure-dependent red, green, and blue
diffuse RMS granularity through a 48-micrometre aperture, but no spatial noise
spectrum. A search result for US 7,899,113 B2 was potentially important because
its Table 1 explicitly assigns an identifier to a `Kodak Vision 500T 5279` grain
model. This note tests the narrow question of what that identifier actually
discloses. It does not repeat the prior mathematical identifiability argument.

## Prior-state and safety audit

- Automation memory, `CALIBRATION_5279.md`, `V21_RESEARCH.md`, all existing
  `RESEARCH_RUN*.md` headings, the two `research_runs/` READMEs, and all earlier
  `research_notes/` priorities were checked before selecting the question.
- The project mirror is not a Git repository. The nested `site/` repository was
  already dirty on `main` at commit `6e170741aa1c71e98e5032915e6e8b0600e6947d`;
  its changes were not touched.
- Separate pre-existing render, ProRes RAW decode, and ffmpeg processes were
  active under the Codex app and writing only to `outputs/`. This run did not
  start, stop, inspect outputs from, or otherwise interact with those jobs.
- No same-automation research writer, open research-note file, or conflicting
  recent modification was found.

## Retrieval method and keywords

Local full-text searches covered 5279, granularity, Wiener spectrum, noise-power
spectrum, microdensitometer, autocorrelation, model identifiers, and previous
research conclusions. Web searches then used combinations of:

- `Kodak 5279 Wiener spectrum granularity`
- `VISION 500T 5279 microdensitometer autocorrelation`
- `5279 film grain model`
- `Cristina Gomila Jill Boyce 5279 JVT`
- `JVT-I013 film grain encoding syntax results`
- `JVT-H022 SEI message film grain encoding`
- Kodak/SMPTE/ITU/patent and archival-finding-aid domain restrictions

The full nine-page patent was read, especially printed pages 5-8. The official
ITU JVT meeting directory was checked for the cited JVT-I013r2 package. The ZIP
is publicly listed, but its contents were not successfully extracted in this
run; no assertion about its internal pages or attachments is made. Kodak and
archive finding aids were also searched for 5279-specific measurement records.

## Sources

### S1 - Kodak 5279 technical data, rechecked stock constraint

- Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
  publication H-1-5279t, March 2003.
- Local reference:
  `experiments/emulsion_reconstruction/references/kodak_5279_H-1-5279t.pdf`
- Stable public scan:
  <https://device.report/m/5e51c79d670196bba47e7f500a4d5cb6b040df42f004110fd5989ce056ea95b1.pdf>
- Relevant printed pages 3-4: image-structure description, MTF, and diffuse RMS
  granularity graph; page 3 specifies a 48-micrometre microdensitometer aperture.
- This is direct 5279 evidence, but it was already known and is not counted as a
  newly discovered source.

### S2 - New stock-specific primary lead: US 7,899,113 B2

- Cristina Gomila and Jill MacDonald Boyce, *Technique for Simulating Film Grain
  on Encoded Video*, US 7,899,113 B2, assigned to Thomson Licensing.
- Provisional priority: 10 April 2003; PCT filing: 24 February 2004; patent date:
  1 March 2011.
- Patent record: <https://patents.google.com/patent/US7899113B2/en>
- Official patent-image PDF:
  <https://patentimages.storage.googleapis.com/93/a0/3e/72e36b773591ac/US7899113.pdf>
- Relevant locators: printed page 5 through page 6, Table 1 and Table 2; printed
  page 6, the passages describing model parameters and the lookup-table
  characterizer; printed page 7, RGB and intensity-dependent modeling remarks;
  claims 3-5 and 17-20 on printed pages 7-8.
- The complete public patent was accessible. It is a Thomson video-coding
  patent, not a Kodak coating disclosure or a 5279 measurement report.

### S3 - Primary standards archive lead, not substantive evidence in this run

- Joint Video Team of ISO/IEC MPEG and ITU-T VCEG, official archive for the
  September 2003 San Diego meeting.
- Directory:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/>
- The directory lists `JVT-I013r2.zip` (2,194,483 bytes). The patent record cites
  Cristina Gomila, *SEI Message for Film Grain Encoding: Syntax and Results*,
  JVT-I013 Revision 2, 2 September 2003, pages 1-11.
- Because the package content was not retrieved successfully, it is only a
  precise next-retrieval target. It supplies no page-level evidence below.

### S4 - Rejected transfer lead: generic NPS synthesis paper

- Ian Stephenson and Arthur Saunders, “Simulating Film Grain using the
  Noise-Power Spectrum,” *EG UK Theory and Practice of Computer Graphics 2007*,
  pages 69-72, Eurographics Association.
- Full text:
  <https://diglib.eg.org/bitstreams/372ec0ad-ff80-497b-81b0-2dd8d7021e48/download>
- Relevant printed pages 69-70, equations and text around Figure 1 and Figure 2;
  printed pages 71-72, limitations and conclusions.
- The paper uses two adjustable dye-cloud diameters, 6.5 and 15 micrometres, but
  does not identify Figure 2's real film or bind those values to 5279. It is
  useful method evidence, not a 5279 measurement.

### S5 - Archive finding aids checked without a 5279 hit

- University of Rochester, *Kodak Research Laboratories* collection contents
  list, 45 pages:
  <https://www.lib.rochester.edu/IN/RBSCP/ATTACHMENTS/Kodak-Research-Laboratory-Materials.pdf>
- British Library, *Kodak Historical Archive*, catalogue root:
  <https://searcharchives.bl.uk/catalog/032-002405150>
- These broad catalogues did not expose a 5279 spectral-granularity item in the
  searchable descriptions. This is not proof that no unindexed or undigitized
  record exists. No archival item was requested or inspected.

## Evidence ledger

### 1. Direct facts

#### F1 - Kodak's public stock sheet still supplies only aperture RMS, not NPS

S1, printed page 3, says the 5279 image-structure samples were tungsten-exposed
and processed in recommended ECN-2 chemistry. It specifies red, green, and blue
microdensitometer readings through a 48-micrometre aperture. Printed page 4 plots
diffuse RMS granularity versus exposure.

The document does not publish a scan trace, autocorrelation, spatial covariance,
Wiener spectrum, frequency bins, sampling pitch, scan length, or repeat
uncertainty. Its separate MTF graph is not a stochastic noise spectrum.

#### F2 - A period patent explicitly names a 5279-specific grain-model key

S2, printed page 5, Table 1, maps identifier `3` to `Kodak Vision 500T 5279`.
The surrounding text says film stocks can have separate identifiers and that
correct down-sampling information helps restore grain at the correct scale.

This is direct documentary evidence that the inventors contemplated a distinct
5279-conditioned model in a video grain-restoration system. It is not evidence
that Kodak supplied the model, that the model was physically calibrated, or that
the lookup table was ever populated in a working product.

#### F3 - The patent describes which parameter classes matter

S2, printed page 6, says a model's parameters should allow adjustment of grain
size, intensity, spatial correlation, and colour correlation. It also says
parameters may depend on signal intensity and colour component. The same page
describes a characterizer that may use a lookup table to return parameters and a
corresponding model from a stock identifier.

These parameter classes are directly relevant to the missing 5279 auto- and
cross-spectral evidence. The patent therefore confirms that one scalar RMS would
not be the only information needed by its more complete model.

#### F4 - The public patent does not disclose the 5279 lookup-table contents

Across S2's specification, tables, figures, and claims, no numeric parameter set
is assigned to Table 1 identifier `3`. Table 2 contains illustrative mathematical
model forms, but it does not map any one of them to 5279. No 5279 spectrum,
autocorrelation, grain sample, dye-cloud radius, frequency cutoff, RGB
correlation, exposure interval, ECN-2 batch, microdensitometer setup, scanner, or
physical cycles/mm calibration is published.

The lookup-table embodiment on printed page 6 says that a table *can* return a
model and parameters; it does not print that table's values. Thus “model ID 3” is
a label, not the missing numerical model.

#### F5 - The patent's measurement object is potentially downstream video

S2, printed pages 5-7, starts from an incoming video stream. One embodiment
derives samples by subtracting a filtered video from the input, and the grain
information can change between groups of frames. Printed page 6 explicitly warns
that a compact model is an estimate that can differ from actual film.

The public document does not say that the hypothetical 5279 entry came from a
uniform processed-negative microdensitometer map rather than a telecined,
resampled, colour-converted, compressed, or creatively graded image.

#### F6 - Generic 6.5/15 micrometre values are not 5279 evidence

S4, printed page 69, says its two dye-cloud diameters are adjustable to match
specific coatings and then chooses 6.5 and 15 micrometres. The paper does not
identify the real-film example in Figure 2 by manufacturer, stock, process,
exposure, record, or scanner. Printed pages 71-72 also label independent
per-colour grain and equal diameters as assumptions.

Therefore these values cannot be promoted to direct 5279 grain or dye-cloud
diameters. They are an explicit generic modeling choice.

### 2. Bounded inferences

#### I1 - The model identifier narrows the archive search but not the spectrum

Reasoning chain:

1. Table 1 explicitly associates identifier `3` with 5279 (F2).
2. The described lookup table would need model and parameter contents (F3).
3. Those contents are absent from the public patent (F4).
4. Therefore the identifier is evidence of a potentially recoverable historical
   artifact, not evidence for any numerical spatial response.

Boundary: the missing table may exist in a provisional filing, JVT attachment,
prototype, demo bitstream, or private implementation. Its existence and contents
cannot be inferred from the patent language alone.

#### I2 - Even a recovered encoder model would not automatically be a film NPS

Reasoning chain:

1. The patent operates on incoming video and allows subtraction-based grain
   extraction (F5).
2. It treats down-sampling scale as necessary metadata (F2).
3. A video residual can contain the negative, processing, telecine aperture,
   colour conversion, resizing, filtering, and compression history.
4. Therefore recovered parameters would first be evidence for a specific digital
   observation chain. They become physical 5279 evidence only if provenance ties
   them to controlled processed-negative measurements and physical units.

Boundary: a well-documented period telecine model could still be valuable for a
historical scan observer. It must not be mislabeled as intrinsic emulsion
morphology or Status-M density NPS.

#### I3 - The existing 5279 morphology remains underidentified

The new patent confirms the relevance of size, intensity, spatial correlation,
colour correlation, intensity dependence, and scale. It supplies none of their
5279 values. Consequently it does not justify changing current fast/medium/slow
diameters, cloud radii, cross-record coupling, or observer transfer. The 48
micrometre normalization remains a stock-specific amplitude constraint; the
morphology remains a bounded candidate.

### 3. Model candidate hypotheses for future testing

1. **Recoverable-LUT hypothesis:** an official JVT attachment, provisional
   filing, prototype, or archived Thomson implementation contains the actual
   Table 1 identifier-3 model/parameter record.
2. **Observer-entanglement hypothesis:** any recovered identifier-3 parameters
   will change with input down-sampling or telecine processing, indicating a
   video-observer model rather than an invariant processed-negative NPS.
3. **Held-out-scale hypothesis:** a genuinely physical model with documented
   cycles/mm calibration will predict grain covariance after multiple known
   scanner apertures/resolutions without refitting its intrinsic spectrum.

These are future test candidates only. No model or parameter was changed.

### 4. Still unknown

- Whether the Table 1 5279 lookup-table entry was ever implemented or measured.
- The contents of US provisional application 60/462,389 and whether it included
  appendices or sample tables omitted from the public patent.
- Whether JVT-H022 or JVT-I013r2 contains a 5279-tagged model, sample, result, or
  demo bitstream; the package contents were not obtained in this run.
- The source negative, exposure, ECN-2 processing, telecine/scanner, resolution,
  colour space, filtering, and down-sampling behind any proposed identifier-3
  model.
- All processed-5279 per-record auto-spectra, cross-spectra, autocorrelation,
  repeat uncertainty, and exposure dependence.
- Any 5279-identified item hidden below collection-level archival descriptions.

## Potential relationship to the existing model

The patent adds one useful research handle: `5279` plus the Thomson/JVT film-grain
coding lineage. It does not add a calibration value. No current stochastic,
fast/medium/slow, dye-cloud, scanner, or print parameter should change on this
evidence.

If a provenance-rich model is later recovered, it should first be classified by
measurement domain. A model derived from compressed or telecined video belongs
only in a historically bounded observer branch. Only frequency-resolved density
measurements of controlled ECN-2 5279 patches can constrain intrinsic negative
NPS without that observer ambiguity.

## Falsifiable future experiment design - not executed

1. Retrieve JVT-H022 and JVT-I013r2 from the official ITU archive, including all
   attachments and demo bitstreams, and search them for `5279`, `identifier 3`,
   `Vision 500T`, lookup tables, frequency cutoffs, and sample provenance.
2. Obtain the public file wrapper/prosecution history for provisional
   60/462,389 if available, plus the related Thomson database-of-grain-patterns
   patent family. Record exact document/page identifiers.
3. For any recovered parameter set, document colour space, resolution, pixel
   aspect ratio, density/exposure interval, source stock, process, scanner,
   filtering, and whether the values are measured or illustrative.
4. Convert spatial parameters to cycles/mm only when a traceable negative width
   or sampling scale exists. Do not infer physical scale from an encoded frame
   width alone.
5. Test the recovered model against held-out uniform 5279 scans at two known
   apertures/resolutions and at multiple exposures, without refitting intrinsic
   parameters. Separate scanner MTF/noise from negative NPS.

## Denial conditions

This note's negative result is denied if a primary source publishes the numeric
identifier-3 lookup-table/model contents with a traceable 5279 sample and enough
measurement metadata to reconstruct spatial frequency and colour/exposure
dependence.

A numeric LUT without sample/process/scanner provenance would deny only the claim
that the model contents are unpublished; it would not establish a physical 5279
NPS. A model is denied as intrinsic emulsion evidence if its fitted spatial scale
changes with digital resizing, its parameters absorb scanner filtering, or it
fails held-out apertures/exposures beyond predeclared measurement uncertainty.

## Conclusion

### Confirmed

- A 2003-priority Thomson patent explicitly assigned identifier `3` to a Kodak
  VISION 500T 5279 grain model.
- The patent identifies grain size, intensity, spatial correlation, colour
  correlation, intensity dependence, and scale as relevant model information.
- Kodak's public 5279 sheet still supplies only MTF and 48-micrometre diffuse RMS
  granularity, not a frequency-resolved noise measurement.

### Denied

- The claim that patent Table 1's `5279 = model 3` entry is itself a published
  5279 spectrum or numerical spatial model.
- The transfer of the generic 6.5/15 micrometre synthesis values in S4 to 5279.
- Any algorithm or morphology change based on either source.

### Still unknown

- Whether a numerical 5279 LUT survives in the JVT/provisional/prototype archive.
- Whether such a LUT, if found, represents intrinsic processed-negative density
  structure or only a particular downstream video observation chain.
- The actual frequency-resolved and cross-record quantities for processed 5279.

## Next highest priority

Retrieve and inspect the complete official JVT-H022 and JVT-I013r2 packages and
the file wrapper for provisional 60/462,389, then search the related Thomson
database-of-film-grain-patterns patent family for the identifier-3 lookup-table
contents. Require a 5279 label plus sample/process/scanner/scale provenance before
treating any number as stock evidence. Do not revisit generic NPS formulas or
unidentified dye-cloud diameters unless they lead to that provenance.

## Safety and modification audit

- No algorithm, source code, RAW decoder, ffmpeg process, long computation,
  renderer, A/B test, version, manifest, output, finished image, screenshot,
  calibration baseline, `V21_RESEARCH.md`, site file, Git commit/push, or
  deployment was created or changed.
- `sources/` and all forbidden paths were untouched.
- An unrelated active session continued modifying/building the already-dirty
  nested `site/` during final verification, including `dist/` artifacts and a
  newly modified `vite.config.ts`. This run did not start or interact with that
  activity, and it did not overlap `research_notes/`.
- No research attachment was retained; stable public links and exact locators
  were sufficient for this negative-result note.
- The only intended project changes are this note and one conflict-free line in
  `research_notes/INDEX.md`.
