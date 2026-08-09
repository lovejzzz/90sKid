# V42 engine recovery and research conformance · 2026-08-09

## Why this is V42

The recovered package was initially called “V2” to mean a second-generation
software boundary. That name conflicted with the image-research history, which
already reached V41. The engine is therefore V42.

V42 is not a claim that a new Kodak spectral curve, coating formula, DIR
coefficient, scanner response or 5279 grain NPS has been measured. It freezes
V41's accepted image model and advances the project in three falsifiable ways:

1. the latest accepted research conclusions are executable runtime gates;
2. the validated Production execution graph is the default rather than an
   implicit command-line convention;
3. every viewing deliverable derives from one encoded professional master.

## Recovery provenance

The authored V41 engine was reconstructed from successful Codex `apply_patch`
audit events after the local `experiments/emulsion_reconstruction` directory
disappeared. This is a real data-loss incident, not a euphemism for refactoring.
It was not a rewrite from website parameters: 895 recorded file operations
recovered 199 source, profile, test and research files. Generated video was
excluded.

### Incident investigation

The evidence supports a precise but limited conclusion:

- the former experiment path is absent;
- the public repository's history through V41 contained the website and release
  media record, but no engine source—the engine first enters Git in recovery
  commit `9f1d1dd`;
- the former engine therefore had one local, unversioned source-of-truth;
- the available Codex command histories contain no command deleting that
  directory, and the Git reflog begins with the new clone on 2026-08-08;
- there is no evidence that the Python crash, macOS watchdog panic, Claude, or a
  specific cleanup command caused the disappearance.

The deletion trigger is consequently **unknown**. The established root cause of
the loss being dangerous is not unknown: important source lived outside version
control, while generated outputs and authored code shared an experimental
workspace boundary. Attribution without a filesystem event log would be false.

### Prevention now enforced

1. All recovered engine source, profiles, tests and research records are tracked
   in the same Git repository as the site and pushed to the remote; generated
   ProRes/RAW/output media remain deliberately excluded.
2. `engine/SOURCE_MANIFEST.sha256` inventories and hashes the protected authored
   files. GitHub Actions rejects a deletion, unrecorded source file or checksum
   drift until the manifest is intentionally regenerated and reviewed.
3. Required generated runtime data have versioned builders and pinned expected
   hashes. A clean checkout recreates the 193³ 2383 lattice with
   `python3 engine/bootstrap.py` and refuses a mismatched result.
4. A release is not considered a baseline until source, research note, tests and
   manifest are committed and pushed. Large rendered video is never the only
   record of an algorithm.
5. Temporary experiments belong under ignored `work/` or `outputs/`; canonical
   algorithms and conclusions belong under tracked `engine/src/` and `engine/`.

Independent assets were then rebuilt or verified:

- Panasonic V-709 diagnostic LUT SHA-256:
  `f99223675b29933952da2153bdb3137dd749d12964d0753db85e47576ca4578d`;
- analytical 193³ 5279-density → 2383 monitor lattice SHA-256:
  `5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c`;
- T003 DKC-Pro frame-160 input/colour audit regenerated from GH7 ProRes RAW.

## What the Archive identity test proves

The recovered historical V41 Archive/CPU entry and the first explicit-stage
entry produced six byte-identical T003 frame-160 artifacts. This proves that the
refactor did not alter the Archive equations or delivery samples. It does not
claim that NumPy's random realization is the same realization as the released
Metal/Philox Production sampler.

| Archive artifact | SHA-256 |
| --- | --- |
| projection BT.1886 ProRes 4444 XQ | `01e42d2f74e6d3990997934cc14e24f6156b097c4b41457d26ceb6a1c694b03f` |
| projection sRGB ProRes 4444 XQ | `11458d0d7c2c484a7309e445ad5b49c2af53d3a2a49c055d166bcb6cf05b6722` |
| projection sRGB JPEG | `667d04706a2f787a3357513bb5534c7ede1a3fb67615e45d887a082375fef338` |
| scan BT.1886 ProRes 4444 XQ | `ed0842dfbc3c413127931f98ff875e2cb03c5e7b6b30f7ec5f0eed870465bf57` |
| scan sRGB ProRes 4444 XQ | `d1cbc68665f5a0ef0aadad758604f9afe8c86eed8fc4f046600d0b316d9a183c` |
| scan sRGB JPEG | `c1f4369cdaa24b7fae3472160834ec5f4cfd1853e1d0a917f2e5f57b90b08629` |

## Research-to-code contract

V42 refuses baseline rendering if any accepted invariant below drifts:

| Research result | Executable V42 ownership |
| --- | --- |
| V37 independent sites with a stable 30° balanced operator | stable phase mode, 0.38-native-pixel radius and π/6 offset are asserted |
| V40 published granularity belongs to processed 5279 density | post-coupling residual calibration is asserted |
| V40 isolated primary-colour failure is withdrawn | observer grain management is active; duplicate high-frequency opponent reinjection is zero |
| unmeasured stochastic 2383 populations are withheld | print stochastic domain must be `none` |
| V41 saturated signed basis is physical only when all record exposures remain non-negative | record-positive signed boundary is asserted |
| T003/T005 only authorize a conservative chroma residual | D65 luminance/neutral-preserving matrix and 0.125 strength are asserted |
| unidentified Resolve D60 calibration is not Kodak evidence | strength must remain exactly zero |
| baseline is not a grade | +0.45 stop, grain scale 1, oversample 1 and salt 0 are frozen unless an output is explicitly marked experimental |

The default sampler is the V35–V41 validated Philox-u32 Bernoulli Metal graph.
It gives all 45 record/population/size identities a unique absolute-frame seed.
Archive CPU and unaccelerated NumPy remain reference modes; they implement the
same research model but are not labeled Production execution.

## Single picture authority

V42 writes only the two 12-bit BT.1886 observer masters during image formation.
After those actual ProRes 4444 XQ files close, it decodes them, reconstructs
reference light, applies the sRGB transfer and writes the QuickTime companions.
The review JPEG is captured from that master-derived path. This implements the
V39–V41 conclusion that stills, QuickTime and web media must never become an
independent lossy realization. V29's delivery boundary is also restored at
finalization: full renders stream-copy source PCM/timecode; partial renders use
sample-accurate 24-bit PCM trim and source-frame-offset timecode.

## Native validation

T003 frame 160 completed through the V42 default Production graph at
5760×4320. Both branches produced 12-bit ProRes 4444 XQ masters, master-derived
sRGB companions and stills. Runtime provenance reported every research gate
true, the Philox Production sampler active and the delivery authority explicit.

- image-model conformance: pass;
- Production execution conformance: pass;
- wall time including master-derived delivery and source-stream finalization:
  63.87 seconds;
- Production identity audit: 45/45 calls, zero duplicate identities;
- output audit: four 5760×4320 12-bit ProRes 4444 XQ files, 24-bit PCM and
  timecode `12:32:56:08`; BT.1886 masters signal 1-1-1 and sRGB companions
  signal 1-13-1.

Unit gates cover research constants, experimental-override labeling, extended
linear highlights, transfer equivalence, master-derived delivery metadata and
master/companion light agreement. The recovered physics/colour suites remain
separate so a V42 API change cannot silently rewrite older evidence.

## Deliberately unresolved

V42 does not invent missing measurements. Exact 5279 NPS, proprietary speed-layer
coating geometry, stock-specific DIR transport, 2383 grain covariance, Spirit
spectral sensitivity and controlled D65/tungsten GH7 characterization remain
open evidence boundaries. Future changes need matched measurements and must not
enter V42 as aesthetic tuning.
