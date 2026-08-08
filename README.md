# 5279 Emulsion Project

A bilingual, evidence-led reconstruction of Kodak VISION 500T 5279 image formation from Panasonic GH7 ProRes RAW. The project models finite silver-halide events, dye clouds, speed layers, DIR interimage effects, the coloured negative mask, Kodak 2383 print formation, and a period 2K scan.

中文网站记录从 GH7 ProRes RAW 到 5279 负片、2383 放映与时期 2K 扫描的研究、算法、错误复盘和逐版画面对照。艺术调色始终留在 baseline 之外。

## Live site

[lovejzzz.github.io/90sKid](https://lovejzzz.github.io/90sKid/)

## Current baseline: V41

- Two-chart-bounded colour transport: T003 fits the input-chroma residual direction, the independent T005 holdout confirms it, and only a conservative 12.5% step is applied
- Record-safe signed intermediates replace V40's hard basis clip; V40 grain, black, contrast and gamma stay frozen
- Matched physical 5279, FSD finite-site-density, and deterministic no-grain controls share the same V41 colour boundary
- Three one-second, 5760×4320 scene comparisons with 12-bit ProRes 4444 XQ masters
- Native-frame release gates reject sparse chroma impulses and metadata mismatches
- T003/T005 DKC-Pro controls document what the outdoor charts do and do not identify
- Public deployments stream optimized comparison media from the GitHub Pages archive; full masters remain local

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
