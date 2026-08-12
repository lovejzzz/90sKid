# V79 — projection grain-policy ownership

Date: 2026-08-11
Status: **research-only; no image profile changed**

## Decision

Retain V72's current managed projection for released images, but classify it
accurately: it is a historical defect-containment boundary, not a measured
property of 5279, 2383, a projector, or a scanner.

V79 tested the tempting alternative of restoring the projection colour texture
that V40 removed. It fails. On the same formed T020 negative, restoring only
V31's high-frequency projection opponent publication increases isolated dark
mean-relative opponent events above `0.08` from `1` to `215`. Restoring both
V24's local high-frequency opponent remainder and V31 publication raises the
count to `4,275`. The fully unmanaged mathematical endpoint produces
`402,394` such events.

The current filter is therefore suppressing a real failure in the present
underidentified model. Removing it would not reveal true 35 mm colour grain;
it would reveal the model's missing cross-record covariance.

At the same time, V79 explains why the current result can feel too coarse in
colour at 2K. On uniform log-exposure `-1`, exact 3×3 optical-style integration
retains only `46.48%` of luma-grain RMS but `96.15%` of opponent-grain RMS. At
log-exposure `0`, the figures are `43.40%` and `96.03%`. The display-space
opponent low-pass has moved most surviving colour variation below the 2K
aperture cutoff. It prevents electronic colour speckles, but it also causes
colour texture to survive reduction much more strongly than luma texture.

The next physically meaningful advance is therefore not a weaker blur. It is
to identify or bound the negative's missing cross-record spatial covariance
upstream, while preserving Kodak's measured marginal granularity.

## The two V40 boundaries that had been conflated

The current projection has two independent historical management stages:

| Stage | Current operation | Evidence status |
|---|---|---|
| local projection grain finish | Rec.709 luma/opponent decomposition; opponent Gaussian σ `0.62 px at 2K`; high-frequency retention `0`; opponent strength `0.66` | historical colour-impulse containment; not a Kodak coefficient |
| final projection publication | scan low-frequency OKLab a/b at σ `0.72 px at 2K`; projection high-frequency opponent retention `0`; exact projection Rec.709 luma | historical V31/V40 monitor policy; not pure 2383 projection |

The first stage changes the stochastic projection delta. The second stage also
changes the deterministic mean colour. It is consequently inaccurate to call
the complete operation merely "grain reduction."

The released projection still has distinct 2383 tone and luma structure, but
its published low-frequency colour is scan-referenced. This is one concrete
reason the projection and scan can appear more similar than their labels imply.

## Audit design

Every endpoint uses:

- the same V72 RAW decode and one identical formed 5279 negative;
- the same identity record-formation boundary;
- the same measured/inherited H-D, 48 µm RMS, MTF, dye spectra and DIR graph;
- the same archive-pointwise signed stochastic projection observer;
- the same 2383 mean spectral observer;
- an exactly identical scan branch;
- no codec.

Only the two projection colour-frequency boundaries are varied.

| Endpoint | local HF retention | local opponent strength | final publication | publication HF retention |
|---|---:|---:|---|---:|
| current V72 managed | 0 | 0.66 | scan-referenced | 0 |
| restore V31 publication only | 0 | 0.66 | scan-referenced | 1 |
| historical V24 + V31 | 0.36 | 0.66 | scan-referenced | 1 |
| direct managed projection | 0 | 0.66 | direct projection | — |
| direct unmanaged projection | 1 | 1 | direct projection | — |

The direct unmanaged result is an upper mathematical endpoint, not a claim of
physical truth.

## T020 native result

| Endpoint | opponent/luma grain RMS | isolated >0.08 events | opponent RMS vs current |
|---|---:|---:|---:|
| current V72 managed | 0.2227 | 1 | 1.000× |
| restore V31 publication only | 0.2393 | 215 | 1.074× |
| historical V24 + V31 | 0.3454 | 4,275 | 1.552× |
| direct managed projection | 0.2402 | 246 | 1.078× |
| direct unmanaged projection | 1.0615 | 402,394 | 4.817× |

The event count is measured after subtracting the same-path deterministic mean,
then removing the local 3×3 median component. It therefore does not confuse
natural coloured scene detail with stochastic grain, correcting the older
whole-image gate discussed in V77.

Restoring only V31 changes deterministic colour as well as stochastic texture:
T020 deterministic mean differs from current by linear-RGB MAE `0.001710` and
median OKLab Δ `0.004725`. Direct publication differs by linear-RGB MAE
`0.002217` and median OKLab Δ `0.006011`. These are not grain-only toggles.

## Exact 5.7K-to-2K integration

RMS retained after an exact non-overlapping 3×3 linear-light mean:

| Uniform field | Endpoint | luma retained | opponent retained |
|---|---|---:|---:|
| log E −1 | current V72 managed | 46.48% | 96.15% |
| log E −1 | restore V31 publication only | 46.48% | 91.28% |
| log E −1 | historical V24 + V31 | 46.48% | 69.26% |
| log E −1 | direct managed projection | 46.48% | 91.32% |
| log E −1 | direct unmanaged projection | 46.57% | 53.23% |
| log E 0 | current V72 managed | 43.40% | 96.03% |
| log E 0 | restore V31 publication only | 43.40% | 92.26% |
| log E 0 | historical V24 + V31 | 43.40% | 70.37% |
| log E 0 | direct managed projection | 43.40% | 91.21% |
| log E 0 | direct unmanaged projection | 43.44% | 48.92% |

The unmanaged endpoint has a more similar luma/opponent scale response because
both contain substantial high-frequency energy. It nevertheless fails by an
enormous amplitude and tail margin. A frequency ratio that looks more natural
does not rescue the wrong joint colour statistics.

On T020, the current native opponent/luma ratio rises from `0.2227` to `0.3688`
after 2K integration. The 2K picture is not inventing additional colour grain;
it is removing luma grain much faster than the deliberately low-frequency
opponent field.

## Corrected interpretation

The project's central statement remains valid:

> Grain is not an overlay. The stochastic density field participates in image
> formation.

V79 adds an equally important qualification:

> The colour of that field is a joint, spatial statistic. Three marginal RMS
> curves do not determine it, and a display-space opponent blur cannot become
> evidence for the negative's real layer covariance.

V70 already showed that V72's predecessor predicted only weak record
correlation and that Kodak's public 48 µm curves contain no off-diagonal
covariance or cross-power spectra. V72 correctly withdrew an unmeasured direct
record-mix operator, but the conservative identity endpoint makes no claim
that real 5279 layers are independent. V79 now shows the visible cost of that
unknown: the release pipeline must hide the resulting primary-colour tails
downstream.

This is also why merely reducing the strength of the current blur is the wrong
next move. A physically plausible common-mode covariance would reduce
opponent amplitude at formation while allowing its spectrum to pass through
the same optical apertures as luma. The current display filter instead reduces
high-frequency opponent energy selectively, concentrating the remainder at
coarser scales.

## Production consequence

- V72 pixels are unchanged.
- V24/V31 restoration is rejected.
- the direct unmanaged endpoint is rejected.
- the historical projection management is now emitted in engine provenance.
- future reviews must call this result a managed projection monitor delivery,
  not an unqualified direct 2383 projection measurement.
- future physical candidates must preserve every published marginal 48 µm RMS
  point and vary only the unmeasured joint covariance.

## Next measurement or bounded experiment

The decisive real measurement remains multiple uniform 5279 patches scanned
without grain reduction or sharpening, with repeated scanner passes. Required
observables are per-record auto-NPS, complex R-G/R-B/G-B cross-power spectra,
exposure dependence, and higher-order joint tails.

Before such material exists, a valid next audit may sweep positive-semidefinite
cross-record covariance endpoints while preserving the three measured marginal
RMS curves exactly. That sweep can quantify how much upstream common-mode
correlation would be required to remove the downstream safety filter. It must
remain an uncertainty analysis, not a new stock coefficient.

## Artifacts

- implementation: `src/audit_v79_projection_grain_policy_ownership.py`
- machine-readable audit:
  `research_runs/v79_projection_grain_policy_ownership_audit.json`
- runtime provenance contract: `emulsion5279/view_policy.py`
- implementation SHA-256:
  `16910e2348abb1f032bef6d7c83bb846eeeffa7e675764d5807ec0b9d47faa7f`
- audit SHA-256:
  `41c588d657ecb14af8cc24e8515a31f51818bc1aaec739f2dd1b0810cfe9e3c5`

## Primary-source boundary

V79 adds no new stock measurement. It relies on the source boundary already
audited in V70:

1. Eastman Kodak Company, *KODAK VISION 500T Color Negative Film 5279 / 7279*,
   H-1-5279t, March 2003: marginal H-D, MTF, spectral and 48 µm diffuse-RMS
   curves; no cross-record covariance or cross-NPS.
2. Eastman Kodak Company, [US 5,641,596, *Adjusting film grain properties in
   digital images*](https://patents.google.com/patent/US5641596): level,
   within-channel spatial correlation and interchannel correlation are
   separate measured statistics.
3. [EP 1,627,359 B1, *Method and apparatus for representing image granularity
   by one or more parameters*](https://patents.google.com/patent/EP1627359B1/en):
   a general colour-layer correlation framework, not a 5279 coefficient.
