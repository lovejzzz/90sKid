# V24 — 35 mm texture separation

## Question

Why can V23 be attractive yet read as early CCD or 16 mm rather than 35 mm
5279, even though its per-record granularity is calibrated to Kodak's 48 µm
diffuse-RMS curves?

## Official constraints

- H-1-5279t describes 5279 as fine grain / high sharpness and publishes three
  marginal RMS-granularity curves measured with a 48 µm aperture.
- A single aperture RMS is an amplitude constraint, not a complete Wiener or
  noise-power spectrum.
- Kodak E-58 states that final print graininess also depends on magnification,
  the negative's granularity and frequency, negative and print contrast, print
  material granularity, and the MTF of the negative, print material, and
  printing system.
- The 2383 and Spirit paths therefore cannot be treated as neutral windows onto
  one universal visible grain field. They are different observers.

## Diagnosis of V23

V23 retained three perceptual cues associated with smaller-gauge film or early
digital acquisition:

1. too much probability in the largest dye-cloud quadrature points;
2. a high visible opponent-colour/luminance grain ratio;
3. the source camera's high local acutance surviving under the grain field.

V24 addresses the first two while deliberately leaving deterministic colour,
tone and the published-stock MTF fit unchanged. This isolates texture from
grading.

## Candidate decision

Selected profile: `fine35_integrated`.

- correlation scale: `0.86 → 0.76`
- size fractions: `[.10,.24,.34,.22,.10] → [.16,.30,.32,.17,.05]`
- radius factors: `[.62,.78,.98,1.22,1.55] → [.50,.68,.86,1.08,1.34]`
- projection opponent integration: sigma `.62 @ 2K`, HF retention `.36`,
  strength `.66`
- scan opponent integration: sigma `.72 @ 2K`, HF retention `.30`, strength
  `.64`

The stronger `fine35_quiet` candidate was rejected because it moved the visible
grain too close to neutral-luminance-only texture and risked becoming a generic
monochrome grain overlay.

## Validation

- Maximum 48 µm RMS relative error across three test exposures and records:
  approximately `0.6–1.4%`.
- Deterministic mean-output maximum absolute change from V23: `0.000000` for
  both output branches and both real scenes.
- T020 projection opponent/luminance RMS ratio: about `1.58 → 0.93`.
- T020 scan opponent/luminance RMS ratio: about `1.72 → 0.92`.
- T032 projection opponent/luminance RMS ratio: about `2.07 → 1.15`.
- T032 scan opponent/luminance RMS ratio: about `2.11 → 1.08`.

Full numerical output is in `metrics.json`; 100% candidate crops and full-frame
strips are in `candidates/`.
