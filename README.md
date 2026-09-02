# 5279 Emulsion Project

A bilingual, evidence-led reconstruction of Kodak VISION 500T 5279 image formation from Panasonic GH7 ProRes RAW. The project models finite silver-halide events, dye clouds, speed layers, DIR interimage effects, the coloured negative mask, Kodak 2383 print formation, and a period 2K scan.

中文网站记录从 GH7 ProRes RAW 到 5279 负片、2383 放映与时期 2K 扫描的研究、算法、错误复盘和逐版画面对照。艺术调色始终留在 baseline 之外。

## Live site

[lovejzzz.github.io/90sKid](https://lovejzzz.github.io/90sKid/)

## Current visual release: V46 · certified spectral inverse

- Holds the complete finite-site stochastic state at Kodak's measured granularity endpoints, removing the rare divergent dye-density tail
- Replaces the clipped Status-M inverse with an exact nonnegative active-set/KKT solution
- Uses a 129³ base atlas plus 25,333 real-footage-demanded 5³ exact microbricks
- Passes the real-frame printer-density gate at a worst measured error of 0.0005094 D, below the 0.001 D release limit
- Shares one formed-negative printer-density observation between projection and scan, removing duplicate work without changing branch math
- Keeps cross-record covariance unselected because the public 48 µm curves constrain marginals, not the missing cross-spectrum
- Delivers T020, T032 and T007 as one-second native 5760×4320, 12-bit ProRes 4444 projection and scan masters

The full release boundary and the distinction between public V46 and legacy
internal V46–V86 laboratory-note IDs are recorded in
[`engine/V46_PUBLIC_CERTIFIED_SPECTRAL_INVERSE_RELEASE_2026-08-11.md`](engine/V46_PUBLIC_CERTIFIED_SPECTRAL_INVERSE_RELEASE_2026-08-11.md).

## Consolidated research evidence inherited by V46

- V86 proves that common record events trade opponent noise for roughly 1.48–1.67x luma grain, then locates a separate shared shadow error: the 29³ joint Status-M spectral LUT misses direct integration by up to 0.013987 D at −3 logE, with the largest red-record error
- V85 re-renders and vector-extracts the March 2003 source: R/G/B paths, the 0–4 to −4–0 exposure translation and the Status-M domain all pass; the large blue marginal is real public evidence, while cross-record covariance/cross-spectra remain unpublished
- V84 renders the legal shared-event family as a paired real-RAW crop through both observers and rejects it as a free colour-noise cure: alpha 0→1 lowers opponent RMS but raises luminance grain 43–54% and total RGB grain 23–26%
- Across 7,500 record-population/exposure parameter sets, 3,462 independent pair-alpha combinations are jointly impossible; 1,484 remain impossible even though their 3×3 correlation matrix is positive-semidefinite
- No RGB population triplet can support all three pair correlations at ρ=0.99 simultaneously, although V81 found 13 individually feasible pair cases
- The single common-alpha V81 family passes exact eight-cell nonnegativity and marginal closure everywhere tested, but remains an unmeasured uncertainty coordinate rather than a promoted image parameter
- V81 derives the exact Bernoulli/Fréchet limit for any future shared activation model: ρ=0.99 is feasible in only 13 of 180 tested record/population/exposure cases
- A shared-latent-event mixture can preserve every Bernoulli marginal and finite nonnegative count exactly while making achieved correlation exposure dependent; it is a valid uncertainty architecture, not a measured 5279 coefficient
- No sampler or image is promoted until site topology, 48 µm closure, native tails, deterministic CPU/Metal identity and both observers can all pass
- V80 proves the missing layer statistic cannot be repaired with a post-formation 3×3 covariance matrix, even while closing every marginal 48 µm RMS value to within 5.28e-10 relative
- At ρ=0.99 T020 opponent/luma approaches the managed result, but luma rises 1.63×, opponent remains 1.77×, 10,446 severe colour events remain, and finite density falls as low as about −0.60 D
- A fixed correlation also fails across exposure and materially changes the scan; the next defensible uncertainty model must share bounded finite events during population activation/development rather than mix completed density
- V79 separates the two V40 projection colour-frequency boundaries and proves they are historical defect containment, not measured 5279/2383 coefficients
- Restoring only V31 projection opponent publication raises T020 isolated mean-relative >0.08 colour events from 1 to 215; restoring V24+V31 raises them to 4,275, and the unmanaged endpoint to 402,394
- The current safety boundary remains necessary, but exact 5.7K→2K integration retains only 43–46% of luma RMS versus about 96% of its low-passed opponent RMS, quantitatively explaining coarser colour texture
- V72 pixels remain unchanged; future physical progress must identify upstream cross-record spatial covariance instead of tuning a display-space blur by eye
- V78 validates V76 on a complete 1920×1440 uniform formed-minus-mean NPS: maximum-budget `prores_ks` cuts default-XQ band error from 3.39% to 1.79% and total-RMS error from 9.95% to 5.18%
- VideoToolbox preserves uniform NPS more closely but has about three times the T020 RGB/OKLab error and slight high-pass overshoot; maximum-budget `prores_ks` remains the normal QuickTime delivery
- FFV1 RGB16 is effectively lossless and remains a separate research control rather than silently changing the player/workflow contract
- V77 re-tests V40's archive pointwise projection-grain observer in the corrected V72 spectral coordinates and does not promote the formed-density candidate
- The direct candidate leaves deterministic projection and scan unchanged but raises paired mean-relative isolated >0.06 opponent events from 70 to 137; both have zero events above 0.08 after V76 XQ
- V77 also proves the old whole-image colour-tail gate confounds deterministic scene detail with grain; future stochastic gates must subtract the same-path deterministic mean
- At 1920 viewing scale projection luma grain retains only about 43–47% of native RMS while its already-low-passed opponent component retains about 97%, doubling the opponent/luma ratio and helping explain fine sharpness with coarser colour texture
- V76 isolates the final review codec and retains `prores_ks` XQ with its explicit maximum 8192 bits/MB budget
- Versus the previous default, mean linear error falls about 65% in projection and 73% in scan; high-pass luma/opponent retention improves to roughly 96–99%
- Apple VideoToolbox XQ slightly overshoots high-pass luma/opponent energy, while RGB16 FFV1 is exactly lossless but is not the normal QuickTime viewing contract
- The delivery change applies to future renders only; V72 film pixels and all film-formation parameters remain unchanged
- V75 verifies the actual V72 delivery path: 5760→1920 `INTER_AREA` is an exact 3×3 linear-light mean to float32 precision
- A pure-grain native strip retains 1.88–2.00× too much RMS under a sharp Lanczos diagnostic versus correct area integration, enough to make a fine native field read much coarser
- On real T020 frames Lanczos raises high-pass luma by 1.76× in projection and 1.16× in scan; an unknown QuickTime/window resize is therefore not an emulsion measurement
- The encoded 1920 ProRes XQ review retains about 85–95% of exact integrated high-pass structure; it owns 2K viewing geometry, not mathematically lossless NPS amplitude
- V74 proves that passing Kodak's 48 µm RMS does not identify the native 5.7K texture: the active model carries about 5.1–7.0× more single-pixel density RMS than survives the measurement aperture
- A new 5760-wide stochastic strip validates both the published RMS and the analytic native/48 µm ratio within 1.56%; the former 1920-wide strip remains an amplitude gate, not a native-NPS gate
- Dark exposure is fast-population dominated and spatially coarser; higher exposure transfers variance to the finer slow population, but the exact shares remain a patent-bounded prior rather than measured 5279 layers
- The current morphology still inherits V24's perceptually selected fine35 candidate, which moves about 19–23% more fixed aperture variance into native frequencies than V23; neither candidate is a measured 5279 Wiener spectrum
- Blue-record finite-site variance requires roughly 3.1–11.8× normalization across the published range, proving that the microscopic population parameters do not independently predict Kodak's marginal RMS
- V73 changes no pixels: it expands the complete active DIR prior and finds all 54 possible cross-record fast/medium/slow transport edges are nonzero, although period Kodak layer recipes are selective and asymmetric
- The active DIR effect is restrained: developed off-record response peaks at about 0.000417 D/logE and a same-RAW zero-DIR ablation has projection OKLab P95 about 0.0010
- DIR remains because mobile inhibitor transport owns a real, distinct development mechanism; its exact dense tensor and diffusion scales are now explicitly unmeasured 5279 priors pending separation/white-light wedge data
- V72 withdraws the unidentified direct speed-population record-mix matrix to exact identity while retaining sensitivity overlap, DIR, net dye/mask spectra and spectral printer integration
- The 48 µm marginal-RMS gate, T020 native tail gate, paired T003 chart/tail gates and all 57 engine regressions pass
- Chart colours recover about 1.7–1.8% median chroma with less than 0.72° maximum hue movement; neutral, black, gamma, exposure and highlight policy are not fitted or changed
- Identity is the current minimum-assumption baseline, not a claim that real 5279 records have zero covariance or no asymmetric off-hue coupler contributions
- A new state-isolation gate proves V72 cannot leak its identity map into V66 or any older reproducible profile
- V71 separates spectral sensitivity overlap, direct speed-population record mixing, DIR inhibition, net dye/mask spectra and printer integration
- The old direct record-mix prior owns roughly 1–2.5% off-record deterministic response and lowers separation/neutral gamma ratios, while current DIR is much smaller and acts in the opposite direction
- Net dye spectra and printer integration retain substantial physical cross-channel response even with identity record mapping
- V70 proves that Kodak's three published 48 µm RMS curves constrain marginal record amplitude, not the joint colour of 5279 grain
- The current formed-negative model predicts only weak cross-record correlation; almost all of it comes from the explicitly unmeasured speed-population record-mix prior
- Paired ablation shows the current stochastic DIR term contributes almost none of the same-position colour covariance, although deterministic interimage chemistry remains a separate colour-separation mechanism
- Scanner/view nonlinearities change covariance further, while the historical managed Blu-ray branch is the dominant monochromatic-grain treatment
- V70 is research-only: no covariance prior or image profile is promoted without controlled 5279 uniform-field scans
- V69 proves the historical Blu-ray scan is not a pure DPX view: it also consumes a hidden deterministic mean and removes about 61% of native high-frequency opponent RMS on T020
- Two named single-input policies now consume only the printing-density DPX: an open monitor and a pointwise Blu-ray finish
- The legacy managed result remains bit-exact and explicitly classified as a historical colour-grain finish, not a property of 5279 or Cineon
- V68 adds an independent, code-exact 10-bit RGB printing-density DPX delivery from the same formed negative and Spirit aperture as the scan observer
- V68 does not change V66 image pixels: both decoded 12-bit projection and scan masters remain bit-for-bit identical
- DPX is exchange data, not a display-ready Rec.709 image; named viewing and Blu-ray finish policies remain downstream
- V68 also fixes a process-history fault where V59+ print D-min/scanner anchors could leak into an older profile after a downgrade
- V66 corrects the scan/Cineon calibration target from a partial independent-Status-M approximation to the active 5279→2383 printing-density coordinate
- This is a data-coordinate correction, not a white-balance, saturation fit, creative grade or claim that proprietary Spirit spectra are known
- V64 withdraws a continuous 2383 density-neutral shaper that rewrote Kodak's separated H-D curves by up to 0.114 D without measured off-LAD wedge data
- The published red/green/blue exposure responses remain nonlinearly inverted to analytical C/M/Y dye amounts before spectral recombination
- V63's actual 5279-to-2383 projection-neutral trajectory remains active
- V62's identity endpoint for unidentified positive-film interimage effects remains active
- Off-neutral projection colour stays on the frozen scan-referenced boundary pending controlled 5279-to-2383 measurements
- V45's official CIE 1931 2° 1 nm observer and all accepted V37–V63 grain, density, colour and delivery gates remain enforced
- Runtime gates enforce the accepted V37–V66 grain, density, colour, observer and delivery boundaries
- The validated Philox-u32 Bernoulli Metal graph is the Production default; Archive CPU remains reproducible
- Projection retains 2383 lightness/texture and the gated V31 normal-process low-frequency scan-chroma boundary
- One native 5760×4320 12-bit BT.1886 master is picture authority
- Display review decodes the master to linear light, performs pixel-area integration, then applies sRGB
- Review stills decode the same frame from the final encoded review movie
- Native-frame release gates reject sparse chroma impulses and metadata mismatches
- T003 DKC-Pro control documents what the outdoor chart does and does not identify
- Public deployments stream optimized comparison media from the GitHub Pages archive; full masters remain local

## Reconstruction engine

The recovered research engine, V24–V42 profiles, measurement scripts and the
new explicit-stage API live in [`engine/`](engine/). Full-resolution RAW and
rendered video remain local and are excluded from Git. The explicit API keeps one
shared stochastic negative and derives projection and scan observers plus two
colour-explicit delivery encodings from one encoded picture authority.

See [`engine/V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md`](engine/V42_ENGINE_RECOVERY_AND_CONFORMANCE_2026-08-09.md)
for the recovery provenance and research-to-code matrix, and
[`engine/V44_OBSERVER_INTEGRITY_AND_SCALE_HONEST_REVIEW_2026-08-10.md`](engine/V44_OBSERVER_INTEGRITY_AND_SCALE_HONEST_REVIEW_2026-08-10.md)
for the observer ablations, display-sampling equation and current limits.
V45's single-variable spectral revision and cache-integrity boundary are recorded
in [`engine/V45_OFFICIAL_CIE_1NM_OBSERVER_2026-08-10.md`](engine/V45_OFFICIAL_CIE_1NM_OBSERVER_2026-08-10.md).
The current scan-coordinate evidence boundary is recorded in
[`engine/V66_CINEON_PRINTING_DENSITY_COORDINATE_AUDIT_2026-08-11.md`](engine/V66_CINEON_PRINTING_DENSITY_COORDINATE_AUDIT_2026-08-11.md).
The following display-ownership audit intentionally leaves V66 pixels unchanged:
[`engine/V67_CINEON_DISPLAY_LAYER_OWNERSHIP_AUDIT_2026-08-11.md`](engine/V67_CINEON_DISPLAY_LAYER_OWNERSHIP_AUDIT_2026-08-11.md).
The implemented DPX exchange contract, native code-exact audit and profile-state
isolation fix are recorded in
[`engine/V68_CINEON_DPX_AND_PROFILE_ISOLATION_2026-08-11.md`](engine/V68_CINEON_DPX_AND_PROFILE_ISOLATION_2026-08-11.md).
The named DPX-only view policies and the hidden mean-relative colour-grain audit
are recorded in
[`engine/V69_NAMED_CINEON_VIEW_POLICY_AND_GRAIN_OWNERSHIP_2026-08-11.md`](engine/V69_NAMED_CINEON_VIEW_POLICY_AND_GRAIN_OWNERSHIP_2026-08-11.md).
The following cross-record covariance audit reconciles the earlier 48 µm,
multilayer, DIR and scan-delivery findings without changing image pixels:
[`engine/V70_5279_JOINT_COLOUR_COVARIANCE_AUDIT_2026-08-11.md`](engine/V70_5279_JOINT_COLOUR_COVARIANCE_AUDIT_2026-08-11.md).
The deterministic mechanism audit and identity-record-mix candidate boundary
are documented in
[`engine/V71_5279_RECORD_COUPLING_OWNERSHIP_AUDIT_2026-08-11.md`](engine/V71_5279_RECORD_COUPLING_OWNERSHIP_AUDIT_2026-08-11.md).
The accepted single-variable implementation, renewed period-layer evidence,
native/chart gates and remaining covariance boundary are documented in
[`engine/V72_5279_EVIDENCE_MINIMAL_RECORD_FORMATION_2026-08-11.md`](engine/V72_5279_EVIDENCE_MINIMAL_RECORD_FORMATION_2026-08-11.md).
The subsequent research-only audit exposes all 54 active population-domain DIR
transport edges, rechecks their separation-gamma and real-frame magnitude, and
records why no sparse or zero-DIR image change is yet justified:
[`engine/V73_5279_DIR_TOPOLOGY_IDENTIFIABILITY_AUDIT_2026-08-11.md`](engine/V73_5279_DIR_TOPOLOGY_IDENTIFIABILITY_AUDIT_2026-08-11.md).
The native-width population audit then separates published 48 µm amplitude from
the still-hypothetical 5.7K NPS, exposes the V24 visual morphology provenance,
and validates the analytic native high-frequency reservoir with a 5760-wide
stochastic strip:
[`engine/V74_5279_POPULATION_ACTIVATION_AND_NATIVE_NPS_BOUNDARY_2026-08-11.md`](engine/V74_5279_POPULATION_ACTIVATION_AND_NATIVE_NPS_BOUNDARY_2026-08-11.md).
The scale-integration audit then verifies the actual V72 ProRes files, separates
view aperture from sharp resampling and lossy delivery, and states which
QuickTime file owns which observation claim:
[`engine/V75_5279_SCALE_INTEGRATION_AND_QUICKTIME_VIEW_BOUNDARY_2026-08-11.md`](engine/V75_5279_SCALE_INTEGRATION_AND_QUICKTIME_VIEW_BOUNDARY_2026-08-11.md).
The following fixed-input codec audit selects maximum-budget `prores_ks` XQ
over default XQ, VideoToolbox XQ and the lossless research reference, without
changing the V72 image model:
[`engine/V76_SCALE_INTEGRATED_PRORES_XQ_CODEC_AUDIT_2026-08-11.md`](engine/V76_SCALE_INTEGRATED_PRORES_XQ_CODEC_AUDIT_2026-08-11.md).
The physical-frequency audit then reopens V40's projection-grain observer in
the corrected V72 spectral coordinates, replaces the confounded whole-image
tail diagnostic with a paired mean-relative measurement, and quantifies the
viewing-scale luma/opponent imbalance:
[`engine/V77_FREQUENCY_OWNERSHIP_AND_PROJECTION_GRAIN_OBSERVER_2026-08-11.md`](engine/V77_FREQUENCY_OWNERSHIP_AND_PROJECTION_GRAIN_OBSERVER_2026-08-11.md).
The full-frame uniform-NPS codec audit reconciles that result with V76's real
T020 picture metrics and retains maximum-budget `prores_ks` as the most accurate
ordinary ProRes compromise:
[`engine/V78_UNIFORM_GRAIN_CODEC_NPS_AUDIT_2026-08-11.md`](engine/V78_UNIFORM_GRAIN_CODEC_NPS_AUDIT_2026-08-11.md).
The following ownership audit separates local projection opponent filtering
from the scan-referenced publication adapter, rejects restoration endpoints
that reopen primary-colour tails, and records the current result as a managed
monitor policy rather than measured 5279/2383 physics:
[`engine/V79_PROJECTION_GRAIN_POLICY_OWNERSHIP_2026-08-11.md`](engine/V79_PROJECTION_GRAIN_POLICY_OWNERSHIP_2026-08-11.md).
The subsequent covariance-bound audit preserves every channel's original
48 µm RMS while sweeping positive-semidefinite frequency-band correlation. It
rejects post-formation density mixing and locates the remaining physical problem
in exposure/population-dependent shared finite events and higher-order tails:
[`engine/V80_5279_CROSS_RECORD_COVARIANCE_BOUNDS_2026-08-11.md`](engine/V80_5279_CROSS_RECORD_COVARIANCE_BOUNDS_2026-08-11.md).
The analytic follow-up derives the exact Bernoulli/Fréchet feasible set for a
bounded shared-event model, rejects arbitrary common correlation at activation,
and defines the pre-render contract for any future finite-site sampler:
[`engine/V81_SHARED_FINITE_EVENT_BERNOULLI_BOUNDS_2026-08-11.md`](engine/V81_SHARED_FINITE_EVENT_BERNOULLI_BOUNDS_2026-08-11.md).
The three-record follow-up reconstructs the complete eight-cell RGB Bernoulli
law, rejects independent pair-correlation controls, and validates only the
single-common-event family as a mathematical uncertainty architecture:
[`engine/V82_THREE_RECORD_BERNOULLI_COMPATIBILITY_2026-08-11.md`](engine/V82_THREE_RECORD_BERNOULLI_COMPATIBILITY_2026-08-11.md).
The next exact transfer audit reproduces V72's actual post-coupling residual
calibration, carries the valid common-event law through all five size classes
and stochastic DIR, and verifies the Fourier result with direct finite
multinomial/binomial samples. Marginal RMS closes at every tested endpoint, but
the same Kodak curves permit near-zero or roughly 0.7–0.95 record correlation:
[`engine/V83_SHARED_EVENT_DIR_RMS_CLOSURE_2026-08-11.md`](engine/V83_SHARED_EVENT_DIR_RMS_CLOSURE_2026-08-11.md).
The paired real-RAW follow-up then proves why marginal closure is insufficient:
shared sites redirect opponent power into luminance power, alter projection and
scan differently and survive exact 3×3 integration. No alpha is promoted; the
next audit returns to the official blue-record granularity curve and its
Status-M-to-visible-colour mapping:
[`engine/V84_SHARED_EVENT_VISUAL_UNCERTAINTY_2026-08-11.md`](engine/V84_SHARED_EVENT_VISUAL_UNCERTAINTY_2026-08-11.md).
The source-domain follow-up then re-renders the official PDF, reproduces the
three vector paths and all twelve Sigma-D ticks, verifies the exposure
translation and confirms ISO Status-M as the correct colour-negative
granularity coordinate. It changes no pixels and isolates the unpublished
joint covariance as the next boundary:
[`engine/V85_5279_GRANULARITY_MEASUREMENT_DOMAIN_2026-08-11.md`](engine/V85_5279_GRANULARITY_MEASUREMENT_DOMAIN_2026-08-11.md).
V86 then propagates every positive-semidefinite covariance allowed by those
marginals and directly cross-checks the runtime printer-density LUT against the
V61 joint spectral equations. It changes no pixels, but identifies a localized
toe error shared by scan and projection and sets a below-0.001 D V87 gate:
[`engine/V86_OBSERVER_COVARIANCE_AND_SHADOW_SPECTRAL_LUT_AUDIT_2026-08-11.md`](engine/V86_OBSERVER_COVARIANCE_AND_SHADOW_SPECTRAL_LUT_AUDIT_2026-08-11.md).

## 5279 Studio · the app

[`studio/`](studio/) is a local, CPU-only application built on the same physics:
input any video, expose it onto 5279, form the negative with finite
silver-halide sites and the V49 common-density boundary, then export the 2383
projection print, the Spirit/Cineon Blu-ray scan, or Cineon DPX exchange data.
Every parameter is adjustable; the defaults are the 5279 baseline. It replaces
the historical 29³/25³ spectral caches with the V87 dense lattices.

macOS, one command, then a double-click app in `~/Applications`:

```bash
curl -fsSL https://raw.githubusercontent.com/lovejzzz/90sKid/claude/film-texture-video-app-axqm4s/studio/mac/install.sh | bash
```

From a clone on any platform:

```bash
pip install -r studio/requirements.txt
python3 studio/app.py        # http://127.0.0.1:8765
```

See [`studio/README.md`](studio/README.md).

## Current research cycle: V87 · dense spectral lattice gate

- Reproduces V86's 29-cube toe error on Linux CPU: +0.0112 / +0.0077 / +0.0024 D at −2.98 logE, worst ±1 σ toe error 0.0171 D, mid-scale already 0.0004 D
- A power-2 129³ printer-density lattice closes the toe gate at 0.00079 D and the mid-scale gate at 0.00005 D on every physically reachable probe
- The residual 0.004 D lies only on unreachable microscopic triplets outside the nonnegative dye gamut, where the joint inverse has a kink; no trilinear lattice can represent it
- The 25³ 2383 projection lattice was also too coarse: 0.024 OKLab on the neutral axis; 129³ brings formed-frame error to p99 0.00015
- Measured display consequence of the runtime cube: an achromatic lift of the deepest toe (ΔL ≈ +0.011 at display Y 0.0009) with 0.0002–0.0012 OKLab of directionless chroma; V86's inferred green/cyan shadow cast is not supported
- Details: [`engine/V87_DENSE_SPECTRAL_LATTICE_GATE_2026-09-01.md`](engine/V87_DENSE_SPECTRAL_LATTICE_GATE_2026-09-01.md)

## Local development

Requires Node.js 22 or later.

```bash
npm ci
npm run dev
```

Validation commands:

```bash
npm test
npm run build:pages
```

`npm run build:pages` creates the static GitHub Pages site in `out/`. Pushing `main` runs the Pages deployment workflow automatically.

## Evidence boundary

Published 5279 material constrains neutral characteristic curves, MTF, spectral sensitivity, net dye density and 48 µm diffuse RMS granularity. It does not identify a unique frequency-resolved grain NPS, proprietary three-layer coating recipe, stock-specific DIR matrix, or Spirit scanner spectral calibration. Those quantities remain explicit model priors until physical measurements are available.
