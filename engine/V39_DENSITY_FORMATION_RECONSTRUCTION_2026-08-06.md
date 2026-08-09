# V39 density-formation reconstruction

Date: 2026-08-06
Status: **withdrawn as a viewing baseline** · structural gates passed but the
visible colour-covariance/tail contract was incomplete

## Erratum: isolated primary-colour grain

Native-resolution dark-region inspection exposed sparse red, green and blue
impulses in both V39 observers, with the projection branch most severe. This is
not accepted as 35 mm colour grain. The original gates measured marginal
R/G/B density RMS and conditional mean, but did not measure cross-record
covariance, kurtosis or delivered high-frequency opponent-colour tails.

Three V39 assumptions are therefore withdrawn:

1. Kodak's published diffuse RMS is a post-process density measurement; it does
   not identify a pre-DIR source-layer amplitude or its inverse chemistry.
2. Moving the negative to density space does not justify bypassing the
   observer's high-frequency opponent-colour integration.
3. The public 2383 data do not identify independent per-record Poisson grain,
   its covariance or its exposure-dependent amplitude.

V40 retains density-domain MTF and signed RAW record formation, restores the
published post-process RMS boundary and conservative observer integration, and
withholds the extra 2383 stochastic term. A new native delivered-image gate
measures dark-region primary tails and opponent/luma high-pass energy.

## Decision

V39 is a structural correction, not a grade. V38 colour authority,
sensitometric curves, black decisions, gamma and dual delivery remain frozen.
The change is that the negative and print are now reconstructed in the physical
variables in which Kodak measures their image structure:

\[
D(x,y,\lambda)=-\log_{10}T(x,y,\lambda).
\]

The V38 graph rendered two positives, subtracted them, filtered the mean and
then re-added a display residual. V39 instead forms one realized negative:

\[
D_{5279}^{\mathrm{real}}=
\operatorname{MTF}_{5279}(D_{5279}^{\mathrm{mean}})
+\delta D_{5279}^{\mathrm{sites}}.
\]

The scan and print observers receive that density image directly. The print
branch then forms one realized 2383 density:

\[
D_{2383}^{\mathrm{real}}=
\operatorname{MTF}_{2383}(D_{2383}^{\mathrm{mean}})
+\operatorname{MTF}_{2383}(\delta D_{2383\leftarrow5279})
+\delta D_{2383}^{\mathrm{sites}}.
\]

No V39 print-grain operation multiplies, adds to or ratios a display RGB image.

## Findings resolved

### 1. 5279 MTF was in the wrong domain

The published 5279 MTF is measured on tungsten-exposed, ECN-2 processed film.
V38 applied the fit to a display-linear positive. V39 applies the same fitted
R/G/B transfer to processed negative record density before spectral scanning
or optical printing. Signed edge excursions are retained until the relevant
density observer owns their physical boundary.

### 2. Granularity normalization occurred after stochastic chemistry

V38 multiplied the fully combined post-DIR residual by the Kodak 48-micrometre
RMS target. That meant inhibitor coupling never saw a correctly scaled chemical
event. V39 applies the published-amplitude constraint to developed source-record
dye yield before stochastic DIR/interimage transport. Destination spectral
record mixing is included in the predicted aperture variance.

At 18% neutral in the synthetic release gate, the V39 measured R/G/B density
RMS is 0.006135 / 0.008985 / 0.033836 versus official-curve targets
0.006144 / 0.008974 / 0.033930. Relative errors are below 0.3%.

This does **not** identify Kodak's unpublished coating recipe. Large inferred
yield factors remain evidence that the public H-D and RMS curves do not uniquely
determine grain counts, clustering and layer chemistry. V39 fixes the order of
operations and keeps the official observable exact; it does not relabel an
underidentified latent recipe as measured fact.

### 3. 2383 MTF and grain were display operations

V38's final print-grain term was a monochrome display-luminance ratio. V39 gives
each 2383 colour record an independent finite Poisson dye-cloud realization in
Status-A density. The print MTF acts on print density before xenon projection,
the monitor proof and the display transfer.

The new 2383 density entry is regression-checked against the old analytical
wrapper: when supplied with the same unfiltered print density, maximum absolute
output difference is exactly 0.0. Therefore the observer is unchanged; only
the placement of spatial structure changes.

The public 2383 documents used here do not publish enough exposure-conditioned
record granularity data to identify an exact print-population amplitude. The
print term is explicitly subordinate and evidence-bounded rather than tuned to
make the image look grainier.

### 4. Wide-gamut negative basis values were clipped too early

Apple's Standard ProRes RAW decoder supplies extended-linear BT.2020/D65. The
BT.2020-to-film-basis matrix can legitimately produce signed basis components
for saturated or very dark pixels. V38 clipped those components before the
three 5279 record sensitivities combined them. V39 preserves the signed basis,
forms the physical record exposures, then clamps those exposures once at zero.

This is a gamut-basis boundary correction, not white balance. It is expected to
affect a small subset of saturated/deep-shadow pixels and must not be used as a
global green/magenta trim.

### 5. Profile parameters had two ownership leaks

- V37 documented a 0.38-native-pixel stable phase radius but its `apply()` did
  not own the assignment. V37 and descendants now set it explicitly.
- The production renderer read the projection crossover sigma from a hardcoded
  V31 module. It now reads the active profile.
- V38 now explicitly restores Archive domain switches, so V39→V38 profile
  switching in one interpreter is idempotent.

### 6. The accurate print path exposed duplicate computation

The first 5760×4320 V39 T031 probe took 73.53 seconds per source frame for both
masters. Profiling showed that the monitor calibration evaluated the same
analytical 2383 projection twice. V39 now reuses the first result, precomputes
the scan-reference density once, and shares deterministic negative/scanner
intermediates between the two production observers. Regression tests give a
maximum pixel error of 0.0 for each optimization.

The second probe fell to 63.26 seconds per frame. The fully shared formal
T002/T007/T031 renders completed 72 native 5760-by-4320 frames and both observer
families in 4251.82 seconds before hashes and delivery finalization, or 59.053
seconds per source frame. Their individual render times were 1372.71, 1381.41
and 1497.69 seconds. Decoder, encoding and file writing remain a small fraction;
the analytical observer is dominant. This remains slower than V38 because V39
evaluates the analytical observer after spatial print formation instead of
sampling the old pointwise 193³ negative-to-output cache. Quality has priority;
no first-order or lower-resolution shortcut is accepted for the release.

The final delivery audit exposed one more V38-era boundary: independently
compressing the BT.1886 and sRGB copies was no longer transparent once V39
carried fine projection-density structure. V39 now treats the encoded 12-bit
BT.1886 master as picture authority, decodes that actual file back to reference
light, and derives the Mac sRGB companion from it using 12-bit ProRes 4444 XQ.
Across all three scenes, the worst mean per-channel light disagreement is
0.001092; every branch passes the 0.0015 gate. JPEG and web motion are decoded
only from this master-derived companion. Delivery finalization (companion,
source PCM/timecode and hashes) added 137.15 seconds across the three scenes;
the complete summed processing time was 4388.97 seconds.

## What is deliberately not claimed

The following remain empirical observer/calibration boundaries because the
public documents do not identify them uniquely:

- exact 5279 rem-jet scatter and camera-side halation;
- separation of GH7 sensor noise from film granularity without a calibrated
  dark/gray/ColorChecker capture;
- exact Spirit 2K spectral sensitivities and period scanner processing;
- Kodak's internal DIR/interimage transport coefficients;
- exposure-conditioned 2383 record granularity and interimage response;
- projector Callier effect, auditorium flare and xenon spectral variation;
- a specific Blu-ray restoration, grading and compression history.

The released “projection” remains a normal-process Rec.709 monitor proof whose
low-frequency colour boundary is scan-referenced. The physical 2383 projection
functions remain separately available. This is recorded as an observer model,
not misrepresented as a measurement of a particular theatre or scanner.

## Frozen constraints

- 5279 H-D, dye spectra and Kodak 48-micrometre diffuse RMS targets;
- V37 temporally stable 45-class integration phase;
- normal ECN-2 / ECP-2D, with no retained-silver or bleach-bypass term;
- V38 scan/projection colour authority and final low-frequency adapter;
- scan and projection black decisions;
- display-linear observer boundary;
- 12-bit ProRes 4444 BT.1886 reference master and master-derived 12-bit ProRes
  4444 XQ sRGB QuickTime companion;
- comparison windows T002 0–23, T007 276–299 and T031 132–155.

## Release gates

1. Profile V39→V38 reset is deterministic.
2. 5279 18% neutral R/G/B 48-micrometre RMS error is below 1%.
3. Old and new 2383 analytical entry points are pixel-identical before spatial
   print formation.
4. 2383 density grain has less than 0.0001 D conditional mean bias per record.
5. Physical record exposure is never negative after the signed-basis transform.
6. Neutral black-to-white scan transfer remains V38-identical.
7. Projection deterministic differences are attributable to density-domain MTF
   and removal of the 193³ pointwise observer approximation, not a grade.
8. Both master and QuickTime files are 5760×4320 yuv444p12le; the professional
   master is ProRes 4444 and the master-derived sRGB companion is ProRes 4444
   XQ, with complete colour metadata and mutually consistent display light.
9. All three matched 24-frame windows complete without duplicate sampler IDs,
   decoder short reads, non-finite pixels or encoder failure.

Machine-readable structural gates are produced by
`src/audit_v39_density_reconstruction.py`.

## Primary references

- `references/kodak_5279_H-1-5279t.pdf`, image-structure and spectral-dye
  sections, especially pages 3–4.
- `references/kodak_2383_H-1-2383.pdf`, Status-A characteristic curves and
  spectral-dye-density sections.
- `references/kodak_E58_print_grain_index.pdf`, granularity, MTF, magnification
  and perceived print-grain discussion, especially pages 1–3.
- `references/kodak_H61_LAD_color_analyzer.pdf`, LAD aims and laboratory
  printer/analyzer calibration boundary.
- `references/kodak_patent_US5314793_multilayer_speed_granularity.pdf`,
  multilayer speed/granularity architecture; used as a qualitative constraint,
  not as a disclosed 5279 formula.
- Newson, Delon and Galerne, “A Stochastic Film Grain Model for
  Resolution-Independent Rendering,” 2017; spatial point-process reference,
  not a Kodak stock parameter source.
