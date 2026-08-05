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
    year: "CURRENT BASELINE",
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
};

export function translateBranchLabel(label: string) {
  return label
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
