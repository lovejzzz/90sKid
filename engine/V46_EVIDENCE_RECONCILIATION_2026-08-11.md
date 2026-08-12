# V46 research reconciliation: what is correct, inferred, and still unknown

Date: 2026-08-11
Release class: research-only audit
Image change: none

## Decision

V45 remains the current conservative executable baseline, but it must not be
described as a measured digital twin of KODAK VISION 500T 5279. Its stage order
is substantially more faithful than an overlay-grain emulation: exposure forms
three negative records, finite populations create density variation, processed
stock MTF acts in density, and the same realized negative enters the scan and
print observers. However, several latent quantities and two delivered observer
boundaries are empirical. Passing the current regression suite proves internal
research conformance and delivery integrity; it does not prove material
equivalence to one roll of 5279 printed to 2383.

This audit therefore makes no image-changing V46. It corrects the evidence
ledger and adds a physical-aperture RMS test. The next image-changing version
must isolate one newly measured or clearly falsifiable quantity.

## Reconciled evidence ledger

### Directly constrained by stock or standards documents

- 5279's three characteristic curves, D-min, processed-stock MTF, net spectral
  dye-density shapes and exposure-dependent diffuse RMS granularity graph;
- the interpretation of negative spectral lobes as net density change including
  coloured masking-coupler consumption, rather than three all-positive dyes;
- 5279 processing in ECN-2 and the 48-micrometre aperture attached to its RMS
  observation;
- 2383's separated Status-A curves, ECP-2D-era layer order, print MTF, peak-
  normalized dye-density shapes and xenon viewing intent;
- the 2383 LAD aim of 1.09 R / 1.06 G / 1.03 B for visual-neutral density 1.0;
- the CIE 1931 2-degree observer table now used at 1 nm.

These sources provide representative production-coating curves, not toleranced
factory specifications for every roll. Kodak explicitly reserves coating,
storage, exposure and process variation.

### Correct model placement, but not stock-identified parameters

- fast, medium and slow populations are a physically meaningful way to divide a
  colour record, and finite-site `p(1-p)` variance correctly quiets at both
  unexposed and saturated limits;
- DIR/interimage influence belongs during development, before final record
  observation;
- deterministic processed-stock MTF should be applied once in negative density,
  rather than sharpening a finished display image;
- successive motion-picture frames should use new emulsion realizations. The
  stable 30-degree phase removes raster-kernel breathing without temporally
  freezing the grains;
- a print observer should expose 2383 through the complete 5279 orange-mask
  spectrum, invert separated Status-A density to dye amount, and integrate
  transmitted projector light spectrally.

These statements support the architecture. They do not disclose 5279's exact
nine-population coating formula, cloud radii, clustering, site density, DIR
species, transport strengths or cross-record covariance.

### Explicit empirical or provisional boundaries in the current baseline

1. **Digital RGB to film-record exposure.** A demosaiced three-channel RAW
   rendering does not contain the scene spectrum. The broad 3x3 record-
   sensitivity mapping is therefore a tristimulus surrogate; it cannot reproduce
   5279 metamer differences without camera sensitivities, illuminant spectra and
   scene spectral data.
2. **Input colour residual.** V41's 12.5-percent chroma residual is bounded by
   the outdoor T003/T005 chart captures. It is not a complete GH7 characterization
   and cannot establish white balance, illuminant or absolute saturation.
3. **Negative morphology and DIR.** The five size classes, fast/medium/slow
   weights, radii, site counts and DIR matrices are constrained priors. Kodak's
   public 48 um RMS and MTF curves do not identify them uniquely.
4. **2383 interimage.** Matrix placement is supported by analytical film-preview
   literature, but the current matrix is a cross-vendor surrogate rather than a
   disclosed 2383 factory measurement.
5. **Period scanner.** Spirit 2K's xenon source, line-array architecture and
   broad workflow are documented; its actual dichroics, CCD sensitivities,
   optical film match, flare and restoration settings are not.
6. **Intrinsic 2383 grain.** It remains deliberately zero in V45 because public
   2383 data do not identify the print's frequency-resolved record covariance.
7. **Projector and room.** The digitized xenon curve does not contain a specific
   lamp's lines, age, reflector/filter transmission, screen reflectance or
   auditorium flare.

## Important observer clarification

The delivered V45 projection view is a normal-process Rec.709 monitor proof,
not an unadapted measurement of light from a theatre screen.

Its deterministic mean follows the analytical path:

```text
5279 density -> orange-mask printer spectrum -> 2383 Status-A density
             -> 2383 dye spectrum -> xenon -> CIE XYZ -> monitor proof
```

The visible stochastic colour detail is more conservative and hybrid. V40
withdrew V39's independent record propagation after it produced sparse primary-
colour impulses. The accepted path obtains the grain delta from the earlier
pointwise 5279-to-print observer, transfers it through the print spatial kernel,
removes the unidentified highest-frequency opponent remainder, and adds it to
the analytical deterministic mean. The monitor colour is also bounded toward
the provisional Spirit/scan reference.

This is a defensible artifact-prevention policy while covariance is unknown. It
is not a complete physical derivation of coloured 5279 grain through 2383. Later
documentation should say "hybrid monitor-proof observer" rather than implying
that every delivered projection pixel is produced by one measured spectral
chain.

## New 48-micrometre RMS verification

### Historical gate problem

`audit_v39_density_reconstruction.py` compared the standard deviation of the
unfiltered pixel residual with Kodak's 48 um diffuse RMS target on a fixture
only 320 pixels wide. With the project's 24.9 mm image-width mapping, the 48 um
aperture radius there is about 0.31 pixel and rasterizes to one sample. The gate
therefore did not test aperture averaging, even though it was named as a Kodak
48 um check.

### Corrected experiment

`src/audit_v46_5279_aperture_rms.py` uses a 1920 x 384 uniform patch, for which
the 48 um aperture radius is 1.8506 pixels and the circular kernel has real
spatial support. It measures ten log-exposure points from -4 to +1 after
applying the physical aperture to each formed density record.

Result from the fixed V45/V42 negative:

| quantity | result |
| --- | ---: |
| tested log-exposure points | 10 |
| tested record observations | 30 |
| worst absolute relative RMS error | 1.263% |
| accepted audit tolerance | 2.0% |
| unfiltered-pixel / 48 um RMS ratio | about 2.68-2.72 x |

The corrected gate passes. This supports the implementation's aperture-weighted
marginal amplitude calibration across the modeled exposure range. It also
explains why the native high-frequency density field can look much more active
than the plotted Kodak number: the published statistic is measured only after a
48 um aperture has averaged that field.

This result does **not** validate spatial NPS, grain shape, temporal tails,
cross-record covariance, DIR coefficients or observer transfer. Many different
fields can pass the same aperture RMS test.

## 2005 versus 2026 2383 curve check

The period March 2005 H-1-2383t sheet remains the appropriate 5279-era process
reference. The March 2026 Kodak sheet changes the surrounding process text to
ECP-2E, but the plotted sensitometric, MTF and granularity figures retain the
same graph identifiers and the displayed curve page still names ECP-2D. Visual
comparison did not establish a material curve change that justifies a new
image version. The code's visually digitized 2383 curves remain approximate;
they should be traced from the 2005 graph explicitly in a future provenance
cleanup rather than described simply as "the 2026 curve."

## What earlier research got right

- V28 correctly stopped applying Panasonic's RAW-Gamut camera LUT to an
  AVFoundation buffer already reported as extended-linear BT.2020/D65.
- V34 correctly removed duplicate deterministic adjacency already represented
  in processed-stock MTF.
- V36 correctly separated density from sharpness and exposed a frame-window
  comparison error.
- V37 correctly identified numerical phase breathing without adding temporal
  smoothing.
- V39 correctly moved the image variable into density, then correctly withdrew
  its unsupported pre-DIR inversion and independent 2383 grain after the V40
  colour-tail failure.
- V45 correctly replaced the approximate colour-matching observer without
  pretending that interpolation creates missing material spectra.

The common weakness was not the order of operations. It was occasionally
promoting a constrained surrogate or a passing internal gate into stronger
language than the evidence allowed.

## Next research priorities

1. **Input characterization:** uniform D65 and tungsten ColorChecker plus gray,
   black and exposure brackets from the GH7/recorder combination. This can
   replace or reject V41's residual, but it still cannot identify 5279 chemistry.
2. **Processed 5279 image structure:** uniform patches at toe, RMS maxima,
   midscale and shoulder, scanned at known sampling pitch and aperture. Estimate
   per-record auto- and cross-spectra with uncertainty and hold out at least one
   aperture and exposure.
3. **5279-to-2383 colour:** same-batch separation/neutral wedges printed under a
   controlled ECP-2D process, with Status-M negative, Status-A print and spectral
   transmission measurements. This can replace the negative and print
   interimage surrogates.
4. **Observer characterization:** measured projector SPD/screen or a documented
   scanner response. Keep theatre transmission and Rec.709 monitor proof as
   separately named outputs.
5. **Algorithm candidate, not baseline:** compare the current finite-site field
   with a continuous Boolean/analytical Gaussian renderer fitted to the same
   measured constraints. Newson et al. support that model family and Zhang et
   al. show a much faster analytical form, but neither paper supplies 5279 stock
   parameters.

Until those measurements exist, further global colour, contrast or grain-size
tuning would be a hypothesis edition, not a more accurate 5279 baseline.

## Primary references

1. Eastman Kodak, *KODAK VISION 500T Color Negative Film 5279/7279*,
   H-1-5279t, revised March 2003.
2. Eastman Kodak, *KODAK VISION Color Print Film 2383/3383*, H-1-2383t,
   revised March 2005.
3. Eastman Kodak, *LAD for KODAK VISION Color Print Film*, H-61B.
4. CIE, *CIE 1931 colour-matching functions, 2 degree observer*,
   DOI 10.25039/CIE.DS.xvudnb9b.
5. A. Newson, J. Delon and B. Galerne, "A Stochastic Film Grain Model for
   Resolution-Independent Rendering," *Computer Graphics Forum* 36(8), 2017,
   DOI 10.1111/cgf.13159.
6. A. Newson, N. Faraj, B. Galerne and J. Delon, "Realistic Film Grain
   Rendering," *Image Processing On Line* 7, 2017,
   DOI 10.5201/ipol.2017.192.
7. K. Zhang, J. Wang, D. Tian and T. N. Pappas, "Film Grain Rendering and
   Parameter Estimation," *ACM Transactions on Graphics* 42(4), 2023,
   DOI 10.1145/3592127.
8. A. Ishii, "Color Management Technology for Digital Film Mastering," IS&T
   CIC 11, 2003; includes 401 measured EK5279-to-EK2383 colour patches but does
   not publish a complete stock-specific microscopic model.
9. Apple, *Adjust ProRes RAW camera settings in Final Cut Pro*.
10. Panasonic, *RAW output data V-Log/V-Gamut conversion LUT*, GH7-compatible
    ProRes RAW workflow.
