# Wavefront Tile Lab v0.0.1

Date: 2026-08-09  
Status: accepted as an isolated lab milestone; not enabled in V43H Production  
Machine: Apple M4 Max, 48 GB unified memory  
Holdout: `NJARAW_S001_S001_T020`, absolute frame 0, 5760 × 4320

## Outcome

v0.0.1 establishes the first exact lifetime-contracted planar stage. It removes
one full `H × W × 3 × 3` DIR marginal allocation by changing the existing
activation tensor into that marginal in place, after the last consumer of the
original activation probabilities has finished.

The selected 250k spatial-pixel workset:

- changed zero float32 formed-density values;
- changed zero projection or scan uint16 values;
- reduced negative-formation peak RSS by about 475 MiB (6.36%);
- improved repeated negative-formation median time by about 1.16%;
- used one persistent 8.50 MiB tile scratch instead of another 854.30 MiB
  nine-plane full-frame tensor.

This is a useful result, but it remains a lab path until T032, T007, synthetic
ramps/primaries and longer thermal runs pass. V43H and Quality-XPU defaults are
unchanged.

## The lifetime error in the old layout

After all 45 finite-site classes have been sampled and calibrated, the full
nine-plane `activations` tensor no longer needs to retain activation
probabilities. DIR immediately derives

```text
marginal = clip(4 * activation * (1 - activation), 0, 1)
```

The accepted implementation allocated `marginal` as another full tensor while
also retaining:

- the original activations;
- the nine-plane layer deviation;
- the copied nine-plane coupled output;
- expression temporaries and scalar filtering buffers.

At 5760 × 4320 float32, one scalar plane is 94.92 MiB and one nine-plane tensor
is 854.30 MiB. The marginal was mathematically new data but did not require new
lifetime storage: the activation buffer had reached its final consumer.

## Exact v0.0.1 transition

The new stage processes full-width row tiles and performs the same float32
ufunc order as the accepted NumPy expression:

```python
complement = 1.0 - tile
tile = tile * 4.0
tile = tile * complement
tile = clip(tile, 0.0, 1.0)
```

The actual implementation uses `out=` for every operation. A single scratch
array holds `complement` and is reused for every row tile. No DIR strength,
Gaussian, border, dye-record mix, calibration, random identity or observer
equation changes.

The coupled-output copy is allocated only after the activation-to-marginal
transition. The default path retains its historical allocation order; this
reordering exists only when v0.0.1 is explicitly installed.

## Workset selection

All three native candidates were exact:

| Requested spatial pixels | Maximum actual pixels | Scratch | Negative formation | Peak RSS |
| ---: | ---: | ---: | ---: | ---: |
| 250,000 | 247,680 | 8.50 MiB | 18.890 s | 6.8273 GiB |
| 500,000 | 495,360 | 17.01 MiB | 18.857 s | 6.8278 GiB |
| 1,000,000 | 996,480 | 34.21 MiB | 18.984 s | 6.8271 GiB |

The timing spread is too small to distinguish from normal run variation. 250k
was selected because it provides the smallest scratch and the same exactness.

The final implementation allocates the 250k scratch once and reuses it. Its
marginal stage measured 0.1938, 0.1914 and 0.1925 seconds across three runs.

## Repeated negative-formation evidence

Fresh alternating runs after scratch reuse:

| Path | Seconds | Median | Peak RSS median |
| --- | --- | ---: | ---: |
| accepted V43H | 18.539, 18.909 | 18.724 s | 7.2912 GiB |
| v0.0.1 250k | 18.169, 18.506, 18.692 | 18.506 s | 6.8277 GiB |

The observed median speed improvement is 1.16%. The RSS reduction is 0.4636
GiB, approximately 475 MiB or 6.36%. The measured saving is smaller than the
854.30 MiB tensor size because allocator high-water marks and other overlapping
arrays determine process RSS; the important evidence is that the saving is
repeatable and not merely theoretical.

## Complete physical-observer confirmation

One final paired run included 5279 formation, 2383 projection, Period/2K scan
and reference delivery encoding:

| Path | Negative | Dual observer | Total | Peak RSS |
| --- | ---: | ---: | ---: | ---: |
| accepted V43H | 19.151 s | 23.488 s | 43.208 s | 8.6211 GiB |
| v0.0.1 | 18.730 s | 23.204 s | 42.499 s | 8.5789 GiB |

The paired total was 1.64% faster. Full-process RSS improves by only about 43
MiB because later observer tensors create a different peak. That does not erase
the 475 MiB negative-stage reduction, but it shows where v0.0.2 must work next.

## Exactness evidence

Every candidate and repeated run matched the reference arrays. The final
physical run retained these hashes:

| Array | SHA-256 |
| --- | --- |
| formed 5279 density float32 | `43dcb77057f8a21956a74c8105da10a83294cd33934006382ba077e9853e72be` |
| projection uint16 signal | `f909c68f278e0c6b5a4929a556dce937ecd7a0d90a4310150dc581ae68f0aee1` |
| scan uint16 signal | `3e25af9c3ab0424fc5d31d9da70dfa2bb81f3e87359d0748b3d18d116c200a80` |

For all three arrays:

- maximum absolute delta: `0`;
- changed values: `0`;
- sampler identity audit: 45 unique calls, no collisions.

## Interface and isolation

`engine/src/wavefront_tile_lab_v001.py` owns:

- semantic version `0.0.1`;
- the exact in-place transition;
- workset validation;
- persistent scratch allocation per call;
- stage time, call count, maximum tile and scratch telemetry;
- an explicit installer that sets an experimental flag only after the normal
  engine has been configured.

`engine/src/benchmark_v43h_wavefront_tiles.py` exposes the experiment through
`--marginal-workset-pixels`. Supplying no flag executes the unmodified V43H
baseline.

## Acceptance boundary and v0.0.2

Update: v0.0.2 has now completed this optical-buffer contraction with exact
T020, T032 and T007 results. See
`WAVEFRONT_TILE_LAB_V0.0.2_2026-08-09.md` for the implementation and evidence.

v0.0.1 proves that lifetime analysis can improve both memory and time without
changing film. It does not yet create the full resident Metal island.

The next lab version should contract the dominant stochastic island:

```text
finite-site count
  -> disk integration
  -> Gaussian optical integration
  -> population accumulation
  -> layer storage / DIR input
```

The goal is to stop materializing two full scalar filtered planes for every one
of 45 size classes while preserving global Philox identity and physical frame
borders. It must retain v0.0.1's zero-difference gate and demonstrate gains on
T020, T032 and T007 before any Production discussion.

## Reproduction

```text
PYTHONPATH=engine/src:. python3 engine/src/benchmark_v43h_wavefront_tiles.py \
  <T020.MOV> --decoder <prores_raw_float_decode> --cache <frame.npy> \
  --output <result> --reference <baseline> --frame 0 \
  --marginal-workset-pixels 250000
```

Generated density and observer arrays remain under the untracked `work/` tree
and are not committed.
