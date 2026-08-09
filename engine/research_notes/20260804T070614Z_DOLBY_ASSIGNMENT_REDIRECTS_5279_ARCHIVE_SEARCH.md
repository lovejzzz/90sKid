# Dolby assignment redirects, but does not complete, the 5279 archive search

- **Note ID:** `20260804T070614Z_dolby_assignment_redirects_5279_archive_search`
- **Run UTC:** 2026-08-04T07:06:14Z
- **Access date:** 2026-08-04
- **Scope:** research and evidence organization only
- **Result type:** bounded negative exhibit census plus a documented archive-route correction

## Research question

Does a bounded search of public P-TACTS and USITC material expose a contemporaneous
10 April-31 July 2003 email that explains the `5279 -> 5218` stock-table change
between provisional 60/462,389 and JVT-H022? If not, which documented successor is
the best next records-inquiry target for the specific patent family containing
US 7,899,113?

## Why this was still unresolved

The preceding note established that a public selection of Karsten Suehring's JVT
reflector mail survives in IPR2024-00572, but that selection stops in 2002 and does
not cover the target 2003 interval. It then named InterDigital as a plausible
successor lead based on a separate acquisition of Technicolor video-coding patents
and personnel.

That was not yet a family-specific chain of title. Before preparing any inquiry, the
specific 5279-bearing patent family needed to be traced in an official assignment
record. Patent ownership also had to be kept distinct from custody of lab notebooks,
email exports, draft standards contributions, source data, or inventor files.

## Safety and conflict gate

- The project root is not a Git repository; no project-root Git state could be
  reported.
- No `site/.git` directory exists in the current project mirror, so there was no
  nested site state to inspect.
- No matching 5279, emulsion-reconstruction, or `research_notes` writer was running
  immediately before the note was created.
- `research_notes/INDEX.md` retained the prior run's SHA-256
  `f9d176dae51810bb36488ab0f1e03542b6ae71d1d67ee3928d16b1a71aab28bb`
  at the pre-write check. No recent note modification or `sources/` modification
  was detected.
- The official assignment PDF was downloaded only to `/tmp` for read-only visual
  inspection. It was not retained as a project attachment because the USPTO URL is
  public and stable and the 8.7 MB duplicate was not necessary.
- The final audit detected unrelated external mtime updates during this run in
  `PIPELINE_OPTIMIZATION_2026-08-04.md`, `outputs/performance_v27/`, several files
  under `src/`, and `src/__pycache__/`. No matching writer remained at the final
  process check. Those changes did not overlap this note or its index entry and
  were not opened, altered, attributed, reset, or cleaned by this research run.

## Retrieval method and bounded search scope

### Exact keys

- `US 7,899,113`, `7899113`, `10/552,179`, `10552179`
- `60/462,389`, `PU030116`, `PU030116-US-PCT`
- exact patent title: `Technique for simulating film grain on encoded video`
- `JVT-H022`, `H022`, `JVT-I013`, `5279`, `5218`
- inventor/contributor keys: `Cristina Gomila`, `GomilaC@tce.com`,
  `cristina.gomila@thomson.net`, `Jill Boyce`, `BoyceJ@tce.com`, and
  `jill.boyce@thomson.net`

### Public-record routes checked

1. Exact-key searches restricted to public P-TACTS document URLs.
2. Exact-key searches restricted to public USITC and EDIS URLs.
3. Month-specific searches for public Karsten Suehring email exhibits in April,
   May, June, and July 2003.
4. Reinspection of the IPR2024-00572 Patent Owner Response exhibit list, printed
   pages ix-xli, and the separately filed contributor list.
5. Complete visual inspection of all ten pages of USPTO Patent Assignment reel
   041214, frame 0001.

This was a deliberately bounded public-web census. Search-engine non-indexing,
sealed material, discovery productions not filed as exhibits, private participant
mailboxes, and records held by a successor are outside it.

## Sources

### A. USPTO Patent Assignment, reel 041214, frame 0001

- **Institution:** United States Patent and Trademark Office, Assignment Center
- **Document:** *Worldwide Patent Assignment*, Thomson Licensing SAS to Dolby
  Laboratories Licensing Corporation
- **Execution / recording evidence:** cover sheet dated 9 February 2017; seller
  execution dates shown as 7 February 2017; purchaser signature dated 9 February
  2017; the operative clause states an effective date of 30 December 2016
- **Relevant pages:** PDF pages 1-4 and duplicate cleaner counterpart pages 7-10
- **Stable source:**
  <https://assignmentcenter.uspto.gov/ipas/search/api/v2/public/download/patent/41214/1>

### B. Nokia Patent Owner Response, IPR2024-00572

- **Institution:** USPTO Patent Trial and Appeal Board, P-TACTS
- **Document:** Patent Owner Response concerning US 7,724,818
- **Relevant pages:** printed pages ix-xli, especially the exhibit list entries
  2048-2451
- **Stable source:**
  <https://ptacts.uspto.gov/ptacts/public-informations/petitions/1555393/download-documents?artifactId=A34-fZL5CXNXG62kNfWGg1GSA8OwEYSpw1lTl1gtjcJR3Ahd7rnGyY0>

### C. Nokia Exhibit 2031, `contributors.h`

- **Institution:** USPTO Patent Trial and Appeal Board, P-TACTS
- **Document:** contributor list from the JVT reference software record
- **Relevant page:** PDF page 5
- **Stable source:**
  <https://ptacts.uspto.gov/ptacts/public-informations/petitions/1555393/download-documents?artifactId=1kMCyM8jMf5gEHFxXf9bFnAOU1-cTBkwBD34Uvsl3jOZSB0RdSoZ5rg>

No secondary article or forum was used as substantive evidence.

## Evidence, with boundaries

### 1. The 5279-bearing US patent is explicitly inside the Thomson-to-Dolby assignment

**Direct fact.** USPTO assignment PDF page 3, repeated more clearly on page 7,
lists case reference `PU030116-US-PCT`, filing date 24 February 2004, application
`10/552179`, and grant `7899113`. This is the same US family already tied by the
patent and priority record to provisional 60/462,389 and its 5279 stock table.

**Direct fact.** The cover sheet on PDF pages 1-2 records Thomson Licensing under
several name variants as conveying party and Dolby Laboratories Licensing
Corporation as receiving party. The cover identifies 28 US property numbers,
including application number `10552179`. The attorney docket field is
`TECHNICOLOR II`.

**Boundary.** `TECHNICOLOR II` is a docket label in this transaction. It does not
identify an archive collection, a laboratory, an inventor file, or the location of
the 2003 source measurements.

### 2. The operative document transfers patent rights, not a documented research archive

**Direct fact.** USPTO assignment PDF page 4, repeated on page 8, states that as of
30 December 2016 the seller conveys to Dolby its interest in the listed patents,
associated enforcement and royalty rights, and rights to maintain, prosecute,
license, and otherwise exploit them. Pages 5-6 and 9-10 contain counterpart
signatures; the cover records the assignment on 9 February 2017.

**Direct document observation.** The enumerated conveyance does not identify
JVT reflector exports, `H022` drafts, `PU030116` engineering data, film-stock LUTs,
scanner measurements, lab notebooks, or inventor mailboxes as transferred records.

**Bounded inference.** Dolby is the documented patent-right successor and is
therefore a better first family-specific inquiry target than InterDigital. It does
not follow that Dolby received, retained, indexed, or may disclose the underlying
2003 working records.

### 3. The located P-TACTS mail selection still does not enter the target window

**Rechecked direct fact.** The IPR2024-00572 response's exhibit list identifies a
filed selection of Suehring email records. The first dated email exhibit in that
sequence is 2 May 2002; the last is 24 December 2002. Printed pages ix-xli list
the sequence. The response contains no `5279` or `H022` occurrence.

**Rechecked direct fact.** Exhibit 2031 page 5 names Jill Boyce and Cristina Gomila
as Thomson contributors. This establishes their participation in the period JVT
software record, not the subject matter or survival of any 2003 film-grain email.

**Negative result.** Exact patent, docket, title, author-email, stock, and document
keys produced no indexed public P-TACTS or USITC hit containing a target-window
film-grain message. Month-specific searches for public Suehring email exhibits in
April-July 2003 likewise produced no result.

**Boundary.** That absence applies only to the checked public and indexed record.
It does not prove that the original reflector carried no such discussion, that no
participant retained it, or that no unindexed/sealed litigation production exists.

## Claims classified

### Direct facts

1. Official USPTO reel 041214/frame 0001 includes US application 10/552,179 and
   grant 7,899,113 in a Thomson-to-Dolby assignment.
2. The assignment's operative date is 30 December 2016; signatures and recording
   occurred in February 2017.
3. The filed P-TACTS email selection inspected here covers 2002, not the target
   April-July 2003 interval.
4. No target message was found by the exact-key public P-TACTS/USITC searches
   recorded above.

### Bounded inferences

1. InterDigital should no longer be described as the family-specific patent-right
   successor for US 7,899,113. That earlier lead arose from a different Technicolor
   video-patent transaction.
2. Dolby is now the highest-priority first inquiry for the *patent chain*, but the
   assignment alone supplies no evidence of research-record custody.
3. A further untargeted P-TACTS document-directory crawl is unlikely to answer the
   question unless it is driven by a newly identified case, exhibit list, custodian,
   or production range.

### Model candidate hypotheses

No numerical emulsion or grain parameter is proposed.

The only candidate hypothesis is archival and testable: Dolby's patent or records
team may be able to confirm whether the acquired `PU030116` prosecution portfolio
included any non-prosecution working file, or may identify the seller-side custodian
to whom a narrowly framed records inquiry should be redirected.

### Still unknown

1. Why H022 changed the provisional's 5279 row to 5218.
2. Whether the change corrected a label, replaced a measured stock, substituted a
   later model, or merely refreshed an example.
3. Whether any numeric 5279 LUT, NPS, sample image, scanner metadata, or physical
   scale ever accompanied `PU030116` or H022 outside the published documents.
4. Whether Dolby, Technicolor/Thomson, an inventor, an outside patent firm, IMTC,
   RWTH, ITU, or a litigation party retains the relevant 2003 mail or draft.
5. Whether the assignment transaction included a records schedule not present in
   the ten-page recorded instrument.

## Potential relation to the existing reconstruction

The result changes only the evidence-retrieval map. It does not identify a 5279
grain spectrum, morphology, cross-channel covariance, density dependence, scanner
scale, or any production parameter. The existing reconstruction must therefore
remain unchanged.

In particular, neither ownership of US 7,899,113 nor the docket label
`PU030116-US-PCT` turns the patent's stock identifier into a published parameter
set. The earlier identifiability boundary remains intact.

## Falsifiable future archival test — not executed

### Proposed inquiry design

Prepare, but do not send in this research run, one narrow records inquiry to
Dolby's patent-licensing or legal-records contact. Identify:

- USPTO reel 041214/frame 0001;
- `PU030116-US-PCT`, application 10/552,179, grant 7,899,113;
- provisional 60/462,389;
- JVT-H022 and the 10 April-31 July 2003 interval;
- inventors Cristina Gomila and Jill Boyce; and
- the exact requested record classes: draft stock tables, measurement/LUT
  appendices, inventor files, and JVT/IMTC mail exports.

Ask only whether such records exist, whether they are publicly accessible, and—if
Dolby is not custodian—whether a non-confidential custodian or transfer path can be
identified. Do not request trade secrets, credentials, or restricted content.

### Positive condition

A dated, attributable response or public catalog identifies a surviving record,
custodian, accession, production range, or destruction/transfer schedule tied to
`PU030116` or the named inventors.

### Denial / falsification conditions

The archival hypothesis is denied if a competent custodian states that the
transaction contained patent rights/prosecution files only and that no responsive
working records were received, especially if the response provides a different
custodian or a documented destruction/retention boundary.

Even a recovered 5279-labelled numeric file must be rejected as a physical stock
constraint unless its sample, process, scanner, scale, channel meaning, and density
dependence are documented. A video-codec LUT without that provenance remains an
end-to-end encoder model, not an intrinsic emulsion measurement.

## Highest-priority next step

Draft a precise, non-sent inquiry for Dolby that cites reel 041214/frame 0001 and
asks about custody of `PU030116` working records. Before any future send, recheck
current public contact policy and ensure the inquiry asks only for public archive
status or a custodian referral. If Dolby disclaims custody, use the response—not a
generic corporate-acquisition assumption—to select the next archive.

## Run restrictions confirmed

This run did not implement an algorithm, decode RAW or other source media, invoke
ffmpeg, process original footage, render, run an A/B, write to `outputs/`, increment
a version, alter a manifest, edit the site, commit or push Git state, or deploy.
No file under `sources/` was modified.
