# 5279 Emulsion Project

A bilingual, evidence-led reconstruction of Kodak VISION 500T 5279 image formation from Panasonic GH7 ProRes RAW. The project models finite silver-halide events, dye clouds, speed layers, DIR interimage effects, the coloured negative mask, Kodak 2383 print formation, and a period 2K scan.

中文网站记录从 GH7 ProRes RAW 到 5279 负片、2383 放映与时期 2K 扫描的研究、算法、错误复盘和逐版画面对照。艺术调色始终留在 baseline 之外。

## Live site

[lovejzzz.github.io/90sKid](https://lovejzzz.github.io/90sKid/)

## Current release: V44 observer integrity · V42 image baseline

- V44 withdraws V43H's unmeasured negative-NPS, Spirit and stochastic-2383 candidates
- V41's chart-bounded image model remains frozen through the V42 engine-conformance baseline
- Runtime gates enforce the accepted V37–V41 grain, density, colour and observer boundaries
- The validated Philox-u32 Bernoulli Metal graph is the Production default; Archive CPU remains reproducible
- Projection retains 2383 lightness/texture and the gated V31 normal-process low-frequency scan-chroma boundary
- One native 5760×4320 12-bit BT.1886 master is picture authority
- Display review decodes the master to linear light, performs pixel-area integration, then applies sRGB
- Review stills decode the same frame from the final encoded review movie
- Native-frame release gates reject sparse chroma impulses and metadata mismatches
- T003 DKC-Pro control documents what the outdoor chart does and does not identify
- Public deployments stream optimized comparison media from the GitHub Pages archive; full masters remain local

## Reconstruction engine

The recovered research engine, V24–V42 profiles, measurement scripts and the
new explicit-stage API live in [`engine/`](engine/). Full-resolution RAW and
rendered video remain local and are excluded from Git. The explicit API keeps one
shared stochastic negative and derives projection and scan observers plus two
colour-explicit delivery encodings from one encoded picture authority.

See [`engine/V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md`](engine/V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md)
for the recovery provenance and research-to-code matrix, and
[`engine/V44_OBSERVER_INTEGRITY_AND_SCALE_HONEST_REVIEW_2026-08-10.md`](engine/V44_OBSERVER_INTEGRITY_AND_SCALE_HONEST_REVIEW_2026-08-10.md)
for the observer ablations, display-sampling equation and current limits.

## Local development

Requires Node.js 22 or later.

```bash
npm ci
npm run dev
```

Validation commands:

```bash
npm test
npm run build:pages
```

`npm run build:pages` creates the static GitHub Pages site in `out/`. Pushing `main` runs the Pages deployment workflow automatically.

## Evidence boundary

Published 5279 material constrains neutral characteristic curves, MTF, spectral sensitivity, net dye density and 48 µm diffuse RMS granularity. It does not identify a unique frequency-resolved grain NPS, proprietary three-layer coating recipe, stock-specific DIR matrix, or Spirit scanner spectral calibration. Those quantities remain explicit model priors until physical measurements are available.
