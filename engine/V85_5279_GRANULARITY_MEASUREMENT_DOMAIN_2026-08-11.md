# V85 - 5279 granularity measurement-domain re-audit

Date: 2026-08-11
Status: source trace confirmed; measurement interpretation narrowed; no image change

## Why this audit was necessary

V84 kept Kodak's three 48 micrometre marginal density RMS curves fixed while
varying a legal shared-event family.  On one real RAW crop, the blue-record RMS
was approximately 3.86 times red and 2.59 times green.  Sharing events reduced
opponent-colour RMS, but increased luminance and total RGB grain.  Before doing
anything else with covariance, V85 re-opened the source graph and asked four
more basic questions:

1. Were the red, green and blue paths assigned correctly?
2. Was the printed `0..4` horizontal axis correctly mapped to engine log
   exposure `-4..0`?
3. Does the granularity graph belong in Status-M density space?
4. Does the engine preserve that coordinate, or incorrectly treat the three
   values as display RGB or isolated silver-halide layers?

The answer is that the source trace and the V61+ Status-M coordinate are
correct.  The unresolved problem is the unpublished joint noise law, not a
swapped legend or a four-stop axis error.

## Source recovery and visual inspection

The source is Eastman Kodak, *KODAK VISION 500T Color Negative Film 5279 /
7279*, H-1-5279t, March 2003, graph F002_0269AC:

<https://static1.squarespace.com/static/5790488dbe65943e37169f37/t/57ab931e29687fe82091402d/1470862111007/KODAK%2B500T.pdf>

The retrieved file has SHA-256
`f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8`,
identical to the source used by V50-V52.  V85 rendered and visually inspected
printed pages 3 and 4, then read the vector objects directly.  The public PDF is
not redistributed in this repository; the reproducible audit accepts a
caller-supplied copy and rejects any other SHA.

The combined graph on printed page 4 contains two different sets of paths:

- the upper rising paths are companion characteristic curves;
- the lower paths, labelled `B`, `G`, and `R` at the left, are the diffuse RMS
  granularity curves read against the logarithmic Sigma-D axis at the right.

The lower red path is split into three PDF objects around its narrow maximum.
Treating Bezier control points as samples would bias that maximum, so V85
evaluates the cubic segments explicitly.  The locked object groups are:

| record | PDF curve objects |
|---|---:|
| Red | 5, 6, 7 |
| Green | 0 |
| Blue | 3 |

All twelve printed Sigma-D tick marks are fitted in log space.  Their coordinate
residual is `0.45954` PDF points, reproducing V50's approximately two-percent
graphical reading boundary.

## Result 1: V50's numerical trace is correct

The independently reproduced vector values differ from
`data/5279_granularity_trace_2003.csv` by at most `2.885e-6 D`, or `0.0152%`.
That small difference is curve-flattening and printed-coordinate precision,
not a material discrepancy.  The active V72 profile closes to the new trace
within the same bound.

Therefore:

- the red, green and blue path assignment is retained;
- the large blue-record marginal is present in Kodak's graph;
- it must not be relabelled, divided down, or replaced by a prettier value.

The labels describe red-, green-, and blue-filtered **microdensitometer
measurements**.  They do not mean display RGB, and they are not direct isolated
measurements of three microscopic silver-halide populations.

## Result 2: the horizontal exposure mapping is correct

The page-4 graph prints relative log exposure `0..4`; the page-3 Status-M
sensitometric graph prints log exposure `-4..0`.  V85 samples the three page-4
companion characteristic curves, translates only the horizontal coordinate by
four log units, and compares them with the page-3 vector trace.

| record | RMS density difference | maximum absolute difference |
|---|---:|---:|
| Red | 0.01261 D | 0.02284 D |
| Green | 0.01134 D | 0.01791 D |
| Blue | 0.01089 D | 0.01637 D |

Those curves agree closely after the translation.  The residual is also
consistent with Kodak's explicit page-4 footnote that sensitometric and diffuse
RMS curves were produced on different equipment and can differ slightly in
shape.  The engine's `graph 0..4 -> internal -4..0` mapping is retained.

## Result 3: Status M is the correct measurement domain

Kodak's 5279 sheet states that the samples were tungsten-exposed, ECN-2
processed, and that diffuse RMS was read with red, green, and blue
microdensitometer responses through a 48 micrometre aperture.  The granularity
paragraph itself does not repeat the words `Status M`, so V85 checked the
measurement standard rather than inferring it from graph proximity.

ISO 10505:2009, sections 4.3.3 and 4.2.6, states that:

- spectrally selective colour negative films use ISO 5-3 Status-M spectral
  products for RMS-granularity measurement; and
- the circular efflux aperture at the specimen is `48.0 +/- 0.5 micrometres`.

Primary reference:
<https://www.iso.org/standard/50747.html>

The 2009 standard postdates the sheet, but V61 already versions the unchanged
ISO 5-3 Status-M spectral products from the 1984 table.  A current Kodak
technical description independently confirms that RMS granularity is obtained
by scanning uniformly exposed steps with a 48 micrometre microdensitometer and
plotting Sigma-D against relative log exposure:

<https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-2242-3242-5242-technical-information.pdf>

V61+'s negative coordinate is therefore correct in kind: it jointly inverts
the complete Status-M readings through D-min and all three net dye/masking
spectra.  It does not independently equate red density with cyan amount, green
density with magenta amount, and blue density with yellow amount.

## What this does and does not prove

The official curves identify three diagonal entries of the 48 micrometre
Status-M density covariance:

\[
\mathrm{diag}(\Sigma_D)=
\left(\sigma_R^2,\sigma_G^2,\sigma_B^2\right).
\]

They do not publish the three off-diagonal terms, their spatial-frequency
dependence, or higher-order joint tails.  A colour observer sees

\[
\mathrm{Var}(w^T D)=w^T\Sigma_Dw,
\]

so fixing the three official marginal curves cannot determine visible
luminance grain or opponent-colour grain.

The broader literature supports using a noise-power spectrum and dye-cloud
morphology rather than a cosmetic overlay.  For example, Stephenson and
Saunders synthesize grain from a measured NPS and show a two-scale 6.5/15
micrometre example:

<https://diglib.eg.org/bitstreams/372ec0ad-ff80-497b-81b0-2dd8d7021e48/download>

Those radii are an example fit, not 5279 measurements.  Kodak's 1995 dye-cloud
work likewise links cloud diffusion, MTF, NPS and granularity, but does not
publish a 5279 three-record cross-spectrum:

<https://doi.org/10.1080/00223638.1995.11738635>

No retrieved primary source supplied a numerical EK5279 cross-record
covariance or cross-power spectrum.  Absence from this search is not proof that
no proprietary measurement ever existed; it is the present public-evidence
boundary.

## Code audit and decision

The executable audit is:

```bash
PYTHONPATH=engine/src python3 \
  engine/src/audit_v85_5279_granularity_measurement_domain.py \
  /path/to/KODAK_500T_5279_2003.pdf \
  engine/research_runs/v85_5279_granularity_measurement_domain_audit.json
```

It verifies the PDF hash, required source wording, graph paths, Bezier
evaluation, all twelve Sigma-D ticks, page-3/page-4 H-D agreement, versioned
CSV, and the active V72 mapping.

Decision:

1. Keep the V50 marginal curves.
2. Keep the four-log-unit horizontal translation.
3. Keep V61's joint ISO Status-M inverse.
4. Do not reduce blue-record RMS by taste.
5. Do not promote a shared-event alpha without a joint measurement.
6. V72 remains the image release; V85 changes no pixels.

The next defensible step is to derive observer-space **bounds** from all
physically legal Status-M covariance matrices and the local V61 spectral
Jacobian.  That can reveal which visible grain properties are identified and
which remain free, without pretending that one aesthetically pleasing
correlation matrix is measured 5279.
