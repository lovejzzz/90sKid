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

export function AlgorithmEnglish() {
  return (
    <main className="algorithm-page wrap">
      <header className="page-header"><span className="eyebrow">METHOD · CURRENT V30</span><h1>Not a filter.<br />An image-formation chain.</h1><p>V30 retains V29’s 5279 emulsion, grain, DIR and period-scan model, corrects the 2383 channel aims from official Kodak LAD data, and uses a Panasonic V-709 baseline on three scenes to separate source colour from film-observer behaviour. Creative grading remains outside the model.</p></header>

      <section className="pipeline"><div className="pipeline-line"><span>01<b>GH7 RAW</b><small>extended-linear RGB</small></span><i>→</i><span>02<b>Virtual exposure</b><small>V-Gamut / film records</small></span><i>→</i><span>03<b>5279 development</b><small>sites · dyes · DIR</small></span><i>→</i><span>04<b>Observer</b><small>2383 or 2K DI</small></span><i>→</i><span>05<b>12-bit output</b><small>Rec.709 OETF / 1-1-1</small></span></div></section>

      <section className="method-section"><div className="method-index">01</div><div className="method-copy"><span className="section-tag">V28 · RAW INPUT CONTRACT</span><h2>Decoded linear BT.2020 becomes three film records</h2><p>AVFoundation delivers demosaiced, white-balanced RGB tagged extended-linear BT.2020/D65—not Bayer values awaiting a second Camera LUT. V28 performs only a linear BT.2020→XYZ D65→V-Gamut primary conversion, with no repeated white balance or nonlinear camera separation.</p><div className="equation"><span>INPUT PRIMARIES</span><b>RGB<sub>V-Gamut</sub> = M<sub>XYZ→V</sub> · M<sub>2020→XYZ</sub> · RGB<sub>decoded</sub></b><small>All matrices operate in linear light; V-Log is not the ProRes RAW decode curve.</small></div><div className="equation"><span>RECORD EXPOSURE</span><b>E<sub>c</sub>(x,y) = Σ<sub>j</sub>M<sub>cj</sub>RGB<sub>j</sub>(x,y)</b></div><div className="equation"><span>NEGATIVE DENSITY</span><b>D<sub>c</sub> = H<sub>c</sub>(log<sub>10</sub>E<sub>c</sub>)</b><small>Each Hc samples the published 5279 Status-M characteristic curve.</small></div></div></section>

      <section className="method-section"><div className="method-index">02</div><div className="method-copy"><span className="section-tag">FINITE SITES</span><h2>Fast, medium and slow populations</h2><p>Every colour record contains three overlapping speed populations. A logistic transition defines the probability that a site develops. Binomial sampling makes variance fall naturally at both unexposed and fully developed extremes.</p><div className="equation"><span>ACTIVATION</span><b>p<sub>c,k</sub> = σ((logE<sub>c</sub> − μ<sub>c,k</sub>) / w<sub>c</sub>)</b></div><pre><code>{siteCode}</code></pre></div></section>

      <section className="method-section"><div className="method-index">03</div><div className="method-copy"><span className="section-tag">DYE-CLOUD SPECTRUM</span><h2>Grain is a multi-scale optical integral of finite events</h2><p>Each speed population is represented by five cloud-size classes. V26 gives fast, medium and slow populations different class weights, so exposure selects a spatial spectrum. Every record/exposure is then renormalized to Kodak’s published 48 µm RMS.</p><div className="equation"><span>DENSITY NPS</span><b>NPS<sub>c</sub>(f|E) = Σ<sub>k</sub>p<sub>c,k</sub>(1−p<sub>c,k</sub>)|H<sub>c,k</sub>(f)|²</b></div></div></section>

      <section className="method-section"><div className="method-index">04</div><div className="method-copy"><span className="section-tag">DEVELOPMENT DIR</span><h2>Reaction–diffusion happens before record densities are merged</h2><p>Nine sub-emulsions release bounded inhibitor fields at their own lateral scales. A finite transport matrix moves those fields to receiver layers and affects both deterministic density and stochastic deviations.</p><pre><code>{dirCode}</code></pre></div></section>

      <section className="method-section"><div className="method-index">05</div><div className="method-copy"><span className="section-tag">SPECTRAL NEGATIVE</span><h2>Dye formation includes the coloured mask</h2><p>The three records are not ideal CMY. Signed net spectral curves combine newly formed dye with consumed masking couplers. The print path retains the full D-min/orange-base spectrum; the scan performs its own film match.</p><div className="equation"><span>NEGATIVE TRANSMISSION</span><b>T<sub>neg</sub>(λ)=10<sup>−[Dmin(λ)+Σa<sub>c</sub>ΔD<sub>c,net</sub>(λ)]</sup></b></div></div></section>

      <section className="method-section"><div className="method-index">06</div><div className="method-copy"><span className="section-tag">2383 ANALYTICAL DYES</span><h2>Integral Status-A density is inverted before it becomes dye amount</h2><p>The model numerically inverts 2383 principal curves into analytical cyan, magenta and yellow dye amounts, applies LAD-centred print interimage, then integrates the resulting transmission under the xenon/CIE observer.</p></div></section>

      <section className="method-section split-method"><div className="method-index">07</div><div className="method-copy"><span className="section-tag">TWO OUTPUTS</span><h2>One negative, two observation chains</h2><div className="method-branches"><article><b>5279 → 2383 → xenon</b><p>A 3200 K printer light exposes three 2383 records. Print sensitometry, analytical dyes, print MTF/grain, Callier effect and projection flare belong only to this branch.</p></article><article><b>5279 → Period 2K → Cineon</b><p>Broad period RGB responses integrate negative transmission, followed by film matching, a 2K aperture, Cineon 0.002 D/code and restrained SDR finishing.</p><pre><code>{scanCode}</code></pre></article></div></div></section>

      <section className="method-section"><div className="method-index">08</div><div className="method-copy"><span className="section-tag">V30 · OFFICIAL LAD COLOUR ANCHOR</span><h2>Kodak channel densities anchor 2383—not a vendor LUT</h2><p>V30 replaces the simplified equal-density print neutral with H-61B’s official 1.09/1.06/1.03 D aims. The vendor D60 LUT and digitized dye-curve residuals remain in the research record, but their final hue and saturation weights are zero because they are not measured Kodak material evidence.</p><div className="equation"><span>OFFICIAL LAD / EVIDENCE WEIGHTS</span><b>D<sub>LAD</sub>=[1.09,1.06,1.03]　·　w<sub>D60</sub>=w<sub>hue</sub>=w<sub>sat</sub>=0</b></div></div></section>

      <section className="method-section"><div className="method-index">09</div><div className="method-copy"><span className="section-tag">COLOUR-GRAIN SEPARATION</span><h2>The observer integrates grain without regrading mean colour</h2><p>Signed grain delta is split into Rec.709 luminance and opponent components. Observer-specific integration affects only the opponent texture; deterministic mean RGB never enters this operation.</p><div className="equation"><span>SIGNED GRAIN</span><b>δY = wᵀδRGB　·　δC = δRGB − δY</b></div></div></section>

      <section className="method-section"><div className="method-index">10</div><div className="method-copy"><span className="section-tag">OUTPUT STANDARD</span><h2>Observer conditions remain separate from interchange encoding</h2><p>Both monitor masters use Rec.709 OETF and complete 1-1-1 metadata. The 48-nit/gamma-2.6 cinema condition lives inside the projection observer; BT.1886 is a Blu-ray reference-display EOTF. Web media decodes Rec.709 and explicitly encodes sRGB.</p></div></section>

      <section className="method-section"><div className="method-index">11</div><div className="method-copy"><span className="section-tag">EXACT ACCELERATION</span><h2>Cache deterministic colour; parallelize independent silver-halide events</h2><p>A 193³ lattice caches exact analytical print samples. Fixed seeded row stripes parallelize 45 binomial populations while remaining bit-identical across worker counts. Mean negative density is shared rather than recomputed.</p></div></section>

      <section className="method-section"><div className="method-index">12</div><div className="method-copy"><span className="section-tag">V27 · SCAN GRAY AXIS</span><h2>Level-dependent scanner balance with an exact luma lock</h2><p>The V26 period scan was neutral only at its 18% anchor. V27 renders a dense neutral exposure scale, derives a smooth RGB balance over display level and applies it only to the finished scan. The output is then renormalized to the original per-pixel Rec.709 luminance.</p><pre><code>{neutralCode}</code></pre><div className="equation"><span>INVARIANT</span><b>Y<sub>V27</sub>(x,y) = Y<sub>V26</sub>(x,y)</b><small>Black, lower-scale gamma, contrast and the 2K aperture cannot change through this operation.</small></div></div></section>

      <section className="method-section"><div className="method-index">13</div><div className="method-copy"><span className="section-tag">EVIDENCE BOUNDARY</span><h2>Negative findings are part of the algorithm</h2><p>The latest hourly audit found no public, stock-specific 5279 NPS, no measured 5279 DIR matrix and no 5279 parameter payload in the official JVT packages or the complete certified April 2003 provisional. That provisional names 5279; H022 switches the same identifier to 5218; the later patent returns to 5279. This proves document-branch drift, not a hidden measurement. V27 therefore changes none of those parameters.</p></div></section>

      <section className="validation"><span className="section-tag">V30 THREE-SCENE VALIDATION</span><h2>Shared release gates</h2><div className="validation-grid"><div><b>Native resolution</b><p>3 × 24 frames · 5760×4320</p></div><div><b>Film masters</b><p>12-bit ProRes 4444</p></div><div><b>Near-neutral chroma</b><p>≤ 0.00455</p></div><div><b>Observer hue difference</b><p>median ≤ 4.99°</p></div><div><b>Camera original</b><p>Official Panasonic V-709</p></div><div><b>Thread safety</b><p>Sequential · identical pixels</p></div></div></section>
    </main>
  );
}
