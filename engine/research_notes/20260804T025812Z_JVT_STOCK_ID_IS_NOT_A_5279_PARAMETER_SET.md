# The official JVT identifiers do not disclose a 5279 parameter set

- Note ID: `20260804T025812Z_jvt_stock_id_is_not_a_5279_parameter_set`
- Research time: 2026-08-04T02:58:12Z
- Web-source access date: 2026-08-04
- Scope: research and evidence organization only
- Result type: negative result with two newly retrieved primary documents and one denied identifier equivalence

## Research question

Do the complete official JVT-H022 and JVT-I013r2 packages publish a numerical
grain model, lookup-table entry, sample, or measurement chain for Kodak VISION
500T 5279? In particular, can an identifier with value `3` be carried across the
Thomson patent and the two JVT contributions as one stable 5279 model key?

## Why this remained unresolved

The preceding note found that US 7,899,113 B2 names `Kodak Vision 500T 5279`
beside identifier `3` but does not print the associated lookup-table parameters.
It also recorded the two JVT packages as uninspected retrieval targets. Search
snippets and the patent's references did not establish whether the JVT files
contained the missing values, nor whether `model_id` in the standards proposal
meant a film-stock identifier or a generator-function identifier.

This run tests only that documentary equivalence. It does not attempt to infer a
5279 spectrum from generic film-grain models or from the appearance of a motion
picture clip.

## Prior-state and safety audit

- Automation memory, `CALIBRATION_5279.md`, `V21_RESEARCH.md`, existing
  `RESEARCH_RUN*.md` evidence headings, relevant `research_runs/` READMEs, all
  prior `research_notes/`, and `research_notes/INDEX.md` were checked before
  selecting the question.
- The project mirror is not a Git repository. The nested `site/` repository was
  already dirty on `main`, with six modified tracked files. It was not touched.
- During the final audit, independent site/build activity had advanced that
  state to nine modified tracked files plus untracked `public/research/`; source
  and build-file timestamps also changed outside `research_notes/`. These
  changes did not overlap this note or its assets and were not inspected,
  overwritten, reset, staged, committed, or deployed by this run.
- Separate pre-existing V26 render, ProRes RAW decode, and ffmpeg processes were
  active and writing under `outputs/`. They were not started, stopped, queried
  for results, or otherwise modified by this run.
- No same-automation process, research-note writer, recent conflicting note
  modification, or note lock was found at the start or immediately before the
  write.

## Retrieval method and keywords

Local searches covered `JVT-H022`, `JVT-I013r2`, `US7899113`, `model_id`,
`identifier 3`, `5279`, `grain`, `noise-power spectrum`, and prior unknowns.
Web searches were restricted first to the official ITU JVT archive and used:

- `site:itu.int/wftp3/av-arch/jvt-site JVT-I013r2 film grain`
- `site:itu.int/wftp3/av-arch/jvt-site JVT-H022 film grain Gomila`
- `site:itu.int/wftp3/av-arch/jvt-site 5279 film grain`
- `JVT-I013r2 model_id film stock identifier`

The original ZIP packages were downloaded from ITU. Each contains exactly one
legacy Word document. The documents were converted temporarily to PDF for page
stable inspection; all substantive pages and figures were rendered to PNG and
visually checked. The temporary conversions and page renders were not retained
as project artifacts. Text searches across both complete documents found no
occurrence of `5279`.

## Sources

### S1 - New primary source: JVT-H022

- Cristina Gomila and Alexander Kobilansky, Thomson Inc., *SEI message for film
  grain encoding*, JVT-H022, Joint Video Team of ISO/IEC MPEG and ITU-T VCEG,
  Geneva meeting, May 2003; document saved 19 May 2003.
- Official package:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H022.zip>
- Retained original package:
  `research_notes/assets/20260804T025812Z_jvt_stock_id_semantics/JVT-H022.zip`
- Package size: 5,588,441 bytes.
- SHA-256: `e6e7a08a3c7f0cd8c1f97a996dfbcf9d795d424076f979a7cc3fe24c6ea361c3`.
- Relevant printed pages: 2-4 for the processing chain and film-stock lookup
  proposal; 4-6 for parameter classes and generator models; 8-9 for the
  Rollerball video experiment and its numerical synthesis settings.

### S2 - New primary source: JVT-I013r2

- Cristina Gomila, Thomson Inc., *SEI message for film grain encoding: syntax
  and results*, JVT-I013 revision 2, Joint Video Team of ISO/IEC MPEG and ITU-T
  VCEG, San Diego meeting, 2-5 September 2003; document saved 27 August 2003.
- Official archive directory:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/>
- Official package:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013r2.zip>
- Retained original package:
  `research_notes/assets/20260804T025812Z_jvt_stock_id_semantics/JVT-I013r2.zip`
- Package size: 2,194,483 bytes, matching the official directory listing.
- SHA-256: `b6615aee1d58e1efe2d3e14170d4c3d13ada2244ed18cc9a80287bfbc35ca493`.
- Relevant printed pages: 1-2 for syntax and `model_id`; 3-5 for intensity,
  frequency-filter, autoregression, and colour-correlation parameters; 5-6 and
  Figures 1-2 for test-sequence results.

### S3 - Previously known primary cross-check: US 7,899,113 B2

- Cristina Gomila and Jill MacDonald Boyce, *Technique for Simulating Film Grain
  on Encoded Video*, US 7,899,113 B2, Thomson Licensing; provisional priority
  10 April 2003, patent 1 March 2011.
- Record: <https://patents.google.com/patent/US7899113B2/en>
- Relevant printed page 5, Table 1 and its surrounding text; page 6, lookup-table
  and parameter discussion.
- This source was already recorded in the preceding note and is not counted as
  a newly discovered source here. It is used only to test identifier semantics.

## Evidence ledger

### 1. Direct facts

#### F1 - JVT-H022's film-stock table does not identify 5279

S1, printed pages 3-4, proposes that a decoder may select a predefined grain
pattern from a film-stock identifier and an implementation-specific database.
Its Table 1 is explicitly labeled an *example* lookup table. The rows are:

| Identifier | Film stock in JVT-H022 Table 1 |
| --- | --- |
| 0 | Kodak Vision 200T 5274 |
| 1 | Kodak Vision 259D 5246 |
| 2 | Kodak Vision 500T 5263 |
| 3 | Kodak Vision2 500T 5218 |
| N | Kodak PROFESSIONAL SUPRA 100 |

The complete document contains no `5279` string. In particular, identifier `3`
is 5218 in this JVT table, not 5279.

#### F2 - The patent's identifier 3 and JVT-H022's identifier 3 are different rows

S3, printed page 5, Table 1, maps identifier `3` to `Kodak Vision 500T 5279`.
S1, printed page 4, maps identifier `3` to `Kodak Vision2 500T 5218`.

The documents therefore do not define one immutable cross-document namespace.
The same integer cannot be used as evidence that the JVT package contains the
patent's 5279 entry. This directly denies the identifier-equivalence assumption;
it does not establish which table reflects any implemented system.

#### F3 - JVT-H022 publishes generic and clip-specific synthesis parameters, not a stock LUT

S1, printed pages 4-6, describes size/spatial correlation, aspect ratio,
cross-colour correlation, noise intensity, signal intensity, colour space,
generator model, and blending mode. It gives an autoregressive equation and a
filtered-noise alternative. Printed page 6 uses illustrative variances and DCT
cutoffs for synthetic swatches.

S1, printed pages 8-9, then reports a Rollerball movie-trailer experiment. The
clip was 1920x1088 and cropped to 1440x1088. For the displayed QP28 simulation,
the autoregressive settings span spatial-correlation values 0.14-0.02,
cross-colour values 0.5-0.2, and noise variance 0.048-0.005 across three
intensity levels. The alternate FFT model uses 32x32 blocks, a one-quarter
high-frequency cutoff, luma variance 5.75, and a three-tap boundary filter.

The document does not identify the camera stock, negative process, telecine,
colour conversion history, or physical sampling scale of that clip. Printed
page 9 says neither method perfectly matches the original grain. These numbers
are video-synthesis settings for one displayed example, not a 5279 or 5218 LUT.

#### F4 - JVT-I013r2 redefines `model_id` as generator family, not film stock

S2, printed page 2, Table 1, assigns `model_id=0` to frequency filtering and
`model_id=1` to autoregression; values 2 and 3 are reserved. The field therefore
selects a mathematical generator family. It is not the film-stock identifier
shown in S1 or S3.

S2, printed pages 4-5, defines the transmitted parameters by that generator:
Gaussian variance, horizontal/vertical high and low DCT cutoffs, first-order
spatial correlations, aspect ratio, and consecutive-component colour
correlation. The units are decoder-block coordinates and integer syntax, not
cycles/mm or processed-negative density.

#### F5 - JVT-I013r2 does not print a 5279 parameter payload or sample provenance

The complete S2 document contains no `5279`, Kodak stock number, film-stock
identifier field, per-sequence SEI payload, parameter table, scan aperture,
negative process, or source-stock provenance.

Printed pages 5-6 report compression results for five named HD test sequences.
The authors dropped the two least-significant bits to encode at 8 bits, removed
grain with a temporal filter, and reported bit-rate savings. Figure 2 compares
natural and simulated grain for `rolling_tomatoes`, but neither its caption nor
the surrounding text identifies the originating film stock or a physical
measurement scale. The public ZIP contains only the Word contribution, not the
meeting-display sequences or an encoded parameter payload.

### 2. Bounded inferences

#### I1 - The two official JVT packages close this specific recovery route

Reasoning chain:

1. The exact official packages have now been retrieved and completely inspected.
2. H022's stock table points identifier 3 to 5218, not 5279 (F1-F2).
3. I013r2 uses `model_id` for algorithm choice and contains no stock field (F4).
4. Neither package publishes a 5279 parameter set or tagged sample (F3-F5).
5. Therefore these two package contents cannot supply the missing identifier-3
   5279 LUT or a physical 5279 spectrum.

Boundary: this conclusion applies to the archived H022 and I013r2 ZIPs. It does
not cover an unarchived meeting demo, private Thomson database, provisional-file
appendix, source-code repository, or later standards contribution.

#### I2 - H022's Rollerball numbers cannot be transferred to any named stock

Reasoning chain:

1. H022 prints numerical synthesis settings for the Rollerball example (F3).
2. It does not state the stock, processing, scan chain, or physical scale.
3. The settings are fitted or selected in a decoded-video simulation and are
   explicitly imperfect.
4. Therefore they cannot be attributed to 5279, 5218, or intrinsic emulsion
   morphology.

Boundary: they remain primary evidence for the range and semantics of a 2003
Thomson/JVT display-oriented grain simulator. They could constrain a historical
video-observer study only if the exact clip and parameter-estimation chain were
recovered.

#### I3 - The patent's 5279 row is still a retrieval clue, not a calibration value

The table mismatch shows that the patent and JVT examples evolved or were drawn
from different stock lists. It strengthens the need for date- and document-local
identifier interpretation. It does not invalidate the patent's direct statement
that its own Table 1 row 3 is 5279, but it denies importing any H022 or I013
parameter merely because it also uses the integer `3`.

### 3. Model candidate hypotheses for future testing

1. **Revision-drift hypothesis:** provisional 60/462,389 contains the older
   5279 stock table, while JVT-H022 was updated to then-current VISION2 5218
   before the May 2003 meeting. A dated file wrapper can confirm or deny this.
2. **Separate-namespace hypothesis:** the stock identifier and later SEI
   `model_id` were intentionally separate namespaces. Earlier and later JVT
   drafts should show when the stock-ID field was removed or renamed.
3. **Meeting-payload hypothesis:** a San Diego display bitstream or ancillary
   demo file, outside the I013r2 ZIP, contains actual SEI parameter payloads.
   Even if recovered, it will be observer evidence unless its source stock and
   scan chain are documented.

These are future documentary tests only. No model, parameter, or source code was
changed.

### 4. Still unknown

- The contents and exhibits of US provisional application 60/462,389.
- Why the patent and H022 example stock tables differ, and whether either table
  was ever backed by a populated implementation database.
- Whether H022's named lookup database existed outside the proposal and, if so,
  whether it contained a 5279 record.
- The film stocks, negative processes, telecines, scales, and colour histories
  behind Rollerball and the five I013r2 test sequences.
- Whether the San Diego meeting-display sequences or actual SEI payloads survive
  elsewhere in the ITU archive.
- All processed-5279 auto-spectra, cross-spectra, spatial covariance,
  autocorrelation, repeat uncertainty, and exposure dependence.

## Potential relationship to the existing model

The JVT files add no 5279 calibration value. Their most useful contribution is
semantic: stock identity, generator family, colour space, intensity interval,
spatial scale, and observation chain must be kept as separate fields. A bare
integer such as `3`, a generic DCT cutoff, or a clip-fitted autoregression
coefficient must not constrain the existing fast/medium/slow populations,
dye-cloud radii, cross-record coupling, or intrinsic negative NPS.

The H022/I013 parameterization remains relevant only as a possible period
television-delivery observer. Its block-coordinate cutoffs and video residuals
are downstream of unknown scanning and processing and cannot replace density-
domain frequency measurements.

## Falsifiable future experiment design - not executed

1. Obtain the public file wrapper for provisional 60/462,389 and the earliest
   PCT publication image. Compare every stock-table row, document date, and
   change against H022 and the granted patent.
2. Search the complete May and September 2003 JVT meeting directories, agenda
   attachments, and later film-grain contributions for an explicit stock-ID
   syntax revision, demo bitstream, parameter payload, or table erratum.
3. For any recovered payload, record the exact sequence, frame dimensions,
   bit depth, colour space, chroma format, filtering, generator model, and
   stock/process/scanner provenance before interpreting numbers.
4. Deny the physical-5279 interpretation unless a primary record explicitly
   ties the payload to 5279 and supplies a traceable conversion from decoder
   pixels or transform bins to processed-negative spatial units.

## Denial conditions

This note's negative result is denied if the official H022 or I013r2 package is
shown to contain an omitted attachment or embedded payload with a 5279-tagged
numerical model and traceable provenance. The identifier-semantics conclusion is
denied if a primary crosswalk explicitly declares patent Table 1 identifier 3,
H022 Table 1 identifier 3, and I013r2 `model_id=3` to be one shared identifier.

A newly recovered SEI payload without source-stock and scan-chain provenance
would deny only the claim that no numerical meeting payload survives. It would
not establish a physical 5279 NPS or emulsion morphology.

## Conclusion

The complete official JVT-H022 and JVT-I013r2 packages do not publish a 5279
parameter set. H022's analogous stock table assigns identifier 3 to VISION2
500T 5218, while I013r2 uses `model_id` to select frequency-filter or
autoregression generators. H022's printed Rollerball settings and I013r2's
compression results lack stock and measurement provenance and cannot be
transferred to 5279. The patent's 5279 row remains a document-local archival
lead, not a cross-JVT parameter key.

## Next highest priority

Retrieve the public file wrapper and earliest available image for provisional
60/462,389, then compare its dated stock table with JVT-H022 and the later PCT/US
publication. This is now higher priority than searching generic film-grain
coding papers, because it can directly explain whether the 5279-to-5218 table
change reflects revision history and whether any appendix contained the missing
lookup values.

## Scope confirmation

This run performed research and evidence organization only. It did not modify
an algorithm, process source media, decode ProRes RAW, run ffmpeg, render, run an
A/B test, write to `outputs/`, increment a version, modify a manifest, edit the
site, commit or push Git state, or deploy Sites. No file under `sources/` was
modified.
