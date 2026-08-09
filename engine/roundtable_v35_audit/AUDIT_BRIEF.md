# V35 Kodak 5279 pipeline audit brief

## Decision boundary

Quality is the first priority. The production path may change the random realization of grain, but it must preserve the modeled stochastic process, spatial/temporal statistics, tone, color, and 12-bit deliverables. V34 remains the archive-exact CPU reference. V35 is intended to be the statistically equivalent production path and a precursor to a DaVinci Resolve OpenFX/Metal implementation.

## Accepted V35 changes

1. Replace NumPy finite-site binomial draws with a custom Metal Philox4x32-10 counter-based sampler. The counter includes the global pixel coordinate, channel/site-class identity, draw identity, and frame seed, so arbitrary tiling produces the same sample as a full-frame dispatch.
2. Submit Metal draws asynchronously and expose the shared output buffer directly to NumPy. CPU expected-density filtering overlaps the GPU draws; the CPU waits only when the corresponding draw is consumed.
3. Keep spatial intermediates in float32 at validated boundaries.
4. Reuse the V31 final-adapter work buffer.
5. Force both observers to execute serially. This machine's Numba installation exposes only the non-threadsafe `workqueue` backend. A concurrent observer prototype crashed with SIGABRT, and a subprocess/shared-memory alternative was much slower because both observers saturate memory bandwidth.

## Rejected experiments

- Metal Gaussian replacement: faster microbenchmarks but rare random-threshold outliers caused material projection/print-grain code differences.
- Post-formation Metal Gaussian replacement: same problem at the print-grain threshold.
- Metal adapter blur: no useful end-to-end speedup.
- Same-process observer threads: unsafe with Numba `workqueue`; produced a reproducible SIGABRT.
- Observer subprocesses: bit-identical, but about 25.0 s parallel versus 10.94 s serial due to memory pressure and bandwidth contention.

## Measured performance

Machine: Apple Silicon Mac16,5, Darwin 25.5.0. Source and both masters are 5760x4320. V35 production T002, 24 frames:

- total wall including finalization/hash: 623.848 s
- effective time: 25.994 s/frame for both masters
- V34 effective time: 34.313 s/frame
- measured speedup: 24.2%
- scene + mean negative: 5.204 s/frame
- stochastic emulsion: 5.938 s/frame
- two serial observers: 11.079 s/frame
- final projection adapter: 3.245 s/frame
- decode: 0.118 s/frame
- encode both masters: 0.212 s/frame

The remaining dominant cost is the observer pair, followed by formation and the final adapter.

## Sampler validation

Thirty-five binomial cases were tested with 4,194,304 samples each:

- maximum absolute mean z-score: 1.784
- maximum variance-ratio error: 0.00994 (extreme probabilities)
- maximum histogram z-score: 3.052
- maximum spatial lag correlation: 0.001166
- maximum temporal seed correlation: 0.001095

Four full formed-density seeds were compared against the NumPy reference:

- CPU median: 11.210 s
- Metal median: 6.284 s
- formed-density standard-deviation ratios by dye layer: 0.999961, 1.000152, 0.999770
- maximum mean normalized NPS-band delta: 0.00622, below the 0.017-0.024 between-seed range

## End-to-end temporal validation

V34 and V35 T002 were compared over all 24 frames. The paths intentionally use independent but valid grain realizations.

Projection:

- temporal mean RGB delta: 5.48e-7, -1.40e-6, 7.29e-6
- maximum absolute per-frame mean RGB delta: 2.25e-5, 1.29e-5, 6.14e-5
- mean luma p01/p50/p99 delta: 2.84e-6, 1.61e-6, -2.70e-5
- high-pass standard-deviation ratio: 1.000421, 1.000417, 1.000695

Scan:

- temporal mean RGB delta: -1.49e-6, -7.47e-7, 8.09e-6
- maximum absolute per-frame mean RGB delta: 3.08e-5, 3.57e-5, 9.31e-5
- mean luma p01/p50/p99 delta: 2.79e-8, 1.08e-5, -2.41e-5
- high-pass standard-deviation ratio: 1.000269, 1.000218, 1.000900

No systematic color shift was found. The high-pass grain-energy difference is below 0.1%.

## Delivery verification

Both masters report 5760x4320 ProRes 4444, `yuv444p12le`, `bits_per_raw_sample=12`, 24000/1001 fps, and Rec.709 primaries/transfer/matrix.

## OpenFX/Metal direction under review

The proposed first OFX implementation should initially advertise full-frame rendering (`supportsTiles=false`) and avoid host frame-thread concurrency until all dependency halos and instance/thread-safety rules are proven. It should use the host-provided Metal command queue, persistent per-instance pipeline states, and a ring of reusable buffers. One frame should be encoded into as few command buffers as practical, without avoidable CPU/GPU synchronization. Global-coordinate Philox makes the finite-site stage tile-safe, but it does not by itself prove that the full spatially coupled emulsion graph is tile-safe.

## Questions for the audit

1. Do the statistical tests adequately justify production equivalence, or are there missing temporal/color/rare-event tests that should block release?
2. Is any accepted float32 boundary likely to create visually coherent error not captured by the current metrics?
3. Is there duplicated filtering, color conversion, or memory traffic in the included renderer that can be removed without changing arithmetic order or the model?
4. Which remaining stage is the safest next acceleration target: observer graph fusion, formation-filter fusion, adapter fusion, or a resident whole-frame Metal graph?
5. What should the OFX v1 threading, tiling, buffer-lifetime, and determinism contract be?
6. Rank recommendations as: implement now, benchmark behind a flag, or defer/reject. State evidence and quality risk.
