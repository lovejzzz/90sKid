# Engine recovery and V2 validation · 2026-08-08

## Outcome

The complete authored V41 engine was reconstructed from successful Codex
`apply_patch` audit events after the local experiment directory disappeared.
This was not a rewrite from website parameters: 895 recorded file operations
recovered 199 source, profile, test and research files.  Generated video was
deliberately excluded.

V41 was then re-established from its independent boundaries:

- Panasonic's official V-709 diagnostic LUT was downloaded again and matched
  the locked SHA-256 `f99223675b29933952da2153bdb3137dd749d12964d0753db85e47576ca4578d`.
- The T003 DGK DKC-Pro audit was regenerated from GH7 ProRes RAW frame 160.
- The analytical 193³ 5279-density → 2383 monitor lattice was rebuilt from the
  equations and matched SHA-256
  `5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c`.
- All eight recovered physics/colour tests and four new engine-boundary tests
  passed.

## Second-generation boundary

`engine/emulsion5279` is the new public API.  It makes the graph explicit:

1. AVFoundation extended-linear BT.2020/D65 ProRes RAW input;
2. one V41 5279 exposure and one shared stochastic developed negative;
3. 2383 monitor projection and Period-2K/Blu-ray scan observers;
4. one display-linear Rec.709 result per observer;
5. BT.1886/gamma-2.4 professional masters and sRGB QuickTime companions.

The first refactor intentionally retains the validated V41 equations in the
archival backend.  It removes the renderer's profile monkey-patching and gives
future OFX/Metal work stable typed stage contracts.

## Pixel identity gate

GH7 T003 frame 160 was rendered at 5760 × 4320 through the old V41 entry point
and the V2 entry point.  All six review/delivery artifacts were byte-identical:

| Artifact | SHA-256 |
| --- | --- |
| projection BT.1886 ProRes 4444 XQ | `01e42d2f74e6d3990997934cc14e24f6156b097c4b41457d26ceb6a1c694b03f` |
| projection sRGB ProRes 4444 XQ | `11458d0d7c2c484a7309e445ad5b49c2af53d3a2a49c055d166bcb6cf05b6722` |
| projection sRGB JPEG | `667d04706a2f787a3357513bb5534c7ede1a3fb67615e45d887a082375fef338` |
| scan BT.1886 ProRes 4444 XQ | `ed0842dfbc3c413127931f98ff875e2cb03c5e7b6b30f7ec5f0eed870465bf57` |
| scan sRGB ProRes 4444 XQ | `d1cbc68665f5a0ef0aadad758604f9afe8c86eed8fc4f046600d0b316d9a183c` |
| scan sRGB JPEG | `c1f4369cdaa24b7fae3472160834ec5f4cfd1853e1d0a917f2e5f57b90b08629` |

No output video is stored in Git; the hashes make the local gate repeatable.

## First proven simplification

V30–V41 set the third-party Resolve D60 colour-calibration strength to exactly
zero, but the old function still sampled its full lattice and calculated a
neutral guard before multiplying the result by zero.  The new guard skips only
those mathematically dead operations and retains the active OKLab/gamut
boundary.  Rebuilding the 193³ observer cache produced the identical locked
hash, and the full native-frame ProRes/JPEG identity gate also passed.

The one-frame two-master reference path measured about 67 seconds wall time on
this machine; the explicit V2 path measured about 62 seconds in the same
configuration.  Single-frame timing includes process warm-up and is not yet a
throughput claim.  Observer formation remains the dominant stage and is the
next optimization target.
