# V64: 2383 published-curve density boundary audit

Date: 2026-08-11
Real-material check: `NJARAW_S001_S001_T020.MOV`, frame 0
Release class: evidence-withdrawn unmeasured 2383 density shaper

## Result

V64 withdraws one large, underidentified transform and leaves every other
accepted boundary in place.

V63 still contained a density-domain neutral shaper. It bent Kodak's three
vector-traced 2383 H-D curves toward an invented shared principal-density
trajectory, changing them by as much as `0.114 D`. H-61B says a normally
balanced six-step test print should appear neutral, but it does not publish the
six off-LAD Status-A triplets required to identify that continuous rewrite.

Re-reading Kodak's current 2383 sheet confirms that the plotted sensitometric
curves are separate responses to red, green and blue exposure, processed in
ECP-2D and measured by Status-A densitometry. The engine already handles that
coordinate correctly: it nonlinearly inverts each separated Status-A response
to analytical dye amount before recombining the traced C/M/Y spectra. The
problem was therefore not a missing unwanted-absorption correction or a second
dye inversion. It was the additional unmeasured density shaper.

V64 uses the published separated curves directly. It retains:

- V61's joint ISO Status-M inversion of the masked 5279 negative;
- V62's explicit identity endpoint for unidentified 2383 interimage effects;
- V63's actual scene-to-negative-to-print projection-neutral trajectory;
- the frozen scan-referenced off-neutral colour authority; and
- the existing grain, MTF, DIR, RAW-decode and delivery models.

Primary sources:

- Kodak, [KODAK VISION Color Print Film 2383 / 3383 technical information](https://www.kodak.com/content/products-brochures/motion-picture/KODAK-VISION-Color-Print-Film-2383-3383-technical-information.pdf)
- Kodak, [LAD for KODAK VISION Color Print Film, H-61B](https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf)

## What was actually wrong

The historical shaper was not failing because it used a crude substitute for
the active 5279 development. After aligning its neutral film-light coordinate
with the production exposure offset, the simplified and complete V61 paths
differ by only:

```text
maximum density difference  0.00153637 D
mean absolute difference    0.00020701 D
```

The much larger problem is identifiability. Across the tested exposure range,
the shaper rewrites the official curves by:

| record | maximum absolute change | RMS change |
|---|---:|---:|
| red | 0.113786 D | 0.071152 D |
| green | 0.072125 D | 0.042210 D |
| blue | 0.100627 D | 0.071540 D |

That magnitude cannot be justified by a qualitative instruction that six gray
patches should look neutral. A measured neutral wedge could support such a
correction; the public document alone cannot.

## Modeled neutral trajectory before the final view correction

The audit evaluates 225 neutral scene exposures from -8 to +6 stops and
measures OKLab chroma before V63's final projection-view neutral correction.
This isolates what the density shaper itself does.

| density path | median chroma | P95 chroma | maximum chroma |
|---|---:|---:|---:|
| V63 continuous inferred shaper | 0.00604693 | 0.02694877 | 0.02913328 |
| V64 published separated curves | 0.00526566 | 0.01177205 | 0.01336316 |

The inferred shaper more than doubles P95 crossover. Removing it therefore
reduces modeled gray error even before the separately justified V63 view-neutral
trajectory is applied.

The nearest modeled LAD integral Status-A densities remain close:

```text
V63  1.083499 / 1.052820 / 1.023088 D
V64  1.082153 / 1.053226 / 1.023934 D
target 1.090000 / 1.060000 / 1.030000 D
```

The small residual reflects the discrete audit sample nearest the LAD exposure,
not a replacement LAD calibration.

## Real-frame isolation

The formal audit decodes T020 frame 0 through the same AVFoundation ProRes RAW
float path and compares V63/V64 at `1440 x 1080`.

| branch | MAE | P95 absolute | P99 absolute | changed 12-bit components |
|---|---:|---:|---:|---:|
| scan master | 0 | 0 | 0 | 0% |
| delivered scan-referenced projection | 0.0000721 | 0.0002260 | 0.0020568 | 5.60% |
| physical spectral projection | 0.0020307 | 0.0100548 | 0.0196683 | 81.82% |

The scan master is bit-identical, proving that the negative formation and scan
observer were not changed. The physical print branch changes substantially
because the withdrawn shaper had been rewriting most of its 12-bit values. The
delivered scan-referenced projection moves much less because its low-frequency
off-neutral colour remains owned by the frozen display adapter.

No luma clipping or black discontinuity was introduced. Representative physical
projection luma percentiles are:

| path | P0.1 | P1 | median | P99 | P99.9 |
|---|---:|---:|---:|---:|---:|
| V63 | 0.00001117 | 0.00009750 | 0.0270625 | 0.655497 | 0.669533 |
| V64 | 0.00001071 | 0.00010071 | 0.0268633 | 0.656758 | 0.670795 |

Both paths contain zero samples at or below 0 and zero samples at or above 1.

## Historical and implementation isolation

V63 remains reproducible. A deterministic sample of 128 native nodes from its
193-cube was recomputed after the V64 policy gate; every float was exactly equal
and the maximum absolute difference was `0.0`.

V64 owns a separate profile-identical lattice:

```text
engine/cache/print_2383_monitor_output_lut_193_v64.npy
SHA-256 27203fdc8407c446fae65b9f259677cdd8320cdb1ec95961c859105cf211bd32
```

The full regression suite passes 53 tests, including bit-exact archive gates,
both observer branches, delivery encodings, stochastic sampler identities and
the V64 single-variable boundary.

## Native production validation

T020 frame 0 was rendered through the Production Metal path at the complete
source raster, `5760 x 4320`. Both observer masters are ProRes 4444 XQ,
`yuv444p12le`, at `24000/1001` fps with BT.709 primaries, transfer and matrix
metadata. The scan master decodes to the exact V63 frame checksum:

```text
9bad46b6804ad024de342eb291999bea
```

The projection checksum changes from V63
`a32c88b2c943672bf74bdb2ccfca8456` to V64
`3e9cc5e0f6395ffd0376318b3ab08fe4`, confirming that the intended branch reached
the encoded master. Review stills were derived from those masters by
linear-light pixel-area integration. Visual inspection found no sparse RGB
impulses, black discontinuity or independent still/video colour path.

| operation | seconds |
|---|---:|
| negative formation | 15.9093 |
| both observers | 14.8929 |
| delivery preparation | 0.4559 |
| algorithm total | 31.2581 |
| end-to-end wall | 41.9688 |

The release provenance records 45 unique Philox identities with no duplicates,
all V37-V64 conformance gates true, and the expected V64 observer-lattice hash.

Native outputs:

```text
outputs/native_5k_v64_published_hd_density_1f/T020/
```

## What V64 still cannot claim

V64 is more evidence-honest, not a complete measurement of 5279 printed to
2383. Public documents still do not identify:

1. the six processed off-LAD neutral-wedge Status-A triplets;
2. stock/process-specific positive-film interimage coefficients;
3. an end-to-end 5279-to-2383 off-neutral colour transform under documented
   printer lights and ECP-2D processing; or
4. the period projector/lens/screen/flare or scanner spectral observer needed
   to select one unique delivered colour rendering.

The next scientifically separate question is the physical projection colour
authority versus the frozen scan-referenced monitor adapter. It must not be
folded into the V64 density correction because that would make the cause of any
colour change unknowable.

## Reproducible artifacts

- `src/v64_profile.py`
- `src/audit_v64_2383_density_shaper.py`
- `research_runs/v64_2383_density_shaper_audit.json`
- `src/build_v64_print_lut.py`
- `cache/print_2383_monitor_output_lut_193_v64.npy`

Audit JSON SHA-256:

```text
dd764f97b93e7da246f54aa0beab70642b574ba8c24ac79583245fc8f7e98794
```
