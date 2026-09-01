# 5279 Studio

A local, CPU-only application that exposes any video onto Kodak VISION 500T
5279, forms the negative with finite silver-halide sites, and observes it two
ways: as a 2383 print projected under xenon, and as a Spirit 2K scan finished
for Blu-ray. Everything is the research engine's physics (V72 record
formation, V49 common-density grain, V61–V66 spectral chain) with the V87 dense
lattices; there is no LUT look and no creative grade.

把任意视频曝光到柯达 5279 负片、以有限银盐位点形成颗粒，然后以 2383 拷贝氙灯
放映或 Spirit 2K 扫描蓝光成片两种方式观察。默认参数即 5279 的质感和颜色。

## Run

```bash
pip install -r studio/requirements.txt      # numpy, opencv, numba, ffmpeg binary
python3 studio/app.py                       # http://127.0.0.1:8765
```

Python 3.11+. The first start builds the two spectral lattices (about four
minutes on four cores) and caches them in `studio/cache/`. No GPU is needed.

## Workflow

1. Open a clip: type a path, browse the machine, or drop a file onto the page.
   Container colour tags choose the input transfer and gamut; override them if
   the footage is log (V-Log, S-Log3, LogC3), HLG or PQ.
2. Scrub, and compare views: `2383 PRINT`, `BLU-RAY SCAN`, `NEGATIVE` (the
   orange-masked negative on a light table), `SOURCE`, or an `A / B` split.
   `1:1 CROP` renders a full-resolution crop around the point you clicked so
   grain is judged at export scale.
3. Adjust parameters; the preview re-renders on release.
4. Export: choose the branches (film print, Blu-ray scan, Cineon DPX
   printing-density sequence), codec (ProRes 4444 / 422 HQ, H.264, H.265,
   16-bit PNG), frame range and output folder. Audio is copied from the source.

## Parameters

| group | control | meaning |
| --- | --- | --- |
| Input | transfer / gamut | decode the source to scene-linear Rec.709 |
| Input | exposure | stops applied before the negative; 0 places the source's 18 % gray normally, the GH7 RAW research baseline used +0.45 |
| Input | sensor-noise separation | edge-aware removal of electronic noise before the emulsion |
| Input | GH7 chart residual | V41 chart-informed chroma residual (research footage only) |
| Stock & gate | gate / format | Super 35, Academy, Super 16, 16 mm, VistaVision: the same emulsion, different grain size in frame |
| Stock & gate | halation | rem-jet-limited red halation and base scatter (1.0 = 5279) |
| Stock & gate | dye-cloud size / grain amount | morphology scale and stochastic amplitude (1.0 = Kodak 48 µm RMS) |
| Stock & gate | grain quality | 5 dye-cloud size classes (export) down to 1 (fast preview) |
| Stock & gate | grain law | `V49 common`: one density field shared by the records (default); `V72 independent`: three independent records |
| Stock & gate | oversample / seed | 2× internal raster for low-resolution sources; stochastic seed |
| Observers | projection colour authority | `physical`: direct 5279→2383→xenon→CIE; `scan-referenced`: V31 policy with hue/chroma from the scan |
| Observers | projector flare | additive screen flare (0 = scene-referred master) |
| Observers | scan aperture | 2K Spirit (default), 4K, or none |
| Observers | Blu-ray finish grain | `V49 direct` (default) or the historical `V46 managed` opponent-grain finish |
| Delivery | output transfer | Rec.709 / BT.1886 masters or sRGB companions |

## Speed

About 17 s per 1080p frame on a 4-core CPU with the full five-class grain
model (the engine already uses every core through Numba and OpenCV, so the
export queue starts one process per four cores). `grain quality = 1` is
roughly three times faster; a 960-px preview takes 5–6 s.

## Layout

```
studio/app.py            launcher
studio/server.py         HTTP API (stdlib) and export queue
studio/ui/index.html     the interface (no build step)
studio/film5279/         the engine
  priors.py              frozen V72 tables generated from the research engine
  spectral.py            Status-M inverse, 2383 printing, projection, V87 lattices
  negative.py            exposure, H-D, DIR, finite-site grain, MTF
  observers.py           2383 projection and Spirit/Cineon/Blu-ray observers
  video.py               ffmpeg decode/encode, DPX
  fast.py                Numba kernels
studio/tests/            regression tests (python3 studio/tests/test_film5279.py)
```
