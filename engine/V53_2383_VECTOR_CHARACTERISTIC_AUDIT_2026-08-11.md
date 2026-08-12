# V53 — 2383 vector-characteristic audit

Date: 2026-08-11
Status: isolated candidate, native-frame validated
Image-model change from V52: **2383 Status-A characteristic curves only**

## Why this audit was necessary

The recovered engine described its positive-stock table as an approximate
visual digitisation of Kodak's 2026 H-1-2383 graph. Re-reading the project
history showed that an archived March 2005 H-1-2383t PDF contains the original
sensitometric artwork as vector paths. That sheet is also closer to the 5279
period than the 2026 sheet.

The old table mixed two incompatible values for minimum density:

- the H-D table began at `0.01 / 0.01 / 0.01 D`;
- the spectral inverse used `0.04356 / 0.04749 / 0.10272 D`.

Callier handling and print-grain normalisation read the first value, while the
analytical Status-A inverse read the second. V53 makes the vector-traced table
the only D-min source.

## Source and reproducibility

- Kodak publication: *KODAK VISION Color Print Film / 2383*, H-1-2383t
- Revision: March 2005
- Figure: F002_1254AC, page 5
- Exposure: 1/500 second, tungsten, Heat Absorbing Glass No. 2043 and Series
  1700 filter
- Process: ECP-2D
- Densitometry: Status A
- Source PDF SHA-256:
  `76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156`

Reproducer:

```bash
python3 engine/src/extract_v53_2383_characteristic.py \
  /path/to/kodak_2383_H-1-2383t_2005.pdf \
  --output /tmp/2383_characteristic_trace_2005.csv
diff -u engine/data/2383_characteristic_trace_2005.csv \
  /tmp/2383_characteristic_trace_2005.csv
```

The graph x border is calibrated from `-3..+3 log exposure`. Density uses a
least-squares fit to all seven printed `0..6 D` grid lines; axis-fit RMS is
`0.0009894 D`. The runtime table contains the union of all original vector x
nodes. Therefore every published vertex is preserved on the common table; a
coarse second 0.1-logE sampling is not introduced.

## Evidence boundary

Each channel has a different drawn path domain:

| Record | Drawn logE domain | Vector D-min | Vector D-max |
|---|---:|---:|---:|
| Red | -0.40714 .. +2.59396 | 0.04442 | 4.11540 |
| Green | -0.70615 .. +2.21691 | 0.04835 | 4.09964 |
| Blue | -1.00733 .. +1.99378 | 0.10358 | 4.10750 |

Outside a drawn path, V53 explicitly holds its first/last vector value to the
graph borders at logE -3/+3. Those endpoint holds are disclosed extrapolation
policies, not measurements. The curves are representative production data and
are not a batch specification.

## Magnitude of the recovered transcription error

The official vector curve was evaluated at every old table node. Differences
between official-vector density and the old runtime density were:

| Record | Maximum absolute error | RMS error |
|---|---:|---:|
| Red | 0.22569 D | 0.10706 D |
| Green | 0.63570 D | 0.31067 D |
| Blue | 1.11293 D | 0.53582 D |

This is not a creative preference or an imperceptible digitisation tolerance.
It is large enough to change positive-stock toe/straight-line/shoulder
relationships and colour separation.

## Isolation contract

V53 inherits V52 and changes only:

- `PRINT_2383_LOG_EXPOSURE`
- `PRINT_2383_DENSITY_RGB`
- `PRINT_2383_STATUS_A_DMIN_RGB`
- `PRINT_2383_DMAX`
- the projection-monitor lattice derived from those values

It freezes 5279 H-D, net-dye spectra, D-min spectrum, granularity, finite-site
formation, DIR, MTF, 2383 spectral sensitivity, 2383 dye spectra, projector SPD
and all display/delivery policies.

## Native validation

Source: `NJARAW_S001_S001_T020.MOV`, frame 0, 5760 x 4320.
Mode: Archive exact CPU.
Output: `outputs/native_5k_v53_2383_vector_characteristic_candidate_1f/T020`.

- 34 pipeline tests passed.
- All V37–V53 conformance gates passed.
- The V53 193-cube lattice is SHA-locked as
  `e8cb27f28a5884cdc709e47fcda45a035cba4f21bf2fbf89414717794ba6bb26`.
- Both masters are 5760 x 4320, ProRes 4444 XQ, `yuv444p12le`, 12-bit,
  Rec.709 tagged.
- V52 and V53 scan-master decoded-frame MD5 values are identical. This proves
  the RAW decoder, 5279 formation, grain and scan observer did not drift.
- V52/V53 projection 1920-pixel linear-area reviews: PSNR 55.873 dB.
- Projection encoded-Y mean delta is +0.000410; RMS is 0.002487. No new low or
  high code clipping was observed.

The image difference is deliberately smaller than the raw curve-table error.
LAD placement and the six-step neutral shapers remove most neutral crossover;
the remaining change belongs mainly to coloured record separation and local
toe/shoulder response.

## New issue found while re-reading the same official sheet

Page 6 also contains vector spectral-sensitivity and dye-density paths. The
runtime transcriptions are not close enough to treat as final:

- official 2383 cyan and magenta records include short-wave sensitivity lobes
  that the runtime table largely omits;
- under a 3200 K printer lamp, the recovered cyan and magenta effective
  wavelengths move by about -14.4 nm and -13.9 nm respectively;
- the old dye-density peaks occur at approximately 740/580/480 nm for C/M/Y,
  while the official vector paths peak near 660/540/440 nm;
- maximum sampled dye-density errors are about 1.02/0.60/0.44 relative-density
  units for C/M/Y.

These spectral corrections must be tested in separate versions. Combining H-D,
record sensitivity and dye spectra in one release would make a failure
impossible to diagnose. The next defensible sequence is sensitivity-only, then
dye-only, each with a rebuilt lattice and an unchanged scan witness.
