# 2026-08-03 research run: ISO Status-A spectral product and 2383 interimage isolation

## Outcome

The densitometer-response hypothesis was **falsified**. Replacing an assumed
filter response with the ISO 5-3:2009 Status-A 10 nm standard-density weighting
factors does not explain Kodak 2383's simultaneous-neutral DLE trajectory.
Combining those exact weights with the published 2383 CMY spectral dye curves
and the archived separated-light characteristic curves gives a blind odd-step
RGB RMSE of `0.18155 D`, nearly eight times worse than the preceding empirical
full-RGB holdout (`0.02287 D`).

More decisively, the parameter-free spectral model predicts red density above
blue at every tested step. At patent step 7 it predicts `R-B=+0.20583 D`, while
the measured patent trace is `-0.07322 D`. The missing sign reversal therefore
cannot be attributed to using approximate Status-A filter centres. It requires
print-stock behaviour absent from the three published principal curves, most
plausibly the exposure-dependent interimage response that Kodak's own workflow
patents require laboratories to measure separately.

V21 remains the production baseline. No V22, production algorithm change,
formal master, site change, Git commit, Sites version or deployment was made.

## Sources and evidence boundary

1. **ISO 5-3:2009, Table 9 and Annex B.** The standard defines Status-A
   density from spectral transmission and supplies 10 nm abridged weighting
   factors whose per-channel sums are 100. It explicitly distinguishes
   spectral products used to specify filter instruments from weighting factors
   used to compute density from spectral data. The standard remains current
   after its 2025 confirmation. Official record:
   <https://www.iso.org/standard/52915.html>.
2. **Kodak H-1-2383t, March 2005, page 5.** The archived sheet supplies vector
   red-, green- and blue-exposure principal Status-A characteristic curves for
   2383/ECP-2D. These are separated-light curves and do not report the two
   secondary Status-A readings for each exposure. Archived copy:
   <https://www.archives.gov/files/preservation/products/resources/2383-TI.pdf>.
3. **Kodak H-1-2383 spectral dye-density graph.** The CMY curves are
   representative, peak-normalized graph data rather than product
   specifications. Current official sheet:
   <https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf>.
4. **Kodak/IMAX US 6,987,586 B2, Figure 3.** This supplies the independent
   seven-point portion of a 21-step simultaneous-neutral 2383 Status-A DLE
   series, including the red/blue sign reversal and official LAD point:
   <https://patents.google.com/patent/US6987586B2/en>.
5. **Kodak US 2002/0118211 A1.** Kodak states that print-film interimage
   correction must be measured by stepping one colour while uniformly exposing
   the other two, reading all three Status-A channels, converting them to
   analytical density, and observing whether the nominally constant dyes move.
   A correction matrix is then applied if needed:
   <https://patents.google.com/patent/US20020118211A1/en>.
6. **US 8,654,192 B2.** A later analytical film-preview workflow places a 3x3
   interimage matrix in log print exposure before the positive-film
   characteristic curves, anchors it around LAD, and fits it to measured
   DPX-to-theatre-Lab patches. The document confirms model placement, but does
   not publish the 2383 matrix or measurement set:
   <https://patents.google.com/patent/US8654192B2/en>.

## Method

The ISO Table 9 values were copied at 10 nm from 340 to 770 nm in B/G/R order,
then reordered to R/G/B. Their numerical sums are
`100.000 / 100.001 / 99.999`, consistent with the standard's rounding note.
The Kodak 2383 CMY dye curves were linearly interpolated from the existing
20 nm graph digitization to the ISO grid.

For dye amounts `a=(c,m,y)`, spectral density and Status-A density were
computed as:

```text
D(lambda) = c*C(lambda) + m*M(lambda) + y*Y(lambda)
T(lambda) = 10^(-D(lambda))
D_A,k = -log10( sum_lambda[T(lambda) W_k(lambda)] / sum_lambda[W_k(lambda)] )
```

For each archived separated-light curve, its principal net Status-A density
was inverted through the appropriate single-dye spectral model to recover a
dye-amount curve. Three exposure offsets were solved only at the official LAD
point `1.09/1.06/1.03`; this is the necessary printer-light balance, not an
off-LAD trajectory fit. The same relative exposure was then added to all three
balanced offsets, their dye amounts were combined spectrally, and the resulting
Status-A triplets were compared to the patent target at matched mean density.

No empirical cross-talk strength, neutral-trajectory LUT or patent-step fit was
used. Even steps 2/4/6/8 and blind odd steps 3/5/7 are reported separately for
continuity with previous experiments, although this model was fit only at LAD.

## Results

| metric | ISO spectral model | preceding empirical RGB holdout |
|---|---:|---:|
| all-point RGB RMSE | `0.18225 D` | `0.01706 D` |
| even-step RGB RMSE | `0.18277 D` | `0.01081 D` |
| blind 3/5/7 RGB RMSE | `0.18155 D` | `0.02287 D` |
| blind maximum error | `0.32595 D` | `0.03842 D` |
| step-7 R-B | `+0.20583 D` | target `-0.07322 D` |

The model reproduces the official LAD point to numerical precision, so the
failure is not a printer-balance error. It is an off-LAD trajectory and sign
failure. The largest discrepancies show red too high and blue too low in the
dense portion of the scale, exactly the behaviour that a missing interimage
term can alter.

## Release decision

The density gate fails decisively, so no RAW render is justified. Running a
costly visual A/B after a seven-to-eight-fold blind-density regression would
only test a model already rejected by independent evidence. Production files,
V21 masters and the scan branch remain untouched.

This run establishes a stronger boundary than the preceding hard-dye test:
the exact standardized densitometer weighting is now known and still cannot
recover the 2383 neutral trajectory from principal curves. Further changes to
the hard-dye matrix, filter centres or dye-scale normalization cannot identify
the missing chemical behaviour.

## Next priority

Do not add more free dye or densitometer parameters. Search for either:

1. the actual three-channel measurements from a 2383 separated-exposure plus
   two-colour-uniform-exposure experiment; or
2. measured DPX-to-theatre-Lab patches from a period 2383 workflow that can
   identify the LAD-anchored log-exposure interimage matrix described by
   US 8,654,192.

The neutral DLE identifies only the three row sums of such a matrix, not its
off-diagonal colour behaviour. Therefore a matrix fitted only to the neutral
patent curve must not be treated as a validated saturated-colour model.

## Reproducible artifacts

- `research_runs/2026-08-03_status_a_spectral_product/run_holdout.py`
- `research_runs/2026-08-03_status_a_spectral_product/metrics.json`
- `research_runs/2026-08-03_status_a_spectral_product/status_a_spectral_holdout.png`

The script passes Python bytecode compilation and strict JSON output. SHA-256:

- script: `6d1f02aad74fd47eea6ece2d3fa5925e74df172d7a68dc45199d9ba424ea4cca`
- metrics: `596898e0b9df02c1a6f061a9284d12524130fb4946dab16c6f392f7cebd49d28`
- plot: `343b8fa1ea089a692f172fe32bd3b781449ea425af3472f1529e49c23531f0b5`
