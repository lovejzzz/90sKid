# V61 — 5279 ISO Status-M / joint analytical-density audit

Date: 2026-08-11
Status: evidence-corrected candidate; native one-frame validation passed
Image change from V60: negative density coordinate only

## Trigger

V51 had recovered the five vector paths in Kodak H-1-5279t correctly, but its
report explicitly left `Midscale Neutral` unused. Re-reading that graph beside
the current code exposed a more fundamental mismatch: V42--V60 treated three
hand-fitted Gaussian receivers as Status M, then converted each measured H-D
density independently to one dye amount.

That is not a valid coordinate for an orange-masked colour negative. A Status-M
receiver integrates the complete spectral transmission: D-min, formed dye,
unwanted absorption and the opposite density change caused by consumed
coloured masking couplers. It is a three-equation joint inverse, not three
unrelated one-dimensional shapers.

## What the old research got right

- V51's vector paths and interpretation of small negative lobes as net
  dye/coupler changes are correct.
- The dashed `Minimum Density` path is a separate orange-mask/base spectrum and
  must be present for optical printing but removed by scanner D-min setup.
- `Midscale Neutral` is not a fourth dye. It is a measured complete-spectrum
  witness for a typical neutral negative.
- V58--V60's 2383 integral Status-A and D-min registration corrections remain
  valid and are unchanged by V61.
- V57 correctly showed that a neutral LAD patch cannot identify a 3-D
  interimage transform.

The missed item was the coordinate between the 5279 H-D graph and the recovered
net spectra.

## Midscale Neutral closes the spectral model

Let Kodak's traced net curves be (C(\lambda),M(\lambda),Y(\lambda)) and the
dashed base be (D_{min}(\lambda)). Least-squares decomposition of the fourth
traced curve gives

\[
D_{mid}(\lambda) \approx D_{min}(\lambda)
+0.471262C(\lambda)+0.610124M(\lambda)+0.735709Y(\lambda).
\]

The RMS spectral-density residual is `0.00797 D`, and the maximum residual is
`0.01702 D`. A free multiplier on D-min changes the fit by almost nothing
(`0.99496`), so the result is not hiding a missing base term. This is strong
evidence that the vector trace and net-density interpretation are internally
self-consistent.

Through the restored ISO receiver, the same midscale curve measures:

| quantity | R | G | B |
|---|---:|---:|---:|
| total Midscale Neutral | 0.74634 | 1.26834 | 1.58171 |
| spectral D-min | 0.15593 | 0.57436 | 0.88336 |
| density above D-min | 0.59041 | 0.69398 | 0.69836 |

The V61 joint inverse returns analytical C/M/Y
`0.473884 / 0.608837 / 0.735183`, within `0.0027` of the direct spectral fit;
forward closure is below `4e-8 D` per channel. The remaining difference is the
expected consequence of fitting a 20 nm drawn curve and then evaluating its
integral receiver at 1 nm.

## ISO Status-M correction

ISO 5-3:1984 Table 4 defines the log spectral products and tail slopes. The
2009 revision states that the relative spectral products did not change. V61
versions the printed 10 nm values, verifies them by SHA-256, interpolates the
log products to 1 nm, applies the published tails and normalizes the resulting
linear weights.

| receiver | Archive sampled peak | ISO peak | cosine similarity | L1 difference |
|---|---:|---:|---:|---:|
| Red | 680 nm | 640 nm | 0.2643 | 1.4746 |
| Green | 540 nm | 540 nm | 0.9568 | 0.3478 |
| Blue | 440 nm | 450 nm | 0.9865 | 0.2048 |

The Archive Gaussian parameter was centred at 690 nm; its 20 nm sampled maximum
falls at 680 nm. This was not a harmless narrow-band approximation. The red
receiver was materially displaced from the ISO definition and therefore
misread both cyan formation and the long-wavelength orange-mask tail.

## Joint inverse

For analytical amounts (a=(c,m,y)), V61 computes registered Status-M density

\[
d_j(a)=-\log_{10}\!\left(\sum_\lambda
W_j(\lambda)10^{-[D_{min}(\lambda)+a\cdot S(\lambda)]}\right)
-d_j(0).
\]

It solves (d(a)=d_{H-D}-d_{min,H-D}) with a projected Gauss-Newton method and
the physical constraint (a\ge0). Reachable colours close numerically; an
impossible independent triplet is mapped to the nearest nonnegative dye
mixture instead of inventing negative dye.

Only `64.85%` of the complete artificial `0..2.8 D` independent RGB cube is
exactly reachable. That is expected: the cube is the Cartesian product of
three densitometer readings, not the physical gamut of one masked three-layer
negative. The relevant check is developed real material.

On 43,200 spatial samples from the actual T020 ProRes RAW frame after V60's
unchanged input, exposure, H-D and interlayer formation:

- `93.611%` close below `1e-5 D` in every channel;
- nonnegative boundary is active on `6.396%`, mostly very thin shadows;
- RMS projection error is `0.00569 / 0.00083 / 0.00030 D` R/G/B;
- maximum error is `0.10193 / 0.02092 / 0.01048 D`.

This supports the joint model on actual material without pretending that every
synthetic densitometer triplet is physically realizable.

## Negative-to-2383 cross-check

At net Status-M `0.7 / 0.8 / 0.8`, the row-normalized local Jacobian from
negative density to the three 2383 record-weighted printing densities changes
from

```text
V60
1.0000   0.3689   0.0193
0.1045   1.0000   0.2451
0.0562   0.0899   1.0000
```

to

```text
V61
1.0000  -0.0322   0.0085
0.0020   1.0000   0.0606
0.0314   0.0146   1.0000
```

The large V60 G-to-R and B-to-G terms were largely created by the independent
Gaussian coordinate itself. Ado Ishii's measured EK5218-to-2383 linear witness
has row-normalized off-diagonals `0.0748/0.0178`, `0.1528/0.0618` and
`0.0851/0.1363`. V61 is not declared “matched” to that matrix: Ishii explicitly
states that every negative stock must be profiled, and the paper does not
publish its measured EK5279 coefficients. The comparison only bounds gross
cross-talk; it cannot substitute EK5218 for EK5279.

## Native validation

T020 frame 0 was rendered at 5760 × 4320 with the same absolute frame, V60
grain identity, exposure, 2383 observer, scan observer and 12-bit delivery.

- Production compute: `30.69 s`; total wall including delivery: `41.45 s`.
- All 50 current regression tests pass.
- Both professional masters are 12-bit ProRes 4444 XQ with the established
  Rec.709/BT.1886 authority and derived sRGB review chain.
- V60-to-V61 1920-wide review PSNR: `32.17 dB` projection, `33.48 dB` scan.
- Mean encoded displacement stays below `0.0015` per channel, while local
  colour differences are real (99th-percentile absolute code delta about
  `0.073`).

The PSNR is a change measurement, not a truth or quality score.

Outputs:

- `outputs/native_5k_v61_iso_status_m_joint_1f/T020/projection/`
- `outputs/native_5k_v61_iso_status_m_joint_1f/T020/bluray_scan/`

The machine-readable audit is
`engine/research_runs/v61_5279_status_m_audit.json`.

## Remaining boundary

V61 fixes an identifiable error but does not make the complete colour model
identified. The largest remaining uncertainty is now easier to see:

1. `PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE` was fitted to a cross-vendor
   finished-LUT median; it is not a Kodak 5279/2383 measurement and can
   conflate negative printing density, 2383 interimage and display rendering.
2. Ishii measured more than 400 EK5279-to-2383 colours and obtained about
   `0.022/0.023/0.027 D` RMS with a 3×13 polynomial, but did not publish its
   EK5279 coefficients. A 3×3 shortcut is not sufficient over the full range.
3. The Spirit optical-film-match/primary matrix and actual period scanner
   spectral sensitivities remain proprietary.
4. Kodak's graphs are representative curves, not same-batch numerical
   spectrophotometry.

Therefore V61 deliberately retains the Archive 2383 interimage and display
boundaries, marks them unmeasured, and does not tune saturation or hue by eye.
The next justified experiment is a measured/interpretable interimage ablation,
not another aesthetic matrix fit.

## Sources

1. Eastman Kodak, [KODAK VISION 500T Color Negative Film 5279/7279,
   H-1-5279t (March 2003)](https://device.report/m/5e51c79d670196bba47e7f500a4d5cb6b040df42f004110fd5989ce056ea95b1.pdf).
2. ISO, [ISO 5-3:1984, Table 4 Status-M log spectral
   products](https://cdn.standards.iteh.ai/samples/20101/642e3ed0adfe43be85e67b2c413cca56/ISO-5-3-1984.pdf).
3. ISO, [ISO 5-3:2009 overview and revision
   notes](https://standards.iteh.ai/catalog/standards/iso/6cdfb60e-5093-43ae-b7a4-7102bd9170bd/iso-5-3-2009).
4. Eastman Kodak, [Processing Film Images for Digital Cinema,
   US20020118211A1](https://patents.google.com/patent/US20020118211A1/en).
5. Ado Ishii, [Color Management Technology for Digital Film
   Mastering](https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055),
   IS&T/SID Eleventh Color Imaging Conference, 2003.
