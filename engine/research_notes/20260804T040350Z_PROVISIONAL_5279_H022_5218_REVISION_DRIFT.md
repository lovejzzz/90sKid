# The 2003 provisional confirms document-branch drift from 5279 to 5218

- Note ID: `20260804T040350Z_provisional_5279_h022_5218_revision_drift`
- Research time: 2026-08-04T04:03:50Z
- Web-source access date: 2026-08-04
- Scope: research and evidence organization only
- Result type: one newly inspected primary document, one confirmed revision mismatch, and a continued negative result for numerical 5279 parameters

## Research question

Does the certified public copy of US provisional application 60/462,389 explain
why the later patent maps film-stock identifier `3` to Kodak VISION 500T 5279
while JVT-H022 maps identifier `3` to VISION2 500T 5218? Does the provisional
also contain the missing numerical 5279 lookup-table entry or an appendix that
was omitted from the published patent?

## Why this remained unresolved

The preceding run completely inspected JVT-H022 and JVT-I013r2. It established
that H022's example stock table assigns identifier `3` to 5218, while the later
US patent assigns the same integer to 5279. It could not determine whether the
5279 row predated H022, appeared only during later patent drafting, or came from
an unpublished implementation. The provisional file wrapper and its possible
attachments were the highest-priority unresolved retrieval target.

This run tests only that document history. It does not infer emulsion morphology
or a physical spectrum from a stock name or identifier.

## Prior-state and safety audit

- The automation memory path did not contain a memory file. `CALIBRATION_5279.md`,
  `V21_RESEARCH.md`, existing `RESEARCH_RUN*.md` headings, relevant
  `research_runs/` entries, all prior `research_notes/`, and `INDEX.md` were
  checked before selecting the question.
- The project mirror is not a Git repository. The nested `site/` repository was
  clean at the start of research but had unrelated modified and untracked source
  files immediately before this note was written. Those files did not overlap
  `research_notes/` and were not inspected, overwritten, reset, staged, committed,
  or deployed by this run.
- No same-automation process, research-note writer, open note file, or note lock
  was found. A separate V27 render, ProRes RAW decode, and ffmpeg encode began
  during this run and was writing under `outputs/`; it was not started, stopped,
  read for results, or otherwise modified here.

## Retrieval method and keywords

Local searches covered `60/462,389`, `US46238903P`, `PCT/US2004/005365`,
`WO2004095829`, `EP1611740`, `identifier 3`, `5279`, `5218`, `PU030116`, and
the prior unknowns. Web and official-register searches used:

- `60/462,389 film grain`
- `PCT/US2004/005365`
- `WO2004095829`
- `EP1611740 application file priority document`
- USPTO Patent File Wrapper, WIPO/PCT, Google Patents, and EPO Register records

Google Patents identifies the correct European application as `EP04714129`.
The EPO Register's complete 66-item file inspection was then checked. Its
22 November 2004 entry exposes an eight-page electronically transmitted priority
document for 60/462,389. All eight pages were visually inspected in the official
viewer at page-fit scale: the USPTO certification page, provisional cover sheet,
and the complete six-page specification. No attachment was retained because the
official document has a stable public viewer and a duplicate was not necessary.

## Sources

### S1 - New primary source: certified copy of US provisional 60/462,389

- Cristina Gomila and Jill MacDonald Boyce, *A Method for Simulating Film Grain
  on Encoded Video Sequences*, US provisional application 60/462,389, filed
  10 April 2003; internal reference `PU030116`.
- Official EPO Register file inspection for EP04714129 / EP1611740:
  <https://register.epo.org/application?number=EP04714129&tab=doclist>
- Official priority-document viewer, EPO document ID `EICL6DDCDHELFI4`:
  <https://register.epo.org/application?documentId=EICL6DDCDHELFI4&number=EP04714129&lng=en&npl=false>
- EPO file-list entry: 22 November 2004, `Priority document (electronically
  transmitted)`, eight pages.
- Relevant locators: document page 1, USPTO certification and application number;
  document page 2, provisional cover sheet, inventors, title, filing date, and
  specification count; document page 4 / specification page 2, Table 1;
  document page 5 / specification page 3, Table 2 and the symbolic parameter
  example; document pages 6-8 / specification pages 4-6, processing architecture,
  references, and possible claims.

### S2 - Previously retrieved primary comparison: JVT-H022

- Cristina Gomila and Alexander Kobilansky, Thomson Inc., *SEI message for film
  grain encoding*, JVT-H022, Joint Video Team, Geneva meeting, May 2003.
- Official package:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H022.zip>
- Retained in the preceding run at
  `research_notes/assets/20260804T025812Z_jvt_stock_id_semantics/JVT-H022.zip`.
- Relevant printed pages 3-4; Table 1 on printed page 4 maps identifier `3` to
  Kodak VISION2 500T 5218.
- This source was already known and is not counted as newly retrieved here.

### S3 - Previously known primary comparison: later patent publication

- Cristina Gomila and Jill MacDonald Boyce, *Technique for Simulating Film Grain
  on Encoded Video*, PCT/US2004/005365, published as WO 2004/095829 A1; later
  US 7,899,113 B2.
- PCT publication record:
  <https://patents.google.com/patent/WO2004095829A1/en>
- US patent record:
  <https://patents.google.com/patent/US7899113B2/en>
- Relevant US printed page 5, Table 1, and printed page 6, lookup-table and
  parameter discussion. The later patent maps identifier `3` to 5279 but does
  not print its parameter values.
- This source was already recorded in the two preceding notes and is used only
  for dated document comparison.

### S4 - Official access-boundary record: USPTO Patent File Wrapper API

- USPTO Open Data Portal, Patent File Wrapper `Documents` API documentation:
  <https://data.uspto.gov/apis/patent-file-wrapper/documents>
- The current page states that ODP access requires a USPTO account from
  18 June 2026. No credentials were requested, entered, stored, or bypassed.
- This is access-method evidence only. The substantive provisional was obtained
  from the public EPO file inspection in S1.

## Evidence ledger

### 1. Direct facts

#### F1 - The provisional itself maps identifier 3 to 5279

S1, document page 4 / specification page 2, Table 1, prints this example stock
table:

| Identifier | Film grain model |
| --- | --- |
| 0 | Kodak Vision 200T 5274 |
| 1 | Kodak Vision 259D 5246 |
| 2 | Kodak Vision 320T 5277 |
| 3 | Kodak Vision 500T 5279 |
| N | Kodak PROFESSIONAL SUPRA 100 |

The surrounding paragraph says a numerical identifier can describe grain by
identifying the film type when the type and a decoder-side model are known.
Therefore the `5279 = 3` row was present in the 10 April 2003 priority document;
it was not first added during the February 2004 PCT filing or later US prosecution.

#### F2 - H022 changed the row to 5218 after the provisional filing

S2, printed page 4, Table 1, uses the same identifier range and surrounding film-
stock lookup concept but maps identifier `3` to Kodak VISION2 500T 5218. H022's
May 2003 meeting date is later than the provisional's 10 April 2003 filing date.

This directly confirms a dated document mismatch: the patent-priority branch had
5279 before H022's standards contribution used 5218. It denies the narrower idea
that 5279 appeared only in the later granted patent.

#### F3 - The later patent branch retained or restored 5279

S3, US printed page 5, Table 1, again maps identifier `3` to 5279. The dated
sequence visible in the public record is therefore:

`10 Apr 2003 provisional: 5279 -> May 2003 H022: 5218 -> Feb 2004 PCT / later US publication: 5279`

The sequence is not a single monotonic replacement of an old stock by a new one.
It is at least a branch divergence between a patent document and a standards
contribution, followed by continued use of the older patent table in the PCT/US
family.

#### F4 - The provisional contains model forms but no 5279 values

S1, document page 5 / specification page 3, Table 2, lists generic symbolic
generator families: filtered-noise, autoregressive, cross-colour, and other
forms. The following equation says that coefficients such as `a`, `b`, and `d`
would be transmitted and may depend on intensity or colour component.

Across the complete six-page specification there is no numerical coefficient,
frequency cutoff, variance, covariance, grain radius, pixel scale, cycles/mm
calibration, exposure interval, colour-component table, sample image, scan
aperture, process condition, or 5279-specific parameter payload. Document pages
6-8 contain architecture, three references, and six possible claims, not an
appendix or populated lookup database.

#### F5 - The provisional's measurement object is encoded-video grain

S1, specification pages 1-5, describes removing grain from input video,
parameterizing the residual, transmitting side information, and simulating grain
at the decoder. Specification page 4 explicitly allows RGB-domain modeling and
different parameters by colour component or gray-level set, but it also says the
simplest model may be uncorrelated zero-mean Gaussian noise and that decoder
complexity and display quality affect model choice.

The document therefore describes a video-coding architecture and possible model
semantics. It does not document a processed-5279 microdensitometer experiment.

### 2. Bounded inferences

#### I1 - The revision-drift hypothesis is supported, but only as branch drift

Reasoning chain:

1. The certified April provisional already contains `identifier 3 = 5279` (F1).
2. The May H022 contribution uses the analogous table with `identifier 3 = 5218`
   (F2).
3. The later PCT/US patent branch again uses 5279 (F3).
4. Therefore the stock table changed across the patent and JVT document branches.
5. The evidence does not support a simple chronological migration in which 5218
   permanently replaced 5279 everywhere.

Boundary: the documents do not say who changed the row, why it changed, whether
H022 was updated to a then-current product for presentation, or whether either
table was connected to an implemented database.

#### I2 - The provisional closes the most plausible public-appendix route

Reasoning chain:

1. The official file exposes the certified priority copy and identifies a
   six-page specification (S1).
2. All six specification pages and both administrative pages were inspected.
3. The only parameter content is symbolic and generic (F4).
4. No appendix, sample, or numerical table appears in that certified copy.
5. Therefore the publicly filed provisional does not supply the missing 5279 LUT.

Boundary: this does not prove that no private Thomson database, source code,
meeting demo, or separately retained experiment ever existed.

#### I3 - The repeated 5279 row is documentary provenance, not calibration

The provisional proves that the 5279 label was part of the inventors' early
patent concept. Its repeated appearance in the later patent strengthens the
archival lead `PU030116`. It does not establish that a 5279 model was measured,
implemented, or physically scaled, because the filed text contains no values or
sample provenance and permits generic display-oriented models (F4-F5).

### 3. Model candidate hypotheses for future testing

1. **Patent/standards branch hypothesis:** the patent draft retained a legacy
   5279 example while H022 substituted the then-current VISION2 5218 for standards
   presentation. Earlier JVT drafts, slides, or change records should locate the
   replacement and may state its rationale.
2. **Internal-project hypothesis:** `PU030116` or the cover-sheet express-mail
   label indexes a Thomson project file containing a populated stock database.
   A corporate archive catalogue can confirm or deny the existence of such a
   file without assuming its contents.
3. **Unimplemented-example hypothesis:** both stock tables were illustrative
   editorial examples and no stock-specific decoder database was populated.
   Surviving code, demo binaries, meeting payloads, or technical reports should
   either expose a database record or support the absence of one.

These are future documentary tests only. No model, parameter, or source code was
changed.

### 4. Still unknown

- Why H022 replaced 5279 with 5218 and why the later patent branch retained 5279.
- Whether `PU030116` corresponds to a recoverable Thomson laboratory notebook,
  source repository, model database, or only an attorney docket.
- Whether either stock table was implemented, populated, measured, or used in a
  meeting demo or encoded bitstream.
- The film stock, process, scanner, scale, and colour history behind any private
  model that might have existed.
- All processed-5279 auto-spectra, cross-spectra, covariance, autocorrelation,
  repeat uncertainty, and exposure dependence.

## Potential relationship to the existing model

This result changes documentary provenance, not emulsion calibration. It proves
that 5279 was named in the earliest public patent-priority text and that the JVT
stock table diverged shortly afterward. It supplies no physical or video-domain
number that can constrain the current fast/medium/slow populations, dye-cloud
radii, cross-record coupling, NPS, scanner response, or print response.

Any future recovered `PU030116` parameter set must first be classified by stock,
process, scan chain, colour space, resolution, intensity interval, generator
family, and physical scale. A clip-fitted decoder model remains observer evidence,
not intrinsic 5279 emulsion evidence.

## Falsifiable future experiment design - not executed

1. Search official JVT-G/H agenda files, draft revisions, meeting slides, and
   later film-grain contributions for both complete stock-table variants and a
   dated change explanation.
2. Search public corporate-archive catalogues and patent-assignment records for
   `PU030116`, Cristina Gomila, Jill Boyce, and the exact title on the provisional
   cover sheet. Request only indexed, publicly accessible records.
3. Compare the PCT application-as-filed description with the provisional page by
   page, recording textual additions separately from the unchanged 5279 table.
4. If code or a database is recovered, require an explicit 5279 record plus
   sample/process/scanner/scale provenance before interpreting any value.
5. Deny intrinsic-film status if a recovered model changes with encoded-frame
   resizing, absorbs temporal filtering or compression, or lacks density-domain
   units and controlled ECN-2 provenance.

## Denial conditions

The branch-drift conclusion is denied if an official corrected H022 copy shows
that its printed 5218 row was an erratum and the intended row was 5279, or if an
official crosswalk declares the tables one immutable namespace with a documented
clerical error.

The negative parameter result is denied if the certified priority record is shown
to omit a substantive filed attachment, or another official copy of 60/462,389
contains a populated 5279 parameter table with traceable provenance. A numerical
database without stock/process/scanner/scale metadata would deny only the claim
that no values survive; it would not establish intrinsic 5279 morphology or NPS.

## Conclusion

### Confirmed

- The 10 April 2003 provisional already mapped identifier `3` to Kodak VISION
  500T 5279.
- JVT-H022 changed the analogous row to VISION2 500T 5218 in May 2003.
- The later patent branch returned to or retained 5279, so the public record shows
  branch drift rather than a single stable cross-document identifier namespace.

### Denied

- The idea that 5279 was inserted only during later PCT or US patent drafting.
- The idea that the public provisional contains the missing numerical 5279 LUT,
  sample, spectrum, or physically calibrated parameter set.
- Any transfer of the provisional's symbolic model forms to 5279 calibration.

### Still unknown

- The editorial or technical reason for the 5279-to-5218 substitution in H022.
- Whether a populated Thomson stock database or 5279 model ever existed outside
  the public filings.
- Every frequency-resolved, cross-record, exposure-dependent physical quantity
  needed to identify processed 5279 grain.

## Next highest priority

Search the official JVT-G/H revision trail and meeting materials for the exact
stock-table change and its rationale, using both `PU030116` and the provisional's
exact title as archival keys. This is higher priority than more generic grain-
simulation literature because it can distinguish an editorial stock update from
evidence of an implemented model database.

## Scope confirmation

This run performed research and knowledge organization only. It did not modify
algorithms, source code, manifests, calibration baselines, `V21_RESEARCH.md`,
finished media, screenshots, outputs, the site, Git history, or deployment state.
It did not start ProRes RAW decoding, ffmpeg, rendering, A/B testing, versioning,
publishing, or deployment. `sources/` and all forbidden paths were untouched.
