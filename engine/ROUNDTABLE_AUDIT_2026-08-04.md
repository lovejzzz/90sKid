# V27 rendering-pipeline Roundtable audit — 2026-08-04

## Scope and method

Codex CLI, Claude CLI and Antigravity CLI independently inspected a compact,
read-only snapshot of the V27 source, timing manifests, parity results, Metal
bridge and OFX proposal. Their sealed openings were revealed only after all
three had formed an independent position. A second round cross-examined those
positions, and Fable 5 audited the complete transcript. The live project was
29 GB because it contains native 5.7K renders, so the first disposable sandbox
timed out; the successful room used a 228 KB snapshot containing the relevant
source and measured reports. No agent was allowed to modify the snapshot.

The non-negotiable decision rule was:

1. Archive changes must reproduce the frozen V27 output bit-for-bit.
2. Production float32 changes must pass T020/T032 numerical and temporal gates.
3. A speedup that weakens image quality is rejected even if it is substantial.

## What the room agreed on

- The 12.52-second stochastic-emulsion stage, not decode/encode and no longer
  Gaussian filtering alone, is the largest measured opportunity.
- The existing Metal bridge cannot safely become asynchronous merely by
  deleting `waitUntilCompleted`. Shared kernel/temporary buffers, the broad
  `@synchronized` region, and the lifetime of NumPy memory wrapped with
  `newBufferWithBytesNoCopy` all have to be fixed together.
- Full planar GPU residency remains the highest-upside architecture, but
  sub-five-second runtime and sub-four-GB memory are targets, not evidence.
- Philox, generic ROI tiling, analytic gamut replacement and reassociated
  convolution cannot be called Archive exact. Philox may be considered only as
  a separately labelled Production stochastic realization after NPS and
  temporal validation.
- The safest path for the rare Metal gamut-boundary outliers is a sparse
  uncertainty mask plus CPU reference repair, not replacing the defined
  eight-step solver.

## Main-agent judgment and experiments

### Accepted: Archive `copy=False` cleanup

Three redundant float32 `astype` calls were changed to `copy=False`. A native
T020 frame remained byte-identical to the frozen V27 array:

- reference/new SHA-256:
  `8743a072485ebe0f968b07e33b9e8b5a3a809c28e792e4f071d6b04afa29a35a`
- `cmp`: identical

This removes avoidable memory traffic, although the wall-time delta is below
the noise floor and is not advertised as a measured speedup.

### Rejected for default: residual convolution

The room proposed using linearity to replace
`L(sample) - L(expectation)` with `L(sample - expectation)`. It preserves the
PCG64 draws but changes float32 rounding. The isolated T020 experiment reduced
the stochastic stage from 12.90 to 12.24 seconds, only about 0.66 seconds. Its
quality result against Archive was:

- PSNR: 109.38 dB
- maximum difference: 224 of 16-bit, or 14 of 12-bit
- changed 12-bit channel fraction: 0.00431%
- pixels with any changed 12-bit channel: 0.01018%

That is materially worse than the validated Production-float32 CPU path
(138.53 dB, maximum one 16-bit/12-bit code). The optimization therefore remains
behind `--production-residual-convolution` as a research control and is not
selected by the scheduler.

### Accepted: exact neutral H-D specialization

The live source, absent from the audit snapshot, confirmed that a neutral
exposure replicated across RGB produces zero chromatic departure in the full
record-crossover function. A specialized path now evaluates only the three
published neutral H-D interpolations. Validation covered a T020 spatial sample,
two million random RGB exposures, and complete native T020/T032 renders.

- T020 stayed at
  `8743a072485ebe0f968b07e33b9e8b5a3a809c28e792e4f071d6b04afa29a35a`.
- T032 stayed at
  `f8bb2357e3f1c86e8bc7fe7d64842c9e1af3f00754d19e7e3dce0821a7054183`.
- T020 mean-negative stage: 8.07 to 7.39 seconds in the paired profiling runs.
- T032 mean-negative stage: 8.15 to 7.59 seconds.

This change is promoted to Archive because both holdout arrays are byte-for-byte
identical.

### Accepted: exact stochastic memory reuse

Two further changes preserve NumPy's original left-to-right float32 operation
order while avoiding large three-channel broadcast temporaries:

- the nine predicted-aperture-variance updates reuse the already-consumed
  population plane; T020 fell from 1.38 to 0.56 seconds;
- the nine-layer record mix reuses one scalar plane; T020 fell from 0.83 to
  0.33 seconds.

Both complete T020 and T032 arrays retained the frozen hashes above.

The same rule then enabled three more exact changes: one contiguous probability
plane is cached per population instead of copied for all five size classes;
layer distribution/release/finalization run in independent row ranges with the
same per-element operation order; and neutral activation is evaluated directly
from its scalar field instead of constructing a repeated RGB array. With all
accepted exact changes and profiling disabled, T020 strict single-frame time is
25.28 seconds versus the previous 30.00-second strict result and the original
64.46-second reference: 15.7% faster than the prior optimized path and about
2.55x faster than the starting point, without changing one output bit. Peak
resident memory fell from 12.33 to 11.61 GB in the paired memory runs.

Two 8/8/8/8 Archive workers now complete two frames in 33.19 seconds, or 16.59
seconds/frame; the decoded two-frame RGB48 hash remains
`d6fbb0b9dc28c9cdc93a62cfa497edf6e18ac3900d6bbd73da78c473cdb73f8c`.
Three 5/5/5/5 workers measure 17.13 seconds/frame, so the scheduler retired that
formerly faster but memory-heavy topology.

### Accepted as architecture prototype: safe asynchronous Metal flights

An experimental API now gives each in-flight Gaussian its own kernel,
temporary, source wrapper, destination wrapper and command buffer. Python holds
strong references to the page-aligned source, destination and weights until
`wait()` completes. Only shared-queue command creation/commit remains locked;
encoding and mutable resources are per-flight. The synchronous production path
is unchanged.

Two native 5760 x 4320 scalar jobs produced output identical to the same jobs
submitted serially and reduced the measured two-job wall time from 44.37 ms to
39.47 ms (1.12x in this microbenchmark). One sigma-18 native job was 6.29x
faster than OpenCV, with maximum float error `8.34e-7` and zero samples above
half a 12-bit code. This validates the concurrency contract, not yet an
end-to-end renderer speedup.

## New stochastic-stage evidence

Conditional operator instrumentation accounts for essentially the complete
native stage without changing either T020 or T032 hashes. T020/T032 seconds:

| Component | T020 | T032 |
| --- | ---: | ---: |
| PCG64 / NumPy binomial | 5.68 | 6.09 |
| stochastic DIR coupling total | 2.21 | 2.34 |
| predicted aperture variance updates | 1.38 | 1.41 |
| nine-layer record-mix accumulation | 0.83 | 0.83 |
| two disk filters | 0.45 | 0.46 |
| two dye-cloud Gaussians | 0.91 | 0.95 |
| probability contiguous copies | 0.45 | 0.46 |
| subpixel warps | 0.21 | 0.21 |
| full stochastic stage | 13.00 | 13.62 |

After the accepted exact memory reuse, variance is 0.56/0.56 seconds,
record-mix accumulation is 0.33/0.33 seconds, and the full stochastic stage is
11.49/11.94 seconds in the instrumented T020/T032 runs.

The dominant next questions are therefore exact RNG throughput, DIR
factorization, predicted-variance/mix memory traffic, and safe batching across
independent planes. More Gaussian-only tuning has a small ceiling.

## Revised implementation order

1. Preserve the accepted Archive neutral, variance, record-mix, probability
   cache and row-parallel layer work; extend holdouts beyond T020/T032.
2. Use the mean/stochastic profiles to investigate exact DIR and PCG64 costs.
3. Convert the asynchronous Metal-flight prototype into a bounded ring and
   batch independent plane work without weakening the no-copy lifetime contract.
4. Test Production DIR receiver-marginal factorization separately. It is not
   Archive until a byte-identical formulation is demonstrated.
5. Build the planar resident activation-to-density graph only after those
   lower-cost experiments establish the irreducible CPU/RNG cost.
6. Keep counter-based stochastic sampling, sparse gamut repair, ROI, render
   scale and 24-frame thermal/NPS testing as explicit Production/OFX gates.
## Post-audit implementation update

The next quality-gated pass applied the audit's safe-parallelism rule to the
scan tail. Purely pointwise work now runs in row stripes while every spatial
filter retains its original whole-frame support and border convention. T020 and
T032 remain byte-identical. Single-frame Archive time fell to 21.62/22.31
seconds, and a real two-frame ProRes export reached 15.08 seconds/frame with the
frozen decoded hash. CPU Production now saves only 0.34 seconds, so the main
agent rejects it as a default; Archive exact remains the quality-first path.
