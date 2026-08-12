# V59 — 2383 Visual Neutral / processed-base spectral correction

Date: 2026-08-11
Status: evidence-backed isolated image revision
Image change from V58: 2383 processed base/D-min spectrum only, with the LAD
spectral inverse recomputed in the corrected coordinate

> **V60 follow-up:** V59 exposed a small mismatch between the residual
> spectrum's integrated Status-A base and the independently plotted H-D D-min.
> V60 preserves this spectral discovery but registers zero dye to each H-D
> minimum. V59 remains reproducible as the isolated discovery step; V60 is the
> internally consistent current profile. See
> [`V60_2383_DMIN_COORDINATE_REGISTRATION_AUDIT_2026-08-11.md`](V60_2383_DMIN_COORDINATE_REGISTRATION_AUDIT_2026-08-11.md).

## Finding

The March 2005 Kodak 2383 dye-density graph contains four vector curves, not
three: cyan, magenta, yellow and **Visual Neutral**. V55 extracted only the
three peak-normalized dye curves. It therefore used a zero spectral base in
projection and represented the published curve minima only as three scalar
Status-A offsets during inversion. That was internally reproducible, but not a
complete reading of the graph.

V59 extracts the fourth vector path and defines

\[
D_{base}(\lambda)=\max\left(D_{visual\ neutral}(\lambda)-
D_C(\lambda)-D_M(\lambda)-D_Y(\lambda),0\right).
\]

The residual is nonnegative at all 21 runtime wavelengths. Adding it back to
the C/M/Y sum reconstructs the vector-traced Visual Neutral curve to floating
point tolerance. This is the spectral base used both when resolving the
simultaneous H-61B LAD reading and when calculating projected transmission:

\[
T_{2383}(\lambda)=10^{-\left[D_{base}(\lambda)+
\sum_i a_iD_i(\lambda)\right]}.
\]

No display-space colour correction, saturation control or artistic grading was
introduced.

## Source and reproducibility

The authority is Kodak H-1-2383t, March 2005, graph F010_0294AC. The locked
archival PDF and a page-identical mirror were both checked; their graph vector
paths are identical. Runtime samples from 380 through 740 nm come from the
drawn vector path. The 760 and 780 nm values use the disclosed terminal-secant
continuation already used by V55 because Kodak's graph ends at 750 nm.

- Visual-neutral CSV SHA-256:
  `9bc1645f4afe79e01e917dc11c556d671eb2c3b367b884807e010d509bd1e90e`
- V59 193-cube LUT SHA-256:
  `55c7fefe6db0a380e85ce7ea724ceb56f74eca99a95827018229705c9bf17740`
- Reproducer:

```bash
python3 engine/src/extract_2383_2005_spectral_vectors.py \
  /path/to/2383-2005.pdf --output-directory /tmp/2383-vectors
diff -u engine/data/2383_visual_neutral_trace_2005.csv \
  /tmp/2383-vectors/2383_visual_neutral_trace_2005.csv
PYTHONPATH=engine/src python3 engine/src/build_v59_print_lut.py \
  engine/cache/print_2383_monitor_output_lut_193_v59.npy
```

## Numerical closure

V58 and V59 both solve the official simultaneous integral Status-A LAD target
`[1.09, 1.06, 1.03]`; the difference is whether base density is represented as
three scalar offsets or one wavelength-dependent absorption spectrum.

| Quantity | V58 scalar-base approximation | V59 spectral base |
|---|---:|---:|
| Principal R-curve density | 0.9898583 | 0.9925836 |
| Principal G-curve density | 0.8823338 | 0.8840549 |
| Principal B-curve density | 0.8419376 | 0.8475401 |
| Analytical cyan amount | 1.0545850 | 1.0270529 |
| Analytical magenta amount | 1.0300304 | 0.9971411 |
| Analytical yellow amount | 0.9626921 | 0.9746268 |
| Maximum LAD inverse residual | below 1e-7 | below 1e-7 |

The V59 values forward-integrate exactly to the official LAD triplet within
float32 tolerance. Switching back to V58 in the same interpreter restores the
zero-base archive policy; a cache-reset defect found during this audit was also
fixed so no projection or neutral-shaper LUT can leak between profiles.

## Native-frame validation

`NJARAW_S001_S001_T020.MOV`, frame 0, was decoded through the unchanged
AVFoundation extended-linear BT.2020 contract and rendered at 5760 × 4320 in
Archive Exact CPU mode. Both branches were delivered as 12-bit ProRes 4444 XQ.

- all 64 engine, density, Metal-sampler and Wavefront regression tests pass;
- every V59 conformance gate reports true;
- the V58 and V59 decoded scan frames are bit-identical (frame MD5
  `604ead3c60971bb038b8470d5b5492ad`), proving the revision stays in the 2383
  projection branch;
- V58/V59 projection-master PSNR is 67.348 dB and SSIM is 0.999894;
- V59 pipeline compute time was 39.83 s for the native frame (22.01 s negative,
  17.34 s dual observer, 0.48 s encoding), 51.54 s including finalization.

The small visible delta is expected: the current accepted monitor observer
still transfers low-frequency hue/chroma authority from the scan branch. V59
corrects the physical spectrum under that explicitly conservative boundary; it
does not silently adopt V56's fully physical-colour experiment.

## Viewing-illuminant bound

The stored 21-point xenon array was rechecked against the generic xenon-lamp
graph in Kodak's *Essential Reference Guide for Filmmakers*. It is a legitimate
digitization of that generic lamp graph, but it is not a measurement of one
projector's lamp, heat glass, lens and screen.

A 17-cube audit froze all V59 image formation and varied only the viewing SPD,
adapting each open-gate white to D65. Relative to the Kodak generic xenon graph:

| SPD bracket | median OKLab ΔE | p95 | maximum |
|---|---:|---:|---:|
| 5400 K Planck proxy | 0.052 | 0.494 | 0.863 |
| 6420 K Planck proxy | 0.167 | 0.694 | 0.883 |
| Equal energy | 0.108 | 0.396 | 0.497 |

These are uncertainty brackets, not alternative theatre claims. They show that
reasonable white-adapted illuminant choices do not explain the large blue/purple
projection casts seen in earlier versions. The omitted Visual Neutral/base
curve and the low-frequency observer/interimage assumptions are more important.

## Rejected shortcut: published hard-dye matrix as runtime truth

Kodak patent US20020163657A1 publishes a Status-A-to-analytical-dye matrix and
describes physical dye spectrophotometry / DLE calibration. Its printed matrix,
however, produces large negative cross-density terms when inverted and is not
compatible with nonnegative physical absorption as written. It may contain a
decimal or typographical issue, and it is for a hard-dye 2383 calibration
context rather than a disclosed 5279-era production transform. V59 therefore
does not silently replace the vector spectral inverse with that matrix. The
matrix remains research evidence for the need for full calibration, not a safe
numerical coefficient set.

## What remains unidentified

V59 is more accurate than V58 with respect to the public graph, but it is not a
claim that public documents uniquely determine a historical release print.
Still unmeasured are:

- the full optical-printer interimage transform and printer-light calibration;
- a real theatre lamp/filter/lens/screen spectral chain and flare;
- laboratory spectrophotometer readings of a processed 2383 neutral scale;
- the complete 3-D measured negative-to-print colour transform (Kodak's own
  calibration literature uses hundreds of patches / a 3-D LUT);
- 2383 development adjacency and batch/process variation.

V59 intentionally retains V58's empirical interimage matrix and scan-referenced
low-frequency monitor-colour authority. The physical spectrum is now less
wrong, but those downstream boundaries must remain visibly labelled rather than
being disguised as measured 5279 colour.

## Sources

1. Eastman Kodak, [KODAK VISION Color Print Film 2383/3383 technical
   information](https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf).
2. Eastman Kodak, [LAD for KODAK VISION Color Print Film,
   H-61B](https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf).
3. Eastman Kodak, [The Essential Reference Guide for
   Filmmakers](https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf).
4. Eastman Kodak, [US20020163657A1, hard-dye analytical-density
   calibration](https://patents.google.com/patent/US20020163657A1/en).
5. Ado Ishii et al., [A Color Management System for Motion Picture Film
   Production](https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055).
