# V35 grain-perception audit

Date: 2026-08-05
Question: why can V35 read as more turbulent or 8/16 mm when its measured
spatial grain energy and 35 mm sharpness remain close to V34?

## Decision

The observation is valid, but it has two distinct causes.

1. The native 12-bit masters retain essentially the same spatial NPS, average
   high-pass energy and grain-to-edge ratio as V34. V35 has not globally made
   the grain larger.
2. The independent Philox-u32 realization produces heavier local temporal
   tails in T031, especially where dark texture meets the nonlinear scan/black
   boundary. The current inter-frame H.264 website proxy then exaggerates that
   difference substantially.

This combination is perceptually capable of reading as coarse-format motion
grain while the deterministic image remains 35 mm sharp. The resulting sense
of scale mismatch is real even though the earlier energy/NPS release gates pass.

V35 should be retained as an acceleration and coarse-format research branch,
but its current T031 website presentation should not be treated as the final
35 mm 5279 perceptual baseline. V36 should add temporal-tail and proxy-codec
gates before deciding whether Philox-u32 remains the 35 mm Production sampler.

## Native-master findings

Five native-scale 512 x 512 regions were measured over all 24 frames. The
diagnostic removes a sigma-3 local base, then measures spatial high-pass energy,
frame-difference tails, per-pixel temporal variance, connected bursts,
lag-one correlation, opponent/luma motion and normalized radial NPS.

| Scene / branch | Median V35/V34 temporal-difference RMS | Maximum crop | Interpretation |
| --- | ---: | ---: | --- |
| T002 projection | 1.0003 | 1.0012 | no material change |
| T002 scan | 0.9998 | 1.0010 | no material change |
| T007 projection | 1.0030 | 1.0106 | mild increase |
| T007 scan | 1.0057 | 1.0249 | mild, scene-dependent increase |
| T031 projection | 1.0089 | 1.0351 | visible local turbulence |
| T031 scan | 1.0253 | 1.1205 | material dark-texture tail increase |

Across the native comparisons:

- median spatial high-pass energy remains within about 0.4% of V34;
- grain-to-base-edge ratios remain within about 0.3% in the median and within
  about 0.7% over the measured extrema;
- normalized spatial NPS bands remain close and show no global shift to a
  genuinely larger grain radius;
- T031 projection centre has 99.99th-percentile frame jumps about 8.6% higher,
  with thresholded maximum clusters increasing from 3 to 20 pixels;
- T031 scan reaches a local 99.99th-percentile frame-jump ratio of 1.53 and a
  local four-RMS burst-frequency ratio of 6.47;
- lag-one temporal correlation falls consistently in T031, which makes the
  grain read as more freshly redrawn or boiling even when RMS is similar.

T002 does not reproduce the effect. T007 reproduces it weakly. T031 reproduces
it strongly, so this is not a global grain-size change; it is a scene- and
tone-conditioned tail interaction with one deterministic stochastic
realization.

## Website-proxy finding

The current V34 and V35 hover loops use matched settings: 1920 x 1440,
8-bit 4:2:0 H.264, CRF 22, `tune=grain`, inter-frame prediction. Nevertheless,
inter-frame coding reacts differently to the two independent grain mosaics.

For T031 on the published proxies:

| Branch | Native median temporal RMS ratio | Website median ratio |
| --- | ---: | ---: |
| Projection | 1.0089 | 1.1766 |
| Scan | 1.0253 | 1.2424 |

The proxy therefore converts a modest native difference into roughly 18–24%
more median frame-difference energy. It also increases tail kurtosis and lowers
lag-one correlation. This is a codec presentation error, not a new 5279
measurement.

An experimental all-intra H.264 CRF-16 encode reduced the T031 projection
median ratio from about 1.15 in a matched inter-frame experiment to 1.042. It
cost about 18 MB per one-second branch instead of 4.6–4.7 MB. Short-GOP,
all-intra and 10-bit browser-compatible candidates should be evaluated against
both perceptual fidelity and mobile bandwidth before replacing the website
media.

## What can be retained for 8 mm / 16 mm

The Philox-u32 finite-site engine is useful for a future coarse-format branch,
and the current turbulent realization is a valuable stress reference. It is
not, by itself, an authentic 8 mm or 16 mm model: the spatial grain scale,
processed-stock MTF, scanner aperture and deterministic edge response are still
the 35 mm model. Calling it 8/16 mm now would preserve exactly the scale mismatch
identified by the viewer.

A genuine smaller-format profile must change the system together:

- grain size relative to the projected frame area;
- negative and print MTF relative to output pixels;
- lens and scanner/print aperture;
- exposure-conditioned fast/medium/slow populations;
- temporal tails and any gate instability;
- delivery compression used to judge the result.

## Recommended V36 gates

1. Keep V34 Archive exact and retain the current V35 realization unchanged as
   a documented stress/coarse-format candidate.
2. Add native temporal p99/p99.9/p99.99, per-pixel temporal-variance tails,
   connected-burst area and lag-one correlation to the 35 mm gate.
3. Evaluate multiple global Philox domain salts across all three scenes. Use one
   global identity salt, never a per-shot aesthetic seed. Accept it only if it
   falls inside reference between-seed variation on every holdout.
4. If no global salt passes, return 35 mm Production to the V34 PCG64 sampler
   despite the speed cost; quality remains the primary boundary.
5. Replace or clearly qualify the H.264 hover proxy only after a short-GOP,
   intra or 10-bit candidate demonstrably tracks the native master.

## Artifacts

- Diagnostic implementation: `src/diagnose_v35_grain_perception.py`
- Native and proxy reports:
  `research_runs/2026-08-05_v35_grain_perception/`
- Codec experiments:
  `research_runs/2026-08-05_v35_grain_perception/proxy_experiments/`

These measurements are perceptual diagnostics, not published Kodak 5279
acceptance limits. They are deliberately used to reveal a blind spot in the
project's earlier energy-only validation, not to invent stock-specific data.
