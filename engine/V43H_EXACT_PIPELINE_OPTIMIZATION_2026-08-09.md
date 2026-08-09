# V43H exact pipeline optimization audit — 2026-08-09

## Decision

V43H image formation is frozen. This pass changes execution only: no RAW
interpretation, exposure, white balance, 5279 sensitometry, DIR, MTF, grain
statistics, 2383 model, Spirit observer, colour authority, black, contrast,
gamma or delivery transfer was changed.

Every accepted optimization had to satisfy both gates:

1. randomized float32 coverage was bit-exact against the historical formula;
2. a native 5760 × 4320, 12-bit ProRes 4444 XQ release output decoded to the
   same RGB code values as the already published V43H master.

An optimization was rejected when it was merely close, visually equivalent or
inside a tolerance. The accepted maximum difference is zero.

## Errors found

### V43H decode timing was always zero

The release renderer recorded `frame_started - frame_started`. The image was
correct, but the performance report was not. The renderer now times the actual
iterator read and raises an explicit error if the RAW decoder ends early.

Measured reads were 0.266 s for T020 frame 0, 0.270 s for T032 frame 0 and
1.142 s for T007 frame 276. The last value includes seeking to the absolute
source frame and is not emulsion computation.

### Deterministic grain de-bias performed two impossible corrections

The FSD control passed the same deterministic image as both the reference and
stochastic realization. Its grain delta is exactly zero, yet the old path made
two full-frame histogram passes. The optimized path retains the historical
sRGB encode/decode round-trip and skips only the zero corrections.

### Withdrawn authorities still consumed compute

The selected normal-process profile gives physical projection hue and
saturation zero authority, and gives the final projection high-frequency
opponent residual zero retention. The generic implementation still evaluated
those full-resolution branches and multiplied their results by exact zero.
The new guarded paths retain the surviving arithmetic and skip only the terms
whose configured coefficient is zero.

## Exact optimizations accepted

- Fused H-61 density-cube sampling while preserving its historical
  red → blue → green float32 interpolation order.
- Fused 2383 spectral projection-lattice sampling.
- Fused 5279-negative-to-2383-printer spectral sampling.
- Parallel, exact per-record 2383 H-D and neutral-shaper interpolation.
- Fused V31 luma-preserving Rec.709 gamut boundary.
- Exact neutral-curve and projected-gray interpolation kernels, including the
  original float64 factor multiplication before float32 output rounding.
- Parallel per-record tonal-grain bias estimation.
- Scalar handling of V43H's spectrally common print-density hypothesis. The old
  graph allocated three identical records, discarded two corrected records,
  later formed another three-record image and averaged it back to one scalar.
  The replacement preserves each record's addition/subtraction rounding and
  the historical three-value mean without those redundant native RGB images.
- Exact-zero short circuits for deterministic grain de-bias, withdrawn
  projection colour authority and withdrawn high-frequency opponent retention.

Reference NumPy functions remain available as fallbacks. The fused kernels are
execution choices, not new film equations.

## Rejected experiments

Increasing the analytical projection stripe from 96 to 192, 384 or 768 rows
was bit-exact, but six alternating native trials found only about 0.13 s mean
benefit for 192 rows and no stable gain for larger stripes. The higher memory
peak was not justified, so the 96-row boundary remains.

## Native performance evidence

On the same 48 GB Apple-silicon machine, a same-process T020 frame-12 A/B before
the final two zero-authority short circuits measured:

| Graph | Dual observer time |
| --- | ---: |
| Historical execution | 42.141 s |
| Exact fused execution | 27.372 s |
| Saved | 14.769 s |
| Speed ratio | 1.54× |

After all accepted changes, formal one-frame four-route releases measured:

| Source / absolute frame | RAW read | Negative | Dual observer | FSD | Camera | Four writes | Total incl. four finalizations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T020 / 0 | 0.266 s | 12.919 s | 24.032 s | 2.923 s | 0.636 s | 0.440 s | 57.322 s |
| T032 / 0 | 0.270 s | 12.752 s | 23.975 s | 2.984 s | 0.634 s | 0.440 s | 56.870 s |
| T007 / 276 | 1.142 s | 12.864 s | 24.647 s | 2.939 s | 0.649 s | 0.442 s | 61.630 s |

One-frame totals intentionally include four encoder startups, four master
finalizations, four sRGB companion rebuilds and still extraction, so they are
not a 24-frame throughput estimate. The stage times isolate the reusable frame
cost.

## Master-level identity proof

The optimized renderer rebuilt T020 frame 0, T032 frame 0 and T007 frame 276
through all four routes:

- V43H physical 5279 → 2383 projection;
- V43H period Spirit / Blu-ray scan;
- FSD comparator;
- deterministic Panasonic camera witness.

Each new 12-bit XQ master and its published V43H counterpart was independently
decoded to RGB48. Across 12 comparisons, every decoded RGB sample matched:

- maximum code difference: **0**;
- non-matching samples: **0**;
- changed routes: **0 / 12**.

The optimization therefore changes render time and transient memory, not the
delivered picture.

## Regression gates

- `engine.emulsion5279.test_pipeline`: 17 / 17 passed;
- FSD, V32 kernel and V41 colour-transport suites: 8 / 8 passed;
- website build and rendered-HTML suite: 21 / 21 passed;
- native master comparisons: 12 / 12 exact.

The next safe speed work should target resident OFX/Metal ownership and removal
of process/codec startup overhead. Porting the remaining V43H common-density
random realization to another RNG or replacing analytical colour operations
with approximate LUTs would change the picture and is outside this exact pass.
