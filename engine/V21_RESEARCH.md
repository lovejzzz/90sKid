# V21 research and implementation: 5279 layer chemistry, grain formation, and period scanning

## Implementation result

V21 has now been implemented and rendered from the native GH7 ProRes RAW source.
The planned structural changes are present in the production path: record-specific
fast/medium/slow morphology, development-domain DIR before density summation,
stochastic population coupling, and separate Status-M, period-telecine and
optical-print observers.

The validation gates passed as follows:

- neutral H-D maximum absolute deviation: `2.3841858e-7 D`;
- 48 µm diffuse-aperture RMS error across the tested exposure range: about
  `0–1.5%` per colour record;
- separation-wedge DIR density changes remained bounded (about `0.00041 D` or
  less in the flat test separations);
- the representative projection/scan pair has about `4.80°` median and `10.55°`
  90th-percentile absolute OKLab hue separation, without a global purple/blue
  cast;
- both formal outputs are 5760×4320, 12-bit 4:4:4 ProRes masters with explicit
  Rec.709 primaries, transfer and matrix signalling.

One additional defect was found during implementation. V20's monitor projection
borrowed approximately 92% of scan hue and 94% of scan saturation, so its final
screenshots mainly differed in black level. V21 keeps the scan's neutral
lightness aim but retains bounded physical 2383 chromaticity. This corrects the
comparison rather than simply exaggerating contrast or saturation.

## Working conclusion

V20 is directionally correct, but two major approximations are now identifiable:

1. It applies most DIR/interimage behaviour after the fast/medium/slow populations have already been summed.
2. Its scanner measurement is based on narrow Status-M-like bands, although contemporary Kodak work explicitly distinguishes Status-M densitometry from the much broader and differently centred response of a telecine.

V21 should therefore move the colour interaction into the development domain and separate three different observers: Status-M measurement, a period telecine/data scanner, and the 5279-to-2383 optical print path.

## Evidence hierarchy

### Stock-specific constraints

- Kodak 5279 H-1-5279t: neutral R/G/B H-D curves, MTF, 48 µm diffuse RMS granularity, sensitivity and net spectral dye-density curves.
- These remain the final calibration targets. Nothing inferred from a patent is allowed to override them.

### Contemporary Kodak mechanisms

- US 5,500,316, filed December 1994: a motion-picture negative designed for both optical printing and electronic transfer. It describes the mismatch between negative dye spectra and a typical telecine, including red-channel magenta contamination, reduced cyan modulation, extra electronic gain and noise, and deliberate red-record contrast compensation.
- US 5,705,327, filed in the same development period: nonlinear toe/midscale curve design for high-speed negative and direct telecine transfer, with shadow visibility judged by professional telecine operators.
- US 5,298,376, filed 1991: DIR inhibitor transport, barrier-layer position and interimage colour saturation. It defines saturation from separation-exposure gamma divided by neutral-exposure gamma, rather than as a single global saturation control.
- US 5,314,793 remains the source for the existing representative fast/medium/slow decomposition. It is a structural bound, not a disclosed 5279 formula.

### Kodak manuals and factory material

- *Exploring the Color Image* and ECN-2 Module 7 confirm that developed silver is only an intermediate. Oxidised colour developer forms insoluble dye at developed silver sites; bleach and fixer then remove the silver image. The finished colour-negative image is the remaining dye image plus the process-surviving coloured mask.
- Kodak factory/quality-control footage shows step-wedge sensitometry, separate red/green/blue density traces, layer-isolating “candy stripe” samples, inline defect scanning and roll-level release decisions. This supports strict calibration and controlled variation; it does **not** justify adding arbitrary weave, flicker, dust or batch noise to a clean simulation.

## Findings that change the model

### 1. Grain is a dye-cloud field seeded by finite silver-halide sites

The useful physical chain is:

`photon exposure -> finite grain activation -> local silver development -> oxidised developer -> dye formation -> silver removed -> dye cloud observed`

The current binomial site model is a good basis, but the stochastic event should drive both dye formation and inhibitor release before the three populations are combined. Grain chroma should emerge from shared chemistry and spectral observation, not from three independent additive RGB noise images.

### 2. Fast, medium and slow geometry should be colour-record specific

V20 shares one representative ECD sequence (`1.24 / 0.82 / 0.60 µm`) among red, green and blue records. A 1994 Kodak motion-picture negative example instead uses strongly record-dependent tabular-grain architectures:

- cyan-forming record: `0.98 / 1.90 / 3.50 µm`
- magenta-forming record: `0.70 / 1.80 / 4.00 µm`
- yellow-forming record: `1.65 / 2.60 / 2.00 µm`, with a three-dimensional fast component

Those values are not claimed to be 5279. They prove that a universal three-size sequence is too restrictive. V21 should fit channel-specific morphology while forcing the finished result back to 5279’s published per-record 48 µm RMS curves and MTF.

### 3. DIR must become a development-domain reaction/diffusion step

V20 derives a release field from total developed density and applies a fixed receiver/causer matrix after summation. The Kodak DIR work shows that:

- inhibitor release is imagewise and tied to development;
- it changes intralayer gamma and acutance;
- it can diffuse to other colour records and change their gamma differently under neutral and colour-separation exposures;
- interlayers, scavengers and barrier placement can reflect, stop or redirect inhibitor transport;
- the same chemistry can increase saturation in one placement and reduce it in another.

V21 should release inhibitor separately from each fast/medium/slow population, diffuse it laterally and through the physical layer order, then suppress neighbouring site development **before** density summation. Neutral H-D curves will be maintained by solving the base layer capacities again after coupling.

### 4. Saturation is not a global scalar

Kodak’s contemporary measurement is approximately:

`colour-separation gamma / neutral-exposure gamma`

Therefore saturation depends on hue, exposure, local neighbourhood and layer position. The V21 validation chart needs neutral, red, green, blue, cyan, magenta and yellow step wedges. A single colour-matrix or HSV saturation value cannot validate DIR colour reproduction.

### 5. Status-M and a telecine are different observers

The typical telecine response plotted in US 5,500,316 is broad and peaks roughly near blue 470 nm, green 540 nm and red 620 nm. The V20 helper instead uses narrow Gaussian bands centred at 450, 550 and 690 nm to approximate Status-M.

This conflates measurement with acquisition. It is especially consequential in red: the period telecine reads cyan well away from its dye peak and also sees the long-wavelength tail of magenta. Kodak compensated the negative’s red-record contrast so the scanned red/green contrast ratio approached unity before independent channel correction, reducing red amplification noise and colour crosstalk.

V21 should expose three separate transforms:

1. **Status-M observer** — only for matching Kodak H-D and RMS data.
2. **Period DI/telecine observer** — spectral sensor integration, primary correction, 2K aperture and Cineon/DPX encoding.
3. **Optical print observer** — full 5279 transmission, printer spectrum, 2383 exposure/development and xenon projection.

The `Charlie's Angels: Full Throttle` reference remains valuable because it was photographed on 5279, completed as a 2K digital intermediate at EFILM and printed on 2383. However, the surviving Blu-ray may include the 2003 creative grade and later home-video transfer decisions, so it is a perceptual reference rather than an ungraded stock measurement.

### 6. Toe shape, black reproduction and noise must be solved together

The telecine-focused patent shows that simply lowering overall contrast reduces noise but makes midtones flat and does not automatically improve shadow visibility. Its successful examples used a lower toe-to-midscale contrast ratio while preserving useful midscale reproduction; expert observers rated shadow detail better at lower measured granularity.

For V21, the published 5279 H-D curves should be re-digitised at higher precision and analysed for local slope. Black level, toe visibility and density noise should be validated together, rather than tuning display black and grain independently.

## V21 implementation order

1. Preserve the existing high-precision 5279 H-D, MTF, RMS granularity and spectral curve samples as the stock-specific constraints.
2. Replace shared ECD morphology with channel-specific, bounded fast/medium/slow distributions.
3. Couple site activation, dye formation and DIR release in the development domain with limited lateral and cross-record transport.
4. Validate separation responses while locking the neutral H-D curves.
5. Split Status-M, period scanner and optical-print observers.
6. Pass neutral and six-colour diagnostic wedges before rendering the camera source.
7. Render and verify both native 5.7K / 12-bit projection and 2K-DI/Blu-ray masters.

## Sources reviewed

- Kodak 5279 H-1-5279t (local reference)
- Kodak, *Exploring the Color Image* (local reference)
- Kodak, *Processing KODAK Motion Picture Films, Module 7 — Process ECN-2 Specifications*
- Eastman Kodak patents US 5,500,316; US 5,705,327; US 5,298,376; US 5,314,793
- Smarter Every Day 275-B, *Kodak's Film Quality Control Process*
- Smarter Every Day 275-C, *The Chemistry of Kodak Film*
- The Cine Network, *Advanced Emulsion: Silver Halide Crystals, Imaging Couplers, Orange Masks and Processing* (Kodak-approved explanatory video; claims retained only when corroborated by Kodak manuals/patents)
- 2003 reporting on EFILM digital-intermediate work and contemporary 2K scanning
