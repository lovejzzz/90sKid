# V31 — Normal-process 2383 projection colour

## Question

V30's 2383 monitor result looked convincing in texture but suggested partial
silver retention: dense blacks, strong luminance structure and comparatively
restrained colour.  The question was whether that appearance belongs in a
baseline reconstruction of normally processed 5279 printed to 2383.

## Process evidence

Kodak describes colour development as forming dye and metallic-silver images at
the same exposed sites.  In normal ECN-2 and ECP-2D, bleach converts that silver
to removable silver-halide compounds and fixer removes them.  Kodak separately
describes skip bleach, bleach bypass and ENR as non-standard techniques that
increase contrast, darken shadows and reduce colour saturation.

Therefore the default 5279 -> 2383 observer must not acquire a retained-silver
signature unless a separate process branch explicitly models silver retention.

Primary sources:

- Kodak H-24 Module 7, Process ECN-2 Specifications:
  https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-7.pdf
- Kodak H-24 Module 9A, Process ECP-2D Specifications:
  https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-9A.pdf
- Kodak Motion Picture Film Processing Information:
  https://www.kodak.com/en/motion/page/processing-information/

## V30 diagnosis

V30 had no retained-silver term.  The appearance came from a stage-order
interaction in its Rec.709 projection observer:

1. the period-scan reference supplied evidence-gated hue and saturation;
2. the neutral 2383 viewing curve supplied a darker, steeper lightness;
3. chroma was reconstructed as constant saturation, `C = S * L`;
4. whenever the print curve lowered `L`, absolute dye chroma `C` fell with it;
5. full-resolution, luma-dominant 35 mm texture remained strong.

Across matched V30 frame-12 previews, projection median chroma was about
12–17 percent below the scan, its p90–p10 linear-luma span was about 27–32
percent larger, and fine luminance texture was about 48–60 percent stronger.
That combination is a perceptual bleach-bypass discriminator even though the
chemistry model contains no residual silver.

## V31 correction

Two earlier placements were rejected by full-frame regression.  A cached-LUT
change was bypassed by the legacy physical/calibrated hybrid branch; a later
deterministic-mean correction was pulled back by the grain mean-colour stage.
The accepted correction therefore operates once, after both complete V30
observers, where the delivered colour and stochastic texture are both present:

```text
ab_scan_low = GaussianSigma0.72pxAt2K(ab_scan)
ab_print_high = ab_print - GaussianSigma0.72pxAt2K(ab_print)
ab_out = ab_scan_low + ab_print_high
Y_out = Y_print

RGB_out = Rec709GamutCompressAroundTargetY(
  OKLab^-1[L_print, ab_out], targetY=Y_out
)
```

The Period 2K branch supplies only low-frequency dye colour.  The 2383 branch
retains all luminance, including grain, and its own high-frequency opponent
texture.  Exact per-pixel linear Rec.709 Y is restored after constant-hue gamut
compression.  This is not a saturation knob and adds no scene-specific grade.

Across T002/T020/T032, projection-to-scan median chroma retention rises from
82.9/86.0/87.6 percent in V30 to 91.1/93.3/89.2 percent in V31.  Fine-luminance
texture retention versus V30 is 99.2/98.9/99.1 percent.  All three scan masters
remain byte-identical to V30.

## Locked components

- 5279 H-D curves, spectral mask/dyes and D-min
- nine fast/medium/slow stochastic sub-emulsions
- five-class dye-cloud morphology and 48 micrometre RMS calibration
- DIR reaction-diffusion and MTF
- AVFoundation linear-BT.2020 ProRes RAW input contract
- Kodak H-61B 2383 LAD aims: 1.09 / 1.06 / 1.03 Status-A density
- print black, neutral lightness curve, gamma, flare and projection texture
- V27 period 2K / Cineon / Blu-ray observer
- 12-bit Rec.709 1-1-1 delivery

## Boundary

A future bleach-bypass toggle must be a separate process model with an explicit
retained-silver density term and independent process controls.  It must never be
implemented by globally lowering saturation or increasing contrast in the
normal baseline.
