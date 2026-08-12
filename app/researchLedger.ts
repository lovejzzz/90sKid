export type ResearchLedgerEntry = {
  version: string;
  status: "image" | "audit" | "rejected" | "boundary";
  titleZh: string;
  titleEn: string;
  summaryZh: string;
  summaryEn: string;
};

export type ResearchChapter = {
  id: string;
  titleZh: string;
  titleEn: string;
  summaryZh: string;
  summaryEn: string;
  conclusionZh: string;
  conclusionEn: string;
  evidenceIds: string[];
};

export const researchLedger: ResearchLedgerEntry[] = [
  { version: "V46", status: "audit", titleZh: "证据重新核对", titleEn: "Evidence reconciliation", summaryZh: "重新读取5279公开颗粒曲线，确认48 µm扩散孔径RMS是处理后材料的边缘约束，不能直接解释为单一颗粒尺寸。", summaryEn: "Re-read the public 5279 granularity curves: 48 µm diffuse-aperture RMS constrains processed material, not one literal grain size." },
  { version: "V47", status: "boundary", titleZh: "颗粒结构边界", titleEn: "Grain-structure boundary", summaryZh: "把颗粒幅度、空间相关、群体尺寸与记录间统计拆开；公开资料没有给出完整5279 NPS。", summaryEn: "Separated amplitude, spatial correlation, population size and inter-record statistics; the public record does not disclose a complete 5279 NPS." },
  { version: "V48", status: "boundary", titleZh: "密度形成边界", titleEn: "Density-formation boundary", summaryZh: "随机事件必须在染料密度形成中参与，而不是在显示RGB之后叠加；任何候选都要回闭公开RMS。", summaryEn: "Random events must participate in dye-density formation rather than being added after display RGB; every candidate must re-close the published RMS." },
  { version: "V49R", status: "image", titleZh: "共同密度公共修复", titleEn: "Common-density public correction", summaryZh: "删除V48显示RGB残差回注，只在形成负片中发布对称共同密度；同一负片直接进入2383与扫描观察。", summaryEn: "Removed V48's display-RGB residual reinjection and publishes only a symmetric common density inside the formed negative before direct 2383 and scan observation." },
  { version: "V49", status: "boundary", titleZh: "颗粒—锐度共同约束", titleEn: "Grain–sharpness coupling", summaryZh: "确认清晰度与颗粒不能各自独立设定：MTF、染料云频谱和观察孔径共同决定35mm尺度感。", summaryEn: "Sharpness and grain cannot be tuned independently: MTF, dye-cloud spectrum and observer aperture jointly determine the 35 mm scale impression." },
  { version: "V50", status: "audit", titleZh: "矢量追踪颗粒度", titleEn: "Vector-traced granularity", summaryZh: "从官方曲线图重新矢量化颗粒度证据，并把采样、坐标与不确定性写入可复现资产。", summaryEn: "Re-vectorized the official granularity graph and recorded sampling, coordinates and uncertainty as reproducible assets." },
  { version: "V51", status: "audit", titleZh: "负片光谱矢量化", titleEn: "Vector-traced negative spectra", summaryZh: "重新追踪5279净染料密度光谱；确认曲线已是净密度变化，包含有色遮罩耦合剂造成的负向区域。", summaryEn: "Re-traced 5279 net dye-density spectra; the plotted net changes already include negative regions caused by coloured masking couplers." },
  { version: "V52", status: "audit", titleZh: "特性曲线证据分离", titleEn: "Evidence-separated H-D curves", summaryZh: "把官方H-D图、坐标提取与模型插值分开，避免把平滑拟合误称为柯达测量。", summaryEn: "Separated the official H-D graph, coordinate extraction and model interpolation so a smooth fit cannot masquerade as a Kodak measurement." },
  { version: "V53", status: "audit", titleZh: "2383特性曲线审计", titleEn: "2383 characteristic audit", summaryZh: "重建2383各记录的公开特性曲线坐标，并检查印片曝光坐标与中性标定。", summaryEn: "Reconstructed public 2383 record curves and audited printing-exposure coordinates and neutral calibration." },
  { version: "V54", status: "audit", titleZh: "2383光谱矢量提取", titleEn: "2383 spectral-vector extraction", summaryZh: "从2005资料重新提取2383染料密度和氙灯图表，保留原图20 nm的信息边界。", summaryEn: "Re-extracted 2383 dye-density and xenon plots from the 2005 data while preserving their original 20 nm information limit." },
  { version: "V55", status: "audit", titleZh: "2383光谱积分复核", titleEn: "2383 spectral-integration audit", summaryZh: "核对光谱插值、观察者积分和白点归一化；更密的积分轴不能创造材料未发布的细节。", summaryEn: "Checked spectral interpolation, observer integration and white normalization; a denser integration axis cannot invent unpublished material detail." },
  { version: "V56", status: "boundary", titleZh: "放映色彩可辨识性", titleEn: "Projection-colour identifiability", summaryZh: "证明只有公开2383曲线不足以唯一恢复年代影院成片色彩；光源、批次、印片控制与观察条件仍未知。", summaryEn: "Public 2383 curves alone cannot uniquely recover a period theatrical colour result; illuminant, batch, printer control and viewing conditions remain unknown." },
  { version: "V57", status: "rejected", titleZh: "拒绝按记忆拟合放映色", titleEn: "Memory-fit projection colour rejected", summaryZh: "多组看似合理的投影色都能满足有限证据，因此拒绝按观感选择其中一个并称为5279真值。", summaryEn: "Several plausible projection colours satisfy the limited evidence, so selecting one by taste and calling it 5279 truth is rejected." },
  { version: "V58", status: "audit", titleZh: "积分LAD坐标", titleEn: "Integral LAD coordinate", summaryZh: "把2383印片曝光锚定到积分LAD坐标，避免单波长或显示RGB代理悄悄改变印片密度。", summaryEn: "Anchored 2383 printing exposure to an integral LAD coordinate so single-wavelength or display-RGB proxies cannot silently alter print density." },
  { version: "V59", status: "audit", titleZh: "视觉中性底谱", titleEn: "Visual-neutral base spectrum", summaryZh: "检查D-min底色在氙灯与标准观察者下的视觉中性条件；材料底谱不等于显示空间黑位。", summaryEn: "Audited the D-min base spectrum under xenon and the standard observer; material base spectrum is not the same thing as display black." },
  { version: "V60", status: "audit", titleZh: "D-min坐标配准", titleEn: "D-min coordinate registration", summaryZh: "把2383最小密度、曲线起点和光谱底色注册到同一坐标，消除重复加底或重复减底。", summaryEn: "Registered 2383 minimum density, curve origins and spectral base in one coordinate, eliminating double addition or subtraction of base density." },
  { version: "V61", status: "audit", titleZh: "5279 Status-M联合密度", titleEn: "5279 Status-M joint density", summaryZh: "验证净光谱密度、Status-M分析密度与三记录模型之间的联合关系；它们不是可互换的RGB通道。", summaryEn: "Verified the joint relationship among net spectral density, Status-M analytical density and the three record model; they are not interchangeable RGB channels." },
  { version: "V62", status: "boundary", titleZh: "层间效应与观察晶格", titleEn: "Interimage stage and observer lattice", summaryZh: "把DIR层间显影、负片染料密度、2383印片和观察晶格的所有权分离，防止同一色彩效应被计算两次。", summaryEn: "Separated ownership of DIR interimage development, negative dye density, 2383 printing and the observer lattice to prevent double-counting colour effects." },
  { version: "V63", status: "audit", titleZh: "2383中性轨迹", titleEn: "2383 neutral trajectory", summaryZh: "沿印片曝光追踪中性轴，发现现有投影颜色含有历史管理策略，不能全部归因于2383光谱。", summaryEn: "Traced the neutral axis through printing exposure and found historical management policy inside the current projection colour—not only 2383 spectra." },
  { version: "V64", status: "image", titleZh: "移除重复密度整形", titleEn: "Duplicate density shaper removed", summaryZh: "移除公开2383曲线之后的经验密度整形；这是一次成像更正，后续像素由此边界继承。", summaryEn: "Removed an empirical density shaper applied after the public 2383 curves; this was an image correction inherited by later releases." },
  { version: "V65", status: "boundary", titleZh: "投影观察所有权", titleEn: "Projection-observer ownership", summaryZh: "区分负片、正片、投影光、显示变换和网页伴随版；观察器不再被当作乳剂参数。", summaryEn: "Separated negative, print, projection light, display transform and web companion; the observer is no longer treated as an emulsion parameter." },
  { version: "V66", status: "audit", titleZh: "Cineon印片密度坐标", titleEn: "Cineon printing-density coordinate", summaryZh: "复核扫描分支的Cineon/印片密度坐标，并在原生画幅加入综合色颗粒门禁。", summaryEn: "Re-audited the scan branch's Cineon/printing-density coordinate and added native-frame opponent-grain gates." },
  { version: "V67", status: "boundary", titleZh: "Cineon显示层所有权", titleEn: "Cineon display-layer ownership", summaryZh: "把DPX/Cineon码值、显示转换和艺术调色分开；baseline只负责可声明的观察链。", summaryEn: "Separated DPX/Cineon code values, display conversion and creative grading; the baseline owns only a declared viewing chain." },
  { version: "V68", status: "audit", titleZh: "DPX与Profile隔离", titleEn: "DPX and profile isolation", summaryZh: "验证扫描母版、显示伴随版和实验Profile不能共享未版本化缓存或隐藏参数。", summaryEn: "Verified that scan masters, display companions and experimental profiles cannot share unversioned caches or hidden parameters." },
  { version: "V69", status: "boundary", titleZh: "命名的Cineon观察策略", titleEn: "Named Cineon view policy", summaryZh: "把Cineon显示与颗粒管理写成显式策略和provenance，避免交付适配器冒充胶片物理。", summaryEn: "Made Cineon display and grain management explicit named policies with provenance so delivery adapters cannot masquerade as film physics." },
  { version: "V70", status: "audit", titleZh: "记录间协方差所有权", titleEn: "Cross-record covariance ownership", summaryZh: "证明公开48 µm曲线只约束协方差对角线；红绿蓝记录的交叉功率谱仍未测量。", summaryEn: "Proved that the public 48 µm curves constrain only covariance diagonals; cross-power spectra among red, green and blue records remain unmeasured." },
  { version: "V71", status: "rejected", titleZh: "记录耦合算子审计", titleEn: "Record-coupling audit", summaryZh: "现有直接记录混合没有5279证据且改变已测边缘统计，因此被撤回。", summaryEn: "The existing direct record-mix operator lacked 5279 evidence and altered measured marginals, so it was withdrawn." },
  { version: "V72", status: "image", titleZh: "证据最小记录形成", titleEn: "Evidence-minimal record formation", summaryZh: "V46继承的内部基线：恒等记录形成保留H-D、DIR、MTF与各记录48 µm RMS，不假装知道交叉协方差。", summaryEn: "Internal baseline inherited by public V46: identity record formation preserves H-D, DIR, MTF and each record's 48 µm RMS without pretending the cross-covariance is known." },
  { version: "V73", status: "boundary", titleZh: "DIR拓扑可辨识性", titleEn: "DIR-topology identifiability", summaryZh: "公开资料支持DIR存在及其方向，但不足以唯一确定5279的层对层核、距离和强度。", summaryEn: "The public record supports DIR and its direction but cannot uniquely identify 5279's layer-to-layer kernels, ranges or strengths." },
  { version: "V74", status: "boundary", titleZh: "群体激活与原生NPS", titleEn: "Population activation and native NPS", summaryZh: "快、中、慢群体的激活概率随曝光变化；一个固定噪点频谱不能覆盖趾部、中段和肩部。", summaryEn: "Fast, medium and slow population activation changes with exposure; one fixed noise spectrum cannot span toe, mid-scale and shoulder." },
  { version: "V75", status: "audit", titleZh: "尺度积分边界", titleEn: "Scale-integration boundary", summaryZh: "原生5.7K、2K积分与播放器缩放必须分开；锐利缩放会把超Nyquist结构折回为粗颗粒。", summaryEn: "Native 5.7K, 2K integration and player scaling must remain distinct; sharp resizing can fold above-Nyquist structure into coarse grain." },
  { version: "V76", status: "audit", titleZh: "ProRes XQ编码审计", titleEn: "ProRes XQ codec audit", summaryZh: "验证12-bit母版与审看派生的编码边界，静帧必须来自最终视频而不是编码前缓存。", summaryEn: "Audited the 12-bit master and review derivation; stills must come from the final movie, not a pre-encode cache." },
  { version: "V77", status: "audit", titleZh: "频率所有权与投影颗粒", titleEn: "Frequency ownership and projection grain", summaryZh: "把场景色彩和随机综合色分开测量，修正会把真实细节误报为彩噪的旧门禁。", summaryEn: "Separated scene colour from stochastic opponent colour and corrected an older gate that could misclassify real detail as colour noise." },
  { version: "V78", status: "audit", titleZh: "统一场与编码NPS", titleEn: "Uniform-field codec NPS", summaryZh: "用均匀曝光场量化编码前后频谱，确认观察尺度改变的主要来源不是ProRes XQ。", summaryEn: "Measured uniform-field spectra before and after encoding; ProRes XQ is not the main cause of the observed scale change." },
  { version: "V79", status: "boundary", titleZh: "投影颗粒策略所有权", titleEn: "Projection grain-policy ownership", summaryZh: "现有两级投影综合色管理是历史缺陷抑制，不是5279/2383测量。去掉它会让孤立暗部综合色事件从1升至215、4,275乃至402,394。", summaryEn: "The two-stage projection opponent management is historical defect containment, not a 5279/2383 measurement. Removing it raises isolated dark opponent events from 1 to 215, 4,275 or 402,394." },
  { version: "V80", status: "rejected", titleZh: "记录间协方差界限", titleEn: "Cross-record covariance bounds", summaryZh: "即使把每条48 µm边缘RMS闭合到5.28×10⁻¹⁰，成像后的3×3协方差混合仍改变亮度、破坏尾部并产生约−0.60 D负密度，因此被拒绝。", summaryEn: "Even with every 48 µm marginal RMS closed to 5.28×10⁻¹⁰, post-formation 3×3 covariance mixing changes luma, breaks tails and creates about −0.60 D density, so it is rejected." },
  { version: "V81", status: "audit", titleZh: "共享有限事件Bernoulli界限", titleEn: "Shared finite-event Bernoulli bounds", summaryZh: "推导精确Fréchet上界：保持各层Bernoulli边缘时，ρ=0.99只在180个记录/群体/曝光组合中的13个可行。下一步必须在密度形成前使用有界共享事件。", summaryEn: "Derived exact Fréchet bounds: while preserving Bernoulli marginals, ρ=.99 is feasible in only 13 of 180 record/population/exposure cases. Any next model must use bounded shared events before density formation." },
  { version: "V82", status: "audit", titleZh: "三记录Bernoulli兼容性", titleEn: "Three-record Bernoulli compatibility", summaryZh: "两两合法与相关矩阵正半定仍不足够：7,500组独立记录对参数中有3,462组没有非负RGB八状态联合分布，其中1,484组是PSD假通过。单一共用α家族数学上有效，但仍没有5279实测系数。", summaryEn: "Pairwise validity and a PSD correlation matrix are still insufficient: 3,462 of 7,500 independent pair-parameter sets have no nonnegative eight-cell RGB law, including 1,484 PSD false positives. The single-common-alpha family is valid mathematics, not a measured 5279 coefficient." },
  { version: "V83", status: "audit", titleZh: "共享事件DIR／RMS闭合", titleEn: "Shared-event DIR/RMS closure", summaryZh: "纠正一处研究说明：V72实际继承DIR后的残差校准，而不是DIR前染料产率校准。把唯一合法的共享事件家族穿过五尺寸群体与随机DIR后，全部α／曝光端点仍在官方48 µm RMS的1.08%以内；但同一边缘曲线允许近零到约0.7–0.95的记录相关，因此不能选择α。", summaryEn: "Corrected our own description: V72 actually inherits post-DIR residual calibration, not pre-DIR dye-yield calibration. The only legal shared-event family remains within 1.08% of the public 48 µm RMS at every alpha/exposure endpoint after five-class formation and stochastic DIR, yet the same marginals permit near-zero to roughly 0.7–0.95 record correlation and cannot select alpha." },
  { version: "V84", status: "rejected", titleZh: "共享位点不是免费的去彩噪", titleEn: "Shared sites are not free chroma cleanup", summaryZh: "真实RAW配对裁切证明：α从0升到1虽让综合色RMS下降16–18%，却让亮度颗粒上升43–54%、总RGB颗粒上升23–26%，且放映与扫描没有同一个“平衡”点。α=1被拒为默认值，.25/.50只保留诊断；下一步回查蓝记录官方RMS与可见色彩映射。", summaryEn: "A paired real-RAW crop shows alpha 0→1 lowers opponent RMS 16–18% but raises luma grain 43–54% and total RGB grain 23–26%, with no common projection/scan balance point. Alpha=1 is rejected as a default; .25/.50 remain diagnostics while the large official blue-record marginal and its visible-colour mapping are re-audited." },
  { version: "V85", status: "audit", titleZh: "5279颗粒测量域复核", titleEn: "5279 granularity measurement-domain audit", summaryZh: "重新渲染并提取2003官方PDF：R/G/B路径、0—4到−4—0曝光平移和Status-M坐标全部通过；V50数值最大只差2.9×10⁻⁶ D。蓝记录较大是公开图事实，真正缺失的是三记录协方差／交叉频谱。V85不改像素。", summaryEn: "Re-rendered and re-extracted the 2003 source PDF: R/G/B paths, the 0–4 to −4–0 exposure translation and the Status-M coordinate all pass; V50 differs by at most 2.9×10⁻⁶ D. The large blue marginal is in the public graph. Missing cross-record covariance/cross-spectra—not a trace error—remain the boundary. V85 changes no pixels." },
  { version: "V86", status: "audit", titleZh: "观察器协方差与阴影光谱LUT审计", titleEn: "Observer covariance and shadow spectral-LUT audit", summaryZh: "合法协方差外包络确认：共享记录事件会把综合色能量换成更强亮度颗粒，而不是免费降噪。更重要的是，29³联合Status-M光谱LUT在−3 logE阴影相对直接积分最坏多算0.01399 D，且红记录误差最大；这很可能造成扫描与放映共同的青绿阴影。V86不改像素，V87先修精度。", summaryEn: "The legal covariance envelope confirms that shared record events trade opponent noise for stronger luma grain rather than removing grain for free. More importantly, the 29³ joint Status-M spectral LUT differs from direct integration by up to 0.01399 D at −3 logE, with the largest red-record error—a plausible source of the cyan/green shadow shared by scan and projection. V86 changes no pixels; V87 repairs precision first." },
];

/*
 * The V46–V86 identifiers above are preserved as immutable laboratory-note
 * provenance.  They are not public image releases.  The site presents them
 * through the thematic chapters below so a one-line audit no longer appears
 * to be a new film version.
 */
export const researchChapters: ResearchChapter[] = [
  {
    id: "measurement-authority",
    titleZh: "材料测量与数据权威",
    titleEn: "Material measurement and data authority",
    summaryZh: "重新读取5279与2383公开图表，分离原始测量、矢量提取、插值和模型推断；确认Status-M、净染料密度、D-min与颗粒度各自的坐标。",
    summaryEn: "Re-read the public 5279 and 2383 records, separating source measurements, vector extraction, interpolation and inference while registering Status-M, net dye density, D-min and granularity in their proper coordinates.",
    conclusionZh: "公开资料能约束三条边缘RMS与光谱形状，但不能给出5279完整NPS、三记录交叉频谱或专有配方。",
    conclusionEn: "Public evidence constrains the three marginal RMS curves and spectral shapes, but not a complete 5279 NPS, cross-record spectra or proprietary formula.",
    evidenceIds: ["V46", "V50", "V51", "V52", "V53", "V54", "V55", "V61", "V85", "V86"],
  },
  {
    id: "multilayer-randomness",
    titleZh: "多层显影、颗粒与联合统计",
    titleEn: "Multilayer development, grain and joint statistics",
    summaryZh: "把颗粒幅度、空间频谱、快中慢群体、DIR反应扩散和记录间协方差拆开，逐项检查有限事件是否保持非负密度与官方48 µm边缘。",
    summaryEn: "Separated grain amplitude, spatial spectrum, fast/mid/slow populations, DIR reaction–diffusion and cross-record covariance, then tested finite events against nonnegative density and the public 48 µm marginals.",
    conclusionZh: "共享事件不是免费的去彩噪：它会把综合色能量换成更强亮度颗粒；没有交叉频谱测量前不选择相关系数。",
    conclusionEn: "Shared events are not free chroma cleanup: they trade opponent energy for stronger luma grain. No correlation coefficient is selected without cross-spectral evidence.",
    evidenceIds: ["V47", "V48", "V49", "V49R", "V70", "V71", "V72", "V73", "V74", "V80", "V81", "V82", "V83", "V84"],
  },
  {
    id: "print-projection",
    titleZh: "2383印片与影院观察",
    titleEn: "2383 printing and cinema observation",
    summaryZh: "从印片灯、LAD、2383 H-D与染料光谱一路追踪到氙灯、CIE观察者、投影flare和显示伴随版，消除重复密度整形与错误所有权。",
    summaryEn: "Traced printer light, LAD, 2383 H-D and dye spectra through xenon, the CIE observer, projection flare and display companions, removing duplicate density shaping and ownership errors.",
    conclusionZh: "2383材料响应与年代影院最终色彩不是同一个可辨识量；光源、批次、印片控制和观看条件必须独立声明。",
    conclusionEn: "2383 material response and a period cinema result are not the same identifiable quantity; illuminant, batch, printer control and viewing conditions must be declared separately.",
    evidenceIds: ["V53", "V54", "V55", "V56", "V57", "V58", "V59", "V60", "V62", "V63", "V64", "V65", "V77", "V79"],
  },
  {
    id: "scan-delivery",
    titleZh: "扫描、DI与家庭影碟交付",
    titleEn: "Scan, DI and home-video delivery",
    summaryZh: "把负片扫描、Cineon/DPX、显示变换、尺度积分、静帧权威和编码分层。5.7K只作为内部重建/DI母版，不再被称为蓝光成片。",
    summaryEn: "Layered negative scanning, Cineon/DPX, display transforms, scale integration, still authority and encoding. The 5.7K raster is an internal reconstruction/DI master—not a Blu-ray deliverable.",
    conclusionZh: "下一视觉版会从同一Scan/DI母版分别生成蓝光与UHD观察件，明确分辨率、4:2:0、位深、量程和AVC/HEVC压缩；HDR重制不自动假定。",
    conclusionEn: "The next visual release will derive separate Blu-ray and UHD witnesses from one Scan/DI master, declaring resolution, 4:2:0, bit depth, range and AVC/HEVC compression; an HDR remaster is not assumed.",
    evidenceIds: ["V66", "V67", "V68", "V69", "V75", "V76", "V77", "V78"],
  },
];

export const currentVisualRelease = "V49";
export const nextVisualRelease = "measurement-dependent";
export const currentResearchCycle = "08";
export const currentEngineCandidate = "V49 conservative common-density Kodak 5279 / 2383 baseline";
