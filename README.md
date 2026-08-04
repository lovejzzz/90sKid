# 5279 Emulsion Project

A bilingual, evidence-led reconstruction of Kodak VISION 500T 5279 image formation from Panasonic GH7 ProRes RAW. The project models finite silver-halide events, dye clouds, speed layers, DIR interimage effects, the coloured negative mask, Kodak 2383 print formation, and a period 2K scan.

中文网站记录从 GH7 ProRes RAW 到 5279 负片、2383 放映与时期 2K 扫描的研究、算法、错误复盘和逐版画面对照。艺术调色始终留在 baseline 之外。

## Live site

[lovejzzz.github.io/90sKid](https://lovejzzz.github.io/90sKid/)

## Current baseline: V29

- Complete 165-frame, 5760×4320 motion validation
- 12-bit ProRes 4444 projection and period-scan masters
- A new finite-site emulsion keyed by absolute source-frame number
- Bit-exact segment-boundary validation
- Source 24-bit, four-channel PCM and timecode retained in local masters
- Public website includes only optimized stills and short hover previews, not the full output masters

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
