# Wavefront Tile Lab v0.2.0 — algebraic and separable density fusion

Date: 2026-08-09  
Status: implemented and cross-scene audited; **lab-only, Production-statistical
candidate, not Archive bit-exact and not the V43H default**

## Decision

v0.2.0 keeps every V43H image-formation constant and adds two bounded compute
contractions above v0.1.0:

1. V41's D65→D50 residual fit, neutral projection, residual blend, D50→D65
   adaptation and BT.2020 return are composed into one 3×3 operator. The same
   original D65 Y restoration is applied after that operator. No fitted colour
   coefficient, strength, white point, luminance, gamut boundary or highlight
   authority changes.
2. Deterministic DIR departure diffusion is evaluated as three independent
   three-record Gaussian batches instead of nine scalar Gaussian calls. The
   complete 3-record × 3-population source tensor is then applied to every
   receiver in one parallel kernel, preserving the historical source-record,
   source-population accumulation order.

The v0.1.0 same-Metal finite-site/optical island remains unchanged. Normal
`Emulsion5279Engine` configuration does not install either v0.2.0 contraction.

## Why these boundaries

The corrected operator profile showed that deterministic mean development was
3.54 s of an 11.90 s T020 negative, but its Gaussian DIR propagation was only
0.64 s and interlayer updates another 0.64 s. Moving one blur would therefore
not be structural. The same profile exposed a larger repeated traversal before
the negative:

| Scene→film substage | T020 seconds |
|---|---:|
| sensor-noise separation | 0.620 |
| V41 input chroma residual | 1.300 |
| direct BT.2020→film primaries | 0.014 |
| restrained optical scatter | 0.805 |

The residual chain is linear until its final luminance restoration. Composing
the linear chain is algebra, not a colour approximation. On the native T020
frame its own wall time fell from 1.388 s to 0.113 s (12.3×). Actual-camera
domain RMS error was `8.42e-8`; the maximum `6.14e-4` occurred at a rare
near-zero restoration divisor.

The DIR contraction is bit-identical at the final formed-density hash when fed
the same v0.2.0 scene result. Small-array reference tests constrain its maximum
correction difference below `5e-9`.

## Native 5.7K performance

These are same-process medians. T020 uses three adjacent frames and five
512×512 audit regions; T032 and T007 use two adjacent frames and five 384×384
regions.

| Scene | v0.1.0 reference | v0.2.0 | Improvement |
|---|---:|---:|---:|
| T020 | 15.679 s | 12.408 s | **20.9%** |
| T032 | 12.119 s | 10.061 s | **17.0%** |
| T007 | 11.496 s | 9.818 s | **14.6%** |

A separately warmed T020 negative reached 9.572 s. In that run the collapsed
residual used 0.093 s, the mean-DIR batch 0.814 s, and the resident v0.1.0 Metal
emulsion island 0.716 s. Peak RSS was about 12.0 GiB versus roughly 11.1 GiB in
the recent v0.1.0 profile; v0.2.0 trades temporary memory for fewer traversals.

## Statistical quality audit

For every scene, five crop sequences were measured on formed-minus-mean record
density. These metrics test the emulsion structure rather than scene content.

| Maximum across crop sequences | T020 | T032 | T007 | Gate |
|---|---:|---:|---:|---:|
| spatial RMS ratio error | `8.74e-7` | `2.00e-6` | `1.27e-6` | `5e-3` |
| temporal RMS ratio error | `1.05e-6` | `1.62e-6` | `3.28e-6` | `5e-3` |
| normalized NPS-band delta | `2.88e-6` | `3.56e-6` | `9.08e-6` | `2e-3` |
| lag-1 temporal-correlation delta | `1.83e-6` | `3.14e-6` | `3.81e-6` | `5e-3` |
| absolute-density tail ratio error | `4.26e-5` | `2.83e-4` | `3.23e-5` | `1e-2` |

All statistical gates pass. Direct per-pixel identity does not: algebraically
equivalent float32 evaluation can move a finite-site probability across one
Philox/Bernoulli threshold. Isolated crop maxima were 0.0592 D, 0.0427 D and
0.0357 D. Those are different realizations of a tiny number of dye clouds, not
a change in measured RMS, NPS, temporal stationarity or tails.

On complete T020 observers, projection changed 2.116% of 16-bit component
values (mean absolute difference 0.804 code) and scan changed 0.242% (mean
absolute difference 0.0102 code). After 12-bit quantization the changed
fractions were 0.774% and 0.0354%. Rare stochastic threshold flips create large
maxima, so maxima are recorded but are not treated as colour or tone error.
Signed mean differences were below `0.001` of one 16-bit code.

The evidence supports v0.2.0 as a **Production-statistical candidate**. It does
not support Archive substitution. The exact v0.0.2 CPU path remains the
authority when identical realization is required.

## Reproduction

```text
PYTHONPATH=engine/src:. python3 engine/src/benchmark_v43h_wavefront_tiles.py \
  <source.MOV> --decoder <prores_raw_float_decode> --cache <frame.npy> \
  --output <result> --reference <v0.1.0-reference> --v020

PYTHONPATH=engine/src:. python3 engine/src/audit_wavefront_v010_quality.py \
  <source.MOV> --decoder <prores_raw_float_decode> \
  --cache-directory <cache> --output <audit.json> --frames 3 \
  --candidate v020
```

## Remaining boundary

The next worthwhile speed work is not more probability math. The full T020 run
used 10.82 s for negative formation but 19.67 s for the two observers. Future
work should first share deterministic density/observer intermediates and audit
the projection/scan branch graph. The optical-scatter dual Gaussian (about
0.8 s) is a secondary bounded candidate. Neither should be fused until complete
observer output is evidence-gated against this milestone.
