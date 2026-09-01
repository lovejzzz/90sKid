# V87 — Dense spectral lattice gate and the measured shadow consequence

Date: 2026-09-01

Public profile key: none (research + engine-infrastructure release; the
image profile stays V72 / public V49). The result is executed in code by the
standalone `studio/film5279` engine, which replaces the historical 29-cube and
25-cube caches with the lattices selected here.

中文摘要：V86 发现运行时 29³ 印片密度格子在趾部有最大 0.014 D 的误差，并推测这
是“青绿阴影”的来源。V87 在 Linux CPU 上复现了这个误差（−2.98 logE 处
+0.0112/+0.0077/+0.0024 D），并测得它在显示端的真实后果：是**消色的趾部提亮**
（OKLab ΔL ≈ +0.011，显示亮度 0.0009），彩度偏移只有 0.0003–0.0012 OKLab，方向
不稳定——因此 V86 的“青绿阴影”推断不成立。以 2 次幂间距的 129³ 格子在可达密度
上把趾部误差压到 0.00079 D、中段 0.00005 D，显示误差 p99 < 0.0001 OKLab；剩余的
0.0014–0.0046 D 只出现在物理上不可达的微观三元组（非负染料量投影的折点），
不是格子分辨率问题。此外首次审计了 2383 放映 25³ 格子：中性轴最大 0.024 OKLab
误差，129³ 后降到 0.0056（成片帧 p99 0.00015）。

## Question

V86 set five gates before any new image release:

1. replace or densify the 29-cube joint spectral printer stage;
2. rebuild scan and projection from the same direct spectral authority;
3. shadow printer-density error below 0.001 D;
4. mid-scale drift below 0.001 D;
5. compare baseline, scan and projection on identical decoded frames.

V86 also inferred, from the sign of the toe error (red printer density
over-estimated most), that the runtime lattice could be the common cause of the
recurring green-shadow impression. That inference had not been measured.

## Method

`engine/src/audit_v87_dense_spectral_lattice_gate.py` runs on the V72 profile
(the numpy-2 batched `linalg.solve` call was made shape-explicit; results are
unchanged). The direct authority is the V61 joint nonnegative Status-M inverse
followed by 3200 K / 2383 spectral printing. The heavy sweeps use the studio's
Numba kernel of the same projected Gauss-Newton equations; on 15,660 mixed
probes it agrees with the original NumPy solver to 7.2e-7 D.

Probes: the neutral H-D locus at 0.01 logE steps, every ±1 σ Kodak-marginal
sign combination (27 per point), 100,000 uniform and 100,000 near-neutral
random triplets, and a complete formed 480×270 synthetic negative in both the
V49 common-density and the independent-record realization. A second audit
(`studio_lattice_display_audit.json`) repeats the display measurement on a
real 960×540 frame of Rec.709 footage through the studio engine.

Every observer table (2383 gray-scale neutral calibration, LAD viewing
transmission, Cineon mid/high scanner anchors, Spirit gray balance, monitor
display curve) is rebuilt under each printer authority, so both branches
really are derived from the same direct spectral chain (gate 2).

## Result 1 — the V86 error is reproduced

| probe | 29-cube max error (D) | p99.9 | mean |
| --- | ---: | ---: | ---: |
| neutral locus, toe (≤ −2.5 logE) | 0.01118 | 0.01117 | 0.00209 |
| ±1 σ cloud, toe | 0.01706 | 0.01671 | 0.00219 |
| ±1 σ cloud, mid-scale | 0.00041 | 0.00040 | 0.00013 |
| formed frame (V49 common) | 0.02849 | 0.02396 | 0.00106 |
| formed frame (independent records) | 0.02823 | 0.02373 | 0.00106 |

At −2.98 logE the neutral error is (+0.01118, +0.00772, +0.00239) D; V86 had
reported (+0.01101, +0.00767, +0.00237) at −3.0. Mid-scale already passes gate 4.
The largest errors of a formed negative are not on the neutral locus at all:
they sit at low-density triplets where grain pushes one record to D-min while
another stays positive.

## Result 2 — no trilinear lattice passes 0.001 D on unreachable triplets

| lattice | cells | build (s) | toe ±σ | mid ±σ | formed frame | near-neutral random |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform 29 (runtime) | 24,389 | 2.7 | 0.01706 | 0.00041 | 0.02849 | 0.02824 |
| uniform 57 | 185,193 | 16.9 | 0.01129 | 0.00011 | 0.01402 | 0.01413 |
| uniform 113 | 1,442,897 | 130 | 0.00692 | 0.00003 | 0.00683 | 0.00705 |
| power 2, 33 | 35,937 | 3.9 | 0.00333 | 0.00071 | 0.01757 | 0.01827 |
| power 2, 65 | 274,625 | 28 | 0.00135 | 0.00018 | 0.00743 | 0.00810 |
| **power 2, 129** | 2,146,689 | 191 | **0.00079** | **0.00005** | 0.00457 | 0.00486 |
| power 1.5, 129 | 2,146,689 | 127 | 0.00132 | 0.00003 | 0.00402 | 0.00407 |

The power-2 axis (density ∝ t²) closes gates 3 and 4 on every physically
reachable probe. The residual 0.004–0.005 D is localized: the direct solver's
own forward residual is 6e-8 D on the neutral locus and 1.2e-7 D on the
mid-scale cloud, but up to 0.012 D on the toe cloud and 0.144 D on formed
frames. Those triplets are outside the nonnegative dye gamut of the masked
negative; the solver returns the nearest physical mixture, and that projection
has a kink that trilinear interpolation cannot represent. This is the same
region V46 addressed with active-set microbricks. It is a property of feeding
signed microscopic density excursions into a Status-M inverse, not of the
lattice size.

On the real 960×540 frame through the studio engine: unreachable pixels are
0.63 % (V49 common), 2.2 % (independent records) and 0.31 % (deterministic);
lattice error is 0.00144 D at the worst of them, p99.9 = 4.9e-5 D.

## Result 3 — the 2383 projection lattice was also too coarse

The 25-cube 2383 Status-A → xenon/CIE lattice interpolates transmission-space
RGB across 0.17 D cells. Measured against the direct spectral integration:

| lattice | neutral axis max OKLab | formed frame p99 / max OKLab |
| --- | ---: | ---: |
| uniform 25 (runtime) | 0.0239 | 0.0059 / 0.0107 |
| uniform 65 | 0.0092 | 0.00055 / 0.00062 |
| **uniform 129** | 0.0056 | **0.00015 / 0.00016** |
| uniform 257 | 0.0011 | 0.00004 / 0.00004 |

The runtime cube's neutral-axis error is hidden by the gray-scale calibration
table (built through the same cube) but reappears on every perturbed value,
i.e. on grain. 129³ is retained (25 MB, built in 30 s).

## Result 4 — what the 29-cube error does to the picture

Both observers were rendered under the runtime cube and under the direct
authority on identical densities (gate 5). OKLab differences, runtime minus
direct:

| observer | probe | ΔL | Δa | Δb | chroma shift |
| --- | --- | ---: | ---: | ---: | ---: |
| projection | neutral toe −3.0 logE (Y = 0.0009) | +0.0114 | −0.00015 | +0.00116 | 0.0012 |
| projection | neutral toe −3.25 logE | +0.0063 | +0.00035 | −0.00025 | 0.0004 |
| projection | formed frame, darkest quartile | +0.0048 | −0.00031 | −0.00011 | 0.0003 |
| scan | neutral toe −3.0 logE (Y = 0.0002) | +0.0081 | +0.00009 | +0.00021 | 0.0002 |
| scan | formed frame, darkest quartile | +0.0034 | −0.00021 | −0.00010 | 0.0002 |

Per-pixel distances on the formed frame: projection mean 0.0015, p99 0.012,
max 0.0146; scan mean 0.0011, p99 0.0088, max 0.0104. Above −2.75 logE every
difference is below 0.0007.

Conclusion: the 29-cube defect is an **achromatic lift of the deepest toe**
(display luminance below 0.001) plus per-pixel grain lightness error, not a
hue cast. Its chroma component is 0.0002–0.0012 OKLab with an unstable
direction (199°, 65°, 97°, 325° across probes). The V86 "cyan/green shadow"
inference is therefore not supported; the green impression must have another
owner (candidates remain the scan-referenced projection colour policy of V72
and the D-min-registered 2383 base spectrum, both untouched here).

With the selected lattices the studio engine's display error against the
direct authority is: projection max 0.00066 OKLab (p99 4.6e-5), scan max
0.0024 at Y ≈ 1e-5 (p99 0.0010).

## Executable consequence

`studio/film5279` is a standalone CPU engine that carries the V72 negative
formation, the V49 common-density boundary and both observers with:

- printer density: power-2 129³ lattice (`printer_density_129_p2`)
- projection: uniform 129³ lattice (`projection_rgb_129`)
- every calibration table rebuilt from those lattices at start-up

Cross-checks against the recovered engine on the same decoded frame:
mean record density identical to 1.8e-6 D; per-class grain realizations
bit-identical with the archive NumPy sampler; stochastic DIR coupling 7.5e-9;
full formed-negative correlation 0.9987; observer OKLab distance mean 0.003
(dominated by the different grain realization after coupling), scan mean
0.0036. The optional counter-based sampler reproduces Kodak's 48 µm RMS on a
uniform field to 0.6 / 1.1 / 1.3 % (R/G/B) against the archive sampler's
0.6 / 1.4 / 1.2 %, with skewness below 0.01.

## What V87 does not claim

- It does not change the V72 image profile or any public release pixels.
- It does not identify the 5279 cross-record covariance (V80–V86 boundary).
- It does not remove the gamut-projection kink; a future finite-site sampler
  that keeps microscopic excursions inside the nonnegative dye gamut would
  remove the unreachable region at its source.
- It does not find the owner of the green-shadow impression; it only rules
  the 29-cube error out.

## Files

- `engine/src/audit_v87_dense_spectral_lattice_gate.py`
- `engine/research_runs/v87_dense_spectral_lattice_gate/audit.json`
- `engine/research_runs/v87_dense_spectral_lattice_gate/studio_lattice_display_audit.json`
- `studio/film5279/spectral.py` (lattice construction and sampling)
- `studio/tests/test_film5279.py` (gate 3 on physical probes is a regression test)
