# V47–V49: grain structure and microscopic-density boundary audit

Date: 2026-08-11
Status: isolated numerical corrections; stock-specific morphology remains unmeasured

Amplitude-authority note: V49's numerical corrections remain current, but its
coarse historical transcription of Kodak's 48 µm curves is superseded by the
vector-path recovery documented in
[`V50_VECTOR_TRACED_GRANULARITY_2026-08-11.md`](V50_VECTOR_TRACED_GRANULARITY_2026-08-11.md).

## Question

The public 5279 granularity plots give diffuse RMS density through a 48 µm
aperture. They do **not** publish the complete two-dimensional noise-power
spectrum (NPS), cross-record covariance, microscopic density distribution, or
frame-to-frame statistics. The reconstructed engine must therefore distinguish:

1. properties that follow from the physical/numerical contract and can be
   tested without a real 5279 sample; and
2. stock-specific morphology that cannot honestly be selected from the public
   sheet alone.

The V47 audit tests the first category and records, but does not fit, the
second.

## Literature boundary

Newson et al.'s Boolean model places grain centres continuously and forms the
image from the grains themselves, rather than blending a finished noise plate
over an image. Its spatial correlation is part of the image-formation model.
Zhang et al. derive analytical second-order statistics and parameter estimation
for the same class of model, while explicitly limiting that approximation to
conditions where individual grains are not resolved. These results support our
finite-site, density-domain architecture; they do not supply 5279's missing NPS
or coating parameters.

Primary references:

- Newson, Faraj, Galerne and Delon, “Realistic Film Grain Rendering,” *IPOL*
  7 (2017), 165–183. <https://www.ipol.im/pub/art/2017/192/>
- Zhang, Newson, Pappas and Delon, “A Fast and Scalable Implementation of the
  Clustered-dot Model of Film Grain,” *ACM Transactions on Graphics* 42(4)
  (2023). <https://doi.org/10.1145/3592127>
- Kodak, *KODAK VISION 500T Color Negative Film 5279 / 7279*, archived
  technical data. <https://125px.com/docs/motionpicture/kodak/5279.pdf>

## V47 audit contract

`src/audit_v47_5279_structure.py` renders uniform density fields and measures:

- temporal lag-one correlation and the RMS of adjacent-frame differences;
- horizontal/vertical lag-one correlation and their anisotropy;
- normalized radial NPS and twelve angular NPS sectors;
- cross-record covariance eigenvalues;
- skew, kurtosis and tail percentiles;
- exact point mass at numerical density bounds.

Only these are pass/fail gates:

- fresh film frames are statistically independent;
- the numerical raster operator does not introduce material x/y anisotropy;
- covariance is positive semidefinite;
- no hard-bound pile-up is manufactured by the renderer.

Radial NPS shape, RGB covariance magnitude and higher moments are descriptive
only because Kodak does not publish targets for them.

## Finding 1: V37's fixed global phase is directionally biased

V37 correctly stopped the grain kernel from rotating or breathing between
frames, but it translated each complete size-class field by a fixed bilinear
subpixel offset. The continuous grain sites remained independent; the raster
operator did not.

At native 5760-pixel width, a uniform exposure test found V45 x/y lag
anisotropy of 0.045–0.109 and angular NPS peak-to-valley differences of
0.50–0.91 dB. With the translation disabled, lag anisotropy fell below 0.001.
This is a numerical artifact, not evidence about 5279.

## V48 correction: isotropic continuous-site second moment

A site position uniformly distributed within a native pixel contributes
variance 1/12 pixel² per axis. Integrating the result over an output pixel
contributes another 1/12 pixel². V48 removes the fixed whole-field translation
and adds the combined isotropic variance in quadrature to each optical kernel:

\[
\sigma_{48} = \sqrt{\sigma_{45}^{2}+\frac{1}{12}+\frac{1}{12}}
             = \sqrt{\sigma_{45}^{2}+\frac{1}{6}}.
\]

This is a second-moment numerical integration model, not a new 5279 grain-size
measurement. All colour, H-D, finite-site activation, DIR, MTF, 48 µm RMS,
scan, 2383 and delivery parameters remain unchanged.

At width 1920 across four exposures and six frames, V48 measured:

- maximum temporal lag-one correlation: 0.00111;
- maximum error from independent-frame difference RMS: 0.00110;
- maximum x/y lag anisotropy: 0.00131;
- no exact density-bound pile-up in that test;
- worst 48 µm RMS error: 1.47% (2% gate).

## Finding 2: the macro H-D maximum was used as a microscopic clamp

V45/V48 limited every native density sample to the representative
characteristic-curve maximum plus 0.12 density. Kodak's H-D curve is a
macroscopic/aperture representative response; the public data do not identify
that value as the capacity of each approximately 4.3 µm reconstructed sample.

The result was an exact, nonphysical point mass. At native width and logE +1,
about 1.2% of V45 and 1.9% of V48 blue-record samples landed at precisely the
upper guard. This creates a clipped stochastic plateau and alters tails and
high-frequency statistics.

## V49 correction: remove only the unsupported upper guard

V49 retains non-negative total optical density but removes the inferred
macro-Dmax-plus-0.12 per-sample ceiling. It does **not** introduce an invented
replacement tail or claim to measure the coating's microscopic capacity.

Native-width tests at logE 0 and +1, six frames each, measured:

- maximum temporal lag-one correlation: 0.00084;
- maximum independent-frame RMS-ratio error: 0.00108;
- maximum x/y lag anisotropy: 0.00115;
- exact numerical-bound point mass: zero;
- positive-semidefinite record covariance;
- worst 48 µm RMS error: 1.28% (2% gate).

At logE +1, 1.94% of blue samples exceed the former arbitrary guard, but they
now form a continuous negative-skew tail rather than an exact clipped mass.
This fraction describes the current hypothesis; it is not a measured 5279
quantity.

## Current decision

V49 is the most defensible reconstructed baseline so far because both image
changes remove demonstrated numerical artifacts while preserving every
published-data authority. It is still not a measured digital twin of 5279.

The remaining native-grid angular NPS variation is small, and the public data
cannot tell us how much belongs to square pixel integration versus the stock.
Changing the circular-cloud rasterizer solely to make the spectrum look more
isotropic would be an artistic fit. It is therefore withheld pending either:

- a calibrated high-resolution scan of uniform 5279 exposures, or
- a separate, explicitly hypothetical profile with blind comparison.

The subsequent six-frame 5760 × 4320 delivery test completed at 53.7 seconds
per frame. Its display-domain high-pass statistics remained stable while the
uniform-field audit independently proved that V48/V49 removed the raster
anisotropy and hard-bound point mass. V49 is therefore accepted as the
numerical base inherited by V50.
