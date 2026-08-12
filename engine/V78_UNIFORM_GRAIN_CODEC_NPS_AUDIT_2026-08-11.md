# V78 uniform-grain codec NPS audit — 2026-08-11

## Decision

Retain V76's maximum-budget `prores_ks` XQ (`8192 bits/MB`) for normal
QuickTime delivery.

Apple VideoToolbox XQ preserves the aggregate NPS of a full uniform grain field
more closely, but it produces approximately three times the real-scene linear
RGB/OKLab error and slightly overshoots high-pass energy. It is statistically
closer because some coding error replaces lost stochastic power; that does not
make each decoded pixel more faithful.

FFV1 RGB16 remains the lossless research control. It is effectively exact but
is not substituted for ordinary QuickTime review or the native ProRes master.

V78 changes no image-formation parameter and requires no reversal of V76.

## Why V76's scalar result was not enough

V76 compared one real T020 frame and showed that maximum-budget `prores_ks`
greatly improved total high-pass retention and pixel error over default XQ.
V77 then found a small near-Nyquist opponent floor on uniform review strips.

A codec can preserve total RMS while moving power between frequencies. V78
therefore encodes the formed and deterministic-mean images separately, decodes
both, subtracts them and compares the resulting stochastic NPS band by band.
Scene edges cannot enter this measurement.

## Experimental correction

The first V78 pass used 1920×64 strips. This was insufficient for codec
selection:

- default and 8192-budget `prores_ks` produced identical strip sizes and pixels;
- near-zero opponent fields made relative error ratios unstable;
- the rate controller did not see a normal complete frame.

The accepted audit adds a real 5760×4320 uniform logE −1 negative, carries it
through projection and scan, performs exact 3×3 linear-light integration to
1920×1440, and then encodes the complete formed/mean pair. Components below
`1e-8` RMS are classified by absolute added noise rather than relative error.

The original logE −3/−1/0 strips remain descriptive cross-checks, not the final
rate-control authority.

## Full-frame uniform NPS result

The aggregate covers scale-integrated projection and legacy scan luma/opponent
components.

| Codec | Mean band RMSE / reference RMS | Mean total-RMS error | Mean populated-band error | Mean formed+mean bytes |
|---|---:|---:|---:|---:|
| `prores_ks` default XQ | 3.390% | 9.954% | 1.173 dB | 2,896,187 |
| `prores_ks` XQ / 8192 | **1.795%** | **5.177%** | **0.641 dB** | 3,985,588 |
| VideoToolbox XQ | 0.772% | 1.031% | 0.332 dB | 2,721,284 |
| FFV1 RGB16 | 0.000070% | 0.000032% | 0.000032 dB | 11,316,702 |

### Branch detail

| Branch / codec | Luma retained | Opponent retained |
|---|---:|---:|
| projection, default XQ | 93.20% | 89.87% |
| projection, XQ / 8192 | 95.88% | 93.81% |
| projection, VideoToolbox | 100.85% | 100.87% |
| scan, default XQ | 90.76% | 86.35% |
| scan, XQ / 8192 | 95.85% | 93.75% |
| scan, VideoToolbox | 99.82% | 102.23% |

Maximum-budget `prores_ks` clearly improves the uniform stochastic field over
default XQ. VideoToolbox is closer in total NPS but overshoots projection and
especially scan opponent energy.

## Reconciliation with the real T020 picture

Uniform NPS is necessary but not sufficient. The same candidates were already
compared against the exact integrated T020 RGB frame in V76:

| Codec | Mean linear RGB MAE | Mean OKLab P95 | Mean absolute high-pass error |
|---|---:|---:|---:|
| default XQ | 0.0012090 | 0.008270 | 9.41% |
| XQ / 8192 | **0.0003717** | **0.002716** | 2.49% |
| VideoToolbox XQ | 0.0011350 | 0.007705 | **2.18%** |

VideoToolbox's scalar high-pass error is marginally smaller, but its decoded
RGB and perceptual-colour errors are about `3.05×` and `2.84×` those of
maximum-budget `prores_ks`. The apparent NPS advantage therefore comes with a
substantial picture error.

The selection rule is intentionally lexicographic rather than aesthetic:

1. reject a candidate that materially worsens decoded picture/colour parity;
2. among remaining candidates, minimize stochastic band and RMS error;
3. use lossless data as the reference, not as proof that every player supports
   the format.

By that rule, maximum-budget `prores_ks` is the best supplied ProRes delivery.

## Consequence for V76 and future delivery

The shared `_xq_command` remains:

```text
prores_ks · profile XQ · bits_per_mb 8192
```

This applies to newly rendered native masters, native sRGB companions and
scale-integrated reviews. Existing V72 files remain unchanged.

An optional FFV1 or image-sequence conformance authority would be valuable for
future scientific NPS comparisons, but it should be a separate research
artifact. The ordinary viewing file must not silently change its player and
workflow contract.

## Reproducible artifacts

- audit: `src/audit_v78_uniform_grain_codec_nps.py`
- result: `research_runs/v78_uniform_grain_codec_nps_audit.json`
- real-scene input: `research_runs/v76_review_codec_ownership_audit.json`
- image profile: unchanged V72
- delivery implementation: V76 maximum-budget `prores_ks` retained

## Primary source

1. Apple, [*About Apple ProRes*](https://support.apple.com/en-ca/102207), on ProRes 4444/XQ as a virtually lossless exchange family rather than a mathematically lossless codec.
