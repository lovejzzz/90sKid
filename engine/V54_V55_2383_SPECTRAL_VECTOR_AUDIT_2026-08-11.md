# V54/V55 — 2383 spectral-vector audit

Date: 2026-08-11
Status: isolated native-frame candidates
V54 change: 2383 record sensitivity only
V55 change: 2383 formed-dye spectral density only

> **V59 correction (2026-08-11):** the graph also contains a fourth vector
> path labelled `Visual Neutral`. V55's C/M/Y extraction is numerically correct
> but incomplete as a total processed-print spectrum because it omitted that
> path and therefore the wavelength-dependent base/D-min residual. See
> [`V59_2383_VISUAL_NEUTRAL_BASE_SPECTRUM_AUDIT_2026-08-11.md`](V59_2383_VISUAL_NEUTRAL_BASE_SPECTRUM_AUDIT_2026-08-11.md).

## Official source

Both tables come from page 6 of Kodak H-1-2383t, March 2005. Source PDF
SHA-256:
`76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156`.

Kodak describes the sensitivity graph as the reciprocal exposure required to
produce density 1.0 under tungsten/ECP-2D conditions. The dye graph depicts the
absorptions of dyes formed in processing, normalized to form visual-neutral
density 1.0 for xenon-arc viewing; Kodak also identifies C/M/Y curves as
peak-normalized.

Reproducer:

```bash
python3 engine/src/extract_2383_2005_spectral_vectors.py \
  /path/to/kodak_2383_H-1-2383t_2005.pdf \
  --output-directory /tmp/2383-vectors
diff -u engine/data/2383_log_sensitivity_trace_2005.csv \
  /tmp/2383-vectors/2383_log_sensitivity_trace_2005.csv
diff -u engine/data/2383_dye_density_trace_2005.csv \
  /tmp/2383-vectors/2383_dye_density_trace_2005.csv
diff -u engine/data/2383_visual_neutral_trace_2005.csv \
  /tmp/2383-vectors/2383_visual_neutral_trace_2005.csv
```

## V54: record sensitivity

The old visual transcription omitted the plotted short-wave cyan and magenta
lobes and displaced the main bands. At the engine's 20 nm samples, maximum
absolute log-sensitivity errors are about 5.08 C, 5.07 M and 0.69 Y log units.
The large C/M figures occur where the old table used its numerical -6 floor for
a finite official response.

Under the engine's 3200 K printer lamp:

| Record | Old effective wavelength | Vector effective wavelength | Change |
|---|---:|---:|---:|
| C | 679.25 nm | 664.86 nm | -14.39 nm |
| M | 545.08 nm | 531.16 nm | -13.92 nm |
| Y | 445.72 nm | 453.40 nm | +7.68 nm |

Below or equal to 420 nm, the new exposure-weight fractions are about 5.65% C,
2.80% M and 12.57% Y. The old C/M fractions were effectively zero.

The official graph stops drawing each record when it falls below -3. V54 uses
an explicit -6 log10 numerical floor outside each path; that floor is not
claimed as measured sensitivity.

## V55: formed-dye spectra

The old table is materially shifted along its wavelength axis:

| Dye | Old peak | Official vector peak | Max sampled error | RMS error |
|---|---:|---:|---:|---:|
| C | 740 nm | 660 nm | 1.0212 | 0.4326 |
| M | 580 nm | 540 nm | 0.6015 | 0.2283 |
| Y | 480 nm | 440 nm | 0.4371 | 0.1858 |

All runtime samples from 380 through 740 nm lie inside the drawn paths. The
760/780 nm samples are outside Kodak's 750 nm graph; V55 continues each final
vector secant and clips at zero. Those two far-red samples are disclosed
inference. The cyan continuation remains 0.2217 at 760 nm and 0.0288 at 780 nm;
M/Y are already near zero.

## Isolation and native validation

V54 freezes the V53 H-D, old dye graph and xenon SPD. V55 freezes V54's H-D and
sensitivity and changes only dye absorption. Each version has its own SHA-locked
193-cube monitor lattice.

Source: `NJARAW_S001_S001_T020.MOV`, frame 0, 5760 x 4320, Archive exact CPU.

- 36 pipeline tests pass after V55.
- V54 lattice SHA-256:
  `9d67b8f7c9ba58a1eaf00e61d620b7c34aef4853a8d2bd4ef34f5392a9dc141c`.
- V55 lattice SHA-256:
  `d5fe1c9067005a79a47b471c85c8eac0db3cff29138fdeb0a99cf0e7763dfc38`.
- V53/V54 projection review PSNR: 61.143 dB.
- V54/V55 projection review PSNR: 60.756 dB.
- V52, V53, V54 and V55 scan-master decoded-frame MD5 is identical:
  `604ead3c60971bb038b8470d5b5492ad`.
- V55 masters are 5760 x 4320, ProRes 4444 XQ, `yuv444p12le`, 12-bit,
  Rec.709-tagged.

## Critical architecture finding

V30 intentionally set `PRINT_MONITOR_PHYSICAL_HUE_WEIGHT` and
`PRINT_MONITOR_PHYSICAL_SATURATION_WEIGHT` to zero because the old 2383 graphs
were coarse visual digitizations. V31 then made the delivered projection's
low-frequency a/b colour scan-referenced. That boundary remains inherited by
V55. Consequently official H-D/sensitivity/dye corrections affect physical
print lightness and local interactions, but most delivered low-frequency hue
and chroma are still replaced by the scan observer.

This explains both observations:

1. severe spectral-table errors produced surprisingly small final-picture
   differences; and
2. projection and scan versions remained more similar than a literal
   5279-to-2383 optical path should be.

The old choice was an honest guard against untrustworthy spectral tables, not a
valid permanent physical model. Now that the graph data are vector-traced, the
next experiment should remove scan colour authority in one isolated observer
profile while preserving an explicit neutral/lightness display adaptation.
That experiment must not be called a measurement: the 2383 interimage matrix,
xenon SPD, Callier term and complete print-to-monitor appearance transform are
still not directly measured.
