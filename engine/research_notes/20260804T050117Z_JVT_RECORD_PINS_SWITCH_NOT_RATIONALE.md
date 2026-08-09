# The JVT record pins the 5279-to-5218 switch window, not its rationale

- Note ID: `20260804T050117Z_jvt_record_pins_switch_not_rationale`
- Research time: 2026-08-04T05:01:17Z
- Web-source access date: 2026-08-04
- Scope: documentary research and evidence organization only
- Result type: a narrowed chronology, a newly documented standards-design
  boundary, and a negative result for the exact edit rationale

## Research question

Can the official JVT document lists, meeting notes, ad hoc group notes, and all
three public revisions of JVT-I013 determine:

1. when the patent-priority document's example row `identifier 3 = 5279` became
   JVT-H022's `identifier 3 = 5218`;
2. why that stock substitution was made; and
3. whether a film-stock identifier survived into the film-grain SEI proposal
   that JVT agreed to adopt as the basis for draft text?

## Why this remained unresolved

The preceding run established a non-monotonic document sequence: the certified
10 April 2003 provisional used 5279, the May 2003 H022 contribution used 5218,
and the later PCT/US patent branch again used 5279. It did not inspect the
surrounding JVT meeting record or the earlier public revisions of I013. Thus it
could not distinguish an unexplained single-row edit from a broader abandonment
of stock identifiers during standards work.

This run tests only that narrow document history. It does not treat either stock
name as a physical grain measurement or a decoder parameter payload.

## Prior-state and safety audit

- The shell environment did not define `$CODEX_HOME`, so the symbolic memory
  path initially appeared absent. The established Codex home was then resolved
  as `/Users/tianxing/.codex`; the complete existing automation memory was read
  before finalizing this note. Its recorded next priority was precisely the
  G/H revision and agenda search performed here. `CALIBRATION_5279.md`,
  `V21_RESEARCH.md`, the existing `RESEARCH_RUN*.md` conclusions and priorities,
  relevant `research_runs/` entries, all existing `research_notes/`, and
  `research_notes/INDEX.md` were also checked.
- The project mirror is not a Git repository, so a root Git state cannot be
  reported. The nested `site/` repository was clean on `main` before research
  and immediately before this note was written.
- No same-automation process, emulsion renderer, ProRes RAW decoder, ffmpeg
  writer, research-note lock, or open handle under `research_notes/` was found.
  Existing note timestamps remained stable through the pre-write check.
- An unrelated process had completed V27 output before this run and another
  process committed clean site changes during the final audit, advancing the
  nested site to `eafd1a389b287f7b4935f307380297f596610090`. Those changes did
  not overlap `research_notes/`, were not initiated or controlled here, and the
  site was clean after the commit. They were not inspected as research evidence.
- No file under `sources/`, `src/`, `outputs/`, `research_runs/`, `site/`, or any
  prohibited baseline/manifests path was edited.

## Retrieval method and keywords

Local searches covered `H022`, `I013`, `5279`, `5218`, `film stock ID`,
`model_id`, `Gomila`, `Kobilansky`, `Boyce`, `scan dependence`, `AHG`, and the
previous note's unknowns.

Official JVT archive searches covered the March 2003 Pattaya, May 2003 Geneva,
July 2003 Trondheim Professional Extensions AHG, and September 2003 San Diego
records. The following public artifacts were inspected:

- the complete G- and H-series document lists;
- the final available Pattaya and Geneva agenda-with-notes files;
- the Trondheim AHG meeting notes;
- JVT-I013, JVT-I013r1, and JVT-I013r2, compared as extracted text;
- the final available San Diego agenda-with-notes file.

Word documents were downloaded only to a system temporary directory, converted
locally for page location and text comparison, and not retained in the project.
The official ITU URLs are stable and the already retained H022/I013r2 packages
were sufficient for the prior substantive review. No new research attachment was
necessary.

## Sources

### S1 - Official pre-H022 JVT document list and meeting notes

- Joint Video Team, Pattaya meeting, March 2003, `JVT-G000`, *List of
  Documents*:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_03_Pattaya/JVT-G000.txt>
- Official meeting directory:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_03_Pattaya/>
- Gary Sullivan, `AgendaWithNotesPIIdraft7.doc`, last saved 13 March 2003;
  official file:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_03_Pattaya/AgendaWithNotesPIIdraft7.doc>
- Complete public document-list and meeting-note search: no `film grain`,
  `Gomila`, or `Kobilansky` match.
- Temporary-download SHA-256 for the agenda file:
  `020d717330d20f84214800eff382adc6c8cd79605fa95ec8c559a563d91bb326`.

### S2 - Official Geneva document list and meeting record

- Joint Video Team, Geneva meeting, 23-27 May 2003, `JVT-H000r0`, document
  list:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H000r0.txt>
- Official meeting directory:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/>
- Gary Sullivan, `AgendaWithNotes_draft8.doc`, date-saved footer 2 June 2003;
  official file:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/AgendaWithNotes_draft8.doc>
- Relevant printed pages 9-10: H022 discussion, stock-ID questions, maturity
  decision, and AHG action.
- Temporary-download SHA-256 for the agenda file:
  `6eed9b84c914d870849648366ea20de21a33f55dd40bcaef89321dd07ea63b06`.

### S3 - Previously retained H022, rechecked as the dated boundary

- Cristina Gomila and Alexander Kobilansky, Thomson Inc., *SEI message for film
  grain encoding*, JVT-H022, document saved 19 May 2003.
- Official package:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H022.zip>
- Relevant printed pages 3-4: stock-identification proposal and example lookup
  table; printed page 4 maps identifier `3` to VISION2 500T 5218.
- The official Geneva directory exposes one `JVT-H022.zip` and no H022 draft or
  numbered revision package.
- This source was already retained and is not counted as a newly downloaded
  source in this run.

### S4 - New primary comparison: all public I013 revisions

- Cristina Gomila, Thomson Inc., *SEI message for film grain encoding: syntax
  and results*, initial JVT-I013, saved 16 July 2003:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013.zip>
- JVT-I013r1, saved 18 July 2003:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013r1.zip>
- JVT-I013r2, saved 27 August 2003:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013r2.zip>
- Official directory:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/>
- Initial-version relevant printed pages 1-2: syntax and `model_id` table;
  printed pages 4-5: generator parameters and H022 reference.
- ZIP SHA-256, in revision order:
  - JVT-I013: `f3f58497ff3232c52b0defcf3f306976e900af0f5e3b52724f88901505ce0225`
  - JVT-I013r1: `68d97445db3102284ee1bf0ee3a3d3925182e4bcb07e6d828b4c4638bc7f8d51`
  - JVT-I013r2: `b6615aee1d58e1efe2d3e14170d4c3d13ada2244ed18cc9a80287bfbc35ca493`
- Only r2 was retained by a preceding run. The initial and r1 packages were
  inspected from temporary downloads and not copied into the project.

### S5 - New primary context: Trondheim AHG meeting notes

- Gary Sullivan, *JVT AHG on PExt Meeting Notes*, Trondheim meeting,
  22-24 July 2003, `AHGonPExtMeetingNotesDraft1.doc`:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/AHGonPExtMeetingNotesDraft1.doc>
- Relevant printed page 1: film-grain study listed as a significant topic;
  page 2: I013 in the document list; page 6: `JVT-I013 ... Not yet presented.`
- Temporary-download SHA-256:
  `0c7c5baeede51869f045750a3a2563ad890dbfb7fbdeb69f1ea7e409c42a9b37`.

### S6 - New primary context: San Diego meeting record and adoption

- Gary Sullivan, `AgendaWithNotes_draft8.doc`, San Diego meeting,
  2-5 September 2003; official file:
  <https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/AgendaWithNotes_draft8.doc>
- Relevant printed page 4: r2 described as `minor syntax improvements`;
  page 9: agreement to use I013 as the basis for draft text; page 11: AHG
  recommendation and JVT agreement to adopt I013 with editorial improvement.
- Temporary-download SHA-256:
  `1d2b434c32535d4d1bcab4cd5ebda744ea5f5db459315f156290e90a4d43ed32`.

### S7 - Previously inspected patent-priority comparison

- Cristina Gomila and Jill MacDonald Boyce, *A Method for Simulating Film Grain
  on Encoded Video Sequences*, US provisional 60/462,389, filed 10 April 2003;
  certified priority document in the EPO file for EP04714129:
  <https://register.epo.org/application?number=EP04714129&tab=doclist>
- Relevant document page 4 / specification page 2: identifier `3` maps to 5279.
- This source was established in the preceding run and is used only to anchor
  the left boundary of the chronology.

## Evidence ledger

### 1. Direct facts

#### F1 - No earlier public G-series film-grain contribution was found

S1's complete `JVT-G000` document list contains no film-grain contribution and
no Gomila or Kobilansky entry. The final Pattaya agenda-with-notes likewise has
no such match. S2's H-series list first exposes the relevant title as H022 and
separately lists H029, an adaptive-block-transform proposal for film-grain
content.

Boundary: this is a statement about the complete public JVT G-series list and
meeting record. It does not prove that Thomson had no private draft, experiment,
email, or non-JVT discussion before H022.

#### F2 - The public substitution window is 10 April to 19 May 2003

S7's certified provisional, filed 10 April 2003, maps identifier `3` to 5279.
S3's H022 footer and package metadata say it was saved 19 May 2003 and its
printed page 4 maps identifier `3` to 5218. S1 provides no intervening public
JVT film-grain document. Therefore the public record brackets the table edit
between those two dated documents.

This does not identify the day, editor, draft, or reason for the change.

#### F3 - Geneva discussion questioned stock-ID semantics, not the row change

S2, printed page 9, records two direct concerns after H022 presented `Film stock
ID` as useful information:

- a question about scan dependence, answered that other information about the
  process generating the samples would also be needed; and
- a standardization question noting that stock IDs would identify specific
  manufacturers' non-standardized products.

The same discussion says H022 had no specific syntax and was not mature for
adoption, while recording interest in future investigation. Printed page 10
calls for test material, testing conditions, and an AHG.

Neither page names 5279 or 5218, compares the two table rows, or says why the
example was edited.

#### F4 - The first public I013 had already removed stock identification

S4's initial I013 was saved 16 July 2003, before the 22-24 July Trondheim AHG.
Its printed pages 1-2 define `model_id` as a two-bit generator selector:

| value | meaning in initial JVT-I013 |
| --- | --- |
| 0 | frequency filtering |
| 1 | auto-regression |
| 2 | reserved |
| 3 | reserved |

The complete initial document contains no film-stock field, lookup table, 5279,
5218, or Kodak stock number. It does refer to H022 as the previous contribution.
Thus the stock-identifier concept was absent from the first publicly archived
syntax, not removed only in r1 or r2.

#### F5 - Public I013 revisions do not preserve an edit explanation

Text comparison of S4's initial, r1, and r2 documents shows the generator-family
meaning of `model_id` in every version. The r0-to-r1 changes add default values
and experimental results. The r1-to-r2 changes adjust chroma-format handling,
blending-mode syntax, interval counts, multi-generation intervals, and generator
notes. No revision restores a stock field or contains a rationale for deleting
one.

S5, printed page 6, merely says I013 had not yet been presented at the Trondheim
AHG. S6, printed page 4, characterizes the San Diego version as having minor
syntax improvements. Neither meeting record documents a stock-table decision.

#### F6 - JVT adopted the parameterized syntax path, not a stock LUT

S6, printed page 9, records agreement to adopt I013 as the basis for draft text
unless an alternative proved necessary. Printed page 11 records the AHG
recommendation and JVT agreement to adopt I013 with editorial improvement for
an SEI message representing film-grain characteristics.

Because every public I013 version selects a generator family and transmits
parameters rather than selecting a film stock (F4-F5), the public adoption
record supports the parameterized-model path. It does not adopt H022's example
film-stock lookup table.

### 2. Bounded inferences

#### I1 - The row change preceded public JVT review

Reasoning chain:

1. The provisional used 5279 on 10 April (F2).
2. The first public JVT film-grain contribution found is H022 (F1).
3. H022 was saved 19 May with 5218 already in its table (F2).
4. The Geneva minutes discuss that submitted H022, not an earlier 5279 draft.
5. Therefore the 5279-to-5218 row edit occurred before the publicly documented
   JVT review captured in the meeting notes.

Boundary: a private pre-submission review, company presentation, or email may
have prompted the edit; the public archive inspected here cannot identify it.

#### I2 - Stock identification was a discarded proposal branch by 16 July

H022 proposed two routes: stock identification and explicit parameterization.
The first I013 syntax retains only explicit model and parameter signaling (F4),
and that is the path JVT later agreed to adopt (F6). Therefore, by 16 July, stock
identification was no longer part of the public syntax branch that proceeded to
drafting.

Boundary: this does not prove that a decoder-side private stock database ceased
to exist or that the H022 table was formally repudiated.

#### I3 - The Geneva concerns are compatible with removal, but do not prove cause

The scan-dependence concern makes a stock name insufficient to specify the
observed grain after sampling and processing. The standardization concern makes
manufacturer product IDs a fragile normative namespace. Both concerns are
technically consistent with I013's later choice to send explicit parameters.

However, no inspected record states `therefore remove film stock ID`, and I013
was not presented in the Trondheim minutes. It would overstate the evidence to
claim those remarks caused either the 5279-to-5218 substitution or the later
removal of the stock field.

#### I4 - Neither documentary identifier can constrain the 5279 reconstruction

The adopted public syntax does not assign a 5279 stock ID or payload, and H022's
example row is 5218. The provisional's 5279 row belongs to a non-normative
illustrative lookup concept that did not survive into public I013. Therefore no
integer in this document family identifies a physical 5279 NPS, covariance,
dye-cloud radius, scanner scale, or exposure-dependent variance curve.

### 3. Model candidate hypotheses for future testing

1. **Standards-sufficiency hypothesis:** the Geneva scan-dependence and vendor-
   namespace objections caused the syntax work to abandon film-stock IDs in
   favor of explicit parameters. A dated AHG email or change proposal should
   state that link directly.
2. **Editorial-update hypothesis:** 5218 replaced 5279 in H022 merely to show a
   then-current product, without changing any measured database. A pre-H022
   Thomson draft or author correspondence should show a single table-row edit
   unaccompanied by parameter changes.
3. **Separate-author-branch hypothesis:** the Gomila/Boyce patent draft and the
   Gomila/Kobilansky JVT contribution maintained separate example tables. A
   corporate document-control history should show independent source files or
   revision owners.
4. **No-populated-LUT hypothesis:** the stock tables were illustrative from the
   start, and the standards team moved to explicit parameters because no
   portable stock database existed. A recovered implementation or payload would
   falsify this; continuing absence alone would not prove it.

These are future documentary tests. No candidate was implemented or rendered.

### 4. Still unknown

- The exact date, editor, and reason for replacing 5279 with 5218 in H022.
- Whether a pre-submission H022 revision containing 5279 survives.
- Whether the Geneva stock-ID concerns directly caused removal from I013.
- Whether the H022 table ever pointed to a populated Thomson model database.
- Whether `PU030116`, an AHG reflector archive, or corporate records preserve
  the missing review history.
- Any 5279-specific decoder payload, physical scale, scan chain, process state,
  auto-spectrum, cross-spectrum, covariance, or exposure-dependent parameters.

## Potential relationship to the existing model

This result narrows provenance but supplies no calibration number. It supports a
stronger exclusion rule: neither H022's `3 = 5218` nor the provisional/patent's
`3 = 5279` should be connected to I013's `model_id`, because I013 uses the same
small integers for generator families and contains no stock namespace.

The current model's fast/medium/slow populations, dye-cloud geometry, NPS,
cross-record coupling, scanner observer, and print response therefore remain
unchanged. A future recovered SEI payload would still need stock, process,
sampling, colour-space, intensity-interval, and generator provenance before it
could serve even as video-observer evidence.

## Falsifiable future experiment design - not executed

1. Locate the official JVT/VCEG reflector or AHG correspondence from 10 April to
   31 July 2003 using exact searches for `H022`, `film stock ID`, `scan
   dependence`, `non-standardized products`, `I013`, `5279`, and `5218`.
2. Establish immutable dates and authors for every hit, and separate public
   meeting mail from later summaries or mirrored copies.
3. Accept the standards-sufficiency hypothesis only if a contemporaneous message
   explicitly connects the Geneva objections to deleting the stock field.
4. Search archive catalogues for a pre-19-May H022 draft or Thomson project file
   under the exact title, authors, `PU030116`, and both table variants.
5. Accept the editorial-update hypothesis only if a dated version comparison
   shows 5279 becoming 5218 without associated model or payload changes.
6. If a payload or database is recovered, classify its stock, process, scanner,
   spatial units, signal domain, colour representation, and intensity intervals
   before any comparison with the 5279 reconstruction.

## Denial conditions

- Deny the claim that the JVT minutes explain the row substitution unless a
  contemporaneous record names both the edit and its rationale.
- Deny the claim that the Geneva remarks caused stock-ID removal unless an AHG
  or author record explicitly makes that causal link.
- Deny any crosswalk from H022/patent identifier `3` to I013 `model_id` because
  the public documents define different namespaces.
- Deny any 5279 calibration claim based solely on a stock name, integer, generic
  generator family, or clip-level synthesis parameter.
- Deny the claim that the public archive proves no private LUT existed; it proves
  only that the inspected public artifacts do not disclose one.

## Conclusion

### Confirmed

- The public row-change window is now bracketed from 10 April 2003 (provisional:
  5279) to 19 May 2003 (H022: 5218).
- H022 is the first public JVT film-grain contribution found in the complete
  G/H document lists; no public G-series precursor was found.
- Geneva minutes explicitly raise scan-dependence and manufacturer-product
  standardization problems with film-stock IDs.
- The initial 16 July I013 already omits stock identification and uses
  `model_id` for generator family.
- All public I013 revisions retain that meaning, and JVT later agreed to adopt
  the I013 parameterized syntax as the drafting basis.

### Denied

- The inspected meeting records do not explain why 5279 was changed to 5218.
- The public I013 revision history does not preserve a stock-field deletion or
  its rationale; the field is absent from the first archived version.
- The Geneva concerns cannot yet be asserted as the cause of removal.
- The adopted `model_id` values are not film-stock identifiers and expose no
  5279 parameter set.

### Still unknown

- The private edit history between the provisional and H022.
- The causal relationship, if any, between Geneva objections and I013 syntax.
- Whether any populated Thomson stock database or 5279 payload existed.
- All intrinsic 5279 physical and spectral grain parameters absent from Kodak's
  published stock sheet.

## Next highest priority

Search a contemporaneous JVT/VCEG reflector or Professional Extensions AHG mail
archive for the 10 April-31 July 2003 interval. The narrow target is an explicit
message linking H022's stock-ID proposal or the Geneva `scan dependence` /
`non-standardized products` objections to I013's removal of the stock field.
If no official mail archive is public, record that access boundary and switch to
Thomson/Technicolor corporate-archive finding aids rather than repeating the
document-family search.

## Scope confirmation

This run performed research and note-taking only. It did not implement an
algorithm, process original media, decode ProRes RAW, invoke ffmpeg, render,
write to `outputs/`, run an A/B test, increment a version, modify a manifest,
change the website, commit or push Git, create a Sites version, deploy, or
publish anything.
