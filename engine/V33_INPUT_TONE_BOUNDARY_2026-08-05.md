# V33 — camera-input, tone and delivery boundary

## Release decision

V33 makes no image-forming change to the accepted V31/V32 film result. It does
not apply a global magenta offset, gray-world balance or scene-specific grade.
The 5279 negative, stochastic sublayers, grain scale, DIR, MTF, 2383 observer,
Period-2K observer, normal-process colour boundary and +0.45-stop virtual film
EI remain frozen.

The version instead separates four questions that had been visually conflated:

1. untouched/as-shot camera exposure;
2. the explicit virtual exposure used to place the digital source on 5279;
3. observer-specific low-chroma displacement;
4. a future measured Technical Neutral camera-input correction.

Technical Neutral exists only as a disabled product boundary. It cannot be
enabled until a gray card or ColorChecker under the scene illumination shows a
repeatable residual, preferably under more than one illuminant. If authorized,
the correction belongs before virtual 5279 exposure and must remain switchable.

## Three native trials

| Source | Absolute frames | As Shot witness | Film input |
|---|---:|---:|---:|
| T002 | 0–23 | 0.00 stop | +0.45 stop |
| T007 | 276–299 | 0.00 stop | +0.45 stop |
| T031 | 132–155 | 0.00 stop | +0.45 stop |

All camera witnesses, projection masters and scan masters are 24-frame,
5760×4320, 24000/1001, 12-bit ProRes 4444 and Rec.709 1-1-1. Projection and
scan files are the accepted V31/V32 masters, reused byte for byte. The new
camera witnesses use the same AVFoundation extended-linear BT.2020/D65 decode,
linear BT.2020→V-Gamut transform, Panasonic V-Log encode and checksum-locked
official V-709 LUT as the previous camera reference, but exposure is 0.00 stop.

The three 0-stop camera witnesses took 358.35 seconds in total when run safely
in sequence: T002 116.12 s, T007 123.57 s and T031 118.66 s.

## Green-direction gate

The immutable Final Cut Pro Standard witness is T031 source frame 144,
SHA-256 `612077c7535122ea94fa752d470688e0f68bac0aaf18fa93a95b4bbf9761aa88`.
The independent FCP audit already rejected an RGB-order, repeated camera matrix,
missing white balance or double legal-range conversion.

A 1,000-step mathematical neutral ramp through BT.2020→V-Gamut→V-Log→official
V-709 has maximum channel spread `0.00058866`. This is below the `0.001` gate
and rejects a global neutral-axis matrix error. Real low-chroma pixels may still
differ between Apple's Standard observer and Panasonic V-709 because the two
nonlinear display transforms are not identical.

## Black, toe, contrast and gamma gates

Hard display black is defined identically to the FCP audit:

```text
encoded Rec.709 luma <= 1 / 1023
```

| Scene | projection hard black | scan hard black | projection effective power | scan effective power |
|---|---:|---:|---:|---:|
| T002 | 0.00095% | 1.82019% | 1.3520 | 1.5139 |
| T007 | 0% | 0.01330% | 1.3730 | 1.3426 |
| T031 | 0.00133% | 1.34924% | 1.3505 | 1.5045 |

The effective power is a robust log-linear fit from the +0.45-stop camera
baseline to each completed observer, not a claim that the observer is a simple
power function. A 32-bin paired tone curve had zero negative steps in all six
scene/observer combinations. Every branch retains measurable positive toe
occupancy and a non-collapsed p05–p95 contrast span. The scan's black decision
is strongly scene-dependent rather than a uniform crush.

## Partial-range audio and timecode

The complete-source path still stream-copies source PCM and timecode. A selected
range now decodes/re-encodes only lossless PCM so `atrim` can begin and end at
the exact requested sample, and regenerates the timecode track at the absolute
source-frame offset. The 24-frame T002 test contains exactly 48,048 samples at
48 kHz, 1.001 seconds of picture/audio and the correctly advanced timecode
`12:04:06:23` for source start frame 24.

## Memory-safety correction

The first attempt to run three native 5.7K float camera witnesses concurrently
ended with a system restart. The supplied panic report records a watchdog
timeout, 100% compressor-segment usage, 50 swap files and low remaining swap.
No accepted master or source file was damaged; incomplete 36-byte MOV stubs
were overwritten by successful sequential renders.

The full-release scheduler now reserves 16 GiB for macOS/applications and
budgets 20 GiB per native Archive-Exact worker. The 48-GiB reference machine
therefore selects one worker even if a larger count is requested. This changes
only scheduling: absolute source-frame seeds, kernels, precision and output
pixels remain unchanged. Quality is not exchanged for speed.

## Validation

`validate_v33_boundary.py` passes with zero failures. It checks the immutable
FCP witness, neutral V-709 axis, four native masters per scene, exposure order,
black, toe, contrast, monotonic tone mapping, effective-power bounds and full
Rec.709/ProRes signalling.

The website uses the already verified V31/V32 projection and scan media plus
three new matched 0-stop sRGB witnesses. Their H.264 first frames pass the same
channel-MAE and median-luma agreement gates as prior releases.
