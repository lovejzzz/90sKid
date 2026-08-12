export type EnglishVersionCopy = {
  year: string;
  title: string;
  summary: string;
  changes: string[];
  errors: string[];
  discoveries: string[];
  trialNote?: string;
};

export const versionEnglish: Record<string, EnglishVersionCopy> = {
  V4: {
    year: "STRUCTURE PROTOTYPE",
    title: "Sharpness and grain become one medium",
    summary:
      "The first version to stop overlaying noise on a finished image. Detail and randomness are formed together in a virtual emulsion-density field.",
    changes: [
      "Exposure-domain emulsion prototype",
      "Channel-dependent MTF",
      "Independent structure per frame",
    ],
    errors: [
      "Cloud radii and observer blur were too large",
      "Closer to 8/16 mm than 35 mm 5279",
      "Colour still relied on empirical matrices",
    ],
    discoveries: [
      "Coarse grain must be paired with lower high-frequency resolution",
      "Grain belongs to image formation, not a post layer",
    ],
  },
  V5: {
    year: "5279 CALIBRATION",
    title: "From generic film look to one named stock",
    summary:
      "Kodak VISION 500T 5279 documentation begins to constrain scale, record response and grain instead of treating every fast colour negative alike.",
    changes: [
      "5279 curve and sensitivity targets",
      "35 mm image scale",
      "Separate R/G/B records",
    ],
    errors: [
      "RAW/display clipping still affected highlights",
      "Shadow texture resembled digital chroma noise",
      "Speed layers were not explicit",
    ],
    discoveries: [
      "The published blue-record granularity is higher than green and red",
      "Stock character is a joint property of curves, dyes and granularity",
    ],
  },
  V6: {
    year: "RAW HIGHLIGHTS",
    title: "Recover sensor information before shaping a film shoulder",
    summary:
      "The GH7 ProRes RAW linear interpretation was corrected so camera clipping and negative shoulder compression became separate operations.",
    changes: [
      "Linear RAW path",
      "Per-record highlight shoulders",
      "Bounded long-range red scatter",
    ],
    errors: [
      "Grain remained too strong",
      "Halation was initially too generic",
      "Panasonic colour handling was incomplete",
    ],
    discoveries: [
      "A negative shoulder is not a soft clip",
      "5279 rem-jet suppresses exaggerated rear-surface halation",
    ],
  },
  V7: {
    year: "FILM OPTICS",
    title: "Silver halide, scatter and anti-halation in one chain",
    summary:
      "Layer scatter, anti-halation and local edge response turn uniform noise into an exposure-dependent density structure.",
    changes: [
      "Exposure-dependent grain",
      "Controlled halation",
      "Coupled grain and edge response",
    ],
    errors: [
      "Morphology still resembled pushed 16 mm",
      "Speed layers were only broad segments",
      "Black and viewing conditions were conflated",
    ],
    discoveries: [
      "Shadow/highlight grain changes come from different speed populations entering development",
      "Resolution matching matters as much as grain amplitude",
    ],
  },
  V8: {
    year: "35 MM REFINEMENT",
    title: "Pulling a raw 16 mm texture back toward fine 35 mm",
    summary:
      "Smaller dye clouds, more effective sites and reduced shadow excursions move the spatial scale toward 35 mm 5279.",
    changes: [
      "Cloud radii reduced to roughly 0.5–1.3 native pixels",
      "More effective dye-cloud sites",
      "Less shadow colour separation",
    ],
    errors: [
      "Mean response still used a shared curve",
      "Scan and projection observers were not physical",
      "The colour mask was not spectral",
    ],
    discoveries: [
      "Fine grain can still boil organically when sites are smaller and denser",
    ],
  },
  V9: {
    year: "TWO-BRANCH ORIGIN",
    title: "5279 curves, spectral dyes and two viewing results",
    summary:
      "The three Status-M curves are sampled separately and scanning is split from the print interpretation for the first time.",
    changes: [
      "Independent H-D curves",
      "Early net spectral-density model",
      "Separate scan and print branches",
    ],
    errors: [
      "Print dyes still used an empirical positive matrix",
      "Orange-mask negative lobes were incomplete",
      "The two branches lacked a common colour reference",
    ],
    discoveries: [
      "The data-sheet dye curves are D-min-subtracted net changes",
      "Masking couplers must be counted exactly once",
    ],
  },
  V10: {
    year: "FIRST 2383",
    title: "Kodak 2383 becomes a second real material",
    summary:
      "2383 sensitometry, dyes and printer lights replace the idea of applying one display LUT to the negative.",
    changes: [
      "Second H-D curve set",
      "LAD density aim",
      "2383 dyes and print grain",
    ],
    errors: [
      "Net negative dye curves were misread as positive-only dyes, causing severe magenta",
      "Orange base was removed or compensated twice",
      "The steep print curve amplified small spectral errors",
    ],
    discoveries: [
      "5279 D-min must remain in the optical printing path",
      "Scan de-masking and printer-light compensation are different operations",
    ],
  },
  V11: {
    year: "GRAY-SCALE CALIBRATION",
    title: "Calibrate the full gray scale, not only 18% gray",
    summary:
      "LAD and a multi-step neutral scale establish the first Cineon/Spirit-style scanning baseline.",
    changes: [
      "Multi-point neutral calibration",
      "Cineon code 95/445 anchors",
      "Both branches delivered as Rec.709",
    ],
    errors: [
      "Local colour still used a coarse matrix",
      "Scanner spectra were approximated as Status-M",
      "Blu-ray black finishing was incomplete",
    ],
    discoveries: [
      "A neutral mid-gray does not guarantee neutral shadows or highlights",
      "Black is a viewing-chain decision, not a reason to alter negative D-min",
    ],
  },
  V12: {
    year: "COLOURED MASK",
    title: "Preserving negative net-density lobes from masking couplers",
    summary:
      "The 21-point 5279 spectral curves are treated as signed net-density changes, giving the coloured mask its correct direction.",
    changes: [
      "21-wavelength spectral LUT",
      "Signed negative-density lobes",
      "First local DIR adjacency",
    ],
    errors: [
      "The scan observer remained narrow-band",
      "DIR was applied after total density",
      "Colour separation lacked sublayer dependence",
    ],
    discoveries: [
      "Negative values represent masking-coupler consumption",
      "An average-flat correction still leaves stock-specific spectral residuals",
    ],
  },
  V13: {
    year: "PROJECTION SOURCE",
    title: "From a black-body white to a cinema xenon spectrum",
    summary:
      "A structured xenon SPD, CIE observer and restrained projection scatter replace a generic illuminant.",
    changes: [
      "Xenon spectral power distribution",
      "CIE XYZ observation",
      "Conservative Callier/projection scatter",
    ],
    errors: [
      "The first print result was severely magenta",
      "A physical projection looked too dense on a monitor",
    ],
    discoveries: [
      "Physical projection and monitor presentation are distinct targets",
      "2383's steep curves amplify small hue errors",
    ],
  },
  V14: {
    year: "THREE SPEED LAYERS",
    title: "Finite fast, medium and slow sensitive sites",
    summary:
      "Each colour record receives three finite populations; binomial development produces exposure-dependent variance and is normalized to Kodak's 48 µm RMS curves.",
    changes: [
      "Nine finite populations",
      "p(1−p) variance",
      "48 µm aperture calibration",
    ],
    errors: [
      "R/G/B shared representative grain sizes",
      "Each population still had one circular size",
      "Colour covariance felt synthetic",
    ],
    discoveries: [
      "Variance falls again as a population becomes fully developed",
      "Coarse shadows and fine highlights arise from population crossover",
    ],
  },
  V15: {
    year: "COMPLETE PRINT PATH",
    title: "Orange base, printer lights, 2383 and gamut mapping",
    summary:
      "The full spectral path retains the orange base, balances it with printer lights and forms a 2383 positive before viewing.",
    changes: [
      "Full D-min transmission",
      "Printer-light neutral balance",
      "H-61/TAF-style separation calibration",
    ],
    errors: [
      "Projection remained too deep and blue",
      "Dark red and green hues rotated",
      "Scan black/grain ordering was wrong",
    ],
    discoveries: [
      "Some print richness is physical 2383 slope; some was viewing adaptation error",
      "Gamut compression should preserve hue",
    ],
  },
  V16: {
    year: "VIEWING CALIBRATION",
    title: "Projection black, scan black and stable hue",
    summary:
      "Flare-free projection, typical cinema projection and Blu-ray finishing are separated; dark gamut compression becomes hue-stable.",
    changes: [
      "Typical 1% projection flare",
      "OKLab constant-hue compression",
      "Blu-ray lower-scale gamma and black anchor",
    ],
    errors: [
      "Display black created one-sided grain bias",
      "Monitor projection still felt heavy",
      "Scan chroma grain exceeded film references",
    ],
    discoveries: [
      "Projection and Blu-ray blacks come from different chains",
      "A finished movie can constrain the observer, not measure bare 5279",
    ],
  },
  V17: {
    year: "SCAN CORRECTION",
    title: "Integrating a Spirit 2K aperture in transmission",
    summary:
      "The scanner averages light through the negative at 2K before returning to density and Cineon, fixing grain-lifted blacks.",
    changes: [
      "2K transmission-domain aperture",
      "Correct display-boundary ordering",
      "Controlled high-frequency chroma grain",
    ],
    errors: [
      "Monitor projection still needed adaptation",
      "The scan observer remained approximate",
      "Cloud morphology remained regular",
    ],
    discoveries: [
      "A scanner measures transmitted light, not display-clipped RGB",
      "Correct operation order can repair floating blacks without a grade",
    ],
  },
  V18: {
    year: "DISPLAY ADAPTATION",
    title: "Physical 2383 projection versus its monitor presentation",
    summary:
      "A separate Rec.709 viewing result is derived from the physical print while GH7 sensor noise is separated from virtual-emulsion granularity.",
    changes: [
      "Projection-monitor branch",
      "Multi-anchor neutral adaptation",
      "Sensor-noise separation",
    ],
    errors: [
      "Slight blue and saturated-hue shifts remained",
      "Coarse populations still looked regular",
    ],
    discoveries: [
      "Perceived blue can come from nonlinear contrast/chroma ratios",
      "Camera noise must not be preserved as film grain",
    ],
  },
  V19: {
    year: "ORGANIC GRAIN",
    title: "Polydisperse dye clouds and frame-by-frame boiling",
    summary:
      "Each speed population is split into multiple sizes with subpixel phases and sparse larger clouds, reducing the digital chroma-noise impression.",
    changes: [
      "Polydisperse sizes",
      "Subpixel phases",
      "Small-cloud majority with a sparse large tail",
    ],
    errors: [
      "Sublayer colour contribution was static",
      "DIR still followed layer merging",
      "Colour records shared representative ECDs",
    ],
    discoveries: [
      "Organic structure comes from irregular statistics, not larger noise",
      "Fresh sampling must preserve mean density",
    ],
  },
  V20: {
    year: "PREVIOUS BASELINE",
    title: "Exposure-dependent sublayer dye contribution",
    summary:
      "Fast, medium and slow layers alter record mixing through their marginal activation; thin negatives separate less completely than slow-layer highlights.",
    changes: [
      "Marginal-activation record mixing",
      "First coupling of grain and colour formation",
      "More natural scanner-shoulder release",
    ],
    errors: [
      "DIR remained a post-density approximation",
      "Status-M and scanner observers were conflated",
      "Sublayer sizes were not record-specific",
    ],
    discoveries: [
      "Period Kodak patents pre-compensated some films for telecine",
      "Final colour-negative images are dye clouds after silver removal",
      "The next step required reordering the algorithm",
    ],
  },
  V21: {
    year: "DEVELOPMENT REBUILD",
    title: "Development, grain and observers work in their own domains",
    summary:
      "DIR transport moves into nine sub-emulsions; record-specific cloud morphology and distinct Status-M, scanner and printer observers establish the modern structure.",
    changes: [
      "Population-domain DIR reaction–diffusion",
      "Record-specific fast/mid/slow morphology",
      "Separated measurement, scan and print observers",
    ],
    errors: [
      "2383 Status-A densities were still treated as dye amounts",
      "D60 adaptation could contaminate neutrals",
      "Print computation was too slow",
    ],
    discoveries: [
      "Uniform sensitometry already includes uniform chemistry, so local DIR must vanish on a flat field",
      "Measurement observers are not viewing observers",
    ],
  },
  V22: {
    year: "ANALYTICAL PRINT DYES",
    title: "Analytical dyes, interimage coupling and relative-white monitoring",
    summary:
      "Status-A principal curves are inverted to dye amounts; print interimage operates around LAD and D60 contributes relative chroma only.",
    changes: [
      "Analytical 2383 dye inversion",
      "LAD-centered interimage coupling",
      "Neutral-subtracted D60 chroma",
    ],
    errors: [
      "Exact spectral print rendering was expensive",
      "One source scene could not prove generalization",
      "Grain morphology was still discrete",
    ],
    discoveries: [
      "Integral density is not dye amount",
      "White-point calibration must not tint neutral pixels",
    ],
  },
  V23: {
    year: "CROSS-SCENE HOLDOUT",
    title: "Continuous dye-cloud populations and colour generalization",
    summary:
      "Five cloud classes approximate a continuous distribution, new T020/T032 RAW scenes test colour holdout, and a dense analytical print lattice accelerates the observer.",
    changes: [
      "Five-class cloud quadrature",
      "Two new one-second native RAW trials",
      "193³ exact analytical projection cache",
    ],
    errors: [
      "Texture still evoked early CCD or 16 mm",
      "Chroma grain remained too prominent",
      "The public RMS curve did not identify a full spectrum",
    ],
    discoveries: [
      "A colour chain can generalize while texture scale remains wrong",
      "Most compute time lies in negative formation, not encoding",
    ],
    trialNote:
      "Rainy cyan-green foliage and low-contrast texture test whether colour and grain generalize beyond the first scene.",
  },
  V24: {
    year: "35 MM SPECTRUM",
    title: "35 mm grain spectrum and luma/chroma separation",
    summary:
      "Cloud power shifts toward finer scales while the two observers integrate chroma grain separately. Mean colour, tone, MTF and sensitometry remain V23.",
    changes: [
      "Finer cloud-size distribution",
      "Reduced large-cloud tail and correlation scale",
      "Observer-specific chroma-grain integration",
      "One-second live web previews",
    ],
    errors: [
      "The selected spectrum remains bounded, not uniquely measured",
      "48 µm RMS alone cannot determine low-frequency clustering",
      "Creative grading stayed deliberately outside the model",
    ],
    discoveries: [
      "Gauge appearance depends on magnification and low-frequency power as well as RMS",
      "Signed grain deltas can be managed without changing mean colour",
    ],
    trialNote:
      "The rainy T032 scene checks that reduced chroma texture does not return as cyan-green CCD noise.",
  },
  V25: {
    year: "OUTPUT-STANDARD FIX",
    title: "Viewing conditions and interchange masters are not the same thing",
    summary:
      "An initial output error baked inverse display EOTFs into files. The corrected release restores both monitor masters to Rec.709 OETF, full 1-1-1 metadata and consistent sRGB web conversion.",
    changes: [
      "Corrected the accidental brightness lift",
      "Rec.709 OETF/1-1-1 for both monitor masters",
      "BT.1886 kept only as a reference-display EOTF",
      "Exact seeded parallel acceleration",
    ],
    errors: [
      "The first export mixed BT.1886, P3 gamma and Rec.709 tags",
      "Midtones and shadows became 20–28% too bright",
      "Public evidence still could not identify every interlayer parameter",
    ],
    discoveries: [
      "The lift was measurable, not subjective",
      "A reference-display EOTF is not a source-file transfer function",
      "Negative research results prevent unjustified colour changes",
    ],
    trialNote:
      "Dark posts and low-contrast rainy texture test black, gamma and metadata consistency.",
  },
  V26: {
    year: "EXPOSURE-CONDITIONED GRAIN",
    title: "Exposure selects a grain spectrum, not only grain loudness",
    summary:
      "Colour, black, contrast, gamma and Rec.709 delivery stay locked while fast, medium and slow populations receive different five-class cloud distributions.",
    changes: [
      "Separate cloud-size weights for fast/mid/slow layers",
      "A wider large-cloud tail in shadows and a finer slow-layer highlight tail",
      "Independent finite-site development every frame",
      "NPS, activation, mean-drift and temporal-correlation diagnostics",
    ],
    errors: [
      "The public 48 µm RMS does not uniquely identify an NPS",
      "The per-sublayer distributions remain bounded hypotheses",
      "The period scanner used only two gray anchors and retained an invented residual",
    ],
    discoveries: [
      "Fast sensitive crystals dominate shadow grain power",
      "Slow populations dominate highlight texture",
      "The V26 colour branch remained numerically V25",
    ],
    trialNote:
      "T032 tests exposure-conditioned grain in rain, low contrast and cyan-green detail.",
  },
  V27: {
    year: "RESEARCH BASELINE",
    title: "Separating a scanner's green veil from film colour",
    summary:
      "V27 identifies the pale green veil in the Blu-ray branch as a level-dependent scanner neutral-axis error, not 5279 colour or grain. A 2049-level neutral exposure scale corrects RGB balance while preserving each pixel's Rec.709 luminance, black, contrast and gamma.",
    changes: [
      "2049-level scanner neutral-scale calibration",
      "Level-dependent RGB balance after the completed scan observer",
      "Exact per-pixel Rec.709 luminance preservation",
      "Byte-identical V26 projection master and locked V26 emulsion",
      "Review of the certified April 2003 5279 provisional: identifier provenance confirmed, numerical parameters still absent",
      "Complete Chinese / English website switch with remembered preference",
    ],
    errors: [
      "V26 balanced only 18% gray and one dense-negative anchor",
      "An unsupported 18% residual scanner correction left a green hump in shadows and lower mids",
      "A global magenta offset cannot fix an error that changes direction over the gray scale",
      "2K aperture softness and the RGB-axis error appeared together as one green haze",
    ],
    discoveries: [
      "Maximum neutral-channel residual falls from 0.01820 to 0.00236",
      "Maximum green-opponent residual falls from 0.02172 to 0.00242",
      "Maximum per-pixel luminance drift is below 1.8×10⁻⁷",
      "The April 2003 provisional names 5279, May 2003 JVT-H022 switches the same identifier to 5218, and the later patent returns to 5279: document-branch drift, not a calibration payload",
      "The latest hourly audits add evidence boundaries, not invented 5279 parameters",
    ],
    trialNote:
      "T020 tree bark and fungi separate neutral dark texture from real foliage green; T032 tests the correction in rainy cyan-green detail.",
  },
  V28: {
    year: "PREVIOUS BASELINE",
    title:
      "Correcting the boundary between ProRes RAW conversion and Panasonic's Camera LUT",
    summary:
      "V28 traces the remaining green veil to stage order before the negative: AVFoundation already supplies extended-linear BT.2020/D65, but V27 interpreted that RGB buffer again as Panasonic RAW Gamut. V28 uses a linear BT.2020-to-XYZ-to-V-Gamut primary conversion with no second white balance or creative grade; every V27 film, grain, tone and observer parameter stays locked.",
    changes: [
      "Verified the decoded Core Video buffer as extended-linear BT.2020/D65",
      "Removed the second RAW-Gamut Camera-LUT interpretation",
      "Linear BT.2020 → XYZ D65 → Panasonic V-Gamut primary conversion",
      "Retained AVFoundation standard conversion and as-shot metadata with no second white balance",
      "Recomputed both observers from the same corrected negative",
      "Added a hash-validated analytical 2383 cache and bit-identical sampler",
    ],
    errors: [
      "V27 treated an already converted BT.2020 buffer as Panasonic RAW Gamut",
      "A misplaced nonlinear 3D camera separation created scene-dependent green and blue errors",
      "Scan gray-axis calibration could not remove an error introduced before film exposure",
      "A global magenta, saturation or gamma adjustment would be a grade and would damage real foliage green",
    ],
    discoveries: [
      "Camera-LUT validity depends on the input stage, not merely the camera model",
      "The rainy T032 source is genuinely cyan-green; the goal is to remove only the extra fluorescent veil",
      "Near-neutral green/red ratios improve while highlight anchors and clipping remain stable",
      "Uniform synthetic gray stays neutral and the V27 Spirit neutral calibration remains necessary",
      "The accelerated final 12-bit decoded pixels are bit-identical to the reference implementation",
    ],
    trialNote:
      "The genuinely cyan-green rainy forest separates source colour from the extra veil produced by the misplaced Camera LUT.",
  },
  V29: {
    year: "PREVIOUS BASELINE",
    title: "From one-second trials to complete motion validation",
    summary:
      "V29 turns the remaining work from subjective film flavour into falsifiable validation. Public 5279 evidence constrains neutral H-D, MTF and 48 µm RMS, but does not publish a stock-specific NPS, DIR matrix, layer recipe or Spirit spectrum. Those unknown parameters remain V28. The complete 165-frame T002 source receives a new finite-site emulsion at every absolute source frame and is delivered with both observers, source 24-bit four-channel audio and timecode.",
    changes: [
      "Complete 165-frame T002 motion stress test",
      "Absolute source-frame seeds across exact parallel ranges",
      "Shared per-frame negative for the 2383 and Period 2K observers",
      "Full-motion black, highlight, high-frequency, temporal and segment-boundary validation",
      "Source 24-bit/48-kHz four-channel PCM and 12:04:05:23 timecode retained",
      "V28 H-D, MTF, 48 µm RMS, colour, black, gamma and observers locked",
    ],
    errors: [
      "A 48 µm single-aperture RMS value is not a complete grain NPS",
      "A Kodak patent diffusion example is not a 5279-specific DIR matrix",
      "Public Spirit hardware information is not its proprietary spectral calibration",
      "Scene-by-scene tuning without physical comparison would mix creative grading into the baseline",
    ],
    discoveries: [
      "The code-completable portion of the last 15–20% is validation and delivery; stock identification now requires measurement",
      "Successive film frames form new emulsion mosaics rather than translating or looping one texture",
      "Parallel rendering can preserve absolute-frame randomness and exact pixels",
      "Full motion exposes flicker, grain swimming, black bias and highlight discontinuity better than a still",
      "Audio, timecode, colour signalling and frame count are part of an industry-standard master",
    ],
  },
  V30: {
    year: "PREVIOUS BASELINE",
    title:
      "Official LAD aims remove the 2383 cast; three camera baselines isolate what film changes",
    summary:
      "V30 traces the residual blue-magenta projection veil to an equal-RGB LAD shortcut and to unsupported hue authority assigned to a vendor D60 LUT and digitized dye curves. Kodak's published 2383 aims—1.09/1.06/1.03 D—replace the shortcut. T002, T020 and T032 each receive one native-resolution second plus an official Panasonic V-709 camera baseline, so source colour, 5279, 2383 projection and period scanning can be compared directly.",
    changes: [
      "Kodak H-61B 2383 LAD aims: 1.09/1.06/1.03 D",
      "Removed vendor D60 LUT control over Kodak physical hue",
      "Digitized net-dye curves no longer force final hue or saturation",
      "Three 24-frame native 5.7K 12-bit dual-master trials",
      "Official Panasonic V-709 camera baseline for every source",
      "Matched frame-12 sRGB stills and 24-frame hover loops",
      "Safe sequential observers with pixel-identical output",
      "Neutral-chroma, observer-hue, endpoint and format gates",
    ],
    errors: [
      "V29's equal 1.00/1.00/1.00 LAD ignored the official channel aims and introduced a blue-magenta shift",
      "A third-party D60 LUT is not measured Kodak 2383 spectral evidence",
      "Digitization uncertainty cannot justify a high-weight global hue control",
      "An initial camera baseline double-applied legal-range scaling; it was rejected before release",
      "Two Python observer threads could enter Numba's workqueue concurrently and abort",
    ],
    discoveries: [
      "The blue-purple filter dyes in unprocessed 2383 wash out in processing and must not become a uniform projected veil",
      "A warmer scan does not prove projection should be absolutely blue; each observer needs its own neutral-axis test",
      "Official unequal LAD aims explain the correction better than a subjective blue reduction",
      "T032 genuinely contains cyan-green rainy haze; the camera baseline separates scene colour from observer error",
      "Sequential observation is pixel-identical here and avoids contention",
      "A useful original comparison needs a necessary camera display transform; flat Log is not the scene appearance",
    ],
    trialNote:
      "T020 tests neutral bark, fungi and dark texture; T032 tests genuine cyan-green rain haze and low-contrast detail against the same official camera baseline.",
  },
  V31: {
    year: "CURRENT BASELINE",
    title:
      "Normal-process colour no longer acquires an accidental retained-silver signature",
    summary:
      "V31 answers the mild bleach-bypass character in V30 projection. Normal ECN-2 and ECP-2D remove the picture silver image. V30 had no residual-silver term, but it preserved C/L while applying a steeper 2383 lightness curve, so darker regions automatically lost absolute chroma and combined with strong luminance texture to read like retained silver. V31 keeps V30's film, grain, DIR, MTF, black, gamma, LAD and luminance. At the final delivery boundary, Period 2K supplies low-frequency dye colour while the 2383 projection retains its high-frequency opponent texture and exact per-pixel Rec.709 Y.",
    changes: [
      "Normal ECN-2/ECP-2D baseline explicitly excludes retained silver, skip bleach, ENR and bleach bypass",
      "Period 2K supplies low-frequency OKLab a/b; 2383 retains its high-frequency opponent residual",
      "Constant-hue Rec.709 gamut compression around exact projection luminance",
      "V30 Kodak LAD and all 5279/texture parameters locked",
      "Three native 24-frame 5.7K 12-bit dual-master trials",
      "V30 scan masters verified by file SHA-256 regression",
    ],
    errors: [
      "V30 said tone and colour were separated but preserved C/L, so replacing L still changed absolute colour",
      "A cached-LUT placement was bypassed by the legacy hybrid branch and rejected by regression",
      "A deterministic mean correction was pulled back by the grain mean-colour stage and also rejected",
      "A global saturation lift or black adjustment would be a grade, not a baseline repair",
    ],
    discoveries: [
      "A viewing transform can create a bleach-bypass impression without a chemical silver term",
      "Chroma and saturation are not interchangeable when lightness changes",
      "Normal bleaching is a falsifiable process boundary, not a taste preference",
      "Any future bypass toggle must explicitly model residual silver density",
      "The accepted organic texture does not need to be weakened to correct colour",
    ],
    trialNote:
      "T020 tests dark bark colour; T032 tests whether genuine rainy cyan-green atmosphere survives the correction.",
  },
  V32: {
    year: "CURRENT BASELINE",
    title:
      "Freeze the accepted image; turn the next step from taste into repeatable measurement",
    summary:
      "V32 changes no V31 image-forming parameter. Two new GH7 ProRes RAW scenes independently test the 5279 emulsion, normal 2383 projection and period-2K scan without per-shot tuning. Native format, luminance preservation, highlight clipping, temporal texture, neutral-axis stability, OFX tile regions and cinema X′Y′Z′ delivery now become automated release gates. V32 is not a new look; it makes the current credible look portable, reproducible and falsifiable.",
    changes: [
      "Two new 24-frame native-resolution trials: T007 and T031",
      "All V31 image formation frozen; no per-shot exposure, colour, grain or contrast adjustment",
      "Frame-wise luma, p99 highlight, hard-clip, texture-power and near-neutral a/b gates",
      "SMPTE ST 428-1 12-bit X′Y′Z′ lossless DCDM cinema test sequence",
      "P3-D65/gamma-2.6 ProRes transport explicitly rejected because MOV, frame-header and player interpretations are ambiguous",
      "Numerical OFX tile/ROI parity contract for future Resolve migration",
      "Stage timing proves that stochastic emulsion and observers—not ProRes encoding—dominate runtime",
    ],
    errors: [
      "The first P3 ProRes probe repeated V25's cross-player metadata ambiguity and was removed from delivery",
      "A first DCDM round-trip compared against an already reduced web preview and therefore measured a second resampling; final QA decodes the native representative frame",
      "The first T007 V31-boundary command passed a directory where the encoder expected a file; it failed before producing a valid frame and was rerun with the correct path",
    ],
    discoveries: [
      "Once an image is credible, freezing it can advance the model more than another subjective colour move",
      "One parameter set surviving water highlights, fine grass, neutral stone and warm mushrooms is stronger evidence than one attractive still",
      "DCDM can preserve the completed projection observer but cannot invent gamut already absent from its Rec.709 monitor result",
      "Stochastic emulsion and spectral observation dominate native 5.7K runtime; encoding is a small fraction",
      "An OFX halo must use full output width or proxy and tile sizes will silently change the crossover scale",
    ],
    trialNote:
      "T031 uses neutral stone, warm mushrooms, moss and dark leaves to stress neutral-axis, chroma and fine-texture stability.",
  },
  V33: {
    year: "CURRENT BASELINE",
    title:
      "Do not grade away real green light: lock the input, exposure and black boundaries first",
    summary:
      "V33 applies no global magenta compensation and changes no 5279, grain, DIR, 2383 or scan pixel. It separates an FCP Standard witness, a 0-stop As Shot camera view and the explicit +0.45-stop virtual film EI. Across three scenes it adds failing gates for display black, toe occupancy, robust contrast, effective gamma, native masters, partial-range audio/timecode and safe scheduling on the 48-GiB reference machine. Technical Neutral exists as a disabled boundary until a gray card or ColorChecker supplies repeatable evidence.",
    changes: [
      "Native 24-frame 0.00-stop As Shot V-709 witnesses for T002, T007 and T031",
      "The +0.45-stop virtual film EI is explicitly labelled and no longer confused with untouched camera exposure",
      "SHA-locked FCP Standard T031 source-frame-144 witness",
      "Automated display-black, toe, p05–p95 contrast, 32-bin monotonic tone and effective log-luma-power gates",
      "Technical Neutral boundary retained but disabled until neutral-card evidence exists",
      "Sample-accurate PCM trim and absolute-source-frame timecode for partial deliveries",
      "One native Archive-Exact worker on the 48-GiB reference machine; pixels and random seeds unchanged",
    ],
    errors: [
      "The first three-way concurrent 5.7K float attempt created unacceptable system memory pressure; the panic report showed exhausted compressor segments and near-exhausted swap",
      "Defining black as all three channels near zero missed pixels whose luma had reached black but retained tiny chroma; the final gate uses the same encoded-luma threshold as the FCP audit",
      "Without a neutral target under the scene illumination, foliage bounce, As Shot white balance and local V-709 residual cannot be uniquely separated",
    ],
    discoveries: [
      "A neutral mathematical input remains neutral through BT.2020→V-Gamut→V-Log→official V-709; maximum channel spread is 0.000589",
      "The finished scan's hard-black fraction is strongly scene dependent: nearly zero in T007 and roughly 1–2% in darker T002/T031",
      "Both observers retain monotonic robust tone mappings across all three scenes; no hidden gamma reversal appears",
      "Worker count changes scheduling only; avoiding swap on 48 GiB is both safer and more predictable than overcommitting memory",
      "Technical Neutral is now a falsifiable gray-card question rather than a subjective global tint decision",
    ],
    trialNote:
      "T002 stresses sky and dark completion; T007 stresses water highlights, fine grass and an almost zero-hard-black scene.",
  },
  V34: {
    year: "CURRENT BASELINE",
    title:
      "Let developer adjacency happen once—and let each master encode once",
    summary:
      "V34 follows a full algorithm and render audit, not a new grade. Kodak's 5279 MTF was measured after recommended ECN-2 processing, and Kodak explains that MTF above 100% commonly comes from developer adjacency. The old path first added V21 deterministic DIR acutance and then applied a kernel already fitted to the complete processed-stock MTF, creating roughly 1–3.5% local overlap. V34 removes only that duplicate. Grain, interimage DIR, three speed populations, 48 μm RMS, colour, black and gamma are not tuned by taste. The accepted V31 colour boundary now runs in memory, so projection and scan each receive one ProRes generation.",
    changes: [
      "Processed-stock 5279 MTF becomes the sole owner of deterministic adjacency acutance",
      "The accepted V31 colour boundary runs after both complete observers and before delivery encoding",
      "V30 intermediate-master decoding and the projection's second ProRes generation are removed",
      "The idle extended-linear BT.2020→V-Gamut→Rec.709 round trip is fused as the product of the same matrices",
      "Nine zero-contribution native Gaussian passes are skipped with identical output SHA-256",
      "Partial-range manifests now report PCM trim/re-encode and regenerated timecode accurately",
      "Three native 24-frame 5.7K 12-bit dual-master trials: T002, T007 and T031",
    ],
    errors: [
      "Earlier research already identified MTF as a total processed response, but V21 deterministic adjacency was never cross-checked against the fitted MTF",
      "V31 encoded both V30 observers, decoded them for the chroma boundary, then encoded projection again; repeatable did not mean lossless",
      "Two workers reached about 28.85 s/frame on 48 GiB but created about 6.6 GiB of swap and were rejected by the quality/stability gate",
      "The partial-range manifest said stream copied even when PCM was correctly decoded, trimmed and losslessly re-encoded",
      "An uncalled pre-V21 DIR helper remained in source and created ambiguity for a future OFX port",
    ],
    discoveries: [
      "Official processed MTF and DIR chemistry are not two independent sharpness overlays that may simply be multiplied",
      "Removing a ProRes generation improves both speed and image integrity more safely than aggressive process parallelism",
      "The fused matrix keeps 99.9926% of native clipped 12-bit channel codes identical; the remainder are one-code rounding boundaries",
      "Scan median luma and highlight endpoints stay effectively fixed; the model correction is concentrated around formerly double-counted local edges",
      "The next major speedup belongs to a resident Metal/OpenFX graph with resource reuse and host-queue asynchrony—not more Python processes on 48 GiB",
    ],
    trialNote:
      "T002 stresses endpoints; T007 stresses water, grass and fine edges; T031 stresses dark neutral surfaces, warm fungi and green surroundings.",
  },
  V35: {
    year: "CURRENT BASELINE",
    title: "Do not change the film—change the computation: an auditable Production graph",
    summary:
      "V35 is not a new grade and does not rewrite the film. V34 colour, black, gamma, MTF, DIR, grain amplitude and grain spectrum are frozen. What changes is finite-site execution. Pixel, frame, record, speed layer and size class receive deterministic Philox4x32-10 identities; complete uint32 words are compared directly with a 2^32 fixed-point threshold derived from the float32 probability. Asynchronous Metal sampling overlaps CPU expectation filtering and the V31 colour boundary reuses memory. Twenty-four-frame, five-region colour, clipping, RGB high-frequency correlation, grain-energy and temporal-difference gates all pass while both masters render 23.65% faster than V34.",
    changes: [
      "Replaced the 24-bit inverse-CDF candidate with direct Philox-u32 Bernoulli trials; maximum observed probability representation error is 2.269e-10",
      "Asynchronous Metal finite-site submission exposes shared output memory and overlaps CPU expected-density filtering",
      "All 45 record/speed/size identities per frame are decoded, deduplicated and persisted in provenance",
      "Every result records source, algorithm, profile, LUT, bridge, command and stochastic-identity hashes",
      "The V31 final chroma adapter reuses full-frame buffers; the V34 photographic model and creative boundary stay frozen",
      "One native 5.7K 12-bit second for T002, T007 and T031, each with projection and period-scan masters",
    ],
    errors: [
      "Calling the first 24-bit inverse-CDF candidate exact-distribution was too absolute; statistical agreement is not infinite mathematical precision",
      "Same-process parallel observers reproduced a Numba workqueue SIGABRT, so V35 rejects observer_workers=2 before decoding",
      "Shared-memory observer subprocesses were byte-identical but memory-bandwidth pressure worsened about 10.94 seconds of serial work to roughly 25 seconds",
      "Single-Gaussian and full-residual convolution saved 0.65–0.9 s/frame but let ~5e-6 density reorder reach isolated 900–960/65535 projection-code differences through 2383 thresholds, so both are rejected",
      "The Python Metal bridge still owns process-level device/queue state; it is a research tool and cannot become the OFX boundary unchanged",
    ],
    discoveries: [
      "Quality-first validation must include rare threshold events and tails, not only mean colour or PSNR",
      "Direct uint32 Bernoulli is faster than floating inverse CDF in the 30-site native-frame microbenchmark",
      "Four formed-negative seeds give layer standard-deviation ratios 0.999918/1.000264/0.999852; NPS difference stays below ordinary reference seed variation",
      "Twenty-four frames across five regions show no systematic green, blue or magenta shift; scan and projection grain/temporal-energy departures stay below 0.3%",
      "OFX v1 should be full-frame, serial per instance, supportsTiles=false, with host-owned Metal queues and per-instance resource rings",
    ],
    trialNote:
      "T002 carries the complete five-region temporal gate; T007 stresses water, grass and near-zero hard black; T031 stresses dark neutral texture, warm fungi and green surroundings.",
  },
  V36: {
    year: "CURRENT BASELINE",
    title: "Match the frame before judging 35 mm grain and sharpness",
    summary:
      "V36 does not make the grain finer or hide it with extra softness. The audit found that V35 T007 and T031 began at frame 0, while V34 used the curated frame-276 and frame-132 windows. Source motion and texture were therefore presented as a film-model change. V36 locks camera, projection, scan, still and hover video to the same absolute source frames, then rechecks processed-stock MTF and 48 μm diffuse RMS granularity on one physical scale. At the correct T031 window, Production differs from V34 by only about 0.1% in high-frequency, temporal and grain-to-edge measures, so the film model stays frozen.",
    changes: [
      "Lock T002 0–23, T007 276–299 and T031 132–155 as absolute source windows",
      "Expose source frames in every web branch and fail mismatched comparisons",
      "Re-run Philox and spatial-kernel ablations at the correct T031 frame",
      "Add a joint physical-scale audit for 5279 MTF and 48 μm granularity",
      "Freeze V35 colour, black, gamma, MTF, DIR, grain amplitude and spectrum",
      "Use a shorter-GOP, higher-fidelity hover proxy so delivery encoding does not exaggerate grain boil",
    ],
    errors: [
      "The first V36 salt screen repeated the frame-0 mistake; all four-salt results were invalidated once the frame contract was found",
      "V35 recorded 24-frame trials but did not make absolute start frame a release-blocking comparison field",
      "MTF or 48 μm RMS alone cannot prove a 35 mm impression; both must share film geometry and observer scale",
    ],
    discoveries: [
      "The released V35 T031 frame is pixel-identical to a new frame-0 Production render, proving a segment-selection error rather than a hidden model change",
      "At frame 132, Philox/V34 median temporal-difference RMS is 1.00139 and grain-to-edge ratio is 1.00131",
      "Grains constitute the realized density image, but absolute density is not sharpness; MTF describes spatial density-modulation transfer",
      "Kodak E-58 makes noise frequency, negative and print granularity, both MTF stages and magnification joint determinants of visible graininess",
      "Quality first includes refusing to retune a correct film model to compensate for an invalid comparison",
    ],
    trialNote:
      "T002 is the unchanged-window control. T007 restores frame 276 for water and fine foliage; T031 restores frame 132 for dark bark, fungi and surrounding green.",
  },
  V37: {
    year: "CURRENT BASELINE",
    title: "Every frame is new film; the sampler no longer breathes as one field",
    summary:
      "V37 answers the overlay-like boil visible in the local QuickTime master. Successive film frames expose different pieces of emulsion, so silver-halide sites should remain independent from frame to frame. The error was not independence itself: V36 also rotated one whole-frame bilinear subpixel sampling phase every frame, adding a second numerical animation. V37 keeps all 45 new Philox emulsion identities per frame and changes only the integration kernel to a 30-degree stable-balanced phase. In the T031 ablation, whole-frame high-frequency variation in projection falls by about 60% and directional variation by about 71%, while the average orientation remains neutral. Colour, H-D, black, gamma, MTF, DIR, grain amplitude, grain size and both observers remain frozen.",
    changes: [
      "Continue to form independent silver-halide/dye-cloud sites on every frame; add no temporal smoothing, advection or frozen grain plate",
      "Replace whole-frame per-frame subpixel rotation with a 30-degree stable-balanced integration phase",
      "Screen native T031 candidates at 0, 30 and 90 degrees; reject the fixed bias at 0 and over-correction at 90",
      "Keep the 0.38-pixel radius, five size classes, three speed populations and three colour records unchanged",
      "Freeze every V36 colour, density, sharpness, black, gamma and observer parameter",
      "Render one native 5.7K 12-bit second for T002, T007 and T031 in projection and period-scan branches",
    ],
    errors: [
      "The initial V35 T031 tail audit compared frames 0–23 with V34 frames 132–155 and overstated extreme temporal differences; that conclusion is formally withdrawn",
      "A fixed 0-degree phase greatly stabilized temporal energy but left measurable horizontal/vertical preference and could not be released",
      "Reducing grain strength or correlating it over time would hide the symptom while violating frame-independent motion-picture emulsion",
    ],
    discoveries: [
      "Independent random fields do not require whole-frame statistics to breathe; a globally changing numerical integration kernel creates an extra animation",
      "The 30-degree balanced phase retains the V36 mean orientation on T031 while reducing projection high-pass CV to 0.400×",
      "Scanner aperture and scene structure mask part of the phase benefit, so projection and scan must be measured separately",
      "Organic grain motion comes from independent density formation under a stable imaging operator—not from moving one noise texture with the scene",
      "Continuous grain centres and density-domain 2383 formation remain valuable future research, but stay outside the baseline until they pass equivalent gates",
    ],
    trialNote:
      "T002 controls walls, shadows and fine texture. T007 verifies that water and foliage are not frozen or softened. T031 is the phase-selection scene for dark bark, fungi and surrounding green.",
  },
  V38: {
    year: "PREVIOUS BASELINE",
    title: "One observer light, encoded explicitly for each display target",
    summary:
      "V38 corrects the natural-still / dense-QuickTime split in V37. The completed projection and scan observers already produced display-linear light, but the release then applied the BT.709 camera OETF and allowed QuickTime, JPEG and the browser to invert or approximate it differently. Shadows, contrast and colour density diverged even though the film calculation was identical. V38 freezes the complete V37 image model and encodes one observer-linear result two ways: an inverse-BT.1886 gamma-2.4 professional Rec.709 master, and a 12-bit sRGB-transfer QuickTime companion for direct viewing on this Mac. JPEG and web motion derive only from the companion. P3 and HDR are not used as unmeasured saturation or brightness controls.",
    changes: [
      "Freeze the V37 negative, 2383, scan, colour, grain, MTF, DIR, black and gamma",
      "Define delivery input as completed display-linear Rec.709 observer light—not scene-linear camera exposure",
      "Encode the professional master with inverse BT.1886 gamma 2.4 in 12-bit Rec.709 ProRes 4444",
      "Add a separate 12-bit sRGB-transfer QuickTime companion that matches JPEG review in the Mac default display mode",
      "Generate JPEG and web motion from the same companion and the same representative frame",
      "Audit both files by decoding them back to one display-linear result",
    ],
    errors: [
      "Since V25, the release comments treated the BT.709 camera OETF and a BT.1886 reference display as a reversible pair even though they are not inverses",
      "The previous web gate allowed channel MAE up to 2.5% and median-luma error up to 1%, enough for a visible shadow mismatch to pass",
      "V37 JPEG used an exact BT.709 inverse before sRGB encoding while QuickTime applied Apple's video-gamma interpretation; the two paths never shared one ODT",
    ],
    discoveries: [
      "The still was closer to the intended observer-linear image; much of the video's extra density was a delivery/playback artifact rather than 5279 character",
      "This MacBook Pro's Liquid Retina XDR includes a dedicated HDTV Video BT.709–BT.1886 reference mode, which is more appropriate than a speculative P3 or HDR expansion",
      "A P3-capable panel cannot recover colour already bounded by the Rec.709 observer; changing container gamut would add no evidence",
      "Professional and QuickTime files may carry different code values, but must decode to the same display-linear light",
      "Release validation must cross the master, still, web proxy and an actual managed player—not only inspect file tags",
    ],
    trialNote:
      "T002 stresses toe and dark neutral texture. T007 holds water and green fine detail. T031 exposes the original natural-still / dense-video discrepancy.",
  },
  V39: {
    year: "WITHDRAWN EXPERIMENT",
    title: "Grain is not a residual on the image; density is the image",
    summary:
      "V39 resolves structural misplacements found in the complete research and code audit. V38 formed a finite-site negative but still applied MTF to a display positive, represented 2383 grain as a luminance ratio, normalized granularity after stochastic DIR, and clipped signed wide-gamut basis components before the three physical film records were formed. V39 applies 5279 MTF to processed negative density, constrains developed dye yield before stochastic DIR, and lets the scanner or 2383 observe that single realized density. 2383 MTF and three-record dye clouds are formed in Status-A density with no display grain operation. V38 colour, H-D, black, gamma and dual delivery remain frozen. This is not a prettier grade; it puts image structure back in its measured domains.",
    changes: [
      "Move processed 5279 MTF from display-linear RGB into negative record density",
      "Apply the published 48 µm RMS constraint to developed dye yield before stochastic DIR/interimage transport",
      "Move 2383 MTF and independent three-record finite dye clouds into Status-A print density",
      "Remove the final display-luminance-ratio 2383 grain operation",
      "Preserve signed BT.2020-to-film basis components and clamp once after physical record exposure is formed",
      "Make the active profile own the 0.38-pixel phase radius and projection opponent crossover",
      "Make V39→V38 switching restore every Archive-domain setting explicitly",
      "Remove duplicate analytical projection work and share dual-observer intermediates with zero pixel error",
      "Derive the sRGB viewing copy from the encoded BT.1886 master and use ProRes 4444 XQ to retain V39's fine density structure",
    ],
    errors: [
      "V38 applied the published processed-negative MTF to an already formed display positive",
      "V38 scaled the combined residual after stochastic DIR, so chemistry never saw the calibrated developed event",
      "V38's fine 2383 term was a post-projection luminance ratio and remained structurally overlay-like",
      "V38 clipped signed wide-gamut basis values before the film-record sensitivity matrix",
      "A pointwise 193³ negative-to-output cache cannot represent a spatially formed 2383 density image",
      "Independently compressing BT.1886 and sRGB copies from floating-point light ceased to be transparent once V39 carried finer density structure",
    ],
    discoveries: [
      "Density is the image variable, but density magnitude is not sharpness; MTF describes the spatial transfer of density modulation",
      "MTF and granularity must share one physical geometry and density chain while remaining separately measurable properties",
      "Moving the RMS constraint before chemistry fixes layer order but cannot reveal Kodak's unpublished coating recipe",
      "Public 2383 material does not identify exposure-conditioned record granularity, so print grain remains subordinate and explicitly bounded",
      "The released projection is still a normal-process Rec.709 monitor proof with a period-scan low-frequency colour boundary; physical projection remains available but is not mislabelled as a theatre measurement",
      "Quality-first spatial 2383 formation moves the bottleneck from grain sampling to the accurate analytical observer",
      "Both transfers must share the delivered master's compression structure; the master-derived XQ companion limits the worst per-channel mean light error to 0.001092",
    ],
    trialNote:
      "T002 tests toe and low-chroma texture. T007 tests water, grass and high-frequency greens. T031 tests dark organic texture and the full density-to-print path.",
  },
  V40: {
    year: "CURRENT BASELINE",
    title: "Accurate grain constrains energy, covariance and extreme tails",
    summary:
      "V40 withdraws three unsupported V39 inferences: treating Kodak's processed 48 µm RMS measurement as a pre-DIR source-layer target, passing marginal record RMS to the observer without the validated opponent-colour integration, and inventing independent RGB/record Poisson grain for 2383 without stock-specific covariance or NPS evidence. V40 preserves density-domain 5279/2383 MTF and the accepted colour, black and gamma. It restores the RMS constraint to the published post-process boundary, restores opponent integration inside both observers, and prevents the final V31 adapter from reintroducing the high-frequency opponent residual. Intrinsic stochastic 2383 grain remains withheld until it can be measured. This is not chroma denoising; it refuses to create colour degrees of freedom that the evidence does not identify.",
    changes: [
      "Restore the 48 µm granularity constraint to Kodak's measured post-process density boundary",
      "Restore high-frequency opponent-colour integration inside the scan and 2383 observers",
      "Stop the final V31 adapter from re-adding an already-integrated high-frequency opponent residual",
      "Withdraw independent stochastic 2383 record populations until covariance/NPS evidence exists",
      "Withdraw V39's underidentified signed intermediate film-RGB cancellation",
      "Gate opponent energy and isolated 3×3 primary-colour impulses on every native delivered frame",
      "Make the first picture authority 12-bit ProRes 4444 XQ, then derive every viewing and website image from it",
      "Add FSD finite-site density and a deterministic no-grain baseline as controlled comparisons without changing physical V40",
      "Withdraw FSD's random gamut-boundary chroma scaling and reform its density in the post-observer signal domain with a fixed opponent field",
      "Audit the Apple-standard RAW input with the T003 DKC-Pro chart; its warm as-shot evidence does not justify a global magenta trim or automatic white balance",
    ],
    errors: [
      "V39 matched each record's marginal RMS but did not constrain cross-record covariance or distribution tails",
      "Kodak's 48 µm number describes processed film and cannot uniquely invert pre-DIR speed-layer yields",
      "The public 2383 material supplies no exposure-conditioned three-record grain covariance or NPS; independent RGB Poisson was false precision",
      "V39's signed intermediate film basis introduced underidentified channel cancellation in dark green regions",
      "The final V31 adapter was re-adding high-frequency opponent colour after the observer had already integrated it",
      "An 8-bit JPEG representative frame can smooth colour impulses and cannot substitute for a 12-bit movie gate",
    ],
    discoveries: [
      "Grain identity is not only RMS and size: record covariance, skew, extreme tails and observer integration decide whether it reads as silver or digital chroma noise",
      "Density remains the image variable, but a published posterior granularity measurement cannot be moved arbitrarily earlier in the chemistry",
      "Without 2383 stochastic statistics, retaining 5279 structure transferred by print MTF is more accurate than inventing print grain",
      "Native-resolution every-frame tail audits catch sparse failures that representative stills and downscaled proxies miss",
      "The local Silver Efex engine confirms G=inverse-CDF(Binomial(N,p),u)/N followed by Y'=(1-alpha)Y+alpha G, not display-space additive noise",
      "Every Silver Efex B&W stock owns a separate measured 1000-square morphology; this supports stock-specific modelling but cannot become 5279 three-record data",
      "FSD's first linear-RGB colour transport failed the native dark-tail gate; the corrected post-observer signal-domain definition holds opponent colour fixed and removes the sparse primary impulses without blur or desaturation",
      "Without copying a stock texture, FSD at N=176 and sigma 0.597 px matches physical V40's calibration-frame luma RMS, high-pass energy and spatial correlation while retaining much lower opponent residual by design",
      "DKC-Pro rows are not equal height and a printed title strip precedes patches 7–12; the first chroma sampling was withdrawn, and the corrected grid leaves an input matrix as a plausible boundary that still needs controlled-light validation",
      "A synthetic D65 gray ramp stays below 0.00018 maximum delta u-prime/v-prime through both observers, rejecting a neutral-green crossover; a constant warm ramp produces 0.00253/0.00220 exposure-dependent crossover whose true 5279 magnitude remains unmeasured",
      "T003 neutral patches 2–5 average R/G=1.172 and B/G=0.748, rejecting a fixed shared green-decode hypothesis; real daylight still cannot identify a new white balance, black offset or camera matrix",
    ],
    trialNote:
      "T002 stresses dark low-chroma tails. T007 tests water, green fine detail and edge integration. T031 tests organic shadow texture through both observers.",
  },
  V41: {
    year: "CURRENT BASELINE",
    title: "Let the chart reveal direction without turning one shoot into a grade",
    summary:
      "V41 uses T003 to estimate the direction of the remaining input-chroma residual, then treats the closer, mildly defocused T005 as a true holdout. Both clips repeat the same under-chroma and hue-error direction across synthetic and natural colours, so the boundary is probably real. But both were captured outdoors at 5500 K under directional light, which is not enough to characterize the GH7. V41 therefore applies only 12.5% of the fitted correction, preserves scene luminance and the neutral axis, and leaves white balance, exposure, black, contrast and gamma untouched. It also replaces V40's hard intermediate-basis clip with record-safe signed transport: signed values survive only when all three 5279 record exposures remain non-negative; unsafe pixels fall back to V40.",
    changes: [
      "Add the closer T005 chart as an independent holdout that was never used to fit the transform",
      "Estimate a cross-group residual in Bradford-adapted D50 chroma while restoring exact D65 scene luminance",
      "Reject the visibly excessive 100% result and the still-too-large 25% result; retain a conservative 12.5% step",
      "Reduce median hue error in synthetic and natural groups on both T003 and T005",
      "Improve natural-colour chroma error on both clips",
      "Use non-negative 5279 record exposure as the safety condition for signed intermediate transport",
      "Freeze all V40 grain, DIR, MTF, 2383, scan, black, contrast and gamma parameters",
      "Feed physical 5279, FSD and deterministic controls from the same V41 colour boundary",
    ],
    errors: [
      "One outdoor directional-light chart cannot identify a complete camera matrix, illuminant SPD or stock-specific interimage response",
      "The first 100% matrix visibly over-corrected foliage and yellow patches",
      "The 25% candidate passed chart gates but still raised final 2383 median chroma by about 15%, beyond the evidence",
      "T005 defocus is acceptable for patch medians, but local glare and gradients limit individual-patch precision",
      "V41 remains a reversible colour-boundary experiment, not a final GH7 characterization before uniform D65 and tungsten controls",
    ],
    discoveries: [
      "A defocused chart can still witness large-patch statistics when sampling stays away from edges and within-patch dispersion is reported",
      "Repeating the direction on a disjoint clip is more informative than increasing fit order on one chart",
      "A 100% correction in chart space can be amplified by negative and 2383 nonlinearities, so the final formed image needs its own gate",
      "A 12.5% step lowers hue error in both groups on both clips while keeping input luminance change below 1e-5",
      "V40's non-negative intermediate basis was not a RAW clip; the physical safety condition is non-negative exposure in the combined records",
      "FSD and physical 5279 should share a colour boundary while remaining distinct density-formation hypotheses",
    ],
    trialNote:
      "T002 tests dark low-chroma tails and black stability. T007 tests water, green fine detail, saturation and 35 mm sharpness. T031 tests organic shadow texture through both observers.",
  },
  V42: {
    year: "CURRENT BASELINE",
    title: "Make the engine actively defend the conclusions of the research",
    summary:
      "V42 is not a new grade and does not claim a new Kodak measurement. It freezes V41 colour, density, grain, DIR, MTF, black, gamma and both observers, then turns the accepted V37–V41 conclusions into startup gates the engine must pass. The validated Philox-u32 Bernoulli Metal graph is now the Production default. Archive CPU remains a reproducible reference, but a different stochastic implementation is no longer described as the same grain realization. Delivery has one picture authority: encode the 12-bit BT.1886 master first, then derive the sRGB QuickTime companion and still from that delivered file.",
    changes: [
      "Name the explicit engine V42 so a software 'V2' cannot be confused with the image-version history",
      "Assert V37 stable integration, V40 colour-grain repair and V41 colour/record boundaries at runtime",
      "Make the validated Philox-u32 Bernoulli Metal graph the default Production execution",
      "Retain Archive CPU and Reference NumPy as research references without demanding particle-for-particle identity",
      "Freeze +0.45 stop, grain 1.0, oversample 1 and salt 0 for the baseline; any override must be marked experimental",
      "Write only the BT.1886 professional picture during formation and derive sRGB/JPEG from the encoded master",
      "Correct the recovery record: byte identity proves the Archive refactor, not identical Metal and NumPy emulsions",
      "Record the V41 engine-directory loss explicitly and protect 214 authored source, test and research files with a SHA-256 inventory checked by GitHub CI",
    ],
    errors: [
      "Before recovery, the complete engine lived only in an unversioned local experiment directory; its disappearance required reconstructing 199 files from 895 successful edit records",
      "No surviving evidence attributes the deletion trigger to Claude, the Python crash, the macOS watchdog event or a cleanup command; the trigger remains unknown",
      "The public hero currently retains the matched V41 Production witness; the formal V42 one-second three-source rerender is not yet published",
      "Executable gates prevent known research drift but cannot replace missing 5279 NPS, coating or scanner measurements",
      "V41's 12.5% colour residual remains reversible outdoor-chart evidence; the V42 name does not promote it to a complete GH7 characterization",
    ],
    discoveries: [
      "Version correctness should be defined by formation equations, statistical contracts and delivery authority—not one fortunate random pixel hash",
      "Archive and Production may form different emulsion instances while obeying the same H-D, 48 µm RMS, NPS and temporal-independence boundaries",
      "Runtime research assertions prevent profile leakage or optimization code from silently rewriting the image model",
      "Deriving every viewing file from the delivered 12-bit master structurally prevents the still and movie from becoming different pictures",
      "The established failure cause was a single unversioned source copy; the exact deletion mechanism cannot be reconstructed from the surviving logs",
    ],
    trialNote:
      "V42 currently inherits the matched V41 visual witnesses because the image model is frozen; new media will replace them only after native one-second validation.",
  },
  V43H: {
    year: "HYPOTHESIS EDITION",
    title: "Isolate the most likely unmeasured pieces as one reversible experiment",
    summary:
      "V43H asks a bounded question: what might 5279 look like if the most probable—but still unmeasured—negative grain spectrum, period Spirit observer and subordinate 2383 texture were completed? V42 colour, H-D, DIR, MTF, 48 µm RMS, black, gamma and RAW interpretation remain frozen. An isolated profile narrows the 35 mm cloud spectrum, moves one quarter toward a documented-family Spirit candidate and tests weak, spectrally neutral common-density 2383 texture. Projection and scan share one realized V43H negative; FSD remains independent; Panasonic V-709 is only a camera witness.",
    changes: [
      "Create a V43H-only profile with explicit hypothesis_not_measurement provenance",
      "Keep official 48 µm RMS amplitude while narrowing and densifying the candidate 35 mm spatial spectrum",
      "Move the period scanner only 25% toward a candidate bounded by DFT architecture and Kodak's generic telecine plot",
      "Test weak, spectrally neutral common-density 2383 texture, estimate its amplitude from the three-record mean, and prohibit independent RGB print impulses",
      "Produce projection and scan from the same V43H negative realization and reuse one spectral integration for the deterministic observer",
      "Keep FSD as an independent finite-density route rather than promoting it into physical 5279",
      "Render all three requested sources as projection, scan, FSD and official Panasonic V-709 camera witness",
      "Write native 5.7K 12-bit XQ masters first, then derive sRGB companions, stills and hover media from the encoded files",
    ],
    errors: [
      "V43H's grain NPS is not a Kodak measurement; 48 µm RMS cannot uniquely identify a spatial spectrum",
      "The Spirit centres and bandwidths are not disclosed DFT responses—only a quarter-step toward a synthetic candidate",
      "Public 2383 data do not identify three-record grain covariance or exposure-conditioned NPS, so the common-mode term remains subordinate",
      "The outdoor T003/T005 charts do not authorize a new white balance, complete GH7 matrix or global saturation correction",
      "The first discrete-spike gate mistook a Poisson expected count for a hard maximum; 17 real green-edge candidates on T007 failed only because ceil(14.7) was 15",
      "Passing delivery gates proves internal consistency, not that predicted parameters have become 5279 facts",
    ],
    discoveries: [
      "V39's broken-television colour noise came directly from unidentified independent RGB print-Poisson tails; common density does not create isolated primary impulses",
      "One observer integration can return both the physical realization and deterministic mean, so FSD does not require a second 193³ spectral graph",
      "The matched T032 V42→V43H mean-channel change remains below 0.001, preserving a predictive difference without adding a grade",
      "Grain fineness can change while official 48 µm RMS stays fixed because aperture amplitude and spatial NPS are different constraints",
      "A stochastic event rate needs a statistical acceptance bound: 432 tests now use a Bonferroni one-percent family-wise false-rejection rate, while V39's thousands-per-million failure remains orders of magnitude outside it",
      "The central product boundary of a Hypothesis Edition is reversibility: every unmeasured degree of freedom must remain independently removable",
    ],
    trialNote:
      "T032 tests a rainy cyan-green scene, dark columns and low contrast; T007 tests water, green fine detail, local saturation and the sharpness/grain relationship. Every example includes projection, period scan, independent FSD and the unfilmed Panasonic V-709 witness.",
  },
  V44: {
    year: "OBSERVER INTEGRITY",
    title: "Let the negative, observer and display scale carry only their own physical facts",
    summary:
      "V44 is not another guessed grain profile. It answers the cheap coarse texture seen during native 5.7K playback. The unmeasured V43H NPS, Spirit and 2383-grain candidates are withdrawn; the accepted V42 negative returns. A rejected V44 candidate also proves that fully direct analytical projection colour produces unsafe dark opponent tails, so the validated V31 normal-process colour boundary remains instead of inventing a stronger projection difference. Native 5.7K masters remain untouched, while review derives display light from the encoded master, integrates it over actual review pixels and only then applies sRGB. The still decodes the final movie's same frame.",
    changes: [
      "Withdraw all three unmeasured V43H candidates and restore V42 negative morphology and the accepted period scanner",
      "Retain the validated V31 normal-process monitor boundary: 2383 lightness/texture with low-frequency scan-referenced dye chroma",
      "Keep stochastic 2383 grain at zero until a measured three-record NPS/covariance exists",
      "Preserve the native 5760×4320 12-bit XQ master instead of blurring it to solve playback scaling",
      "Add a 1920 review path: BT.1886 decode, linear-light pixel-area integration, then sRGB encoding",
      "Derive the still from the same frame of the final encoded movie, removing the pre/post-encode split authority",
      "Separate theatrical-print evidence, telecine/Blu-ray transfer and web display as three explicit evidence boundaries",
    ],
    errors: [
      "V43H constrained a guessed NPS with official 48 µm RMS, but one aperture integral cannot identify a spatial spectrum",
      "V43H added common-mode 2383 texture without public three-record statistics; ablation shows it explains only about 0.33% of projection high-frequency energy",
      "The first V44 candidate disabled V31 completely; across 24 frames its projection dark opponent p99.99 reached 0.04882 with about 127 isolated >0.06 impulses per million dark pixels, so the candidate was rejected",
      "A player using sharp resize on native 5.7K stochastic structure can fold energy above display Nyquist into coarse false texture",
      "V44 is still not a measured closed loop of 5279 capture, same-batch 2383 and a characterized scanner; it cannot claim absolute reproduction",
    ],
    discoveries: [
      "The coarse result was mainly neither Wavefront error nor the new print grain; image structure and playback scaling acted together",
      "On the matched frame, Lanczos review raises projection high-frequency energy to 1.71× and scan to 1.21× relative to linear-light area integration",
      "The defensible fix is to retain the native master and provide a scale-defined review derivative—not arbitrarily soften the film model",
      "A theatrical print, telecine/Blu-ray transfer and modern reference still have different light sources, white points, resolutions and finishing decisions; none is the other's colour truth",
      "Current evidence supports a scan-referenced normal-process projection monitor; similar branch colour is a declared limitation and is more accurate than an invented theatrical colour difference",
      "Projector flicker and development streakiness remain future measurable modules, not baseline effects added merely because they read as filmic",
    ],
    trialNote:
      "V44 first validates T020 at native 5.7K for one second. FSD and the official Panasonic V-709 camera witness remain independent controls, not V44 film-formation terms.",
  },
  V45: {
    year: "OFFICIAL OBSERVER",
    title: "Let 2383 be seen through a standard observer—not guessed through an approximation",
    summary:
      "V45 is a single-variable spectral measurement revision. Earlier versions sampled an analytical CIE 1931 approximation directly on the Kodak 2383 graph's 20 nm nodes. V45 uses the official CIE 1931 2-degree 1 nm table, linearly interpolates the same 2383 dye-density and xenon graph samples, and integrates them from 380 to 780 nm with explicit trapezoidal endpoint weights. The 5279 negative, H-D curves, three speed layers, DIR, MTF, grain, black, contrast, gamma, scanner and delivery are frozen. White changes by less than 4×10⁻⁷, so this is not a global white-balance move; only specific dye combinations are observed more accurately.",
    changes: [
      "Add and integrity-check the official CIE 1931 2-degree 1 nm observer table",
      "Linearly interpolate Kodak's plotted 2383 dye density and xenon relative SPD from 20 nm to the 1 nm axis",
      "Replace the analytical 20 nm approximation with trapezoidal integration over 380–780 nm",
      "Rebuild and hash-lock a separate V45 193³ monitor lattice so an old runtime cache cannot be reused silently",
      "Freeze V44 5279 formation, DIR, MTF, grain, scan, black, contrast, gamma and delivery",
      "Validate T020, T032 and T007 for 24 native-resolution frames each; decode each web still from its final movie",
      "Add a same-negative observer ablation, six-movie motion-colour gates and a two-transfer delivery-light consistency audit",
    ],
    errors: [
      "V44 and earlier used an analytical CIE approximation rather than the CIE's published one-nanometre standard-observer table",
      "Changing build_2383_projection_lut while still loading V30's 193³ cache would create a completely unchanged false upgrade; V45 binds profile and lattice hash",
      "One-nanometre integration cannot invent unpublished Kodak measurements: the source 2383 dye and xenon graphs remain 20 nm plots",
      "V45 still lacks a closed loop of same-batch 5279, 2383, measured illuminant and characterized scanner, so it is not an absolute reproduction claim",
    ],
    discoveries: [
      "The official one-nanometre observer leaves the dye-free white almost unchanged while producing measurable changes for specific dye mixtures",
      "Across the complete 25³ spectral cube, linear-RGB RMS versus the old observer is 0.00456917 and maximum absolute node change is 0.0398455",
      "After LAD, neutral-scale and normal-process monitor boundaries, the complete 193³ output-lattice RMS is 0.000215819 with mean RGB shift near 10⁻⁶ and a localized maximum of 0.03810",
      "On one already-formed T020 negative, the scan remains bit-identical and projection linear-RGB RMS is only 0.000037904, confirming an observer correction rather than a grade",
      "Peak-normalizing a single 2383 dye does not automatically increase accuracy; Status-A inversion cancels much arbitrary scale, making spectral shape more important than peak height",
      "Spectral sampling, runtime lattice and delivered image must be one versioned evidence object",
    ],
    trialNote:
      "T020 tests mixed foliage and dark bark; T032 tests rainy cyan-green low contrast; T007 tests water, green detail and local saturation. Each case includes projection, frozen scan, independent FSD and the Panasonic V-709 camera witness.",
  },
  V46: {
    year: "CERTIFIED SPECTRAL INVERSE",
    title: "Keep finite silver-halide events and spectral density inside their measurable boundaries",
    summary:
      "V46 is the first complete consolidation after the source-loss rebuild and a genuine numerical image correction. The former model held target RMS beyond Kodak's published granularity support while finite-site activation probability approached zero, creating very rare but enormous dye-density impulses. V46 holds the complete stochastic state at the measured endpoint. It also replaces the clipped iterative Status-M inverse with an exact nonnegative active-set solution. A 129-cubed base atlas plus local exact 5-cubed microbricks bounds maximum real-frame printer-density error to 0.0005094 D. Reliable findings from legacy internal V46–V86 studies are absorbed here, while those labels remain immutable experiment IDs rather than being rewritten as public releases.",
    changes: [
      "Hold the complete stochastic state outside Kodak's measured granularity support, eliminating the catastrophic tail produced as activation probability approached zero",
      "Replace the clipped projected Status-M spectral inverse with an exact nonnegative active-set/KKT solution",
      "Build a power-2 129-cubed base atlas and load exact 5-cubed microbricks only at active-set boundaries and interpolation-disagreement regions",
      "Discover cache demand from every real pixel before/after MTF and in mean/formed density for T020, T032 and T007; all 25,333 final risk cells are covered",
      "Compile the adaptive observer as a parallel CPU kernel with fast-math disabled and bit-identical NumPy-reference output",
      "Share one negative printer-density observation between scan and projection, removing duplicate spectral-inverse work",
      "Keep evidence-minimal identity record formation; do not invent RGB cross-covariance from three 48-micrometre marginal curves",
      "Render each scene as a 24-frame 5760×4320 12-bit ProRes 4444 master with a scale-honest web witness",
    ],
    errors: [
      "The old model held fixed RMS outside published exposure support while activation probability tended to zero, causing calibration amplitude to diverge into rare broken-TV-like dye events",
      "The former Status-M inverse clipped a projected iteration and did not guarantee the KKT optimum; worst shadow error had reached about 0.01399 D",
      "A fixed 27-probe cell test missed active-set boundaries reached by real pixels; V46 uses the exact runtime predicate on complete pipeline states",
      "Presenting legacy V46–V86 audits as dozens of visual releases confused research evidence with rendered releases; their historical IDs remain but the site consolidates them thematically",
      "V46 still lacks a closed measured loop of same-batch 5279, same-batch 2383, measured printer light and a characterized scanner, so it is not an absolute colour-reproduction claim",
    ],
    discoveries: [
      "A granularity endpoint must constrain the complete finite-event state, not only macro RMS; otherwise a mathematically matched RMS can hide an unphysical microscopic tail",
      "Sparse synthetic probes cannot represent real-frame risk; the final cache must cover pre/post-MTF and mean/formed density states",
      "Exact active-set structure is locally sparse, favouring a base atlas plus risk microbricks over an expensive exact solve at every pixel",
      "One negative printer-density result can derive both scan coordinates and projection input; branch differences belong after the shared negative",
      "V70–V85 show that shared record events trade opponent grain for stronger luma grain rather than removing noise for free; identity record formation is the honest boundary without cross-spectral measurements",
      "V46 improves numerical correctness and evidence ownership. It adds no creative grade and does not exaggerate hue merely to make projection and scan look different",
    ],
    trialNote:
      "T020 tests mixed foliage and bark; T032 tests rainy cyan-green shadows and low contrast; T007 tests water, fine green detail and local saturation. Projection and scan are newly rendered from the same V46 negative, while FSD and Panasonic V-709 remain independent controls.",
  },
  V47: {
    year: "SILVER-HALIDE MORPHOLOGY",
    title: "Beyond grain strength: reconstruct complex, heterogeneous silver-halide organization",
    summary:
      "V47 advances the Silver Efex evidence from an architectural clue to a controlled measurement. A 2048-square 16-bit flat-field probe was exported through the locally installed Nik 8 Kodak Tri-X 400 model, measuring RMS, spatial correlation, skew and excess kurtosis across sixteen tones. The first candidate matched strength and correlation length but was stopped mid-render because its near-zero kurtosis was still too orderly. The accepted SHM comparator uses multiscale populations, a slow occupancy field, asymmetric clusters/voids and a thick-tail Hermite population. It remains an independent same-class comparator: it does not replace V46's three-record 5279 or claim that a monochrome still product measures colour motion-picture film.",
    changes: [
      "Measure Tri-X 400 RMS, lag-1, skew and kurtosis across sixteen tones through a controlled local Nik 8 export",
      "Replace FSD's single correlated Gaussian copula with three independently seeded spatial populations",
      "Add a slow occupancy field that varies fine/coarse population balance without creating a low-frequency brightness cloud",
      "Use a second Hermite population for asymmetric clusters and voids and a third Hermite population for measured thick tails",
      "Refit finite-site strength to N=1250 and reject the N=176 candidate that was about twice too strong and read closer to 16 mm",
      "Form density through an inverse-binomial CDF at every tone instead of adding coloured noise to finished RGB",
      "Hold the deterministic opponent field fixed and constrain only scalar-density travel at gamut boundaries",
      "Renew organization per frame without translating or looping a grain plate",
    ],
    errors: [
      "The first SHM candidate audited only the latent field against a broad stock envelope; formed-density kurtosis was slightly negative and still resembled orderly correlated noise",
      "The N=176 prototype measured about 0.0286 RMS on the real frame—roughly twice the controlled Tri-X result and liable to read as 8/16 mm",
      "Silver Efex is a monochrome still-image product and cannot identify 5279 cross-record covariance, pre-DIR layer randomness or motion-picture temporal law",
      "The controlled export covers only 2048 square at Grain Size 1; automatic resolution/format scaling remains unmeasured",
      "SHM operates after V46's deterministic observer, so it is a morphology experiment rather than a replacement physical-negative branch",
    ],
    discoveries: [
      "Equal RMS and grain radius do not guarantee silver-halide character; positive skew, positive excess kurtosis and local spectral variation govern rare clusters and voids",
      "Controlled Tri-X lag-1 stays similar from shadows to highlights; tone mainly changes participation amplitude rather than manufacturing dramatic grain-size breathing",
      "Varying population balance at constant local mean creates heterogeneous organization without an overlay-like mottle",
      "The older FSD is genuinely a different route: it tests finite-density formation, while SHM additionally tests stock-owned complex spatial morphology",
      "The earlier impression that N=176 read as 16 mm was not merely subjective; the controlled black-box test quantifies it",
      "The honest current boundary is to retain physical V46 and keep SHM as a removable comparator on the same deterministic observers",
    ],
  },
  V48: {
    year: "FIRST-PRINCIPLES BASELINE",
    title: "Let 2383 own its colour: separate mean image from stochastic delta",
    summary: "V48 adds no new style and does not continue the Silver Efex route. It corrects one V46 observer-ownership error: projection borrowed scan low-frequency opponent colour to contain speckles caused by unmeasured three-record covariance. The direct 5279-to-2383-to-xenon/CIE chain now owns the projection mean; the old safety transform contributes only the formed-minus-mean stochastic delta. Negative formation, grain, H-D, 48-micrometre RMS, MTF, 2383 and scan remain frozen.",
    changes: ["Direct 2383 observer owns the projection mean", "V46 containment acts only on the formed-minus-mean stochastic delta", "Scan and the complete negative remain unchanged", "One second of paired native 5.7K 12-bit ProRes 4444 XQ"],
    errors: ["V46 wrote scan opponent colour into the projection mean", "Removing all management would reopen speckles because the 5279 cross-spectrum remains unmeasured", "Native NPS, speed-population recipe and exact DIR topology remain unknown"],
    discoveries: ["Observer differences need no exaggerated hue", "A safety filter that changes the mean has become a grade", "Same-negative V48−V46 linear-RGB MAE is only 0.002200"],
  },
  V49: {
    year: "DENSITY-DOMAIN CORRECTION",
    title: "Do not suppress chroma noise—prevent the wrong RGB noise from forming",
    summary: "V49 fixes the remaining ownership error in V48. V48 gave 2383 ownership of deterministic colour but still added a formed-minus-mean residual from another observer graph in display RGB, producing lifted-sensor-like red, green and blue points in shadows. Kodak publishes only each record's marginal 48-micrometre Status-M RMS, not their cross-covariance. V49 therefore does not invent a coloured joint law: it publishes one symmetric common-density component while the image is still a negative and lets both material observers see that same formed negative directly.",
    changes: ["Removed display-RGB formed-minus-mean stochastic reinjection", "Randomness completes inside the 5279 negative before both observers", "Scaled the symmetric normalized common component by the smallest local Kodak marginal RMS", "Raised web motion to 1920x1440 CRF 11 and added opponent-error gates against the still"],
    errors: ["V48's stochastic residual and deterministic mean belonged to different observer graphs", "The public granularity curves do not identify the real 5279 cross-record spectrum", "V49 common density is a conservative hypothesis boundary, not a claim of perfectly registered real record events"],
    discoveries: ["The coloured-point defect was an image-formation ownership error, not merely excessive grain", "Projection opponent RMS falls 62.8% while luma activity remains nearly unchanged", "Unmeasured opponent variance should remain explicit uncertainty rather than being silently decided by an RGB safety filter"],
  },
};

export function translateBranchLabel(label: string) {
  return label
    .replace(/T020 · V49同一形成负片 → 2383氙灯 \/ CIE观察/g, "T020 · same V49 formed negative → 2383 xenon / CIE observer")
    .replace(/T020 · V49同一形成负片 → Cineon \/ Scan-DI观察/g, "T020 · same V49 formed negative → Cineon / Scan-DI observer")
    .replace(/T020 · 5279 → 2383直接确定性颜色 \+ 受控随机差值/g, "T020 · direct 5279 → 2383 deterministic colour + managed stochastic delta")
    .replace(/T020 · 同一V48负片 → Cineon \/ Scan-DI观察/g, "T020 · same V48 negative → Cineon / Scan-DI observer")
    .replace(/V46确定性2383观察 → V47 SHM有限银盐组织/g, "V46 deterministic 2383 observer → V47 SHM finite silver-halide organization")
    .replace(/V46确定性Scan\/DI观察 → V47 SHM有限银盐组织/g, "V46 deterministic scan/DI observer → V47 SHM finite silver-halide organization")
    .replace(/旧FSD单Gaussian-copula有限密度对照/g, "legacy FSD single-Gaussian-copula finite-density control")
    .replace(/Panasonic官方V-709相机见证 · 无胶片管线/g, "official Panasonic V-709 camera witness · no film pipeline")
    .replace(/V46端点稳定5279/g, "V46 endpoint-stable 5279")
    .replace(/V46同一负片/g, "V46 same negative")
    .replace(/同一V46负片/g, "same V46 negative")
    .replace(/Period 2K \/ Cineon扫描/g, "Period 2K / Cineon scan")
    .replace(/2383氙灯放映/g, "2383 xenon projection")
    .replace(/2383放映/g, "2383 projection")
    .replace(/独立FSD有限密度对照 · 不并入V46/g, "independent FSD finite-density control · not part of V46")
    .replace(/Panasonic官方V-709原始观察 · 无胶片管线/g, "official Panasonic V-709 original camera witness · no film pipeline")
    .replace(/Panasonic官方V-709原图/g, "official Panasonic V-709 camera original")
    .replace(/FSD有限密度/g, "FSD finite-site density")
    .replace(/V46端点稳定/g, "V46 endpoint-stable ")
    .replace(/V46经认证光谱逆解/g, "V46 certified spectral inverse")
    .replace(/同一V46负片/g, "same V46 negative")
    .replace(/原始观察 · 无胶片管线/g, "original camera witness · no film pipeline")
    .replace(/原图/g, "camera original")
    .replace(/同一负片/g, "same negative")
    .replace(/完整三记录5279乳剂形成/g, "Full three-record 5279 emulsion formation")
    .replace(/逆二项密度形成的独立对照/g, "Independent inverse-binomial density control")
    .replace(/随机密度关闭；颜色、MTF与观察器保持/g, "Stochastic density disabled; colour, MTF and observer retained")
    .replace(/sRGB本机观看链/g, "sRGB Mac viewing chain")
    .replace(/V38/g, "V38")
    .replace(/V37稳定乳剂/g, "V37 stable emulsion")
    .replace(/2383影院观察/g, "2383 cinema observer")
    .replace(/As Shot见证/g, "As Shot witness")
    .replace(/（与V26相同）/g, "(same as V26)")
    .replace(/中性灰阶约束的/g, "neutral-scale-constrained ")
    .replace(
      /当时尚未拆分两条观看链；这里保留同一实验主图/g,
      "The viewing branches had not yet been separated; both retain the same experiment image",
    )
    .replace(/早期正片解释/g, "Early print interpretation")
    .replace(/负片扫描解释/g, "Negative scan interpretation")
    .replace(/扫描分支沿用/g, "Scan branch retained from ")
    .replace(/放映分支沿用/g, "Projection branch retained from ")
    .replace(/修正后的/g, "Corrected ")
    .replace(/修正遮罩后的/g, "After mask correction · ")
    .replace(/氙灯放映/g, "xenon projection")
    .replace(
      /影院观察的Rec\.709监看/g,
      "Rec.709 monitor view of cinema observation",
    )
    .replace(/蓝光/g, "Blu-ray")
    .replace(/放映/g, "projection")
    .replace(/扫描/g, "scan")
    .replace(/2Kscan/g, "2K scan")
    .replace(/相机原图/g, "camera baseline")
    .replace(/相机基线/g, "camera baseline")
    .replace(/Panasonic官方/g, "official Panasonic ")
    .replace(/不进入胶片管线/g, "no film pipeline")
    .replace(/5279负片/g, "5279 negative")
    .replace(
      /影院观察Rec\.709监看/g,
      "Rec.709 monitor view of cinema observation",
    )
    .replace(/沿用/g, "retained")
    .replace(/多层颗粒/g, "multilayer grain · ")
    .replace(/有机颗粒/g, "organic grain · ");
}
