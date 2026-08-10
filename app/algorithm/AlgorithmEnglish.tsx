const siteCode = `p = sigmoid((logE - speed_centre) / transition_width)
developed = binomial(finite_sites, p) / finite_sites
density_delta = optical_integrate(developed - p, dye_cloud_kernel)
# sample changes every frame; conditional mean does not drift`;

const dirCode = `release = blur(population_density, lateral_sigma) - population_density
transport = population_matrix @ release
population_density += receiver_gain * transport
# uniform exposure produces zero local correction`;

const scanCode = `T = 10 ** (-spectral_density)
sensor_2k = area_integrate(scanner_response * T, width=2048)
D = -log10(sensor_2k / clear_reference)
cineon = 95 + (D - Dmin) / 0.002`;

const neutralCode = `neutral_scale = render_scan(scene_linear=geomspace(1e-5, 10, 2049))
rgb_balance = fit_level_dependent_balance(neutral_scale)
corrected = rgb_balance(display_linear)
corrected *= rec709_y(display_linear) / rec709_y(corrected)
# black, gamma and per-pixel luminance remain unchanged`;

const productionCode = `# V35 Production: keep the complete uint32 random word
threshold = floor(float32(probability) * 2**32)
developed += philox_u32(counter(frame, record, population,
                                size_class, x, y, lane)) < threshold
# all 45 identities per frame must be unique; V34 remains Archive exact`;

const stablePhaseCode = `# V37: frame remains in Philox identity; every frame is new emulsion
sampled_phase = rng.uniform(0, 2*pi)       # consume to preserve Archive sequence
class_id = record * 15 + population * 5 + size_class
phase = 2*pi * frac((class_id + 0.5) * golden_ratio) + pi/6
offset = 0.38 * [cos(phase), sin(phase)]
# only integration phase is stable; grain sites are never reused across frames`;

const deliveryCode = `# V40: the professional master is the sole delivered picture authority
professional = prores4444_xq(pow(Lobs, 1/2.4))
Lmaster      = pow(decode(professional), 2.4)
quicktime    = prores4444_xq(srgb_oetf(Lmaster))
still        = frame(quicktime, 12)   # no second OETF inversion
web_video    = encode_srgb(quicktime) # same first frame and transfer
# EOTF(professional) ~= EOTF(quicktime) ~= Lmaster`;

const densityFormationCode = `# V39: image structure remains in its measured density domains
Dneg_mean = mtf_5279(develop_5279(exposure))
Dneg_real = Dneg_mean + finite_site_density - mean_density
scan = spirit_2k_observe(Dneg_real)

Dprint_mean = mtf_2383(expose_2383(Dneg_mean))
Dprint_real = Dprint_mean + mtf_2383(expose_2383(Dneg_real) - expose_2383(Dneg_mean))
Dprint_real += finite_2383_dye_cloud_density
projection = xenon_observe(Dprint_real)
# no display-RGB grain overlay`;

const v40BoundaryCode = `# V40: constrain randomness only where public data measured it
D5279 = mtf_5279(Dmean) + calibrate_post_process_RMS(delta_after_DIR)
delta_visible = observer_integrate_luma_and_opponent(D5279 - Dmean)

# 2383 has no public record covariance/NPS: do not invent stochastic print grain
D2383 = mtf_2383(expose_2383(D5279))
projection = xenon_observe(D2383)

# final adapter keeps scan low-frequency dye colour and projection luminance
projection = final_adapter(scan_low_chroma, projection_luma, opponent_hf=0)

# gate opponent energy and unsupported isolated 3x3 primary impulses
assert dark_opponent_p9999 <= 0.035
assert isolated_primary_impulses_gt_0_06_per_million <= 5`;

const v41ColourCode = `# V41: chart data estimates direction; retain a conservative 12.5% step
xyz_d50 = bradford_d65_to_d50(bt2020_to_xyz(scene_linear))
chroma  = xyz_d50 - neutral_axis(xyz_d50)
corrected = chroma + 0.125 * (cross_group_matrix @ chroma - chroma)
scene_v41 = restore_exact_d65_luminance(corrected)

# signed intermediates survive only when every combined record is non-negative
signed_records = film_basis_signed @ record_sensitivity.T
records = where(all(signed_records >= 0), signed_records,
                film_basis_clipped @ record_sensitivity.T)`;

const v43hCode = `# V43H overrides only unmeasured candidates; every other V42 constant is frozen
negative_nps = preserve_rms_48um(
    redistribute_spatial_spectrum(scale=0.72, five_size_classes=True))
spirit = lerp(v42_broad_observer, bounded_candidate, weight=0.25)

# weak common print density only; no independent RGB print impulses
delta_print = 0.06 * (binomial(900, p) / 900 - p)
print_light = mean_print_light * 10 ** (-delta_print[..., None])

projection, scan, deterministic = observe_once(realized_negative)
fsd = independent_fsd(deterministic, N=176, sigma=0.597)`;

const v44Code = `# V44 returns to the accepted V42 image-formation profile
negative = form_v42_5279(raw)
projection_light = observe_2383_xenon(negative)
scan             = observe_period_2k(negative)
projection = normal_process_monitor(projection_light,
                                    low_frequency_chroma=scan)

# native 5.7K master remains authoritative
master_light = bt1886_decode(decode(prores_xq_master))
review_light = pixel_area_integrate(master_light, width=1920)
review       = prores_xq(srgb_encode(review_light))
still        = decode_frame(review, middle_frame)`;

export function AlgorithmEnglish() {
  return (
    <main className="algorithm-page wrap">
      <header className="page-header"><span className="eyebrow">METHOD · V44 OBSERVER INTEGRITY / V42 IMAGE BASELINE</span><h1>Not a filter.<br />An image-formation chain.</h1><p>V44 withdraws the unmeasured V43H candidates, retains the gated normal-process colour boundary, and defines display review without altering the native V42 image-formation master.</p></header>

      <section className="pipeline"><div className="pipeline-line"><span>01<b>GH7 RAW</b><small>extended-linear RGB</small></span><i>→</i><span>02<b>Virtual exposure</b><small>V-Gamut / film records</small></span><i>→</i><span>03<b>5279 development</b><small>sites · dyes · DIR</small></span><i>→</i><span>04<b>Observer</b><small>2383 or 2K DI</small></span><i>→</i><span>05<b>Display delivery</b><small>BT.1886 master / sRGB companion</small></span></div></section>

      <section className="method-section"><div className="method-index">V44</div><div className="method-copy"><span className="section-tag">GATED OBSERVERS · SCALE-DECLARED REVIEW</span><h2>Do not change the emulsion to compensate for an unspecified player resize</h2><p>V44 restores V42 image formation because public 48 µm RMS cannot identify V43H’s guessed NPS, and no public measurement supports its Spirit or 2383-grain candidates. Fully direct analytical projection colour failed the native dark opponent-tail gate, so the accepted V31 normal-process monitor boundary remains: 2383 owns lightness and texture while period scan supplies only low-frequency dye chroma. The native 5.7K 12-bit master stays intact; review explicitly measures observer light over a 1920-pixel raster.</p><pre><code>{v44Code}</code></pre><div className="equation"><span>DISPLAY-SAMPLING BOUNDARY</span><b>L<sub>review</sub>=A<sub>pixel</sub>[EOTF<sub>BT.1886</sub>(V<sub>master</sub>)]</b><small>Area integration occurs in linear observer light before sRGB. The still is decoded from the final movie.</small></div></div></section>

      <section className="method-section"><div className="method-index">V43H</div><div className="method-copy"><span className="section-tag">HYPOTHESIS EDITION · ISOLATED / REVERSIBLE</span><h2>Completing an unknown does not turn a prediction into a measurement</h2><p>V43H freezes V42 RAW interpretation, colour, H-D, DIR, MTF, 48 µm RMS, black and gamma. It tests only three central candidates that have documentary direction but no direct numerical measurement: a finer 35 mm spatial spectrum, a 25% move toward a synthetic period Spirit observer, and weak spectrally neutral common-density 2383 texture. Projection and scan share one realized negative; FSD reads the deterministic mean returned by that same spectral integration and remains an independent control.</p><pre><code>{v43hCode}</code></pre><div className="equation"><span>VERSION BOUNDARY</span><b>V43H = V42 + isolated hypotheses</b><small>Every new degree of freedom can be removed independently; the experiment profile cannot rewrite V42.</small></div></div></section>

      <section className="method-section"><div className="method-index">V42</div><div className="method-copy"><span className="section-tag">RESEARCH-CONFORMANT ENGINE · ONE PICTURE AUTHORITY</span><h2>An executable closure of V41 research—not a second “V2” visual style</h2><p>V42 adds no grade and claims no new 5279 material measurement. It makes the V37 stable integration phase, V40 processed-granularity boundary and withheld 2383 randomness, and V41 12.5% chart-bounded transport runtime gates. Production defaults to the validated Philox-u32 Bernoulli Metal realization and requires all 45 stochastic identities per frame to be complete and unique. The two 12-bit BT.1886 masters are written first; sRGB companions, stills and web media may only derive from those delivered files. V29 audio and timecode retention remains part of release finalization.</p><div className="equation"><span>VERSION MEANING</span><b>V42 image model = V41 accepted baseline</b><small>The version advances because engine, audit and delivery contracts became formal release behavior—not because a new aesthetic look was invented.</small></div></div></section>

      <section className="method-section"><div className="method-index">V41</div><div className="method-copy"><span className="section-tag">T003 FIT · T005 HOLDOUT · LUMINANCE PRESERVED</span><h2>Correct a probable error while keeping unsupported magnitude unknown</h2><p>T003 and the independent T005 repeat one hue/chroma residual direction across synthetic and natural colours. Full strength and 25% both become excessive after final 2383 formation, so production retains 12.5% and changes no white balance, exposure, black, contrast or gamma. Wide-gamut intermediates are no longer clipped unconditionally, but signed values survive only when all three combined 5279 record exposures remain non-negative.</p><pre><code>{v41ColourCode}</code></pre><div className="equation"><span>EVIDENCE BOUNDARY</span><b>Direction identified · magnitude provisional</b><small>Two same-condition outdoor clips authorize one conservative step, not a complete GH7 characterization.</small></div></div></section>

      <section className="method-section"><div className="method-index">V40</div><div className="method-copy"><span className="section-tag">MEASURED RANDOMNESS · BOUNDED COLOUR TAILS</span><h2>Density remains the image; unknown stochastic freedom is not film</h2><p>V39 correctly moved image structure into density, but inverted Kodak&apos;s processed 48 µm RMS into pre-DIR speed-layer yields and created independent 2383 Poisson records without covariance or NPS evidence. Marginal RMS could pass while sparse primary-colour spikes appeared in dark regions. V40 restores the 5279 granularity constraint to its measured post-process boundary, restores shared luminance/opponent integration in both observers, and keeps only evidenced deterministic 2383 density and MTF. This is not display-space chroma denoising; the pipeline stops generating unidentified colour randomness.</p><pre><code>{v40BoundaryCode}</code></pre><div className="equation"><span>RELEASE CONDITION</span><b>RMS + Covariance + Tail + Observer</b><small>All 144 delivered frames across three scenes and two branches must pass at native 5760×4320.</small></div></div></section>

      <section className="method-section"><div className="method-index">V39</div><div className="method-copy"><span className="section-tag">WITHDRAWN · DENSITY-FORMATION EXPERIMENT</span><h2>Form one realized density, then let a scanner or print observe it</h2><p>V39 correctly placed MTF and grain inside density-bearing materials, but incorrectly treated processed RMS as a pre-DIR constraint and invented independent three-record 2383 grain. This section remains as an error record, not the current method.</p><pre><code>{densityFormationCode}</code></pre><div className="equation"><span>WHAT REMAINS TRUE</span><b>D<sub>5279,real</sub>=MTF<sub>5279</sub>(D<sub>mean</sub>)+δD<sub>sites</sub></b><small>The density domain is correct; V40 repairs identification of the stochastic term.</small></div></div></section>

      <section className="method-section"><div className="method-index">V39</div><div className="method-copy"><span className="section-tag">ONE MASTER LIGHT · TWO EXPLICIT DELIVERIES</span><h2>Code values may differ; decoded light must agree</h2><p>V38 separated camera OETF from display EOTF, but still compressed two ProRes copies independently from floating-point Lobs. V39's fine density structure made that lossy split measurable. V39 therefore encodes the 12-bit BT.1886 professional master first, recovers Lmaster from that actual file, and creates the sRGB Mac copy as ProRes 4444 XQ. JPEG and web inherit only the companion. P3 and HDR are not used as unmeasured colour or brightness controls.</p><pre><code>{deliveryCode}</code></pre><div className="equation"><span>DELIVERY INVARIANT</span><b>EOTF<sub>BT.1886</sub>(V<sub>master</sub>) ≈ EOTF<sub>sRGB</sub>(V<sub>Mac</sub>) ≈ L<sub>master</sub></b><small>All three native 24-frame scenes pass; the worst per-channel mean light error is 0.001092, below the 0.0015 gate.</small></div></div></section>

      <section className="method-section"><div className="method-index">V37</div><div className="method-copy"><span className="section-tag">INDEPENDENT SITES · STABLE INTEGRATION</span><h2>Every film frame renews; the imaging operator should not jump as one field</h2><p>V36 emulsion sites were already independent on every frame, but each record and speed population also drew one whole-field subpixel phase, rotating the bilinear integration kernel from frame to frame. V37 keeps frame in the Philox identity and fixes the 15 size-class phases as a golden-ratio ensemble rotated by 30 degrees. Grain is neither smoothed, motion-following nor frozen; only the extra numerical breathing is removed.</p><pre><code>{stablePhaseCode}</code></pre><div className="equation"><span>TEMPORAL BOUNDARY</span><b>G<sub>t</sub> ⟂ G<sub>t+1</sub>　·　K<sub>integration,t</sub>=K<sub>integration</sub></b><small>Stochastic emulsion remains independent; the transfer of the integration operator stays stable.</small></div></div></section>

      <section className="method-section"><div className="method-index">V35</div><div className="method-copy"><span className="section-tag">AUDITABLE PRODUCTION GRAPH</span><h2>The realization may be independent; every identity must remain traceable</h2><p>Production need not reproduce the exact V34 PCG64 grain mosaic, but it must preserve the finite-binomial distribution, 48 µm RMS, NPS, layer statistics and temporal independence. V35 compares complete Philox uint32 words with a 2^32 fixed-point threshold derived from float32 probability. Frame, record, speed population, size class and global pixel coordinates define identity. Asynchronous Metal overlaps CPU expectation filtering; all 45 calls per frame are deduplicated and persisted in provenance.</p><pre><code>{productionCode}</code></pre><div className="equation"><span>PROBABILITY BOUNDARY</span><b>|p<sub>u32</sub>−p<sub>float32</sub>| &lt; 2<sup>−32</sup></b><small>The observed three-source maximum is 2.269e-10; V34 remains the byte-exact Archive reference.</small></div></div></section>

      <section className="method-section"><div className="method-index">V34</div><div className="method-copy"><span className="section-tag">PROCESSED MTF · SINGLE GENERATION</span><h2>Compute the total response once; encode the result once</h2><p>Kodak's 5279 MTF is measured on processed film and already contains the mid-frequency rise from developer adjacency. V34 retains that total MTF and disables the later duplicate deterministic intralayer DIR term. Interimage transport and stochastic grain coupling remain in development space. Both observers then complete the V31 colour boundary in linear Rec.709 before their sole delivery encode.</p><div className="equation"><span>DETERMINISTIC STRUCTURE</span><b>MTF<sub>out</sub>=MTF<sub>Kodak, ECN-2</sub></b><small>No second DIR-acutance response is multiplied in.</small></div><div className="equation"><span>SINGLE-GENERATION OUTPUT</span><b>Proj<sub>master</sub>=Encode(A(Proj<sub>lin</sub>,Scan<sub>lin</sub>))</b><small>The scan master is Encode(Scanlin); there is no intermediate ProRes round trip.</small></div></div></section>

      <section className="method-section"><div className="method-index">00</div><div className="method-copy"><span className="section-tag">V33 · INPUT / TONE / DELIVERY CONTRACT</span><h2>Separate camera witness, film exposure and technical neutralization</h2><p>T002, T007 and T031 use one frozen film model. The camera witness is fixed at 0.00 stop, film input is explicitly +0.45 stop, and Technical Neutral is disabled. The validator measures native 12-bit 1-1-1, display black, toe, p05–p95 contrast, a 32-bin monotonic tone curve and effective log-luma power.</p><div className="equation"><span>EXPOSURE BOUNDARY</span><b>Camera=V709(RAW)　·　Film=5279(RAW·2<sup>0.45</sup>)</b><small>If a gray card authorizes WB/tint correction, it belongs before 5279.</small></div><div className="equation"><span>BLACK GATE</span><b>Black = fraction(Y′<sub>709</sub> ≤ 1/1023)</b><small>Black, toe and gamma are reported separately instead of collapsing into a subjective “richer” judgement.</small></div></div></section>

      <section className="method-section"><div className="method-index">01</div><div className="method-copy"><span className="section-tag">V28 · RAW INPUT CONTRACT</span><h2>Decoded linear BT.2020 becomes three film records</h2><p>AVFoundation delivers demosaiced, white-balanced RGB tagged extended-linear BT.2020/D65—not Bayer values awaiting a second Camera LUT. V28 performs only a linear BT.2020→XYZ D65→V-Gamut primary conversion, with no repeated white balance or nonlinear camera separation.</p><div className="equation"><span>INPUT PRIMARIES</span><b>RGB<sub>V-Gamut</sub> = M<sub>XYZ→V</sub> · M<sub>2020→XYZ</sub> · RGB<sub>decoded</sub></b><small>All matrices operate in linear light; V-Log is not the ProRes RAW decode curve.</small></div><div className="equation"><span>RECORD EXPOSURE</span><b>E<sub>c</sub>(x,y) = Σ<sub>j</sub>M<sub>cj</sub>RGB<sub>j</sub>(x,y)</b></div><div className="equation"><span>NEGATIVE DENSITY</span><b>D<sub>c</sub> = H<sub>c</sub>(log<sub>10</sub>E<sub>c</sub>)</b><small>Each Hc samples the published 5279 Status-M characteristic curve.</small></div></div></section>

      <section className="method-section"><div className="method-index">02</div><div className="method-copy"><span className="section-tag">FINITE SITES</span><h2>Fast, medium and slow populations</h2><p>Every colour record contains three overlapping speed populations. A logistic transition defines the probability that a site develops. Binomial sampling makes variance fall naturally at both unexposed and fully developed extremes.</p><div className="equation"><span>ACTIVATION</span><b>p<sub>c,k</sub> = σ((logE<sub>c</sub> − μ<sub>c,k</sub>) / w<sub>c</sub>)</b></div><pre><code>{siteCode}</code></pre></div></section>

      <section className="method-section"><div className="method-index">03</div><div className="method-copy"><span className="section-tag">DYE-CLOUD SPECTRUM · V40 BOUNDARY</span><h2>Grain is a multi-scale optical integral of finite events</h2><p>Each speed population is represented by five cloud-size classes with distinct weights, so exposure selects a spatial spectrum. V40 no longer inverts published granularity into each pre-DIR population: the completed processed-negative residual is calibrated through the published 48 µm aperture after stochastic DIR.</p><div className="equation"><span>DENSITY NPS</span><b>NPS<sub>c</sub>(f|E) = Σ<sub>k</sub>p<sub>c,k</sub>(1−p<sub>c,k</sub>)|H<sub>c,k</sub>(f)|²</b><small>Finite sites determine morphology; the official RMS constrains only its measured processed-density boundary.</small></div></div></section>

      <section className="method-section"><div className="method-index">04</div><div className="method-copy"><span className="section-tag">DEVELOPMENT DIR</span><h2>Reaction–diffusion happens before record densities are merged</h2><p>Nine sub-emulsions release bounded inhibitor fields at their own lateral scales. A finite transport matrix moves those fields to receiver layers and affects both deterministic density and stochastic deviations.</p><pre><code>{dirCode}</code></pre></div></section>

      <section className="method-section"><div className="method-index">05</div><div className="method-copy"><span className="section-tag">SPECTRAL NEGATIVE</span><h2>Dye formation includes the coloured mask</h2><p>The three records are not ideal CMY. Signed net spectral curves combine newly formed dye with consumed masking couplers. The print path retains the full D-min/orange-base spectrum; the scan performs its own film match.</p><div className="equation"><span>NEGATIVE TRANSMISSION</span><b>T<sub>neg</sub>(λ)=10<sup>−[Dmin(λ)+Σa<sub>c</sub>ΔD<sub>c,net</sub>(λ)]</sup></b></div></div></section>

      <section className="method-section"><div className="method-index">06</div><div className="method-copy"><span className="section-tag">2383 ANALYTICAL DYES</span><h2>Integral Status-A density is inverted before it becomes dye amount</h2><p>The model numerically inverts 2383 principal curves into analytical cyan, magenta and yellow dye amounts, applies LAD-centred print interimage, then integrates the resulting transmission under the xenon/CIE observer.</p></div></section>

      <section className="method-section split-method"><div className="method-index">07</div><div className="method-copy"><span className="section-tag">TWO OUTPUTS</span><h2>One negative, two observation chains</h2><div className="method-branches"><article><b>5279 → 2383 → xenon</b><p>A 3200 K printer light exposes three 2383 records. Print sensitometry, analytical dyes, print MTF, Callier effect and projection flare belong only to this branch. V40 withholds intrinsic stochastic 2383 grain because record covariance/NPS is not public.</p></article><article><b>5279 → Period 2K → Cineon</b><p>Broad period RGB responses integrate negative transmission, followed by film matching, a 2K aperture, Cineon 0.002 D/code and restrained SDR finishing.</p><pre><code>{scanCode}</code></pre></article></div></div></section>

      <section className="method-section"><div className="method-index">08</div><div className="method-copy"><span className="section-tag">V30 · OFFICIAL LAD COLOUR ANCHOR</span><h2>Kodak channel densities anchor 2383—not a vendor LUT</h2><p>V30 replaces the simplified equal-density print neutral with H-61B’s official 1.09/1.06/1.03 D aims. The vendor D60 LUT and digitized dye-curve residuals remain in the research record, but their final hue and saturation weights are zero because they are not measured Kodak material evidence.</p><div className="equation"><span>OFFICIAL LAD / EVIDENCE WEIGHTS</span><b>D<sub>LAD</sub>=[1.09,1.06,1.03]　·　w<sub>D60</sub>=w<sub>hue</sub>=w<sub>sat</sub>=0</b></div></div></section>

      <section className="method-section"><div className="method-index">08B</div><div className="method-copy"><span className="section-tag">V31 HISTORY · V40 FINAL-ADAPTER CORRECTION</span><h2>2383 may reshape lightness without mistaking dye colour for silver</h2><p>V30 expressed chroma as C/L and then replaced L with the steeper 2383 neutral curve. Darker regions consequently lost absolute chroma; combined with full luminance texture, the result approached retained silver. V31 corrected the low-frequency colour boundary, but its final adapter also reintroduced the full high-frequency projection opponent residual after the observer had already integrated it. V40 removes that duplicate path: Period 2K supplies the restrained low-frequency OKLab a/b dye colour, projection supplies exact per-pixel linear luminance, and no opponent high-frequency term is added a second time. This is a process-boundary correction—not a saturation grade or display-space denoiser.</p><div className="equation"><span>V40 FINAL OBSERVER BOUNDARY</span><b>ab<sub>out</sub>=G<sub>σ</sub>＊ab<sub>scan</sub>　·　Y<sub>out</sub>=Y<sub>proj</sub></b><small>σ=0.72 px at 2K; gamut is compressed around target Y. 5279, print black, gamma and density-domain grain formation remain unchanged.</small></div></div></section>

      <section className="method-section"><div className="method-index">09</div><div className="method-copy"><span className="section-tag">COLOUR-GRAIN SEPARATION</span><h2>The observer integrates grain without regrading mean colour</h2><p>Signed grain delta is split into Rec.709 luminance and opponent components. Observer-specific integration affects only the opponent texture; deterministic mean RGB never enters this operation.</p><div className="equation"><span>SIGNED GRAIN</span><b>δY = wᵀδRGB　·　δC = δRGB − δY</b></div></div></section>

      <section className="method-section"><div className="method-index">10</div><div className="method-copy"><span className="section-tag">V40 · OUTPUT STANDARD</span><h2>Observer conditions, display light and file transfer are separate boundaries</h2><p>The 48-nit cinema condition remains in the 2383 observer and the period finish remains in the scan observer. Their output is display-linear Rec.709 light. The professional file is ProRes 4444 XQ with inverse BT.1886 gamma 2.4; the direct-view Mac companion is derived from that encoded master and is also ProRes 4444 XQ, with an explicit sRGB transfer. In the XDR HDTV Video reference mode, judge the professional master.</p><pre><code>{deliveryCode}</code></pre></div></section>

      <section className="method-section"><div className="method-index">11</div><div className="method-copy"><span className="section-tag">EXACT ACCELERATION</span><h2>Cache deterministic colour; parallelize independent silver-halide events</h2><p>A 193³ lattice caches exact analytical print samples. Fixed seeded row stripes parallelize 45 binomial populations while remaining bit-identical across worker counts. Mean negative density is shared rather than recomputed.</p></div></section>

      <section className="method-section"><div className="method-index">12</div><div className="method-copy"><span className="section-tag">V27 · SCAN GRAY AXIS</span><h2>Level-dependent scanner balance with an exact luma lock</h2><p>The V26 period scan was neutral only at its 18% anchor. V27 renders a dense neutral exposure scale, derives a smooth RGB balance over display level and applies it only to the finished scan. The output is then renormalized to the original per-pixel Rec.709 luminance.</p><pre><code>{neutralCode}</code></pre><div className="equation"><span>INVARIANT</span><b>Y<sub>V27</sub>(x,y) = Y<sub>V26</sub>(x,y)</b><small>Black, lower-scale gamma, contrast and the 2K aperture cannot change through this operation.</small></div></div></section>

      <section className="method-section"><div className="method-index">13</div><div className="method-copy"><span className="section-tag">EVIDENCE BOUNDARY</span><h2>Negative findings are part of the algorithm</h2><p>The latest hourly audit found no public, stock-specific 5279 NPS, no measured 5279 DIR matrix and no 5279 parameter payload in the official JVT packages or the complete certified April 2003 provisional. That provisional names 5279; H022 switches the same identifier to 5218; the later patent returns to 5279. This proves document-branch drift, not a hidden measurement. V27 therefore changes none of those parameters.</p></div></section>

      <section className="validation"><span className="section-tag">V40 THREE-SCENE · EVERY-FRAME VALIDATION</span><h2>Shared release gates</h2><div className="validation-grid"><div><b>Native resolution</b><p>3 × 24 frames · 5760×4320</p></div><div><b>Dual 12-bit delivery</b><p>BT.1886 master + sRGB companion</p></div><div><b>Colour tails</b><p>144 native-frame audits</p></div><div><b>Temporal structure</b><p>Independent sites · stable integration</p></div><div><b>Display overlays</b><p>Zero grain layers</p></div><div><b>Colour boundary</b><p>V38 frozen · no grade</p></div></div></section>
    </main>
  );
}
