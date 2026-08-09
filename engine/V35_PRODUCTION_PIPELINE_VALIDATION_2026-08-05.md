# V35 Production pipeline validation

Date: 2026-08-05
Machine: Apple Silicon Mac16,5, Darwin 25.5.0
Native test: 5760 x 4320, 24 frames, 24000/1001, two 12-bit ProRes 4444 masters

## Decision

V35 Production is accepted as the current quality-first execution graph after
complete one-second native renders of T002, T007 and T031. It does
not retune colour, contrast, black, gamma, MTF, DIR, grain amplitude or grain
spectrum. V34 remains the archive-exact NumPy/CPU conformance oracle; V35 uses an
independent, statistically equivalent stochastic realization and therefore is
not byte-identical to V34.

The accepted graph is:

1. the unchanged V34 photographic model;
2. validated float32 spatial storage boundaries;
3. asynchronous, no-copy Philox4x32-10 Metal finite-site sampling;
4. direct uint32 Bernoulli trials against a fixed-point float32 probability
   threshold;
5. reliable serial projection/scan observers;
6. V31 final-adapter buffer reuse;
7. immutable hashes, command provenance and per-frame sampler identity audits.

## Performance result

| Metric | V34 | V35 Production | Change |
| --- | ---: | ---: | ---: |
| Effective wall time for both masters | 34.313 s/frame | 26.200 s/frame | 23.65% faster |
| Relative throughput | 1.000x | 1.310x | +31.0% |
| 24-frame V35 wall time | — | 628.791 s | 10m 28.8s |

The three-scene release completed both observer masters with the following
effective wall times:

| Scene | Seconds/frame for both masters | 24-frame wall time | Sampler audit |
| --- | ---: | ---: | --- |
| T002 | 26.200 | 628.791 s | 1,080 calls; 45/frame; zero duplicate identities |
| T007 | 26.030 | 624.716 s | 1,080 calls; 45/frame; zero duplicate identities |
| T031 | 26.193 | 628.638 s | 1,080 calls; 45/frame; zero duplicate identities |

All six outputs were independently probed as 5760 x 4320, 24-frame, 12-bit
ProRes 4444 (`yuv444p12le`) with explicit Rec.709 primaries, transfer and matrix
metadata. Their SHA-256 hashes are retained with the release artifacts.

V35 stage means:

| Stage | Seconds/frame | Share of image-stage time |
| --- | ---: | ---: |
| Scene + mean negative | 5.027 | 19.5% |
| Stochastic emulsion | 6.167 | 23.9% |
| Two serial observers | 11.191 | 43.4% |
| Final projection adapter | 3.216 | 12.5% |
| Decode | 0.159 | 0.6% |
| Encode both masters | 0.240 | 0.9% |

The observer pair is the remaining dominant cost. Source inspection shows the
projection and Spirit/Cineon branches diverge immediately; a reusable common
prefix has not been proven. We do not fuse them based on timing alone.

## Why the sampler changed again

The first V35 candidate used one 24-bit open uniform and a float inverse CDF.
Its measured distribution was good, but “exact-distribution” was too strong a
claim: float CDF accumulation and 24-bit uniform resolution are finite. The
Roundtable audit correctly challenged the rare-event and identity boundaries.

The release candidate instead performs up to 30 direct Bernoulli trials. Each
Philox uint32 word is compared with:

`floor(float32_probability * 2^32)`

The float32-to-u32 threshold is constructed from the IEEE-754 exponent and
significand, so the random word is never reduced to a 24-bit float before the
comparison. Across all extrema and percentiles observed in T002, T007 and T031,
the maximum represented-probability error is 2.2692e-10, below the theoretical
2^-32 bound of 2.3283e-10.

This follows the counter-based design principle of Random123/Philox: stochastic
identity is a pure function of a counter and key, not mutable generator order.
See the [Random123 paper](https://www.thesalmons.org/john/random123/papers/random123sc11.pdf)
and [reference documentation](https://www.thesalmons.org/john/random123/releases/1.00/docs/).

## Actual production domain and identity proof

The three decoded Panasonic/AVFoundation source frames produced:

- probability range: 1.685235e-7 to 0.9863252;
- 22 actual class trial counts: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17,
  18, 19, 20, 21, 23, 24, 25, 27 and 30;
- no exact-zero or exact-one probabilities in the three tested frames.

The upstream seed is:

`30,000,000 + frame*10,000 + record*1,000 + population*100 + size_class`

The Metal counter also includes global pixel index and a sampler-domain tag.
The production renderer decodes every seed back into frame/record/population/
class, rejects an invalid range or duplicate identity, and writes the audit to
the manifest. The 24-frame release render recorded exactly 45 calls per frame,
1,080 calls total, trial counts 1–30 and zero duplicate identities. A separate
1,000-frame proof checked 45,000 seeds with zero collisions.

## Distribution and density validation

The uint32 Bernoulli sampler was tested across all 22 production trial counts,
eight probability points and 4,194,304 samples per case (176 cases):

- maximum absolute mean z-score: 3.057;
- maximum histogram z-score: 3.850;
- maximum spatial lag correlation: 0.001492;
- maximum temporal-seed correlation: 0.001331;
- maximum variance-ratio error: 3.92%, occurring in the deliberately sparse
  p=0.0001, n=1 case; the fixed-point threshold proof is the stronger rare-event
  guarantee there.

Four complete formed-negative seeds were compared with the CPU reference:

- CPU median: 11.361 s;
- Metal median: 6.733 s;
- formed-density standard-deviation ratios: 0.999918, 1.000264, 0.999852;
- maximum mean normalized NPS-band delta: 0.008667;
- normal between-seed NPS range in the reference: 0.021825.

The NPS difference is therefore smaller than ordinary realization-to-realization
variation in the reference process.

## 24-frame end-to-end release gates

The enhanced comparison uses five 512 x 512 regions rather than one centre
crop. It measures temporal mean colour, luma tails, low/high clipping, RGB
high-pass covariance, spatial grain energy and frame-difference grain energy.

### 2383 projection

- temporal mean RGB delta: +2.38e-6, -1.38e-6, -3.10e-6;
- maximum per-frame mean RGB delta: 1.81e-5, 2.07e-5, 7.92e-5;
- maximum clip-fraction delta: 5.14e-5;
- maximum high-pass energy-ratio departure: 0.1485%;
- maximum temporal-difference energy-ratio departure: 0.1234%;
- maximum RGB high-pass correlation delta: 0.00419;
- all release gates passed.

### Blu-ray / Spirit scan

- temporal mean RGB delta: -1.91e-6, -4.88e-6, -5.46e-6;
- maximum per-frame mean RGB delta: 2.39e-5, 3.88e-5, 9.13e-5;
- maximum clip-fraction delta: 4.82e-5;
- maximum high-pass energy-ratio departure: 0.2635%;
- maximum temporal-difference energy-ratio departure: 0.1954%;
- maximum RGB high-pass correlation delta: 0.01367;
- all release gates passed.

The independent V35 grain realization does not create a systematic green,
blue or magenta transform in either branch.

## Rejected acceleration paths

| Candidate | Benefit | Rejection reason |
| --- | ---: | --- |
| Same-process parallel observers | apparent observer reduction | Numba `workqueue` is not concurrency-safe; reproduced SIGABRT |
| Shared-memory observer subprocesses | bit-identical | 25.0 s parallel versus 10.94 s serial from memory-bandwidth pressure |
| Metal Gaussian replacements | fast microbenchmarks | rare random-threshold/2383 outliers, up to material code changes |
| Full residual convolution | about 0.5 s/frame in one run | tiny density reorder amplified to projection outliers up to 960/65535 |
| One Gaussian after disk subtraction | about 0.9 s/frame in one run | tiny density reorder amplified to projection outliers up to 900/65535 |
| Metal adapter blur | negligible | no useful end-to-end gain |
| Tiled OFX v1 | possible host scheduling flexibility | downstream reflected filters, DIR, scatter and Spirit aperture are not tile-safe yet |

The convolution rewrites are mathematically linear, and their formed-density
maximum difference was only about 5e-6. That is still insufficient evidence:
the nonlinear 2383 and print-grain path turns a few such boundary changes into
isolated large code deltas. They stay disabled.

## Crash report resolution

The reported Python failure was a child-process SIGABRT in
`workqueue.cpython-313-darwin.so`, matching Numba's diagnostic that concurrent
access to its workqueue backend is unsafe. It was not a kernel panic and did not
damage completed outputs. V35 now rejects `--observer-workers 2` before render,
uses one reliable observer worker, and completed all 24 frames without failure.

## OpenFX / Resolve contract

OpenFX supports host-managed GPU rendering, including Metal buffers and command
queues. The plugin must enqueue work without adding avoidable CPU/GPU waits; see
the [OpenFX GPU rendering reference](https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html)
and [thread-safety reference](https://openfx.readthedocs.io/en/latest/Reference/ofxThreadSafety.html).
Apple likewise recommends minimizing command-buffer count and CPU/GPU
synchronization; see [Metal command-buffer best practices](https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/CommandBuffers.html)
and [command-structure guidance](https://developer.apple.com/documentation/Metal/setting-up-a-command-structure).

The OFX v1 boundary is therefore:

- full-frame rendering with `supportsTiles=false`;
- serial rendering per plugin instance;
- host-owned Metal command queue/context;
- per-instance pipeline states and bounded reusable buffer rings;
- completion-handler-governed buffer lifetime;
- deterministic frame/record/population/class/pixel identities;
- no process-global `MTLDevice`, queue or `dispatch_once` initialization copied
  from the Python research bridge.

The current ctypes bridge is a research harness, not the plugin architecture.

## Artifacts

- Production masters: `outputs/native_5k_v35_pipeline_bernoulli_u32_1s/{T002,T007,T031}`
- Timing/provenance: `outputs/native_5k_v35_pipeline_bernoulli_u32_1s/T002/timing.json`
- Production-domain audit: `research_runs/2026-08-05_v35_pipeline/production_domain.json`
- Bernoulli statistics: `research_runs/2026-08-05_v35_pipeline/metal_bernoulli_production_domain_statistics.json`
- Multi-seed density/NPS: `research_runs/2026-08-05_v35_pipeline/multiseed_density_bernoulli_u32.json`
- Projection temporal validation: `research_runs/2026-08-05_v35_pipeline/t002_bernoulli_u32_temporal_projection.json`
- Scan temporal validation: `research_runs/2026-08-05_v35_pipeline/t002_bernoulli_u32_temporal_scan.json`
- Roundtable audit packet: `roundtable_v35_audit`

## Release boundary closed

T002, T007 and T031 all completed the planned one-second native production
render with both observer branches. The six masters pass format, provenance and
sampler-identity checks. V35 is therefore ready for the three-scene website
release. This closes the V35 execution-graph boundary; future photographic-model
changes belong to a later version and must not be folded silently into this
performance release.
