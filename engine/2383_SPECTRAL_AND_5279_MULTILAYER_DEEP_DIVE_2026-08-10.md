# 2383 spectral integration and 5279 multilayer development deep dive

Date: 2026-08-10  
Scope: V44 physical audit and exact execution optimization  
Image authority: frozen V44 unless a later profile explicitly adopts a candidate

> **V58/V59 correction (2026-08-11):** this document records the V44 audit and
> should not be read as the final 2383 coordinate model. H-61B's
> `1.09 / 1.06 / 1.03` are simultaneous integral Status-A readings, not three
> separated H-D coordinates (corrected in V58). The 2005 graph also contains a
> fourth `Visual Neutral` vector path whose residual supplies processed-print
> base/D-min spectral absorption (corrected in V59). The stored xenon samples
> match Kodak's generic lamp graph, not a measured projector/filter/lens/screen
> chain.

## Result in one paragraph

The architecture is fundamentally sound: the 5279 negative is formed once in
density space, its complete orange-mask spectrum remains in the optical-printer
path, 2383 is exposed through three broad records, Status-A print densities are
inverted to analytical dye amounts, and the transmitted xenon spectrum is
integrated to tristimulus light. The fast/medium/slow negative decomposition also
does not add a second neutral H-D curve, and V34 already removed the duplicate
deterministic adjacency term that was also present in Kodak's processed-stock
MTF. The largest newly demonstrated numerical weakness is later in the 2383
observer: it uses a 20 nm analytic approximation to the CIE 1931 observer. A
controlled reconstruction with the official CIE 1 nm table changed the 25-cube
linear-RGB LUT by RMS `0.0045692`, with maximum absolute node difference
`0.0398455`. That is large enough to test as a V45 spectral-reference candidate,
but it is not silently inserted into V44 because it changes colour.

## 1. What the optical chain actually computes

### 1.1 Negative to print exposure

For wavelength sample \(\lambda\), the developed 5279 negative is represented as

\[
D_{5279}(\lambda)=D_{min}(\lambda)+
\sum_{i\in\{C,M,Y\}} a_i D_i^{net}(\lambda).
\]

The `net` curves are important. Kodak's 5279 graph has D-min subtracted, so a
curve includes newly formed dye and the opposite change caused by consumption of
a coloured masking coupler. Negative lobes are therefore retained; a second
all-positive dye matrix would count unwanted absorption twice.

Transmission through the negative is

\[
T_{5279}(\lambda)=10^{-D_{5279}(\lambda)}.
\]

Each 2383 record receives a printer exposure proportional to

\[
H_j=\int L_{3200}(\lambda)\,T_{5279}(\lambda)\,S_j(\lambda)\,d\lambda,
\]

and the effective printer density is \(-\log_{10}(H_j/H_{j,clear})\). In the
implementation the wavelength grid is uniform, so its constant interval cancels
when every record weighting is normalized. Separate printer-light placements put
the 18-percent negative at LAD.

### 1.2 Print exposure to processed 2383

The separated R/G/B sensitometric curves map log printer exposure to Status-A
density. The published LAD target is `1.09 / 1.06 / 1.03`, not equal RGB
density. As corrected in V58, those numbers are the three simultaneous integral
Status-A readings of one neutral patch. They must first be spectrally resolved
to separated H-D coordinates; they are not themselves the three principal
curve densities.

The current interimage matrix acts in log exposure about LAD before these three
curves. This placement agrees with the published preview/patent architecture,
but its coefficients are an identified cross-vendor surrogate, not a disclosed
Kodak 2383 factory matrix. It must remain labelled empirical.

### 1.3 Processed 2383 to projected light

Status-A density is an integral instrument measurement, not directly a cyan,
magenta or yellow molecular amount. For each separated record the engine first
solves

\[
D_A(a_i)=-\log_{10}
\left(
\frac{\int 10^{-a_i d_i(\lambda)}w_{A,i}(\lambda)d\lambda}
{\int w_{A,i}(\lambda)d\lambda}
\right)
\]

for dye amount \(a_i\). The combined print spectrum is then

\[
T_{2383}(\lambda)=10^{-\left[D_{base}(\lambda)+\sum_i a_i d_i(\lambda)\right]}.
\]

Finally,

\[
XYZ=k\int E_{xenon}(\lambda)T_{2383}(\lambda)
[\bar x,\bar y,\bar z](\lambda)d\lambda,
\]

followed by a declared Bradford adaptation to D65 and the linear Rec.709 matrix.
This is spectral integration; it is not a three-channel saturation curve.

## 2. Findings about 2383

### 2.1 Peak-normalized dye curves are not a missing saturation multiplier

Both the 2005 and 2026 Kodak sheets say the cyan, magenta and yellow curves are
peak-normalized. Blindly forcing each digitized column to a peak of one is not a
valid colour correction. In this model the separated Status-A inverse changes
the recovered dye amount by the reciprocal scale, so a per-dye spectral scale
largely cancels when the combined spectral density is formed. Only the finite
amount-axis ceiling near extreme D-max prevents exact global invariance. Shape,
especially unwanted absorption, is the useful public information.

### 2.2 The official CIE table matters

The accepted LUT uses 21 samples from 380 to 780 nm and a smooth analytic fit to
CIE 1931. The audit linearly interpolated the same digitized 2383 dye curves and
the same Kodak-graph xenon SPD to 1 nm, then integrated with the official CIE
1931 2-degree table and trapezoidal endpoint weights. Against all `25^3` LUT
nodes:

| comparison | value |
|---|---:|
| linear-RGB RMS difference | `0.0045692` |
| maximum absolute node difference | `0.0398455` |
| clear-print white difference | below `5e-7` |

White remains fixed because each observer is normalized and adapted from its own
source white. The difference is therefore mainly a coloured-transmission error,
not exposure or white balance. A V45 candidate should replace only the CMF and
quadrature, rebuild the offline LUT, and then repeat opponent-tail, neutral-scale,
ColorChecker and real-frame gates.

### 2.3 The xenon spectrum is an evidence boundary, not the dominant tested error

Kodak publishes a plotted xenon viewing condition, not a numerical projector SPD
for one historical theatre installation. The current 21-point SPD is a visual
digitization with extrapolated 380 nm and 720–780 nm tails. Moving to 1 nm avoids
observer-integration error but cannot manufacture unmeasured xenon line structure,
lamp ageing, reflector/filter transmission, screen reflectance or auditorium
flare. Those belong in named observer conditions, not in the 2383 dye model.
The later V59 white-adapted 17-cube bracket found maximum OKLab differences
below 0.89 across generic xenon, 5400 K/6420 K Planck proxies and equal energy.
That does not identify a theatre, but it rules out reasonable illuminant choice
as the cause of the much larger historical blue/purple casts.

### 2.4 The era reference should be the 2005 sheet

5279 and 2383 overlapped historically. The March 2005 H-1-2383t document is
therefore a better baseline for a 5279-era theatrical print than the revised
March 2026 sheet. Both documents agree on the layer order, LAD triplet, visual
neutral requirement, peak-normalized dye curves and xenon viewing intent. The
process label changed from ECP-2D to ECP-2E, so any later curve revision must be
treated as a separate coating/process observation rather than silently merged.

## 3. Findings about 5279 multilayer development

### 3.1 What is measured and what is reconstructed

Kodak directly constrains the processed stock through three H-D curves, three
48-micrometre diffuse-RMS granularity curves, processed-film MTF and net spectral
dye-density curves. It does not publish the 5279 coating's exact nine-population
formula, DIR species, interlayer coverages, record covariance or noise-power
spectrum.

The engine's fast/medium/slow split is consequently a constrained reconstruction:

- the 0.5 and 0.8 log-exposure separations, representative grain ECDs and
  coupler-coverages come from a same-era Kodak multilayer patent example;
- the summed mean is forced back to the published 5279 H-D response;
- finite sites use \(p(1-p)\), so a population becomes quiet when unexposed or
  saturated instead of emitting perpetual additive noise;
- the final 48-micrometre density variance is normalized to Kodak's graph.

These steps make the result physically organized, but do not uniquely identify
the microscopic coating or its full spatial spectrum.

### 3.2 No duplicate neutral sensitometry

For 21 neutral log exposures from -4 to +1, the developed multilayer result
matched direct interpolation of the published H-D curves within
`2.3842e-7 D`. The new regression gate permits only `3e-7 D`. The documentation
should call this numerically equivalent, not bit-for-bit identical, because
partitioning and summing float32 layer densities introduces one-ULP rounding.

### 3.3 Deterministic acutance is owned once

Kodak's 5279 MTF is measured after processing and already includes developer
adjacency. V34 set deterministic intralayer DIR acutance to zero, preventing a
second neutral-edge boost. The remaining deterministic cross-record interimage
term affects colour separations before layer summation. In a 64-patch random
uniform-colour audit its departure from independent H-D curves was median
`0.000408 D`, maximum `0.001063 D`: restrained, but still an empirical 5279
surrogate rather than a measured stock matrix.

### 3.4 Stochastic DIR is not an overlay, but remains underidentified

Finite population events are formed in density space, transported among layers,
mixed into dye records and only then observed through scan or print. This is the
correct architectural meaning of “grain is the image.” The stochastic coupling
is zero-mean before the published-RMS calibration, but Kodak's marginal RMS
curves do not reveal cross-record covariance or the 2D NPS. The current boiling
character therefore cannot be certified from those RMS curves alone. A future
measurement must use scanned uniform 5279 patches at several exposures, retain
native scanner sampling, and estimate per-record auto/cross spectra.

## 4. Exact execution work accepted during this audit

Three changes reduce work without changing the frozen image:

1. The mean and stochastic negative paths share one log-exposure tensor and one
   fast/medium/slow activation tensor.
2. Deterministic and stochastic interlayer Gaussian departures use a dedicated
   four-worker executor; the rest of the full-frame array graph remains at eight
   workers. Native tests showed four workers were faster for this bandwidth-bound
   stage.
3. Float32 forward linear-Rec.709-to-OKLab conversion in the 2383 monitor graph
   uses one fused compiled kernel. Float64 inputs retain the original NumPy path,
   and the inverse direction was rejected because its rounding was not exact.

T020 frame 0, 5760 by 4320, Production Metal, two observer branches:

| stage | seconds |
|---|---:|
| negative formation | `14.1409` |
| dual observer | `12.9919` |
| BT.1886 encode | `0.4508` |
| total | `27.5836` |

Frozen encoded-array hashes remained exact:

- projection: `cfa0d3992e801932963b764704da07a924f53e2eb2b985827632362d53b691a7`
- scan: `b32e7529dd399dd778783daaacde0bd456b3b8ebc1b0053fd9a58e3a3da58f08`
- formed negative: `21310907e675c50dee7c9d2fbc715959876948e9bfdab5a52b01bf527646918a`

Rejected during the same audit: larger observer stripes, approximate inverse
OKLab fusion, and CPU/GPU overlap of adjacent population classes. None produced a
stable exact benefit.

## 5. Recommended next profile

The next image-changing profile should be a spectral-reference experiment, not
a saturation adjustment:

1. Use the official CIE 1931 2-degree 1 nm table.
2. Interpolate the historical 2005 2383 dye and xenon graph samples onto the same
   integration grid; retain an explicit uncertainty band for graph digitization.
3. Keep Status-A inversion, LAD, H-D, Callier and monitor adaptation separate.
4. Publish old/new neutral ramps, six primary/secondary trajectories, ColorChecker
   metrics and T020/T032/T007 moving comparisons.
5. Do not retune the nine-population or DIR constants in the same version. That
   would make a spectral correction impossible to identify.

## Sources

1. Eastman Kodak, [KODAK VISION Color Print Film 2383/3383, H-1-2383,
   revised March 2026](https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf).
2. Eastman Kodak, [KODAK VISION Color Print Film 2383/3383, H-1-2383t,
   March 2005 archival copy](https://125px.com/docs/motionpicture/kodak/lab/lab_h12383t.pdf).
3. Eastman Kodak, [LAD for KODAK VISION Color Print Film,
   H-61B](https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf).
4. CIE, [CIE 1931 colour-matching functions, 2-degree observer, 1 nm,
   DOI 10.25039/CIE.DS.xvudnb9b](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer).
5. Eastman Kodak, [The Essential Reference Guide for
   Filmmakers](https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf).
6. Eastman Kodak, [VISION 500T Color Negative Film 5279, H-1-5279,
   March 1996 archival copy](https://125px.com/docs/motionpicture/kodak/5279.pdf).
7. Eastman Kodak, [US 6,686,136 B1, colour-negative interimage and DIR
   mechanisms](https://patents.google.com/patent/US6686136B1/en).
8. Eastman Kodak, [US 5,314,793, representative multilayer speed and
   granularity architecture](https://patents.google.com/patent/US5314793A/en).
