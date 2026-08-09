# 2026-08-03 research run: Digital LAD cannot identify the 2383 interimage matrix

## Outcome

The hypothesis that Kodak's published Digital LAD material is sufficient to
identify a 3x3 2383 log-exposure interimage matrix is **falsified**.

Kodak H-387 provides a neutral recorder scale and the official Digital LAD DPX
contains six saturated input patches. However, neither the guide nor the image
provides the processed-2383 Status-A triplets or theatre-Lab measurements for
those colour patches. US 8,654,192 B2 explicitly requires such DPX-to-theatre-
Lab pairs, distributed across the input cube and including saturated hues, to
fit its LAD-anchored matrix.

Two bounded counterexample matrices were tested. Both reproduce all twelve
published H-387 neutral code triplets with maximum log-exposure error of zero
within floating-point precision, yet they differ by as much as `0.09712` log
exposure on the official colour patches and by `0.02509` in projected OKLab.
On frame 144 of the original GH7 12-bit ProRes RAW, the two full projection
renders differ at median/P95/P99 OKLab distances of
`0.002886 / 0.008971 / 0.025765`. The scan/Blu-ray branch is bit-identical.

Neither counterexample is a 2383 measurement, so neither may replace V21. No
V22, production code change, formal master, formal screenshot, site change,
Git commit, Sites version or deployment was made.

## Research question

Do Kodak H-387's neutral Digital LAD scale and the official Digital LAD test
image uniquely identify the LAD-anchored 3x3 2383 log-exposure interimage
matrix described by US 8,654,192 B2?

This question is falsifiable: if the published data identified the matrix, two
distinct bounded matrices could not fit all published constraints exactly while
giving different predictions on the same official inputs.

## New and rechecked primary evidence

1. **Kodak H-387, pages 1-5, revised December 2011.** It publishes neutral
   Digital LAD calibration tables, maps 10-bit Cineon/DPX code to printing
   density as `0.002 * code value`, and specifies a `445/445/445` Digital LAD
   patch. It instructs the lab to print that patch to 2383 Status-A
   `1.09/1.06/1.03`, but it does not publish colour-patch output aims.
   <https://www.kodak.com/content/products-brochures/Film/Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf>
2. **Official KODAK Digital LAD Test Image, DPX format.** The Kodak-hosted ZIP
   was downloaded and hashed. Its 2048x1556 10-bit DPX contains six input
   patches with exact RGB codes:

   | patch | R | G | B |
   |---|---:|---:|---:|
   | red | 700 | 93 | 93 |
   | green | 93 | 700 | 93 |
   | blue | 93 | 93 | 700 |
   | cyan | 93 | 700 | 700 |
   | magenta | 700 | 93 | 700 |
   | yellow | 700 | 700 | 93 |

   ZIP:
   <https://www.kodak.com/content/products-zip/KODAK-Digital-LAD-Test-Image-DPX-Format.zip>.
   ZIP SHA-256: `7cce3ca613ba36b97e9c5229631fd42c30fca49a5c1fb6695aa7a677df2ec0ad`.
   The 2K DPX SHA-256 is
   `eae1f09586567bbf20f825df1911b0e0348c047138bd84fdd9c63ee1b789dddb`.
3. **US 8,654,192 B2, Figure 14 discussion.** The matrix is placed in log
   exposure around an LAD offset:

   ```text
   log adjusted exposure = M * (log captured exposure - LAD exposure)
                           + LAD exposure
   ```

   The patent says the matrix can begin at identity, describes an initial
   coordinate-search increment such as `0.08`, and requires measured pairs that
   map DPX triplets to projected theatre Lab. It specifically says input points
   should span the space and may include several saturated hues. It does not
   publish the fitted 2383 matrix or those measurements.
   <https://patents.google.com/patent/US8654192B2/en>
4. **US 2006/0181721 A1, paragraphs corresponding to the DPX/2383 TRC
   construction.** It maps DPX 445 to 2383 green Status-A `1.06`, states the
   `0.002` density-per-code relation, and notes that three separate RGB TRCs
   require gray-balance compensation. It provides a preview construction, not
   the missing saturated-colour measurement set.
   <https://patents.google.com/patent/US20060181721A1/en>

## Facts, assumptions and unknowns

### Documented facts

- H-387's numerical calibration tables are neutral triplets only.
- The official DPX supplies saturated **input** codes but no corresponding
  processed-film or projected output aims.
- The patent's matrix is applied in log exposure about LAD.
- The patent fits that matrix to measured DPX/theatre-Lab pairs and calls for
  saturated hues.

### Model assumptions used only for the falsification test

- The two cyclic matrices use the patent's example `0.08` initial search
  increment:

  ```text
  clockwise = [[0.92, 0.08, 0.00],
               [0.00, 0.92, 0.08],
               [0.08, 0.00, 0.92]]

  counterclockwise = [[0.92, 0.00, 0.08],
                      [0.08, 0.92, 0.00],
                      [0.00, 0.08, 0.92]]
  ```

- Both have row sums of one, so every neutral departure `s*[1,1,1]` remains
  exactly neutral. They are mathematical counterexamples, not estimates of
  Kodak chemistry.
- The published code-density relation is used to express each DPX code around
  the 445 LAD anchor. The existing V21 2383 curves and spectral projection are
  used only to show how the ambiguity propagates; they do not supply a target.

### Still unknown

- The actual 2383 interimage matrix for a period 5279/DI/2383 workflow.
- The processed Status-A or projected Lab values of Kodak's six Digital LAD
  colour patches.
- Batch, process, printer-light, recorder-stock, flare and theatre dependencies
  of any such matrix.

## Controlled experiment

### Digital LAD identifiability gate

The twelve H-387 neutral code values
`0, 22, 95, 200, 445, 520, 685, 800, 900, 968, 1000, 1023` were expanded to
RGB triplets and mapped around the official LAD exposure. Identity, clockwise
and counterclockwise matrices all reproduce the entire scale:

| model | maximum neutral log-exposure error |
|---|---:|
| identity | `0.0` |
| clockwise 0.08 | `0.0` |
| counterclockwise 0.08 | `2.22e-16` |

The clockwise/counterclockwise pair then predicts the following model-to-model
OKLab distances for the official Digital LAD input patches:

| red | green | blue | cyan | magenta | yellow | mean | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `0.00942` | `0.00740` | `0.01390` | `0.02223` | `0.01826` | `0.02509` | `0.01605` | `0.02509` |

This does not say either prediction is correct. It proves the published neutral
constraints cannot select between them.

### Original RAW A/B

- input: `/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV`;
- source: `5760x4320`, ProRes RAW HQ, `12-bit`;
- frame: `144`, chosen previously as the highest-mean 2383-density frame in a
  sparse inventory;
- decode: AVFoundation extended-linear BT.2020 float32;
- controlled render: `1440x1080`, `+0.45` stop, identical V21 frame-index seed;
- changed variable: only the research 3x3 matrix in the 2383 log-exposure
  path, plus mandatory re-solving of the neutral 1D shaper;
- held fixed: V-Log/ProRes RAW semantics, 5279 development-domain DIR,
  record-specific dye-cloud site population and grain, printer spectrum, 2383
  curves and dyes, Callier term, xenon observer, flare, V21 viewing/H-61/monitor
  caches and the independent scan branch.

Pairwise clockwise versus counterclockwise metrics:

| metric | result |
|---|---:|
| linear RGB MAE | `0.00163854` |
| PSNR | `50.53 dB` |
| OKLab median / P95 / P99 | `0.002886 / 0.008971 / 0.025765` |
| 95th-percentile absolute luma delta | `0.002210` |
| changed 8-bit pixels | `86.78%` |
| exact-black pixels | `1.20448% -> 1.21508%` |
| candidate high-clipped channel samples | `0.000193%` |

Manual review of the A/B finds no coarse-grain change or broad global cast.
The magnified difference reveals coherent green/cyan and magenta redistribution
in foliage, the tabletop, coloured paper and bright edges. That is exactly the
kind of hue-dependent change the missing measurements must adjudicate. The
ordinary A/B does not provide a stable preference.

The Cineon/2K/Blu-ray render is bit-identical under both matrix settings:
linear maximum difference `0.0`, OKLab P99 `0.0`, changed 8-bit pixels `0.0%`.
This verifies that the test did not leak the print hypothesis into the scan
branch.

## Release decision

**Reject both matrices; keep V21.**

The experiment finds an identifiable ambiguity, not an improved emulsion. The
two matrices meet the same published neutral evidence yet disagree on colour,
and there is no independent processed-patch target, theatre-Lab set or measured
5279-to-2383 separation series to choose between them. Selecting either by
appearance would be arbitrary colour grading, precisely the kind of subjective
drift excluded by the release gate.

Therefore no new algorithm, version number, master video, formal screenshot,
Changelog, site commit, saved Sites version or private deployment is justified.
V21 and owner-only Sites production version 2 remain current at
<https://emulsion-5279.skylab.chatgpt.site>.

## Next priority

Search for a genuine measurement set rather than another neutral-only proxy:

1. period DPX input triplets paired with projected theatre CIE Lab/XYZ from a
   2383 workflow;
2. processed Status-A triplets for the official Digital LAD six colour patches;
3. a 2383 experiment stepping one exposure while holding the other two uniform
   and reading all three channels.

If none can be recovered, design a future physical 2383 wedge measurement plan
with instrument geometry, printer-light spectrum, ECN-2/ECP-2 process control,
LAD anchoring and xenon projection recorded explicitly. Do not infer a 3x3
matrix from neutral curves alone.

## Reproducible artifacts

- `research_runs/2026-08-03_digital_lad_identifiability/run_identifiability.py`
- `research_runs/2026-08-03_digital_lad_identifiability/metrics.json`
- `research_runs/2026-08-03_digital_lad_identifiability/digital_lad_identifiability.png`
- `research_runs/2026-08-03_digital_lad_identifiability/ab_clockwise_vs_counterclockwise_frame144.png`
- `research_runs/2026-08-03_digital_lad_identifiability/difference_x12_clockwise_vs_counterclockwise_frame144.png`

The script passes bytecode compilation and the metrics file passes strict JSON
parsing. No file under `sources/` was touched.
