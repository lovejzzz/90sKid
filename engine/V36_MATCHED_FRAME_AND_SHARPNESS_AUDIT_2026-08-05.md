# V36 matched-frame and 35 mm image-structure audit

## Decision

V36 does **not** reduce grain, soften the image, change colour, or retune the
5279 MTF.  The apparent V35 shift toward 8/16 mm was chiefly a comparison error:
V34's curated T031 release used source frames 132–155, while the V35 release
used frames 0–23.  T007 was likewise changed from V34 frames 276–299 to V35
frames 0–23.  Source texture and motion were therefore presented as if they
were a film-model change.

The V36 release contract locks the absolute windows:

- T002: frames 0–23
- T007: frames 276–299
- T031: frames 132–155

Camera witness, projection, scan, still and hover video must all name and use
the same source window.

## How the false diagnosis was found

The first T031 seed screen accidentally repeated the same start-frame error.
Four independent Philox salts produced nearly the same apparent temporal tail.
That persistence initially made a deterministic Production kernel look
suspicious.  A two-way ablation was then repeated at the correct frame 132:

1. V34 RNG + Production spatial kernels reproduced V34 essentially exactly.
2. Philox-u32 + Archive spatial kernels differed from V34 only by the expected
   independent stochastic realization:
   - median high-pass luma RMS ratio: 1.00121;
   - median temporal-difference RMS ratio: 1.00139;
   - median grain/base-edge ratio: 1.00131;
   - median opponent/luma temporal RMS ratio: 0.99915.

The completed 24-frame V36 T031 dual masters tightened those estimates further:

- scan median high-pass RMS ratio: 0.99982;
- scan median temporal-difference RMS ratio: 1.00041;
- scan median grain/base-edge ratio: 1.00016;
- projection median high-pass RMS ratio: 1.00039;
- projection median temporal-difference RMS ratio: 1.00039;
- projection median grain/base-edge ratio: 0.99957.

The native T031 render took 610.95 seconds end to end, or 25.456 seconds per
source frame for both 5.7K observers including audio/timecode and final hashes.

The completed T007 frames 276–299 release independently confirms the same
result.  Relative to the matched V34 window, the scan high-pass, temporal and
grain/base-edge median ratios are 0.99924, 1.00075 and 0.99934; projection is
0.99989, 1.00001 and 0.99985.  Its native dual-master render took 613.65
seconds end to end, or 25.569 seconds per source frame.  Both branches retain
5760×4320 yuv444p12le ProRes 4444, Rec.709 1-1-1, four-channel 24-bit PCM and
source timecode 12:21:44:14.

The existing V35 T031 first frame is pixel-identical to a new frame-zero
Production render, confirming that the released segment—not a hidden kernel
change—caused the visual discontinuity.  The invalid frame-zero salt metrics
remain archived as an error record and are not used to tune V36.

## Is density sharpness?

Optical density is the image variable:

\[
D(x,y,\lambda)=-\log_{10}T(x,y,\lambda).
\]

But an absolute density value is not sharpness.  Sharpness concerns how a
spatial density modulation survives the material and viewing system:

\[
\mathrm{MTF}(f)=\frac{M_{\mathrm{out}}(f)}{M_{\mathrm{in}}(f)}.
\]

An edge is therefore a spatial change in density, and its slope/edge-spread
function—not its absolute D—is what produces acutance.  The stochastic grains
do constitute the realized image; they sample the exposure/development field
and create local density.  They do not automatically supply the correct mean
edge response or limiting resolution.

The useful decomposition is:

\[
D_{\mathrm{realized}}(x,y)=D_{\mathrm{mean}}(x,y)+\delta D_{\mathrm{grain}}(x,y),
\]

provided both terms live on the same film geometry and are constrained by the
correct processed-stock measurements.  This is a decomposition of one image,
not an instruction to overlay noise after rendering.

## Official constraints checked

Kodak H-1-5279t explicitly publishes MTF and diffuse RMS granularity as
separate image-structure characteristics from 5279 samples exposed under
tungsten light and processed in recommended ECN-2.  It says perceived
sharpness depends on the complete production system and reports granularity
with a 48-micrometre microdensitometer aperture.  Kodak E-58 further separates
objective density variation (granularity) from subjective graininess and says
that negative noise-frequency content, print granularity, print MTF, printing
system MTF and magnification all affect final graininess.  A poorer lens can
hide grain, but only at the expense of sharpness.

References inspected visually and textually:

- `references/kodak_5279_H-1-5279t.pdf`, especially pages 3–4.
- `references/kodak_E58_print_grain_index.pdf`, especially pages 1–3.

## Current 5279 fit

On a 24.9 mm image-width mapping at 5760 pixels:

- pixel pitch: 4.3229 micrometres;
- Nyquist: 115.66 cycles/mm;
- 48 micrometre aperture: 11.10 native pixels;
- fitted MTF50: R 51.12, G 64.75, B 72.26 cycles/mm;
- fitted MTF peaks: R 102.23%, G 114.17%, B 121.36%.

The fitted R/G/B responses at 3, 10, 20, 50 and 75 cycles/mm all fall inside
broad visual-reading envelopes from the official logarithmic graph.  These
envelopes validate scale and ordering; they are not precise new digitization
targets and do not authorize a retune.

Numerical output is in
`research_runs/2026-08-05_v36_sharpness_grain/audit.json`.

## V36 release gates

1. Fail if any compared branch uses a different absolute source-frame window.
2. Keep colour, black, gamma, MTF, DIR, grain amplitude and NPS frozen.
3. Keep both processed-stock MTF and exposure-conditioned 48 micrometre RMS
   visible in provenance.
4. Evaluate temporal grain only after matching scene time and motion.
5. Treat web codec changes as a viewing proxy boundary, never as evidence for
   changing the native emulsion model.
