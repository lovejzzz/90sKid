# V46 public release — certified spectral inverse

Date: 2026-08-11

V46 is the first public image release after the engine source-loss rebuild. It
does not attempt to reproduce the pixels of the lost implementation. It
consolidates the strongest surviving measurements, source documents, audits
and rejected experiments into an executable, versioned release.

The older internal labels V46–V86 remain immutable laboratory-note IDs. They
were never public visual releases. The public V46 label marks this later
consolidation and the website states the distinction explicitly.

## Two image corrections

### Complete stochastic-state endpoint hold

The old finite-site model extrapolated beyond Kodak's published granularity
support while holding target RMS constant. As activation probability approached
zero, the calibration amplitude could diverge and create rare, enormous
dye-density impulses. V46 holds the complete stochastic state—activation
probability, calibration amplitude and population contribution—at the measured
endpoint. It does not merely clip a finished pixel.

The 48 µm aperture-RMS audit passes after this correction, and formed density
remains bounded on CPU and Metal paths.

### Exact nonnegative Status-M inverse

The previous Status-M-to-negative-dye inverse used a projected iteration and
clipped negative components. That did not certify the nonnegative least-squares
optimum. V46 enumerates the three-record active sets and accepts the exact KKT
solution.

Production uses:

- a power-2 129³ base atlas;
- cubic interpolation in smooth cells;
- risk detection at active-set boundaries or when cubic and linear estimates
  disagree by at least 0.00025 D;
- exact 5³ local microbricks in risk cells;
- a compiled parallel CPU kernel with fast-math disabled.

The compiled implementation is bit-identical to the NumPy reference on the
tested risk set and is about 11.5 times faster there.

## Real-pixel cache certification

Cache demand is discovered with the same predicate used at runtime, not with a
sparse synthetic probe. T020, T032 and T007 are scanned in four states:

- before and after MTF;
- mean and formed density.

The final cache contains 25,333 risk cells. The complete three-source pipeline
reports zero missing cells. Independent exact checks sample 6,000 points per
state. Worst printer-density errors are:

| Source | Mean | Formed |
| --- | ---: | ---: |
| T020 | 0.0002306 D | 0.0005094 D |
| T032 | 0.0002371 D | 0.0004681 D |
| T007 | 0.0002334 D | 0.0003057 D |

All remain below the 0.001 D release gate.

The four versioned demand lists reproduce the production cell array exactly,
including order, not only count. The large generated atlas is excluded from Git
and can be rebuilt and checksum-verified with:

```bash
python3 engine/bootstrap.py --v46
```

## Shared negative, separate observers

V46 computes negative printer density once. The scan coordinate is derived from
that density and projection consumes the same shared result. This removes a
duplicate spectral inverse without changing image math. Branch differences
begin after the common negative.

The V79 projection opponent-delta lattice remains frozen as an explicitly named
defect-containment boundary. Public evidence does not identify a 5279/2383
cross-record projection NPS, so this boundary is not represented as measured
film physics.

## Evidence boundary

V46 retains evidence-minimal identity record formation. Kodak's three 48 µm
Status-M RMS curves constrain marginal variance, not the missing RGB
cross-covariance or cross-spectrum. V70–V85 show that shared events trade
opponent grain for stronger luminance grain rather than removing grain for
free. No visually preferred correlation is promoted as a 5279 parameter.

V46 is a more correct numerical and evidentiary baseline. It is not an absolute
same-batch reproduction because the project still lacks a closed measured loop
of 5279 negative, 2383 print, printer illuminant and characterized scanner.

## Release media

The release uses three one-second, 24-frame, 5760×4320 source witnesses:

- `NJARAW_S001_S001_T020`, frames 0–23;
- `NJARAW_S001_S001_T032`, frames 0–23;
- `NJARAW_S001_S001_T007`, frames 276–299.

Each projection and scan branch is delivered as a 12-bit ProRes 4444 master.
Scale-honest sRGB web companions and stills are derived from the final encoded
movies, not from a separate pre-encode buffer.

The legacy whole-picture colour-tail audit initially rejected three T020
projection statistics. V77 had already proved that those statistics include
deterministic one-pixel scene colour and therefore cannot identify stochastic
grain. V46 did not alter the image to satisfy that invalid test. Instead, the
release rerendered the exact same-path deterministic mean, passed it through
the same BT.1886 master → sRGB ProRes XQ delivery chain, and measured the
formed-minus-mean residual. The reconstructed delivered frame is pixel-exact;
projection stochastic opponent P99.99 is `0.06525`, median-residual P99.99 is
`0.04649`, and there are zero isolated events above `0.08`. The scan likewise
has zero isolated events above `0.08`. All non-confounded native gates, all
metadata/transfer gates and all master/companion light-parity gates pass.

The final release decision is therefore a pass, with the three superseded
whole-picture assertions preserved in the diagnostic report rather than
silently deleted.

Measured wall times on the release machine were 1,237.40 s for T020, 1,196.61 s
for T032 and 1,230.10 s for T007. The corresponding image-formation averages
were 46.09, 44.86 and 45.04 algorithm seconds per frame; remaining wall time
belongs to source audio/timecode finalization and delivery assembly.
