# DIR diffusion factor is not a 5279 cross-layer constant

- Note ID: `20260803T215248Z_dir_diffusion_factor`
- Research time: 2026-08-03T21:52:48Z
- Access date for web sources: 2026-08-03
- Scope: literature research only; no algorithm, source-media processing, rendering,
  A/B test, version change, site change, commit, push, or deployment was performed.

## Research question

Can one fixed receiver/causer coefficient or 3x3 cross-layer matrix be interpreted
as a physically measured, stock-specific DIR diffusion constant for Kodak VISION
500T 5279?

## Why this was still unresolved

`V21_RESEARCH.md` already establishes that DIR release is imagewise, occurs during
development, can alter both intralayer and interlayer development, and is affected
by layer/barrier placement. The current research history does not, however, cite a
reproducible assay that defines a DIR transport quantity or shows its range across
different inhibitor compounds. Without such an assay, it remained unclear whether
the model's fixed receiver/causer values could be given a stronger physical meaning
than an end-to-end phenomenological approximation.

This note does not reopen or modify V21. It tests only that interpretation.

## Prior-state and safety audit

- Read the automation memory, `CALIBRATION_5279.md`, `V21_RESEARCH.md`, the
  existing `RESEARCH_RUN*.md` summaries and next-priority sections, and the
  DIR/interimage-related entries under `research_runs/`.
- `research_notes/` did not exist before this run; therefore there was no prior
  note or index entry on this exact question.
- The project mirror itself is not a Git repository. The nested `site/` repository
  was on `main` with pre-existing tracked modifications. They were not touched.
- Separate V24 render/ffmpeg/ProRes RAW processes were already active and writing
  `outputs/`. They were not started, inspected for results, interrupted, or altered.
  No process matching this automation's name and no research-note lock was found.
- `sources/` remained read-only and untouched.

## Retrieval method and keywords

Searched the web for combinations of:

- `Eastman Kodak DIR inhibitor diffusion interlayer barrier motion picture`
- `development inhibitor releasing coupler diffusion factor`
- `DIR release linkage Lippmann emulsion density reduction`
- `Kodak color negative reduced granularity electronic conversion patent`

The search was restricted conceptually to Kodak patents and official Kodak
processing material. A broad search result was followed to the US patent-family
member because its PDF provides stable patent-page and table references. Existing
Kodak patent US 5,298,376 was rechecked as context, not counted as a new source.

## Sources

### New primary source

1. Allan F. Sowinski, Richard P. Szajewski, Frank R. Brockler, Edward J.
   Giorgianni, John D. Buhr, Lois A. Buitano, and Maria J. Gonzalez; assignee
   Eastman Kodak Company. **US 6,190,847 B1, _Color negative film for producing
   images of reduced granularity when viewed following electronic conversion_.**
   Priority 1997-09-30; filed 1998-04-24; published 2001-02-20.
   - Stable HTML: https://patents.google.com/patent/US6190847B1/en
   - Public patent PDF: https://patentimages.storage.googleapis.com/51/93/67/9d2605443427a5/US6190847.pdf
   - Local research copy:
     `assets/20260803T215248Z_dir_diffusion_factor/US6190847B1.pdf`
   - SHA-256:
     `39a7d43dd80cfc0a9aee029cedaa43faa7fcbb2539d9606367fae5fead0a7ba6`
   - Relevant locations: patent pp. 1-2, “Definition of Terms” and “Background”;
     pp. 21-24, “Diffusion Factor Determinations” and Table I; pp. 27-30,
     Table II and “Evaluations of Samples”; pp. 31-32, Tables V-VII.

### Rechecked primary context

2. Richard P. Szajewski et al.; assignee Eastman Kodak Company. **US 5,298,376
   A, _Photographic silver halide material with improved color saturation_.**
   Filed 1991-10-01; published 1994-03-29.
   - Stable HTML: https://patents.google.com/patent/US5298376A/en
   - Relevant locations: “Background of the Invention,” “Summary of the
     Invention,” and “Detailed Description” discussion of layer placement,
     inhibitor reflection/scavenging, and separation-exposure gamma ratios.
   - This source was already part of `V21_RESEARCH.md`; it is not new evidence
     for the archive count in this run.

## Evidence ledger

### Direct facts supported by the new patent

1. **DIR is a release mechanism, not merely a density matrix.** The patent defines
   a DIR compound as one that cleaves to release a development inhibitor during
   colour development and explicitly includes anchimeric and timed-release
   mechanisms (US 6,190,847 B1, patent p. 1). It defines “diffusion factor” as the
   extent of diffusion of the released inhibitor (patent pp. 1-2).

2. **Kodak's assay measures receiver inhibition through an intervening sink.** Two
   test coatings are compared. Sample 2 adds a fine-grained, unsensitized Lippmann
   emulsion in the overcoat. A developer concentration is first chosen to reduce
   the underlying layer's midscale density by about 50% in Sample 1. The density
   reduction remaining in Sample 2 is divided by the Sample-1 reduction to obtain
   the diffusion factor (patent pp. 21-22, steps 1-6).

3. **The assay's endpoints encode adsorption/transport, not geometric distance.**
   A factor near 0 corresponds to strong adsorption by the Lippmann emulsion; a
   factor near 1 corresponds to weak or absent adsorption, allowing the inhibitor
   to reach the underlying light-sensitive layer (patent p. 22, step 6).

4. **Release kinetics can change what must be measured.** If the precursor releases
   promptly, precursor and released inhibitor give essentially similar factors.
   If the release linkage significantly retards release, the precursor itself must
   be tested to obtain an accurate factor (patent p. 22, immediately after step 6).

5. **The transport quantity is compound-specific.** Table I reports ten
   representative DIR compounds spanning diffusion factors `0.2`, `0.3`, `0.7`
   and `0.8`, rather than one universal value (patent pp. 23-24, Table I).

6. **The worked coatings separate a formulation variable from a final scan
   correction.** Table II distinguishes samples with 28% versus 70% of their DIR
   population below diffusion factor 0.4. The samples are then scanned and their
   unwanted dye absorptions and chemical interimage effects are removed by
   film-dependent transforms before displayed-noise comparisons (patent pp. 27-30,
   Table II and “Evaluations of Samples”). Tables V-VII report lower displayed
   signal deviations for invention Sample 104, but the patent does not isolate a
   single cross-layer coefficient as the cause (patent pp. 31-32).

### Bounded inferences

1. A fixed 3x3 matrix can be an **empirical end-to-end correction or local
   approximation** for a specified exposure and process state. It cannot, on this
   evidence, be called the physical diffusion factor itself. The patent's factor is
   a measured ratio of density suppressions in a defined coating/process assay,
   while the final scan transform also absorbs dye spectral overlap and chemical
   interimage effects.

2. Any mechanistic DIR surrogate needs at least enough freedom to distinguish
   **release timing/precursor identity** from **transport/adsorption at a receiver
   or sink**. This follows from patent p. 22 plus the compound spread in Table I.
   It does not establish that a particular reaction-diffusion equation, kernel, or
   number of parameters is correct.

3. The new patent is consistent with V21's development-domain placement and with
   treating current receiver/causer values as bounded phenomenological priors. It
   does not validate their magnitudes, signs, spatial scales, or record ordering.

### Model candidate hypotheses for a future experiment

1. **Local-linear hypothesis:** over a restricted midscale range under a fixed
   ECN-2 process, the net receiver-density change from each colour-separation
   exposure can be approximated by one constant cross-record coefficient.

2. **State-dependent alternative:** the effective coefficient changes with source
   exposure because inhibitor release, adsorption/sinks, and remaining developable
   sites change with development state.

3. **Transport-scale alternative:** a high-contrast colour-separation edge will
   yield a record- and density-dependent inhibition spread rather than one shared
   lateral kernel.

These are candidates only. No experiment was run and no model was changed.

### Still unknown

- The identity, concentration, release linkage, layer placement, and diffusion
  factor of any DIR compounds actually used in 5279.
- Whether the patent's direct-scanning, largely unmasked, C-41 examples share any
  DIR formulation with 5279. No such equivalence is claimed.
- How the patent's C-41 assay transfers numerically to ECN-2 time, temperature,
  gelatin swelling, layer thickness, rem-jet-backed motion-picture construction,
  or Status-M measurement.
- The lateral diffusion length, cross-layer path, and fast/medium/slow receiver
  dependence in 5279.
- Whether a fixed matrix is adequate within a deliberately narrow operating range;
  the patent neither proves nor disproves that engineering approximation.

## Potential relation to the existing model

The current V21 research rationale should retain its evidence boundary: the
development-domain release/transport/receiver structure is physically motivated,
but its numerical receiver/causer matrix is not a measured 5279 diffusion matrix.
The new evidence strengthens that wording because it supplies a Kodak-defined
transport assay and shows that release kinetics and inhibitor identity matter.
It does not authorize any implementation or parameter change in this run.

## Falsifiable future experiment design

Use fresh 5279 exposed with registered neutral and single-colour step wedges plus
high-contrast single-colour edges, all processed in one controlled ECN-2 laboratory
run with replicate strips and measured process-control variation. Measure red,
green and blue Status-M density for each step and the cross-edge density profiles.

1. Estimate neutral and colour-separation local gammas at matched source densities.
2. For every causer/receiver pair, fit one coefficient on a pre-registered midscale
   subset only.
3. Hold out lower and higher exposure steps and edge profiles.
4. Quantify repeatability from replicate strips before judging model residuals.

**Support condition for the local-linear hypothesis:** held-out receiver-density
residuals show no systematic trend with exposure and coefficient variation across
replicates is no greater than twice the independently measured repeatability.

**Denial condition:** a monotonic exposure-dependent residual exceeds three times
repeatability in any record pair, or edge-spread width changes systematically with
source density/record after scanner MTF is independently bounded. Either result
rejects one fixed coefficient or one shared lateral kernel over that tested range.

This experiment could estimate net 5279 interimage behaviour. It still would not
identify a patent-style molecular diffusion factor without custom receiver/sink
coatings analogous to the Lippmann-emulsion assay.

## Conclusion

### Confirmed

- Kodak defined a reproducible DIR diffusion-factor assay based on density
  suppression transmitted through an adsorbing overcoat.
- The measured factor is inhibitor/precursor dependent; representative values in
  the patent span 0.2-0.8, and delayed release changes the required assay object.

### Denied

- The strong interpretation that a universal fixed cross-layer coefficient, or
  the present 3x3 receiver/causer matrix, is itself a measured 5279 physical
  diffusion constant is not supported and should be rejected.

### Still unknown

- All stock-specific DIR chemistry and numerical transport parameters for 5279,
  including their ECN-2 dependence and lateral scale.

## Next highest priority

Search Kodak motion-picture patents, ECN-2 technical publications, and SMPTE
papers for a colour-separation experiment that reports interimage density changes
or DIR transport under an ECN-2 process. The target is a motion-picture-specific
measurement, not another generic DIR mechanism description.
