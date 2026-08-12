# V47 SHM: Silver-Halide Morphology comparator

Date: 2026-08-11
Status: experimental comparator; controlled Silver Efex Tri-X fit, not 5279 measurement

## Decision

V47 adds **SHM (Silver-Halide Morphology)** as a separate comparator. It does
not replace the physical 5279 branch. Its purpose is to test the strongest
useful lesson from Silver Efex: density is formed by a finite, spatially
organized population; a finished RGB noise plate is not added afterward.

“Silver Efex-like” here means that confirmed mathematics and controlled output
statistics are reproduced by independent code. The controlled black-box run was
performed through the installed application UI because the processing path is not
exposed through a public command-line interface. It does **not** mean that DxO's
copyrighted stock patch, program code, or every undisclosed decision has been
copied. It also does not turn a monochrome still-image product into evidence
for 5279's three-record colour-negative morphology.

## New evidence in this cycle

A neutral 2048 × 2048, 16-bit TIFF containing a continuous ramp, sixteen flat
steps, and a hard edge was processed in the locally installed Nik 8 Silver
Efex. The Film Grain (Branded) filter was set to Kodak Tri-X 400, Intensity 100,
Grain Size 1, then exported as uncompressed 16-bit TIFF.

The flat fields showed:

- middle-tone signal RMS rising to approximately 0.0143;
- normalized horizontal/vertical lag-one correlation near 0.38 across tones;
- positive skew around 0.09–0.15 and positive excess kurtosis around 0.17–0.37;
- a strongly asymmetric tone-amplitude envelope, but no evidence for a large
  tone-dependent change in normalized grain radius.

This rejected the first SHM prototype. Its `N=176` setting produced about
0.0286 RMS on the real frame—roughly twice the Tri-X black-box result—and its
large shadow/highlight scale bias manufactured false “breathing.” Those
settings were not released.

## Accepted SHM formulation

The deterministic V46 observer result is converted to its sRGB signal domain.
Silver Efex's confirmed scalar axis is used:

\[
Y=0.299R+0.587G+0.114B.
\]

Three independent isotropic Gaussian population fields at native-pixel scales
0.45, 0.90 and 1.80 are combined with weights 0.50, 0.27 and 0.23. A slow
occupancy field changes the local fine/coarse population balance without
changing the local image mean. A weak second Hermite term creates asymmetric
clusters and voids, while a third Hermite population supplies the independently
measured thick tails:

\[
Z'=Z+a(x,y,Y)(Z^2-1).
\]

\[
Z''=Z'+b(Z'^3-3Z'),\qquad b=0.020.
\]

The latent field is mapped to a uniform variate. A 512 × 512 inverse-binomial
lookup then forms a finite-site density candidate with `N=1250`:

\[
G(Y,U)=F^{-1}_{\operatorname{Binomial}(N,Y)}(U)/N.
\]

The confirmed Silver Efex endpoint taper `A(Y)` and the measured Tri-X
flat-field envelope `T(Y)` control participation:

\[
Y'=Y+s\,A(Y)\,T(Y)\,[G(Y,U)-Y].
\]

Only this scalar density axis moves. The deterministic signal opponent field
is held fixed; gamut boundaries limit the requested scalar excursion rather
than modulating chroma with the random variate. This prevents the sparse RGB
“broken television” impulses seen in the rejected V39 experiment.

## Statistical gate

The earlier candidate matched RMS and lag but failed a stricter audit: its
formed-density excess kurtosis was slightly negative, unlike the controlled
Tri-X values of approximately 0.17–0.37. It was stopped during the 24-frame
render and never released. The accepted thick-tail formulation measured:

| Tone | lag-1 | skew | excess kurtosis | local spectral-ratio CV |
|---|---:|---:|---:|---:|
| shadow | 0.3795 | 0.1261 | 0.3034 | 0.0767 |
| middle | 0.3860 | 0.1334 | 0.2809 | 0.0771 |
| highlight | 0.3914 | 0.1373 | 0.2610 | 0.0773 |

The executable audit owns the final numeric table. In addition to the broader
five-stock envelope, it now has an explicit positive-thick-tail gate so an
ordinary correlated Gaussian field cannot pass merely by matching RMS and
lag. Local spectral-ratio variation must also remain nonzero; SHM is not one
stationary blurred Gaussian field.

## Image gate

A 5760 × 4320 T020 frame was reconstructed from the V46 deterministic mean and
encoded as 12-bit ProRes 4444 XQ through both projection and scan observers.
The rejected prototype and accepted Tri-X fit were both inspected at native
1:1 and after 1920-pixel linear-light area integration. The accepted fit:

- no longer reads as the coarse `N=176` layer;
- preserves projection/scan colour separation;
- has effectively zero stochastic mean bias;
- produces no independent RGB impulses;
- survives area integration as subtle texture rather than aliased coarse grain.

## Withheld claims

- The SHM morphology is not a pixel-identical Silver Efex replica.
- Tri-X is a B&W still-film reference, not a substitute measurement for 5279.
- Silver Efex's automatic resolution/film-format scaling remains to be measured
  at multiple export resolutions.
- Motion-picture temporal morphology is not identified by a still-image tool.
  SHM renews its stochastic field for each frame without translation or global
  phase animation; temporal validation is reported separately.

## Sources

1. DxO, [Nik Silver Efex user guide](https://userguides.dxo.com/nikcollection/en/silver-efex/).
2. DxO, [The science of film](https://www.dxo.com/en/technology/science-of-film).
3. Local read-only executable/resource audit in
   `SILVER_EFEX_GRAIN_RESEARCH_2026-08-06.md`.
4. Kodak, *KODAK VISION 500T Color Negative Film 5279 / 7279* technical data.
