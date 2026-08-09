# V37 temporal-grain formation research

Date: 2026-08-05
Status: V37 native release validated

## Viewer observation

The V35 native ProRes 4444 master can read as a boiling layer rather than as
the image-forming structure of 35 mm 5279. The observation is not caused only
by the website proxy: it remains visible in QuickTime from the local master.

## Physical boundary

Successive motion-picture frames expose different pieces of emulsion, so the
microscopic grain realization should be approximately temporally independent.
Temporal smoothing, advecting one grain plate with the scene, or making grains
persist across frames would create a different digital artifact. Kodak also
describes projected detail as the cumulative perception of different random
grain mosaics at 24 frames per second.

The useful distinction is therefore not `independent` versus `correlated` time.
It is:

- authentic: a new, dense, spatially correlated image-forming mosaic in every
  film frame;
- synthetic: a stable deterministic image plus a numerically redrawn residual
  whose sampling transfer, tail energy or whole-field orientation changes.

Primary references:

- Kodak, *The Essential Reference Guide for Filmmakers*.
- Newson, Delon and Galerne, “A Stochastic Film Grain Model for
  Resolution-Independent Rendering,” 2017.
- Munekata et al., “A Reproduction Model of Film Grain Texture for Digital
  Movies,” 2011.

## Confirmed findings

### 1. The first V35 tail diagnosis was invalidated by a frame mismatch

The first audit compared V35 T031 frames 0--23 with the curated V34 frames
132--155. Its large p99.99 and burst-rate differences mixed source motion and
texture with sampler behavior and are not evidence against the Production
sampler. A corrected, absolute-frame-matched V36/V34 audit puts the principal
high-frequency, temporal and grain-to-edge measures within roughly 0.1%.
Philox-u32 and the Production spatial kernel therefore remain in V37.

### 2. Per-frame subpixel phase creates numerical breathing

For every colour record and fast/medium/slow population, the current code draws
one new phase angle per frame. Five independent size-class fields are then
shifted with bilinear interpolation around a radius of 0.38 native pixel. The
underlying random fields are already independent, so changing this numerical
sampling phase is not needed to obtain film-frame independence.

A matched flat-field density experiment at log exposure -2.5 used identical
random draws in both branches and changed only phase radius:

| density-domain measurement | random phase each frame | zero phase control |
|---|---:|---:|
| framewise high-pass RMS coefficient of variation | 0.64% | 0.09% |
| x/y anisotropy standard deviation | 0.0596 | 0.0050 |
| temporal lag-one correlation | 0.00015 | 0.00029 |

The temporal independence remains in both controls, but the random-phase branch
adds about seven times more whole-frame high-frequency amplitude fluctuation and
about twelve times more directional fluctuation. Zero phase is not the final
solution because it leaves a fixed raster preference. The accepted V37 model
therefore keeps one temporally stable but spatially balanced phase ensemble.

### 3. Real-scene phase screening selected a 30-degree ensemble

The stable ensemble was screened at 0, 30 and 90 degrees on eight native T031
frames. Zero degrees removed temporal breathing but introduced a small fixed
x/y bias. Ninety degrees over-corrected it. Thirty degrees retained the temporal
gain without a meaningful directional shift:

| T031 native measurement | projection | scan |
|---|---:|---:|
| mean x/y anisotropy delta versus V36 | +0.00596 | +0.00359 |
| framewise high-pass RMS CV ratio | 0.400 | observer-limited |
| x/y anisotropy standard-deviation ratio | 0.287 | observer-limited |

The projection result cuts whole-frame high-frequency amplitude variation by
about 60% and directional variation by about 71%. The scan branch gains less
because its scanner aperture and scene content dominate those measurements.
Both branches preserve independent film-frame realizations.

### 4. The density result is still assembled as a calibrated residual

The negative code computes:

```text
formed_density = mean_density + combined_deviation * calibration
calibration = published_48um_sigma / predicted_48um_sigma
```

It later computes `formed_display - mean_display`, adds that stochastic delta
to the separately MTF-filtered deterministic image, and applies the viewing
branch. Exposure, sub-emulsion populations, DIR and dye-record mixing all shape
the residual, so this is more physical than an ordinary display overlay. It is
nevertheless a residual architecture, not a direct rendering of a continuous
population of exposed grain centres.

For the present guessed site densities and morphology, the local RMS correction
is substantial:

| record | correction-factor range over log exposure -4 to +1 |
|---|---:|
| red/cyan | 0.92–3.32 |
| green/magenta | 1.04–4.69 |
| blue/yellow | 3.53–12.45 |

The official 5279 diffuse RMS curve must still be met. The problem is not the
target. The risk is forcing an underidentified finite-site distribution to the
target pointwise: rare events, nonlinear display mapping and the black boundary
can acquire the correct RMS but the wrong temporal tails.

### 5. The final 2383 fine-grain layer is structurally impure but not dominant

The projection branch currently adds a very fine, luminance-ratio 2383 grain
after the negative and projection rendering. It should ultimately be replaced
by print-stock exposure and dye formation in density/transmission space.

An isolated 5760-wide flat-field test shows a 2K temporal-difference RMS of
0.00155 at 18% linear level and 0.00189 at 50%. The measured T002 projection
wall is about 0.02094. The extra layer therefore contributes below one percent
of temporal-difference variance in that example. Removing it alone cannot fix
the false boil.

### 6. Source sensor noise is present but secondary

At the same T002 wall and 2K-equivalent scale, the camera baseline has temporal
difference RMS 0.00698 versus 0.02094 for the V35 projection. In variance terms,
the baseline accounts for roughly eleven percent of the finished fluctuation.
Sensor-noise treatment should still be audited, but it is not the main source of
the observed boil.

### 7. A finished 5279 Blu-ray supports independence, not temporal smoothing

Low-motion regions were selected from the local *Charlie's Angels: Full
Throttle* Blu-ray. A sky patch gives a temporal-difference/high-pass-RMS ratio
of about 1.34 and lag-one correlation of about 0.075; ideal independent noise is
sqrt(2) and zero. This is consistent with mostly independent film texture plus
scanner, restoration and H.264 persistence. The file is an 8-bit 4:2:0 finished
master and cannot set negative-stock tail limits. It is a perceptual envelope,
not a 5279 laboratory measurement.

## V37 candidate architecture

1. Keep new grain sites for every film frame; do not temporally smooth them.
2. Remove the per-frame numerical phase rotation. V37 uses the accepted
   30-degree stable-balanced ensemble; a continuous-centre point-process
   renderer remains a future structural experiment, not an unvalidated release
   change.
3. Sample exposure at grain centres and accumulate developed dye-cloud coverage
   into density. Fit site density, clustering and cloud radii so the official
   H-D and 48-micrometre RMS curves emerge without a large pointwise residual
   multiplier.
4. Split the processed-stock MTF into exposure/layer integration and restrained
   development adjacency, then apply it in an order shared by image detail and
   stochastic formation. Do not preserve a razor-stable digital carrier under
   a separately redrawn field.
5. Form 2383 from negative printer exposure through its own print populations;
   remove the final display-space fine-grain add-on once the density model is
   validated.
6. Keep V34/V35 colours, H-D curves, black, gamma and observer transforms frozen
   while testing grain formation. A grain experiment must not become a grade.

## Required release gates

- official 5279 per-record 48-micrometre RMS versus exposure;
- official processed-stock R/G/B MTF envelope;
- spatial NPS, x/y isotropy and framewise NPS stability;
- lag-one correlation near temporal independence without global phase breathing;
- p99, p99.9 and p99.99 frame-difference tails and connected burst area;
- flat field, smooth gradient, edge, fine texture, T002, T007 and T031;
- camera baseline, scan and projection measured separately;
- at least several sampler identities so acceptance does not depend on choosing
  one aesthetically fortunate random seed.

V37 changes no colour, H-D, black, gamma, MTF, DIR, grain strength, grain size
or observer parameter. Its one image-model change is the integration phase:
new emulsion sites are still generated for every frame, while the numerical
sampling kernel no longer rotates across the whole image from frame to frame.

## Final 24-frame native validation

All three source windows were rendered at 5760 x 4320 as 12-bit ProRes 4444,
Rec.709 1-1-1, with source 24-bit/48 kHz four-channel PCM and partial-range
timecode. Each timing is the effective wall time per source frame for both
observer masters together:

| source window | wall time | seconds/frame |
|---|---:|---:|
| T002 0--23 | 610.20 s | 25.43 |
| T007 276--299 | 616.16 s | 25.67 |
| T031 132--155 | 612.36 s | 25.51 |

Against the matched V36 baseline, the 24-frame median crop ratios are:

| branch | mean high-pass RMS | framewise RMS CV | x/y variation |
|---|---:|---:|---:|
| T002 projection | 1.00354 | 0.79954 | 0.17363 |
| T007 projection | 1.00236 | 0.44487 | 0.15643 |
| T031 projection | 1.00008 | 0.37511 | 0.19014 |
| T002 scan | 1.00108 | 0.86739 | 0.76354 |
| T007 scan | 1.00014 | 0.91768 | 0.83935 |
| T031 scan | 0.99992 | 0.91365 | 0.75200 |

Static high-frequency energy stays within about 0.36% at the median crop while
projection-phase breathing falls substantially in every scene. The scan gains
are smaller, as predicted, because the 2K scanner aperture and source structure
dominate. Temporal-difference RMS, grain-to-edge ratio and lag-one correlation
remain essentially unchanged on T031, confirming that V37 did not temporally
freeze, smooth or advect the grain.
