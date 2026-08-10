# V44 — Observer Integrity and Scale-Honest Review

Date: 2026-08-10  
Release class: evidence-boundary and delivery revision  
Image-formation baseline: accepted V42  
Test source: `NJARAW_S001_S001_T020.MOV`, frames 0–23, 5760×4320, 24000/1001

## Question

V43H looked coarse and inexpensive in native QuickTime playback. Its sharpness
still read as 35 mm, while the moving texture suggested 8 or 16 mm. Projection
and scan also appeared insufficiently distinct. The task was to determine
whether this came from Wavefront execution, speculative 2383 grain, the
negative observer, the guessed V43H NPS, or display scaling before changing the
film model.

## Ablation record

All tests used the same T020 frame.

| Test | Result | Interpretation |
|---|---:|---|
| Wavefront v0.2 vs pre-merge exact projection RMS | ≈0.000366 code | execution is not the visible cause |
| V43H projection high-frequency RMS | 0.013498 | reference condition |
| V43H with speculative 2383 grain disabled | 0.013453 | only ≈0.33% lower |
| Full formed-density projection observer | 0.014116 | 4.9% higher than no-print control |
| V42 projection high-frequency RMS | 0.013741 | reverting NPS alone is not a smoothing operation |
| Lanczos / area-integrated projection review | 1.71× | sharp resize folds native structure into false coarse texture |
| Lanczos / area-integrated scan review | 1.21× | the same effect is present but smaller |

The 48 µm diffuse-RMS measurement is an aperture integral. It does not uniquely
identify the continuous 5279 noise-power spectrum. V44 therefore does not tune
another guessed NPS to make the result look smoother.

## V44 image boundary

V44 calls the accepted V42 profile, then explicitly withholds the three V43H
hypotheses:

- no V43H negative-correlation/NPS candidate;
- no synthetic Spirit response candidate;
- no stochastic 2383 common-density grain without measured three-record
  covariance and exposure-conditioned NPS.

H-D curves, net dye spectra, V41 input-colour boundary, nine speed populations,
DIR, processed 5279 MTF, 48 µm RMS, black, gamma and exposure remain frozen.

## Observer-publication gate

The historical V31 publication adapter combined low-frequency scan Oklab
chroma with projection luminance and high-frequency opponent residual. That was
a documented normal-process monitor boundary. It also explains why scan and
projection have similar low-frequency colour.

The first V44 candidate removed it and published analytical 2383 colour
directly. The reduced still appeared plausible, but the complete 24-frame
native audit failed:

- projection dark opponent p99.99: 0.04882 (gate 0.035);
- projection high-pass opponent/luma RMS: 0.2960 (gate 0.20);
- isolated opponent impulses above 0.06: about 127 per million dark pixels;
- scan passed its established tail and impulse gates.

That candidate is retained as a failed experiment and is not released. V44's
accepted contract is:

```text
projection_light = observe_2383_xenon(realized_5279_negative)
scan             = observe_period_2K_Cineon(realized_5279_negative)
projection       = normal_process_monitor(
                     lightness_and_texture=projection_light,
                     low_frequency_dye_chroma=scan)
```

2383 still owns projection luminance, black, contrast and texture. Period scan
supplies only low-frequency dye chroma through the already accepted V31
boundary. Similar branch colour is an explicit evidence limit; V44 does not
invent a stronger theatrical colour difference without a measured print,
projector light and reference viewing condition.

## Scale-honest review

The professional master remains 5760×4320, 12-bit ProRes 4444 XQ with Rec.709
primaries and BT.1886 reference intent. A separate review derivative is formed
from the encoded master:

\[
L_{review}(i,j) = A_{pixel}\left[
  EOTF_{BT.1886}\left(V_{master,5.7K}\right)
\right]
\]

where \(A_{pixel}\) integrates linear observer light over one 1920×1440 review
pixel. sRGB is applied only after integration:

\[
V_{review}=OETF_{sRGB}(L_{review})
\]

This is not a blur parameter in the film model. It is an explicitly declared
sampling operation for a particular display raster. It prevents a player from
using an unknown sharp resize that can alias above-Nyquist grain and detail into
coarser false texture.

The still is decoded from the selected frame of the final encoded review movie.
The pre-encode float image is no longer a second still authority.

## Practitioner evidence from the supplied video

The user supplied [“How Hollywood Fakes the 90s Film Look Today” — CinePro Film
School / Walter Volpatto](https://www.youtube.com/watch?v=rSKAV2AQ4I4).
The useful claim is architectural, not numerical:

- a theatrical print, telecine/tape/Blu-ray transfer and a modern reference
  still are different targets;
- grain, resolution loss, print/projector light, projector flicker, development
  unevenness, contrast and colour can belong to different stages;
- a later transfer is evidence for that transfer, not automatically for the
  original theatrical white point or print colour;
- a rigorous recreation would need a negative rescan, the print stock and the
  projector-light spectrum.

V44 uses this to separate evidence targets, not to manufacture a theatrical
colour target from incomplete data. It does **not** add flicker, streakiness or
development unevenness. Those remain future measurable modules, not baseline
aesthetic effects.

## Release probes

- native masters: 5760×4320, ProRes 4444 XQ, `yuv444p12le`;
- review files: 1920×1440, ProRes 4444 XQ, `yuv444p12le`, sRGB transfer tag;
- source audio: 24-bit PCM retained;
- source timecode: retained at `11:10:43:00` for frame 0;
- highlight hard clip: none in either branch;
- sampler: 45 unique record/population/size identities, zero duplicates;
- V44 conformance: every engine check passes;
- rejected direct-colour candidate: retained locally and blocked by the
  24-frame colour-tail audit;
- accepted normal-process publication: all projection and scan gates pass over
  the complete 24-frame native-resolution sequence;
- accepted projection worst dark opponent p99.99: 0.02927; isolated impulses
  above 0.08: zero;
- accepted scan worst median opponent p99.99: 0.03770; isolated impulses above
  0.08: zero;
- total wall time: 1163.49 seconds for 24 frames (48.48 seconds/frame including
  finalization); image computation: 1088.06 seconds (45.34 seconds/frame);
- image-computation split: negative formation 476.94 seconds, dual observer
  598.24 seconds, delivery encoding 12.87 seconds.

## Remaining limits

V44 is an internally consistent, evidence-bounded reconstruction. It is not a
closed measurement of a particular 5279 batch through a known 2383 batch and a
characterized projector or scanner. The following remain unknown:

- the stock-specific continuous 5279 NPS and sublayer morphology;
- three-record 2383 grain covariance and exposure dependence;
- actual Spirit spectral response and its historical calibration;
- projector lamp spectrum, print ageing and theatre flare for any reference;
- transfer and grading decisions behind a Blu-ray reference.

These unknowns stay visible in provenance rather than being hidden by a grade.
