# V43H Hypothesis Edition / 假想版

## Question

> If the most likely but still unmeasured parts of the existing 5279 research
> are completed with bounded central estimates, what might the stock look like?

V43H is a falsifiable prediction, not a newly measured Kodak 5279 profile and
not a creative grade. V42 remains the accepted research-conformant baseline.
V43H is isolated behind its own profile so every speculative term can be
removed without changing V42.

## Evidence ledger

### Measured or documented anchors retained exactly

- the three published 5279 characteristic curves, net spectral dye-density
  curves, D-min and diffuse RMS granularity observations through Kodak's
  48-micrometre aperture;
- the processed-stock 5279 MTF boundary;
- the 2383 Status-A curves, analytical-dye inversion, LAD aim and normal ECP-2D
  bleach/fix path;
- Apple Standard ProRes RAW as extended-linear BT.2020/D65, converted once into
  the Panasonic/film-record input boundary;
- the V37 stable 30-degree integration phase, V40 post-process colour-grain
  covariance repair and V41's reversible 12.5% chart-residual boundary.

These anchors are inherited from V42. V43H does not change white balance,
exposure, black, contrast, gamma, saturation, DIR coefficients or the published
48-micrometre RMS targets.

### Bounded V43H hypotheses

1. **Finer 35 mm negative morphology.** Public aperture RMS fixes one weighted
   integral of the noise-power spectrum, not the spectrum itself. V43H keeps
   that measured integral but chooses a narrower, denser central morphology:

   - spatial correlation scale: `0.72 ×` V42;
   - radius factors: `[0.46, 0.64, 0.83, 1.04, 1.30]`;
   - optical factors: `[0.72, 0.83, 0.94, 1.06, 1.18]`;
   - fast fractions: `[0.10, 0.25, 0.36, 0.22, 0.07]`;
   - medium fractions: `[0.17, 0.32, 0.32, 0.15, 0.04]`;
   - slow fractions: `[0.26, 0.36, 0.27, 0.09, 0.02]`.

   The processed record residual is still renormalized to the same official
   exposure-dependent 48 µm RMS. This changes spatial allocation, not grain
   loudness.

2. **Period Spirit spectral observer, quarter-step candidate.** DFT documents a
   xenon source, RGB beam splitter and three CCD line arrays; Kodak publishes a
   generic telecine response plot. Neither publishes the Spirit's actual lamp,
   dichroics, CCD quantum efficiencies or period calibration matrix. V43H moves
   only 25% from V42's broad observer toward the synthetic candidate:

   - centres: `[622.5, 542.5, 467.5] nm`;
   - sigmas: `[49.4, 41.8, 36.1] nm`.

   This is deliberately too small to masquerade as a measured scanner profile.

3. **Subordinate 2383 common-density texture.** V39's independent RGB Poisson
   records were not identified by public 2383 data and produced sparse primary-
   colour impulses. V43H tests only a weak common-mode, spectrally neutral
   optical-density event whose amplitude is estimated from Status-A density:

   - record covariance: `1.0` common mode;
   - density scale: `0.06`;
   - effective sites: `900`;
   - radius: `0.30 px` at 5760 pixels;
   - optical sigma: `0.23 px` at 5760 pixels.

   The same scalar density perturbation multiplies the three mean projection
   light records before the existing observer integration:

   ```text
   delta_D_print(x,y) = 0.06 * [k(x,y)/900 - p(x,y)]
   L_print,c(x,y) = L_mean,c(x,y) * 10^(-delta_D_print(x,y))
   ```

   No independent red, green or blue print sites are generated. The term is
   intentionally subordinate to negative granularity and is absent from the
   scan branch. A controlled T020-frame-12 ablation also passed the same random
   field through three equal Status-A record increments and the full spectral
   print observer. Relative to the released neutral-density interpretation,
   its mean-channel difference was below `0.000003`; absolute pixel MAE was
   `0.00180` and 4×4 low-pass p99 was `0.00199`. The difference is therefore a
   microtexture hypothesis, not evidence that either unmeasured covariance is
   Kodak's construction. V43H retains the neutral case because it is the
   conservative candidate that cannot reintroduce V39's opponent-colour tails.

### Explicitly not inferred

- Kodak patent “diffusion factor” values are molecular assay quantities, not
  stock-specific 5279 DIR matrix coefficients. V43H changes no DIR constants.
- A completed feature film, Blu-ray master or Silver Efex preset is not treated
  as an ungraded 5279 measurement.
- The outdoor T003/T005 chart does not authorize a new GH7 white balance,
  complete camera matrix, exposure offset or global saturation correction.
- The 2383 public curve set does not identify three-record print-grain NPS or
  covariance. The common-density term remains a prediction to be rejected by a
  real print measurement.

## Three comparison routes

All four views start from the same Apple-decoded RAW frame. The two V43H film
views share one realized 5279 negative:

```text
RAW -> V43H realized 5279 density -> 2383 / xenon -> projection
                                   -> period Spirit / Cineon -> scan
RAW -> deterministic V43H observer -> independent FSD density comparator
RAW -> Panasonic official V-709 -> camera witness (no film pipeline)
```

FSD is not upgraded into the 5279 model. It stays an independent finite-site
density comparator inspired by the Silver Efex investigation, using `N=176`,
`sigma=0.597 px` and density strength `1.0` after the deterministic observer.

## Controlled A/B result before release

The T032 representative frame was rendered once through the frozen V42 graph
and once through V43H with the same absolute frame and seed identity.

| Branch | Mean RGB change | Mean absolute change | Low-frequency p99 |
| --- | --- | ---: | ---: |
| Projection | `[+0.00047, +0.00086, +0.00089]` | `0.00728` | `0.00354` |
| Period scan | `[+0.00037, +0.00075, +0.00080]` | `0.00376` | `0.00333` |

The small cyan/blue direction is a predicted consequence of the observer
candidate, not a correction for taste. Its magnitude remains below one
thousandth in the mean channels. The common-density print term produces no
independent RGB impulses by construction.

## Delivery and first formal timing

Each requested source is one second, 24 frames, native `5760 × 4320`. Every
branch has a 12-bit ProRes 4444 XQ Rec.709/BT.1886 professional master. The
sRGB QuickTime companion and JPEG are decoded from that encoded master rather
than rendered through a second picture path. Source audio and source-offset
timecode are restored during finalization.

T020 completed in `1708.30 s` wall time (`71.18 s/frame`) for all four outputs
together. Mean formation costs were:

- negative formation: `13.89 s/frame`;
- shared physical projection + scan observer: `49.00 s/frame`;
- independent FSD density: `3.08 s/frame`;
- official Panasonic camera witness: `0.74 s/frame`;
- writing all four XQ masters: `0.49 s/frame`;
- final master-derived companions, stills and source-stream remux: `83.86 s`.

The deterministic observer timing is near zero because it is returned from the
same spectral integration as the physical pair; it is not a bypassed observer.
The original timing collector did not separately measure decoder wait, so its
`decode_read=0` field must not be interpreted as a zero-cost RAW decode.

T032 independently completed in `1725.66 s` (`71.90 s/frame`). Its mean costs
were `14.24 s/frame` for negative formation, `49.08 s/frame` for the shared
physical observers, `3.12 s/frame` for FSD, `0.74 s/frame` for the camera
witness and `0.51 s/frame` for four-master writing. The close agreement with
T020 is evidence that the timing is representative rather than a one-scene
cache accident.

T007 completed in `1699.91 s` (`70.83 s/frame`): negative formation averaged
`14.14 s/frame`, the shared physical observers `48.11 s/frame`, FSD
`3.11 s/frame`, the camera witness `0.72 s/frame`, and four-master writing
`0.57 s/frame`. Across all three scenes the total effective rate spans only
`70.83–71.90 s/frame`.

## Release gates

The release audit checks all three scenes and all delivered frames for:

- 5760 × 4320, 24 frames, XQ, 12-bit 4:4:4;
- BT.709 primaries/matrix, BT.1886 master and sRGB companion transfer labels;
- manifest hashes and explicit `hypothesis_not_measurement` provenance;
- 45 unique Production sampler identities per frame with no duplicates;
- FSD's independent-pipeline contract and 24 unique absolute frame identities;
- native-frame dark-region opponent tails and isolated primary-colour impulses.

The initial discrete gate incorrectly used `count <= ceil(expected count)` as
if a stochastic rate implied a deterministic maximum. On T007 scan frame 4 it
rejected 17 candidates where the 5-per-million reference rate predicts 14.7;
all 17 localized to real foliage, shoreline or stem edges, none exceeded 0.08,
and the remaining tail gates passed. V43H therefore uses a one-sided Poisson
upper bound with a Bonferroni 1% family-wise false-rejection rate across 432
frame/branch/threshold tests. This changes only the audit statistics—not the
image—and still rejects V39's thousands-per-million primary-colour failure by
orders of magnitude.

Passing these gates proves internal consistency and delivery integrity. It does
not convert V43H's unmeasured parameters into Kodak facts.

## References already archived by the project

1. Kodak, *VISION 500T Color Negative Film 5279 / 7279 Technical Data*,
   H-1-5279t.
2. Kodak, *VISION Color Print Film 2383 / 3383 Technical Data*.
3. DFT, *Spirit 2K Product Data Sheet*.
4. Kodak, *Exploring the Color Image*.
5. ISO 10505:2009, *Photography — Root mean square granularity of photographic
   materials — Method of measurement*.
6. Newson et al., *Realistic Film Grain Rendering*, IPOL 2017.
7. Kodak patents US 5,314,793 and US 5,298,376, used only as qualitative
   architecture/mechanism evidence.
