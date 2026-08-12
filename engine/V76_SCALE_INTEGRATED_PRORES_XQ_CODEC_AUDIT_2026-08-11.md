# V76 scale-integrated ProRes XQ codec audit — 2026-08-11

## Decision

V76 changes only the future delivery encoder budget. It does not change the
V72 image profile, 5279 negative, grain realization, projection/scan observer,
viewing aperture, transfer function or colour metadata.

The current FFmpeg `prores_ks` XQ encoder is retained, but every explicit-engine
XQ writer now requests its documented maximum `8192 bits/MB`. This is the most
accurate practical QuickTime-compatible result in the controlled comparison:
it greatly reduces decoded colour error and restores high-pass energy without
the small luma/opponent overshoot produced by Apple VideoToolbox XQ.

No existing V72 output has been silently replaced. The change applies when a
new master, native sRGB companion or scale-integrated review is rendered.

## Why this audit followed V75

V75 independently proved that 5760→1920 `INTER_AREA` equals an explicit 3×3
linear-light mean. It also found that the completed 1920 ProRes XQ review
retained only about `85–95%` of the exact integrated high-pass structure.

That result could have come from the integration, transfer, RGB/YUV conversion
or codec budget. V76 freezes one exact integrated RGB16 sRGB frame and changes
only the final encoding path.

The existing V72 review and a newly encoded default `prores_ks` file produce
the same metrics to numerical precision. This reproduces the issue and confirms
that V75 did not accidentally compare different float images.

## Controlled candidates

Each projection and scan candidate receives identical 1920×1440 RGB16 input:

1. exact 3×3 integration of the decoded native BT.1886 master in linear light;
2. sRGB encode;
3. quantize once to RGB16;
4. encode with one candidate;
5. decode to RGB16 and compare in both sRGB code and linear light.

Candidates:

- current/default `prores_ks`, profile XQ;
- `prores_ks` XQ with `bits_per_mb=8192`;
- Apple `prores_videotoolbox`, profile XQ;
- FFV1 RGB16 lossless reference.

All ProRes candidates are finalized with the existing V39–V44 1-13-1 MOV colour
contract after encoding. Metadata remuxing does not change picture samples.

## Projection result

| Encoder | Linear RGB MAE | P95 absolute | Luma retention | Opponent retention | One-frame bytes |
|---|---:|---:|---:|---:|---:|
| existing V72 review | 0.0010144 | 0.0038881 | 94.82% | 89.90% | 2,910,788 |
| `prores_ks` default XQ | 0.0010144 | 0.0038880 | 94.82% | 89.90% | 2,885,577 |
| `prores_ks` XQ / 8192 | **0.0003595** | **0.0014259** | **98.60%** | **96.77%** | 5,154,487 |
| VideoToolbox XQ | 0.0009077 | 0.0035557 | 100.11% | 103.46% | 2,730,294 |
| FFV1 RGB16 | 0 | 0 | 100% | 100% | 12,183,429 |

The maximum-budget `prores_ks` result reduces mean linear error by `64.6%`
relative to default and recovers most of the suppressed structure. VideoToolbox
has slightly lower mean error than default but raises opponent high-pass RMS by
`3.46%`; it is not the most neutral grain carrier.

## Scan result

| Encoder | Linear RGB MAE | P95 absolute | Luma retention | Opponent retention | One-frame bytes |
|---|---:|---:|---:|---:|---:|
| existing V72 review | 0.0014036 | 0.0049029 | 92.51% | 85.14% | 2,913,985 |
| `prores_ks` default XQ | 0.0014036 | 0.0049030 | 92.51% | 85.14% | 2,888,766 |
| `prores_ks` XQ / 8192 | **0.0003839** | **0.0014242** | **98.30%** | **96.38%** | 6,143,199 |
| VideoToolbox XQ | 0.0013622 | 0.0050726 | 100.96% | 104.19% | 2,743,590 |
| FFV1 RGB16 | 0 | 0 | 100% | 100% | 12,886,797 |

Here the maximum budget reduces mean linear error by `72.6%` and P95 error by
`70.9%`. VideoToolbox again overshoots both high-pass measures and has a worse
P95 error than default despite a slightly lower mean.

## Why not FFV1 for the normal viewing file

FFV1 proves the reference and audit are code-exact: RGB16 round-trips with zero
difference. It is valuable for archival interchange and conformance, but it is
about two to 2.5 times the size of maximum-budget XQ in this single-frame test
and does not provide the same ordinary QuickTime viewing contract.

The project can add an optional lossless research authority later. It should
not replace the native 12-bit ProRes master or the convenient review by default.

## Implementation

`emulsion5279.io._xq_command` now promotes profile 5 and inserts:

```text
-bits_per_mb 8192
```

The shared command is intentionally used by the native master writer, the
master-derived native sRGB companion and the scale-integrated review builder.
This avoids a hidden quality hierarchy in which one delivery branch receives a
different compression budget.

A regression test asserts both profile XQ and the maximum macroblock budget.
The complete explicit-engine suite passes: `50/50` tests in `276.824 s`.

## Accuracy boundary

This is a delivery-accuracy correction, not new 5279 evidence. It cannot
identify the native Wiener spectrum, layer populations or colour covariance.
It prevents the codec from obscuring those questions by as much as the previous
default budget did.

The high-pass ratios are diagnostic summaries, not a claim that every spatial
frequency is equally preserved. A future audit should store radial luma and
opponent transfer/error spectra, then confirm the new budget over a multi-frame
native release. Because ProRes is an intra-frame family, the single-frame result
does isolate spatial coding, but multiple frames remain necessary for release
runtime, size and content-range validation.

## Reproducible artifacts

- audit code: `src/audit_v76_review_codec_ownership.py`
- machine-readable result:
  `research_runs/v76_review_codec_ownership_audit.json`
- delivery implementation: `emulsion5279/io.py`
- regression: `emulsion5279/test_pipeline.py`
- image profile: unchanged V72

## Primary source

1. Apple, [*About Apple ProRes*](https://support.apple.com/en-ca/102207), on the ProRes family and its “virtually lossless” exchange role.
