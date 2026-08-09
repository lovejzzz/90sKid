# V34 pipeline and image-model audit — 2026-08-05

## Release decision

The audit found one evidenced image-model overlap and several pipeline-only
redundancies. A V34 release is warranted. It is not an artistic grade: no global
saturation, hue, white-balance, black, contrast or gamma control is added.

V34 makes four accepted changes:

1. remove a duplicate deterministic intralayer adjacency term while retaining
   the fitted processed-stock 5279 MTF;
2. apply the accepted V31 projection colour boundary in memory before delivery
   encoding, so each master receives one ProRes generation;
3. fuse the algebraically cancelling AVFoundation BT.2020 -> V-Gamut ->
   Rec.709 primary round trip;
4. remove dead computations and correct the partial-range audio manifest.

The three-speed populations, stochastic morphology, stochastic DIR coupling,
cross-record interimage transport, seed, 48-micrometre RMS normalization,
spectral dye model, 2383 observer, Spirit/Cineon observer, exposure, black,
gamma and Rec.709 delivery remain frozen except where explicitly stated below.

## Finding 1 — processed MTF and V21 deterministic adjacency overlapped

Kodak H-1-5279t says the published MTF, resolving-power and granularity data
were generated from 5279 exposed to tungsten light and processed in the
recommended ECN-2 process. Kodak's Essential Reference Guide separately says
MTF values above 100% commonly result from developer adjacency. The data-sheet
MTF is therefore a total processed-stock response, not an optical-only kernel.

The pre-V34 implementation did both of the following on the deterministic
scene signal:

- `develop_5279_record_density_from_log_exposure` added a V21 local
  density-domain intralayer adjacency term;
- `apply_5279_mtf` then applied a kernel already fitted to the complete Kodak
  processed-stock MTF, including its 10–20 cycles/mm adjacency rise.

A neutral sinusoid sweep showed the product exceeding the fitted target by
about 1–3.5% depending on channel and frequency; the largest excess was in the
blue record. V34 sets only the deterministic intralayer coefficient to zero.
The off-diagonal interimage operator remains because the neutral MTF graph does
not identify colour-separation transport. The stochastic intralayer morphology
also remains frozen because Kodak does not publish a 5279 noise-power spectrum.

This correction does not globally soften the image. Kodak's fitted MTF still
owns the complete deterministic acutance and high-frequency roll-off once.

## Finding 2 — V31 used an unnecessary intermediate ProRes generation

The accepted V31 release sequence was:

`negative -> V30 projection + scan -> encode both -> decode both -> OKLab adapter -> encode projection again`.

The final adapter itself took about 6.6 seconds wall time and 5.7 GB peak RSS for
one 5760 x 4320 frame, including two decoders and a second projection encoder.
The ProRes round trip was deterministic, but it was not lossless in RGB signal:
comparing the in-memory adapter result with the decoded encoded result produced
mean absolute signal error `0.00285`, p99 `0.01177` and maximum `0.05097`.
This is codec quantization/colour-component loss, not random nondeterminism: two
identical adapter runs produced identical SHA-256 masters.

V34 renders both observers in linear Rec.709, applies the unchanged V31
low-frequency scan a/b plus projection high-frequency opponent residual and
exact projection luma, then encodes projection and scan once. A pipeline-only
probe proved the scan master remains byte-identical to V30. The projection
changes because an unnecessary lossy generation has been removed.

## Finding 3 — the AVFoundation V-Gamut round trip had no operation inside it

For Apple's already converted extended-linear BT.2020/D65 buffer, the old path
performed:

`BT.2020 -> XYZ -> V-Gamut -> XYZ -> Rec.709`.

No V-Log encoding, camera LUT, white balance or nonlinear operation occurred
between the two V-Gamut matrices, so the middle round trip cancels
algebraically. On native T020, one fused `cv2.transform` reduced this portion
from roughly `0.79–0.89 s` to `0.03–0.05 s`. Mean absolute float error was
`1.8e-8`, p99 `2.38e-7`, maximum `1.19e-6`; `99.9926%` of clipped 12-bit channel
codes were identical and the remainder were rounding-boundary one-code cases.
The fused matrix is the product of the exact historical matrices, not a new
colour transform.

## Finding 4 — zero coefficients still executed nine native Gaussian blurs

After the deterministic adjacency coefficient is removed, the corresponding
nine source-release Gaussian blurs have a mathematically zero contribution.
Both the reference and accelerated CPU implementations now skip those blurs
when the coefficient is zero. T020 projection and scan ProRes SHA-256 values are
identical before and after the skip.

The optimized V34 native one-frame time is `36.08 s` before hashes, down from
`40.03 s` before the dead-blur skip. The old V30 plus external V31 adapter took
about `43.5 s/frame`; V34 is therefore about 17% faster on the reference scene
while also avoiding one lossy generation.

## Finding 5 — two native workers are unsafe on the 48-GiB reference Mac

A two-worker, two-frame probe was pixel-identical and reached `28.85 s/frame`,
but system swap rose to approximately `6.6 GiB`. That result is rejected. The
reference machine previously suffered a watchdog panic under excessive native
parallel pressure, so V34 auto scheduling reserves 26 GiB for macOS and active
apps, caps at one worker on 48 GiB, and requires at least 64 GiB plus healthy
launch-time memory pressure before selecting two. Quality and system stability
take precedence over the tempting throughput number.

## Finding 6 — partial-range audio reporting was inaccurate

The renderer correctly decodes, frame-accurately trims and losslessly
re-encodes PCM for a partial range, but the manifest always said `stream
copied`. V34 reports stream copy only for a complete-source render. Partial
ranges now report PCM decode/trim/re-encode and regenerated source-offset
timecode; video-only validations report no audio.

## Dead and deliberately retained code

The superseded pre-V21 `apply_5279_dir_interimage` helper and its private
acutance coefficient had no callers and duplicated the active
population-domain model conceptually. They were removed to reduce future OFX
porting risk. The following apparent repetitions are deliberate and retained:

- mean and formed-density observer renders are both required to separate
  deterministic MTF from stochastic grain delta;
- projection and scan observer branches must remain separate after the shared
  negative because they model different physical viewing chains;
- stochastic DIR coupling remains before record summation and is normalized to
  Kodak's 48-micrometre RMS constraint rather than reusing deterministic MTF.

## Holdout results before the one-second release

- T020 native frame 0: no new global cast; scan median linear luma changed from
  `0.041421` to `0.041382`, p99 remained `0.47962`; low-pass gradient p95 moved
  from `0.06540` to `0.06521`.
- T032 native frame 12: projection and scan retained the accepted green,
  low-contrast rainy-scene direction without adding a global magenta repair;
  no black lift, highlight clipping or chromatic edge halo was observed.
- Pipeline-only scan isolation: SHA-256 exactly matched the old V30 scan.
- Dead-blur optimization: both V34 master SHA-256 values exactly matched the
  pre-optimization V34 candidate.

## Plugin-oriented pipeline conclusion

The current CPU renderer should remain a reference implementation. The largest
future speedup requires a resident Metal/OpenFX graph rather than more process
parallelism: keep intermediate planes on the device, enqueue work on the host's
Metal command queue, avoid synchronous waits, reuse temporary resources, and
respect ROI halos and absolute-frame stochastic seeds. OpenFX explicitly lets a
host issue concurrent render actions, and its Metal suite passes host-managed
buffers and a command queue; the plugin must enqueue on that queue and return
without waiting. Apple's Metal Performance Shaders guidance likewise favours
fewer command buffers, no synchronous waits, temporary-resource reuse and
tiling multi-pass filters when working-set pressure benefits.

That GPU architecture remains a separate quality-gated project. It does not
justify weakening the current PCG64/binomial distribution, stochastic NPS,
edge support, border modes or 12-bit delivery today.

## Primary references

- Kodak, *KODAK VISION 500T Color Negative Film 5279*, H-1-5279t, pp. 3–4,
  local archival copy `references/kodak_5279_H-1-5279t.pdf`.
- Kodak, *Essential Reference Guide for Filmmakers*, image-structure section,
  local archival copy `references/kodak_essential_reference_guide.pdf`.
- Apple, [Adjust ProRes RAW camera settings in Final Cut Pro](https://support.apple.com/en-euro/guide/final-cut-pro/ver3eb60032c/mac).
- OpenFX, [Image Effect Plug-in Rendering](https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html).
- OpenFX, [Multi-threading Suite](https://openfx.readthedocs.io/en/latest/Reference/ofxThreadSafety.html).
- Apple, [Metal Performance Shaders tuning hints](https://developer.apple.com/documentation/metalperformanceshaders/tuning-hints).
- Apple, [Metal Performance Shaders](https://developer.apple.com/documentation/MetalPerformanceShaders).
