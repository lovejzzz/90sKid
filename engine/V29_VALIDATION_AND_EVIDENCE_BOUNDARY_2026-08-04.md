# V29 — evidence-gated full-motion validation

Date: 2026-08-04

## Decision

V29 does not add a new aesthetic look. It retains V28's corrected ProRes RAW
input contract and the V27/V26 negative, observer and delivery parameters. The
remaining public evidence does not identify a unique 5279 noise-power spectrum,
fast/medium/slow coating formula, DIR transport matrix or period scanner
spectral response. Altering those values until one scene "looks more filmic"
would reduce objectivity rather than complete the model.

V29 instead implements the measurable portion of the remaining work:

- complete-source rather than one-second rendering;
- deterministic finite-site sampling keyed by absolute source-frame number;
- exact segment-parallel rendering without a grain reset at the boundary;
- both observer masters from the same negative realization;
- native 5760 x 4320, 12-bit ProRes 4444 and Rec.709 1-1-1 delivery;
- source 24-bit, 48-kHz, four-channel PCM, source metadata and timecode retention;
- full-motion black, highlight, temporal texture and metadata validation;
- an explicit evidence boundary for quantities that require physical film tests.

## What the official record determines

Kodak H-1-5279t supplies three neutral characteristic curves, three MTF curves,
three exposure-dependent diffuse RMS granularity curves measured through a
48-micrometre aperture, spectral sensitivity and net spectral dye-density
curves. The word *net* is important: the dye-density graph includes the opposite
density change from consumed coloured masking couplers; small negative lobes are
not errors.

For one colour record and sub-emulsion population, the finite-site variance is

`Var[p_hat] = p(1-p)/N`.

It naturally falls at both unexposed and saturated limits. After dye-cloud,
optical and 48-micrometre aperture kernels, the formed record is normalized to
Kodak's measured density standard deviation:

`D_formed = D_mean + delta_D * sigma_5279(logE) / sigma_predicted(logE)`.

This fixes the measured marginal amplitude. It does not uniquely recover the
two-dimensional frequency distribution of that amplitude.

Kodak also explains that MTF can exceed 100 percent because of developer
adjacency. The baseline therefore retains a narrow record-dependent core plus a
bounded density-domain adjacency band; it does not sharpen after adding grain.

## What remains unidentified

### Frequency-resolved grain structure

A single 48-micrometre RMS observation is one aperture-weighted integral of a
noise-power spectrum. Even several aperture sizes would not uniquely recover an
arbitrary spectrum without a morphology prior. No public 5279-specific Wiener
spectrum, autocorrelation function or microdensitometer trace was found. V29
therefore retains the bounded V26 morphology and labels it as a prior, not a
published Kodak formula.

### Exact interimage chemistry

Kodak patents establish that DIR compounds differ in diffusion and can alter
both intralayer adjacency and interlayer colour reproduction. They do not
publish a 5279 receiver/causer matrix. ECN-2 control limits measure laboratory
process stability; they are not uncertainty bounds for that missing matrix.
V29 keeps the restrained, uniform-field-zero operator rather than fitting new
coefficients to T002.

### Exact period scanner

The Spirit 2K documentation establishes a diffuse xenon source and three 2048
pixel RGB CCD lines, but not the proprietary spectral match or complete transfer
matrix. V29 retains the neutral-scale-constrained observer and does not claim to
replicate one serial-numbered telecine.

## T002 production target

- Source: `NJARAW_S001_S001_T002.MOV`
- Camera/recorder: Panasonic DC-GH7 / Atomos Ninja RAW
- Source video: ProRes RAW HQ, 5760 x 4320, 12 bit, 24000/1001 fps
- Frames: 165
- Video duration: 6.881875 seconds
- Sound: PCM signed 24 bit, 48 kHz, four channels
- Timecode: 12:04:05:23
- White balance / EI metadata: 5500 K / EI 500

The final timing, hashes, full-motion metrics and delivery checks are stored
beside the two masters in `timing.json`, the observer manifests and
`validation.json`.

## Remaining path to a measured 5279 characterization

The unresolved portion now requires new evidence rather than more code-only
tuning: a controlled 5279/GH7 paired exposure of a calibrated spectral chart,
neutral and single-colour separation wedges, and high-resolution raw scanner
captures suitable for a frequency-resolved granularity measurement. Those data
would allow the current bounded priors to be replaced with measured values.

## Primary references

- Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
  H-1-5279t, revised March 2003.
- Eastman Kodak Company, *The Essential Reference Guide for Filmmakers*,
  sections on sensitometry, granularity and MTF.
- Eastman Kodak Company, *Processing KODAK Motion Picture Films, Module 1:
  Process Control*, H-24.01.
- Eastman Kodak Company, *Effects of Mechanical & Chemical Variations in
  Process ECN-2*, H-24 Module 8.
- Eastman Kodak Company, US 5,314,793, multilayer speed/granularity architecture.
- Eastman Kodak Company, US 6,190,847 B1, electronically viewed colour-negative
  granularity and diffusion-factor measurement.
- Digital Film Technology, *Spirit DataCine / Spirit 2K* technical data.
