# V32 — Measurement-first generalization

## Release decision

V32 makes no visual change to the accepted V31 baseline.  It freezes the 5279
negative, nine stochastic sublayers, five cloud-size populations, DIR, MTF,
grain amplitude and spectrum, normal-process colour correction, black, gamma,
Kodak 2383 LAD and both existing observers.  A change is allowed only when a
new measurement can distinguish an error from scene colour or creative taste.

## New independent scenes

Both sources are Panasonic GH7 / Atomos Ninja 12-bit ProRes RAW HQ, 5760×4320
Open Gate, 24000/1001 fps, recorded as V-Log/V-Gamut metadata at ISO 500 and
5500 K.

- `NJARAW_S001_S001_T007`, frames 276–299: lake reflections, pale sky, bright
  grasses, fine foliage and deep water/forest separation.
- `NJARAW_S001_S001_T031`, frames 132–155: near-neutral stone, warm mushroom,
  moss, dark foliage and shallow-depth high-frequency detail.

Each range is exactly 24 source frames.  No scene-specific exposure, colour,
grain or contrast parameter is introduced.

## Four delivery observations

1. Panasonic official V-709 camera baseline, used only as a displayable source
   reference.
2. V31 normal-process 5279 → 2383 projection observer in 12-bit Rec.709.
3. V31 5279 → Period 2K / Cineon / Blu-ray scan observer in 12-bit Rec.709.
4. An appearance-preserving SMPTE ST 428-1 DCDM test sequence derived from the
   completed V31 projection: 24 fps, 12-bit X′Y′Z′ codes stored in the high
   12 bits of uncompressed 16-bit TIFF channels.

The fourth result is explicitly **not a packaged DCP**.  It is the uncompressed
DCDM image sequence that precedes JPEG 2000 compression, MXF packaging and any
distribution encryption.  An earlier P3-D65/gamma-2.6 ProRes transport probe
was rejected because its RGB meaning is not expressed consistently across
ProRes frame headers, MOV colour atoms and players—the same class of error
already found in V25.

Primary standards:

- ITU-R BT.709-6: https://www.itu.int/rec/R-REC-BT.709-6-201506-I/en
- DCI Digital Cinema System Specification:
  https://www.dcimovies.com/dci-specification/
- Definitive DCI specification HTML:
  https://dcss.dcimovies.com/0c0cff34d231b516cb89ae3fad352d5cf37a9515/dcss.html
- SMPTE ST 428-1:2019:
  https://pub.smpte.org/pub/st428-1/st428-1-2019.pdf

## Measurement gates

The release validator checks all 24 frames, not only a representative still:

- native 5760×4320, 24-frame, 12-bit ProRes 4444 format and complete colour
  signalling;
- exact scan regression against the shared V30/V31 observer output;
- per-pixel linear Rec.709 luminance preservation through the V31 adapter;
- hard-clip fraction and 99th-percentile highlight continuity;
- frame-mean, texture-power and near-neutral opponent-axis temporal stability;
- DCDM X′Y′Z′ → linear Rec.709 appearance round-trip error;
- full-frame versus tiled OFX-region computation parity.

For the finite Gaussian crossover, the plugin region of interest is

```text
sigma_full = 0.72 * output_width / 2048
halo = ceil(6 * sigma_full)
```

The tile uses the full output width to calculate sigma and requests the halo
from its source.  This avoids the common plugin error in which render scale or
tile width silently changes the physical grain/colour crossover.

## OFX migration contract

- float32 scene kernels; 12-bit ProRes remains the interchange verification;
- stochastic fields keyed by absolute source-frame index, never render order;
- Resolve schedules frames; the plugin must not add an uncontrolled frame pool;
- immutable LUTs and stock constants may be cached, image state may not;
- Archive Exact remains authoritative whenever a GPU path fails numerical and
  statistical parity.

## Results

Both native-resolution trials passed with zero validation failures.

| Measurement | T007 | T031 |
| --- | ---: | ---: |
| Dual-master core wall time | 668.79 s | 589.25 s |
| Effective wall time / source frame / both masters | 27.87 s | 24.55 s |
| V31 final boundary | 116.12 s | 107.79 s |
| Camera V-709 baseline | 135.99 s | 125.56 s |
| DCDM sequence | 13.55 s | 23.56 s |
| Adapter linear-Y p99 error | 0.001820 | 0.001575 |
| DCDM linear-RGB p99 round-trip error | 0.000553 | 0.000375 |
| OFX tile/full-frame signal p99 error | 2.98e-8 | 2.98e-8 |
| Projection hard-clip fraction | 0 | 0 |
| Near-neutral temporal a/b maximum std | 0.000046 | 0.000049 |

All camera, projection and scan masters are 24-frame, 5760×4320, ProRes 4444,
12-bit, Rec.709 1-1-1.  The two scan delivery files are byte-identical to their
locked base-observer outputs.  Both DCDM sequences contain 24 sequential,
uncompressed 2880×2160 uint16 TIFF frames, with the 12-bit X′Y′Z′ code in the
high bits and every low four-bit word equal to zero.

The profiler also rejects encoding as the useful optimization target.  Across
the two two-worker renders, stochastic emulsion consumes roughly 18–21 seconds
per frame per worker and the two observers roughly 15–17 seconds; dual ProRes
encoding consumes only about 0.38–0.58 seconds.  Future acceleration must keep
the reference stochastic distribution and observer output invariant.
