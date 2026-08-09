# Wavefront Tile Lab v0.0.2

Date: 2026-08-09  
Status: accepted as an isolated lab milestone; not enabled in V43H Production  
Machine: Apple M4 Max, 48 GB unified memory  
Holdouts: T020 frame 0, T032 frame 0, T007 frame 276 at 5760 × 4320

## Outcome

v0.0.2 extends v0.0.1 with exact lifetime contraction inside every one of the
45 finite-site size classes:

1. the sampled finite-site plane becomes the disk-filter output, Gaussian
   output, sample-minus-expectation deviation and subpixel-warp output in place;
2. the expected plane becomes its Gaussian output in place;
3. the completed class deviation becomes its own weighted scratch before it is
   accumulated into the population deviation.

No sensitometry, Philox identity, trial count, filter kernel, border, DIR,
calibration, projection, scan or delivery equation changes.

On T020, repeated negative formation improved from v0.0.1's 18.999-second
median to 17.579 seconds, about 7.48%. Complete physical delivery improved from
42.502 to 41.363 seconds, about 2.68%. Every float32 density and uint16 observer
value remained identical.

## Exact buffer flow

The accepted class path conceptually materialized successive full scalar
planes:

```text
developed fraction
  -> disk sampled
  -> Gaussian sampled
expected disk
  -> Gaussian expected
sampled - expected
  -> warped deviation
class weight * deviation
```

v0.0.2 retains only the already-required sampled and expected planes:

```text
sampled buffer:
  developed -> disk -> Gaussian -> subtract -> warp -> weighted class

expected buffer:
  disk expected -> Gaussian expected
```

OpenCV receives the same float32 input, kernel, sigma and `BORDER_REFLECT`, but
its `dst` is the source plane. NumPy multiplication and addition preserve the
original left-to-right float32 order with `out=`. Synthetic tests cover zero
and non-zero subpixel offsets, multiple disk radii and Gaussian sigmas.

## T020 repeated negative formation

Three alternating v0.0.1/v0.0.2 pairs used the same decoded RAW frame and
reference hash:

| Path | Seconds | Median | Peak RSS median |
| --- | --- | ---: | ---: |
| v0.0.1 | 18.999, 18.624, 20.234 | 18.999 s | 6.8273 GiB |
| v0.0.2 | 17.792, 17.366, 17.579 | 17.579 s | 6.8278 GiB |

The 7.48% incremental speed gain appears in all three v0.0.2 runs. Peak RSS is
effectively unchanged: v0.0.1 already removed the nine-plane allocation that
set the negative-stage high-water mark. v0.0.2 removes repeated scalar-plane
allocations that improve traffic and time but not that global peak.

Across v0.0.2 runs, the 45 in-place optical stages summed to about 2.25–2.29
seconds and the 45 class accumulations to about 0.28 seconds.

## Complete projection and scan evidence

Two alternating complete v0.0.1/v0.0.2 pairs included 5279 formation, 2383
projection, Period/2K scan and reference encoding:

| Path | Negative median | Observer median | Total median | Peak RSS median |
| --- | ---: | ---: | ---: | ---: |
| v0.0.1 | 18.561 s | 23.371 s | 42.502 s | 8.5128 GiB |
| v0.0.2 | 17.424 s | 23.386 s | 41.363 s | 8.4753 GiB |

The observer time is unchanged within run variation, as expected. The complete
2.68% gain comes from retaining about 1.14 seconds of the negative-stage
improvement after fixed observer cost.

All complete runs preserved:

- formed 5279 density float32 hash:
  `43dcb77057f8a21956a74c8105da10a83294cd33934006382ba077e9853e72be`;
- projection uint16 hash:
  `f909c68f278e0c6b5a4929a556dce937ecd7a0d90a4310150dc581ae68f0aee1`;
- scan uint16 hash:
  `3e25af9c3ab0424fc5d31d9da70dfa2bb81f3e87359d0748b3d18d116c200a80`.

Maximum absolute delta and changed-value count were zero for every array.

## Cross-scene native holdouts

T032 and T007 each generated their own current-V43H authority before v0.0.2
was compared. These are single-run timing checks and exactness holdouts, not
claims about stable speed distributions.

| Scene | Current V43H | v0.0.2 | Improvement | V43H RSS | v0.0.2 RSS | Exact |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| T032 frame 0 | 18.634 s | 17.457 s | 6.32% | 7.2910 GiB | 6.8274 GiB | yes |
| T007 frame 276 | 19.113 s | 17.277 s | 9.61% | 7.2910 GiB | 6.8277 GiB | yes |

Their formed-density hashes were respectively:

- T032: `f911e575c1dc195962c6b0bd624efbcfca06e91f401ec2c816afd010b7c8cc6d`;
- T007: `b58c2e1e9e0933e02d462ab4ec890bb5fd4d8703c905e40752ade031f3992530`.

Both had zero changed float32 values and zero maximum difference.

## Isolation and interface

`engine/src/wavefront_tile_lab_v002.py` owns the two new exact operators,
versioned telemetry and explicit install/uninstall functions. Installing v0.0.2
first installs v0.0.1 with its selected 250k marginal workset, then adds:

- `_WAVEFRONT_INPLACE_OPTICAL_BUFFERS`;
- `_WAVEFRONT_INPLACE_CLASS_ACCUMULATION`.

Without those flags, V27/V35 retain their historical allocation and operation
path. The release renderer does not install the lab.

The benchmark enables v0.0.2 only with `--v002`. Generated arrays remain under
the untracked `work/` tree.

## Decision and v0.0.3

v0.0.2 is a successful lab milestone: it is exact on three native scenes and
provides a repeatable incremental time reduction. It is not promoted to the
default after three isolated frames. Promotion requires a longer sequence,
thermal interleaving and synthetic ramp/primary/boundary coverage.

The next credible contraction is the nine-plane DIR/coupled-output high-water
mark. v0.0.3 should investigate destination-tiled DIR accumulation or a
resident planar Metal island with explicit frame-border halos. It must not
overwrite a source layer before every destination has consumed its original
value. That dependency is the main correctness problem, not kernel syntax.

## Reproduction

```text
PYTHONPATH=engine/src:. python3 engine/src/benchmark_v43h_wavefront_tiles.py \
  <source.MOV> --decoder <prores_raw_float_decode> --cache <frame.npy> \
  --output <result> --reference <scene-baseline> --frame <absolute-frame> \
  --v002 --marginal-workset-pixels 250000
```
