# V52: evidence-separated 5279 characteristic curves

Date: 2026-08-11
Status: implemented candidate; native one-frame validation passed

## Why V51 was not the end of the graph audit

V50 corrected the published 48-micrometre RMS granularity curves and V51
corrected the negative net-dye and minimum-density spectra. The remaining
graph-backed 5279 authority was the three-record sensitometric/H-D table. The
Archive table was a reasonable visual transcription, but it mixed two values
that Kodak actually plotted with values inferred outside the plotted curve.

V52 corrects that evidence identity. It does not introduce an artistic tone
curve.

## Primary source and graph conditions

Kodak H-1-5279t, March 2003, graph `F010_0238AC`:
<https://static1.squarespace.com/static/5790488dbe65943e37169f37/t/57ab931e29687fe82091402d/1470862111007/KODAK%2B500T.pdf>

Retrieved SHA-256:
`f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8`.

The graph declares:

- 3200 K tungsten exposure;
- 1/50 second exposure time;
- ECN-2 processing; and
- Status-M densitometry.

Kodak also states that these are representative production-coating results,
not specifications for an individual roll or batch.

## Reproducible vector recovery

The source PDF contains the three H-D strokes as vector polylines. Curve labels
split each stroke into several PDF objects, so the extraction reconstructs the
red, green and blue paths before sampling them.

The horizontal calibration uses the printed `-4/-3/-2/-1/0` log-exposure ticks.
The vertical calibration is a least-squares fit to the D=0 and D=3 border
centres and the printed D=1 and D=2 ticks. The four-point residual RMS is
0.0019466 density, which is retained as extraction uncertainty rather than
hidden by over-precise table values.

The reproduction utility is
[`src/extract_v52_characteristic.py`](src/extract_v52_characteristic.py). Given
the SHA-locked PDF it recreates
[`data/5279_characteristic_trace_2003.csv`](data/5279_characteristic_trace_2003.csv)
byte for byte.

## Three evidence classes, not one fictional official table

The graph axis covers internal log exposure `-4..0`, but all three drawn paths
begin at approximately `-3.795937`. V52 therefore records three distinct
policies:

1. `-4..-3.795937`: hold the first drawn D-min value. This is an explicit
   low-exposure plateau inference, not a traced stroke.
2. `-3.795937..0`: interpolate the reconstructed Kodak vector paths at quarter
   log-exposure intervals.
3. `+0.5` and `+1.0`: preserve the Archive shoulder *increments* relative to the
   new traced endpoint. These two points remain explicitly inferred because
   Kodak's graph ends at zero.

The last policy gives continuity without pretending that a hard endpoint hold
or a newly invented asymptote was measured. Its slopes decrease monotonically:

| record | last traced slope | 0→+0.5 | +0.5→+1.0 |
|---|---:|---:|---:|
| red | 0.3103 | 0.2800 | 0.1600 |
| green | 0.3666 | 0.3200 | 0.1800 |
| blue | 0.3534 | 0.2400 | 0.1200 |

Units are density per log-exposure unit. No hard highlight plateau is inserted.

## Difference from the Archive table

Across `-4..0`, dense interpolation of the two tables measures:

| record | maximum absolute difference | RMS density difference |
|---|---:|---:|
| red | 0.01376 D | 0.00633 D |
| green | 0.02780 D | 0.01597 D |
| blue | 0.02530 D | 0.01354 D |

The traced D-min values are R/G/B = 0.15897/0.59503/0.92530 D. The traced graph
endpoints at logE zero are 1.58417/2.21421/2.54885 D. These values now drive
both deterministic mean density and the density capacities used by finite-site
formation. The separate wavelength-dependent orange-mask/D-min spectrum remains
the V51 trace.

V52 deliberately does not refit the proprietary fast/medium/slow layer
decomposition. That decomposition is not published 5279 data; changing it at
the same time would prevent an isolated H-D comparison. Neutral uniform fields
remain exactly on the active traced curves.

## Native T020 validation

The same GH7 ProRes RAW frame used for V50 and V51 was rendered again at
5760×4320 with the same input transform, exposure, absolute frame identity,
V50 granularity, V48/V49 spatial formation, V51 spectra and two observers.

Input exposure coverage confirms that this is a valid in-domain test:

| record | pixels in the drawn path | below logE -4 | above logE 0 |
|---|---:|---:|---:|
| red | 98.867% | 0.944% | 0% |
| green | 99.868% | 0.075% | 0% |
| blue | 99.391% | 0.393% | 0% |

Consequently, T020 validates the vector-traced body and D-min handling but does
not validate the inferred high-exposure shoulder.

On the final 1920-pixel scale-integrated sRGB reviews, V51→V52 measured:

| observer | all-channel RMS code delta | PSNR | mean luma delta |
|---|---:|---:|---:|
| 2383 projection | 0.00832 | 41.60 dB | -0.00218 |
| period scan | 0.00861 | 41.30 dB | -0.00301 |

For both observers, pixels below encoded luma 0.1 became lower on average while
pixels above 0.7 became higher. This is the traced H-D slope change propagating
through the already frozen observers, not a post-film contrast operation.
There were no new code-value clamps or channel discontinuities.

Both professional masters were verified as ProRes 4444 XQ, `yuv444p12le`,
5760×4320, 12-bit, with Rec.709 primaries/transfer/matrix signalling. Engine
time was 45.68 seconds and complete wall time was 58.36 seconds for one frame.

## Result and remaining boundary

V52 is more accurate than V51 where the source provides a vector measurement.
It is also more honest at the two boundaries because inferred values are no
longer presented as if Kodak plotted them.

The largest remaining graph-transcription uncertainty is 2383. Kodak's
currently available 2383 technical PDF embeds its characteristic, spectral
sensitivity and dye-density plots as raster artwork. Those curves require a
calibrated raster extraction with resolution/line-width uncertainty before any
further release table can be replaced.
