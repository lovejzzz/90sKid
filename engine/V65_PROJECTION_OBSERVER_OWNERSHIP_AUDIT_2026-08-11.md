# V65: projection-observer ownership audit

Date: 2026-08-11
Status: research-only; no image-version promotion
Image authority after audit: V64 unchanged

## Result

V65 does not change a pixel. It identifies why the released projection and
scan observers look similar and tests two smaller optical assumptions before
deciding whether another image revision is justified.

The current projection delivery is intentionally hybrid:

```text
2383/xenon spectral model -> projection lightness and structure
period scan observer      -> low-frequency OKLab a/b
```

V40 and later set the final projection high-frequency opponent retention to
zero. The delivered projection therefore does not claim that a physical 2383
projection naturally has the scan's hue/chroma. It uses the scan as a safety
boundary because public 5279/2383 material does not identify a complete
off-neutral theatre transform.

## Source re-read

Kodak's public 2383 curves constrain processed-film response, granularity, MTF
and peak-normalized dye spectra. They do not measure one projector's complete
viewing chain.

The optical chain required by published analytical models is:

```text
xenon lamp x heat-glass transmission x lens/port transmission
x print transmittance x screen reflectance + spatial/ambient flare
```

Glenn Berggren's studio/lab measurements also show that real xenon screen
illumination varies and cannot be specified by colour temperature alone.
FilmLight reports that the Callier effect in colour print film is subtle and
uses manufacturer/stock-family scatter calibrations rather than one universal
coefficient.

Sources:

- Berggren, [The Color of Light on the Screen—New Measurements at Studios and Laboratories](https://journal.smpte.org/periodicals/SMPTE%20Journal/106/3/7/)
- FilmLight, [Setting a Truelight Profile](https://www.filmlight.ltd.uk/pdf/whitepapers/FL-TL-TN-0416-SettingTLProfile.pdf)
- [EP1987665A1, analytical projector model](https://patents.google.com/patent/EP1987665A1/en)
- Trumpy and Gschwind, [Conflicting Colors: Film Scanning versus Film Projection](https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/25/1/art00031)

The Trumpy/Gschwind experiment concerns strongly scattering silver/toned
historical materials and cannot be transferred quantitatively to modern
dye-only 2383. It is useful here only for the general distinction between
directed projection and diffuse scanning. Its own text says the Callier factor
of modern low-scattering dye film is close to one.

## Observer-ownership magnitude

T020 frame 0 was decoded once at `1440 x 1080`, converted to one shared
deterministic V64 5279 record-density image, and sent through each observer
variant. This removes stochastic grain and RAW differences from the test.

| comparison | linear RGB MAE | P95 abs | P99 abs | OKLab P95 | changed 12-bit components |
|---|---:|---:|---:|---:|---:|
| physical spectral vs delivered scan-referenced projection | 0.0128051 | 0.0645551 | 0.1333862 | 0.0952741 | 93.9985% |
| internal scan-reference match vs final publication adapter | 0.0021026 | 0.0076569 | 0.0201883 | 0.0145267 | 90.4632% |
| scan branch across variants | 0 | 0 | 0 | 0 | 0% |

The first row is the dominant unresolved interval. It is far larger than the
Callier or flare assumptions below. It also explains why projection and scan
look similar: the similarity is an explicit publication policy, not a measured
property of the two optical paths.

The second row is numerically widespread because the final adapter replaces
each a/b value with a spatially low-passed scan field while retaining projection
lightness. Its magnitude is much smaller than the physical-versus-scan colour
interval.

## Callier ablation

V64 uses a small generic density gain of `0.012 / 0.010 / 0.014` for its
directed-light print prior. No public 2383 Q-versus-density/spectrum measurement
identifies those exact values.

| comparison after setting Callier gain to zero | linear RGB MAE | P95 abs | OKLab P95 | changed 12-bit components |
|---|---:|---:|---:|---:|
| physical spectral experiment | 0.00013549 | 0.00056813 | 0.00128059 | 36.5942% |
| delivered scan-referenced projection | 0.000000934 | 0.000002742 | 0.000001313 | 0.3799% |

The physical branch records the expected subtle effect. At the accepted
delivery boundary, it is nearly extinguished. Removing it would substitute an
unmeasured zero for an unmeasured but literature-consistent small prior, with
no material improvement to the delivered image. V65 therefore retains the
existing value and labels it as uncertainty rather than measurement.

## Flare reachability

The source contains a `1%` typical cinema-flare constant. Both active monitor
colour-authority paths currently take their projected light from the no-flare
neutral-view branch; the flare-bearing H-61 calibration branch is skipped when
physical hue/saturation authority is zero and is later bypassed by the V56
physical experiment.

Setting the constant to zero changes every audited physical pixel by exactly
`0.0`. It cannot explain the current black level, contrast or projection/scan
difference. A future spatial projector/lens/port/room flare model must be a new
measured observer, not an adjustment of this dormant scalar.

## Decision

No V65 image profile is created.

1. V64 remains the latest evidence-corrected image model.
2. The Callier prior remains small, explicit and underidentified.
3. The dormant scalar flare is documented but not removed merely for code
   tidiness; it is still used by historical looks and profiles.
4. The next image-changing projection version requires a controlled target
   measured both through the scan path and as reflected screen light under a
   documented lamp/filter/lens/screen setup.

Until then, the scientifically accurate labels are:

- **scan**: a period-scan-style display observer;
- **projection delivery**: 2383-derived lightness/structure with provisional
  scan-referenced low-frequency colour; and
- **physical spectral experiment**: an uncertainty endpoint, not a calibrated
  theatre match.

## Reproducible artifacts

- `src/audit_v65_projection_observer_ownership.py`
- `research_runs/v65_projection_observer_ownership_audit.json`

Audit JSON SHA-256:

```text
e6995caa7967765fd8d302dc23c482696dbde03ad059bdaecb756cd03d3dbe74
```
