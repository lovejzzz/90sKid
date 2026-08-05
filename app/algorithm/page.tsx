"use client";

import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { useLanguage } from "../i18n";
import { AlgorithmEnglish } from "./AlgorithmEnglish";

const activationCode = `def subemulsion_activation_probabilities(log_exposure):
    centres = fast_centre[:, None] + speed_offsets[None, :]
    z = (log_exposure[..., :, None] - centres) / widths[:, None]
    return 1.0 / (1.0 + exp(-clip(z, -16, 16)))`;

const grainCode = `developed = rng.binomial(site_count, probability) / site_count
sampled  = optical_integrate(developed, cloud_kernel, scanner_aperture)
expected = optical_integrate(probability, cloud_kernel, scanner_aperture)
density_deviation = sampled - expected   # 颗粒改变，但平均密度不漂移`;

const dirCode = `# V21实际执行：先在九个亚层中形成抑制场，再合并记录密度
release = blur(population_density, lateral_sigma) - population_density
transport = population_transport @ release
population_density += receiver_gain * transport
population_deviation += stochastic_coupling * transport_deviation
# 对均匀中性曝光，修正项严格为零；平均H-D轴不漂移`;

const scanCode = `T = 10 ** (-spectral_density)                 # 负片透射率
sensor = integrate(lamp * T * scanner_response, wavelength)
sensor_2k = area_integrate(sensor, aperture=2048)
D = -log10(sensor_2k / clear_reference)
cineon = 95 + (D - Dmin) / 0.002`;

const printCode = `# Status-A积分密度不是染料量；逐条主曲线做非线性反演
dye_amount = invert_status_a_principal_curves(status_a_density)
print_logE = interimage_matrix @ (print_logE - lad_logE) + lad_logE
positive_density = positive_hd_curves(print_logE)
xyz = integrate(xenon_spd * 10 ** (-spectral_dyes(dye_amount)), cie_xyz)`;

const cloudCode = `# V26: rows are fast / medium / slow; every row sums to one
weights = [[0.12, 0.26, 0.34, 0.20, 0.08],
           [0.16, 0.30, 0.32, 0.17, 0.05],
           [0.22, 0.34, 0.29, 0.12, 0.03]]
radius  = [0.50, 0.68, 0.86, 1.08, 1.34] * base_cloud_radius
optical = [0.68, 0.80, 0.92, 1.05, 1.18] * base_optical_sigma
phase_k = phase_0 + k * 2.3999632297       # 黄金角；避免三向周期
# 随后仍逐记录、逐曝光回标5279的48µm RMS`;

const colourGrainCode = `delta_y = dot(grain_delta_rgb, rec709_luma)
delta_c = grain_delta_rgb - delta_y[..., None]
delta_c = blur(delta_c, sigma_at_2k) + hf * highpass(delta_c)
visible_grain = delta_y[..., None] + opponent_strength * delta_c
# 只处理signed grain delta；mean RGB不进入这个函数`;

const outputLutCode = `# 每个格点仍由完整分析染料 / 2383 / 氙灯 / D60相对色度链计算
print_lattice = exact_print_renderer(record_density_grid(size=193))
mean_display   = trilinear(print_lattice, mean_density)
formed_display = trilinear(print_lattice, formed_density)
# MTF、逐帧负片形成和正片细颗粒仍在格点之外执行`;

const observerCode = `# reconstructed 是完成胶片/扫描链后的 monitor-linear Rec.709 外观
projection_signal = rec709_oetf(projection_monitor_linear)
bluray_signal = rec709_oetf(cineon_bluray_linear)
# 两份ProRes均写完整Rec.709 1-1-1；BT.1886只在参考显示端验证
web_proxy = srgb_oetf(rec709_inverse_oetf(master_signal))`;

const parallelCode = `# 固定8条带和固定SeedSequence；worker数只改变调度，不改变样本
for stripe in fixed_row_stripes(8):
    rng = Generator(SeedSequence([frame_record_layer_class_seed, stripe.index]))
    developed[stripe] = rng.binomial(site_count, p[stripe])
# 1 worker 与 8 workers：5760×4320 max_abs_delta == 0`;

const scanNeutralCode = `# V27: 在完整扫描链上预计算2049级中性曝光，而不是猜一项全局品红
scale_y, scale_rgb = build_spirit_neutral_scale(samples=2049)
rgb_balanced = rgb * interpolate(scale_y, scale_rgb, rec709_luma(rgb))
y_before = rec709_luma(rgb)
y_after  = rec709_luma(rgb_balanced)
rgb_v27  = compress_unit_gamut(rgb_balanced * y_before / max(y_after, 1e-8))
# 2383分支不调用此函数；V26负片、颗粒、DIR和扫描2K孔径保持不变`;

export default function AlgorithmPage() {
  const { language } = useLanguage();
  if (language === "en") return <><SiteHeader /><AlgorithmEnglish /><SiteFooter /></>;
  return (
    <>
      <SiteHeader />
      <main className="algorithm-page wrap">
        <header className="page-header"><span className="eyebrow">METHOD · CURRENT V32</span><h1>算法不是一枚滤镜。<br />它是一条成像链。</h1><p>V32冻结V31的全部成像参数，并增加独立场景、时序测量、SMPTE ST 428-1 DCDM与OFX分块同一性。它不加入新的look；每次未来变化必须先通过可重复的测量。</p></header>

        <section className="pipeline"><div className="pipeline-line"><span>01<b>GH7 RAW</b><small>扩展线性RGB</small></span><i>→</i><span>02<b>虚拟曝光</b><small>V-Gamut / 光谱记录</small></span><i>→</i><span>03<b>5279显影</b><small>位点 · 染料 · DIR</small></span><i>→</i><span>04<b>观察分支</b><small>2383 或 2K DI</small></span><i>→</i><span>05<b>12-bit ODT</b><small>Rec.709或DCDM X′Y′Z′</small></span></div></section>

        <section className="method-section"><div className="method-index">00</div><div className="method-copy"><span className="section-tag">V32 · MEASUREMENT / DELIVERY CONTRACT</span><h2>冻结像素，用不变量约束下一次变化</h2><p>T007与T031都直接调用V31完整链，不允许逐镜头参数。验证器检查原生12-bit Rec.709 1-1-1、亮度保持、高光、硬裁切、纹理时序、中性轴、扫描SHA回归、DCDM回环和OFX tile同一性。</p><div className="equation"><span>OFX ROI</span><b>σ<sub>full</sub>=0.72·W/2048　·　halo=ceil(6σ<sub>full</sub>)</b><small>σ取完整输出宽度，不取tile或代理宽度；随机种子取绝对源帧号。</small></div><div className="equation"><span>SMPTE ST 428-1</span><b>CV=round[4095·(48·XYZ/52.37)<sup>1/2.6</sup>]</b><small>12-bit X′Y′Z′写入16-bit TIFF高12位；低四位为零。</small></div></div></section>

        <section className="method-section"><div className="method-index">01</div><div className="method-copy"><span className="section-tag">V28 · RAW INPUT CONTRACT</span><h2>从解码后的线性BT.2020到三条感色记录</h2><p>AVFoundation交付的是已经白平衡、去马赛克并标记为extended-linear BT.2020/D65的RGB，不是等待再次套Camera LUT的Bayer数据。V28只做线性BT.2020→XYZ D65→V-Gamut原色变换，不重复白平衡或非线性相机分离；虚拟曝光随后投向5279三条重叠感色记录。</p><div className="equation"><span>输入原色变换</span><b>RGB<sub>V-Gamut</sub> = M<sub>XYZ→V</sub> · M<sub>2020→XYZ</sub> · RGB<sub>decoded</sub></b><small>所有矩阵在线性光域执行；V-Log不是ProRes RAW解码曲线。</small></div><div className="equation"><span>记录曝光</span><b>E<sub>c</sub>(x,y) = Σ<sub>j</sub> M<sub>cj</sub> · RGB<sub>j</sub>(x,y)</b><small>c ∈ 红感、绿感、蓝感；M是受公开感色曲线约束的重叠响应。</small></div><div className="equation"><span>负片密度</span><b>D<sub>c</sub> = H<sub>c</sub>(log<sub>10</sub>E<sub>c</sub>)</b><small>Hc分别采样5279公开的R/G/B Status-M曲线。</small></div></div></section>

        <section className="method-section"><div className="method-index">02</div><div className="method-copy"><span className="section-tag">FINITE SITES</span><h2>快／中／慢有限位点</h2><p>每个颜色记录包含三个速度群体。逻辑斯蒂曲线给出某曝光下可显影位点的概率；二项采样保证群体完全未曝光或完全显影时随机方差自然下降。V21让青、品红、黄记录分别拥有自己的有效云尺寸、光学扩散和位点数量。</p><div className="equation"><span>激活概率</span><b>p<sub>c,k</sub> = σ((logE<sub>c</sub> − μ<sub>c,k</sub>) / w<sub>c</sub>)</b><small>k ∈ 快、中、慢；速度中心相互错开但显影区间重叠。</small></div><pre><code>{activationCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">03</div><div className="method-copy"><span className="section-tag">V26 · EXPOSURE-CONDITIONED DYE CLOUDS</span><h2>颗粒是有限事件的多尺度光学积分</h2><p>每个快／中／慢群体再分成五种尺寸类别，作为连续染料云分布的数值求积。V26不再让三层共用同一套权重：快层保留稍宽的大云尾部，慢层提高小云比例。因为三层激活概率随曝光交叉，阴影、中间调与高光会自然形成不同空间频谱。</p><div className="equation"><span>密度方差</span><b>σ²<sub>fraction</sub> = p(1−p) / n</b><small>形态改变后再次通过48µm圆孔径回标5279公开RMS曲线，所以“更细”不是简单降低噪声幅度。</small></div><pre><code>{cloudCode}</code></pre><pre><code>{grainCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">04</div><div className="method-copy"><span className="section-tag">V21 · DEVELOPMENT DIR</span><h2>从后处理邻接，改为显影时的反应—扩散</h2><p>V20使用总密度生成二维DIR场。V21让九个亚层的显影事件分别释放不同尺度的抑制场；它们在平面内扩散、按有限矩阵传播到接收层，并在各颜色记录合并前反馈到密度和随机偏差。</p><div className="equation"><span>显影域耦合</span><b>ΔD<sub>c,k</sub> = β<sub>c,k</sub> Σ<sub>j,m</sub> T<sub>c,k←j,m</sub>[G<sub>σj,m</sub>＊D<sub>j,m</sub> − D<sub>j,m</sub>]</b><small>均匀区域括号项为零，因此中性H-D保持不变；边缘和颜色分离曝光才产生耦合。</small></div><pre><code>{dirCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">05</div><div className="method-copy"><span className="section-tag">SPECTRAL NEGATIVE</span><h2>染料形成与有色遮罩</h2><p>三条记录并不是理想CMY。每条5279净染料曲线含有新染料与遮罩耦合剂消耗的合成结果。总透射率由完整D-min/橙色底与带符号的净密度共同决定。</p><div className="equation"><span>负片透射率</span><b>T<sub>neg</sub>(λ) = 10<sup>−[Dmin(λ)+Σ a<sub>c</sub>ΔD<sub>c,net</sub>(λ)]</sup></b><small>印片路径保留D-min；扫描匹配路径可以在正确观察器中估计并去底。</small></div></div></section>

        <section className="method-section"><div className="method-index">06</div><div className="method-copy"><span className="section-tag">V22 · ANALYTICAL PRINT DYES</span><h2>Status-A测到的密度，不能再当一次染料量</h2><p>状态密度计看到的是三种正片染料在指定光谱权重下共同形成的积分密度。V21把三条Status-A主曲线输出再次乘以CMY染料光谱，等于重复计算旁带吸收。V22逐曝光反解分析染料量，再在LAD附近施加层间曝光耦合，最后经过2383的非线性正片曲线。</p><div className="equation"><span>Status-A积分</span><b>D<sub>A,k</sub> = −log<sub>10</sub>[Σ<sub>λ</sub>10<sup>−Σj a<sub>j</sub>d<sub>j</sub>(λ)</sup>W<sub>k</sub>(λ) / Σ<sub>λ</sub>W<sub>k</sub>(λ)]</b><small>由三条主曲线数值反演a<sub>j</sub>，而不是把D<sub>A,k</sub>直接当a<sub>j</sub>。</small></div><div className="equation"><span>层间曝光</span><b>E′<sub>print</sub> = M(E<sub>print</sub> − E<sub>LAD</sub>) + E<sub>LAD</sub></b><small>LAD锚点不动；矩阵只描述锚点附近不同记录的互感方向。</small></div><pre><code>{printCode}</code></pre></div></section>

        <section className="method-section split-method"><div className="method-index">07</div><div className="method-copy"><span className="section-tag">THREE OBSERVERS · TWO OUTPUTS</span><h2>同一负片之后，结果开始分叉</h2><div className="method-branches"><article><b>5279 → 2383 → 氙灯</b><p>3200K印片灯穿过负片；2383三条感色层得到曝光，经过其陡峭H-D曲线形成正片染料，再用氙灯光谱和CIE观察器积分。正片MTF、细颗粒、Callier效应和投影flare属于这一支。</p></article><article><b>5279 → Period 2K → Cineon</b><p>Status-M只负责数据表测量轴。成片扫描用较宽的时期RGB探测响应积分透射光，再进行Spirit式film match、2K孔径、Cineon 0.002D/code与蓝光显示完成。</p><pre><code>{scanCode}</code></pre></article></div></div></section>

        <section className="method-section"><div className="method-index">08</div><div className="method-copy"><span className="section-tag">V30 · OFFICIAL LAD COLOUR ANCHOR</span><h2>用Kodak通道密度锚定2383，不让供应商LUT定义胶片颜色</h2><p>V30把2383的打印中性点从简化的相等密度改为H-61B官方目标1.09/1.06/1.03 D。供应商D60 LUT与数字化染料曲线的残差仍保留作研究记录，但它们没有足够证据支配最终色相或饱和度，因此显示权重为零。</p><div className="equation"><span>官方LAD与证据权重</span><b>D<sub>LAD</sub>=[1.09,1.06,1.03]　·　w<sub>D60</sub>=w<sub>hue</sub>=w<sub>sat</sub>=0</b><small>这是物理校准修正，不是减蓝或减饱和的创作调色。</small></div></div></section>

        <section className="method-section"><div className="method-index">08B</div><div className="method-copy"><span className="section-tag">V31 · NORMAL-PROCESS CHROMA / TONE DECOUPLING</span><h2>2383可以改变明暗，但不能因此把染料颜色当成银影抽走</h2><p>V30把综合色度写成C/L，再以更陡的2383中性曲线替换L；暗部因此同时失去绝对综合色度，与完整亮度颗粒叠加后接近留银。V31在两条完整观察器之后分离频率：Period 2K提供低频OKLab a/b染料颜色，2383保留自己的高频综合色颗粒；V30逐像素线性亮度保持不变。正常ECN-2/ECP-2D移除银影，因此这是工艺边界修正，不是增艳。</p><div className="equation"><span>最终观察边界</span><b>ab<sub>out</sub>=G<sub>σ</sub>＊ab<sub>scan</sub>+[ab<sub>proj</sub>−G<sub>σ</sub>＊ab<sub>proj</sub>]　·　Y<sub>out</sub>=Y<sub>proj</sub></b><small>σ=0.72px@2K；色域围绕目标Y压缩。5279、2383黑位、Gamma与颗粒形成参数全部不变。</small></div></div></section>

        <section className="method-section"><div className="method-index">09</div><div className="method-copy"><span className="section-tag">V24 · COLOUR-GRAIN SEPARATION</span><h2>输出链观察颗粒，但不重新调色</h2><p>三条独立染料记录经过光谱观察会生成较强综合色纹理。V24在signed grain delta中分离Rec.709明度与综合色分量：明度纹理原样保留，综合色纹理分别按2383投影和Period 2K扫描孔径积分。确定性mean RGB不进入这一步，因此平均色相、饱和度和黑白灰严格不动。</p><pre><code>{colourGrainCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">10</div><div className="method-copy"><span className="section-tag">V25 · OUTPUT OBSERVERS</span><h2>观看条件不是源文件的传递函数</h2><p>第一次V25把BT.1886参考显示EOTF的反函数写入蓝光码值，又把已经完成Rec.709监看适配的2383分支重新编码为P3 gamma 2.6。播放器仍按Rec.709解释文件，导致中间调和暗部明显变亮。修正版让两个监看母版都回到Rec.709 OETF与完整1-1-1；48 nit影院条件保留在投影观察模型中，BT.1886只用于显示端验证。</p><pre><code>{observerCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">11</div><div className="method-copy"><span className="section-tag">EXACT ACCELERATION</span><h2>缓存固定颜色，复用平均负片，并行独立银盐事件</h2><p>193³格点继续缓存固定的分析染料与2383颜色物理。V25另删除每帧一次重复的确定性负片显影，并把45组二项抽样切成固定种子条带。分辨率、粒层数量、随机分布、光学积分和48µm回标都不变。</p><pre><code>{outputLutCode}</code></pre><pre><code>{parallelCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">12</div><div className="method-copy"><span className="section-tag">V26 · NPS + TEMPORAL VALIDATION</span><h2>“有机”必须能被空间与时间测量</h2><p>V26分别计算阴影、中间调和高光的径向密度噪声功率谱，并统计三速度层的贡献。它不把一张噪点纹理做平移或循环：帧号进入每个颜色记录、速度层和粒径级的固定随机种子，每一帧形成独立显影事件。</p><div className="equation"><span>时间独立约束</span><b>|corr(δD<sub>t</sub>, δD<sub>t+1</sub>)| → 0</b><small>四帧均匀场、三记录的最大绝对lag-1相关为0.0074；最大平均密度漂移0.00015D。</small></div></div></section>

        <section className="method-section"><div className="method-index">13</div><div className="method-copy"><span className="section-tag">V27 · FULL NEUTRAL-SCALE SCAN CALIBRATION</span><h2>只修扫描RGB比例，不重新塑造黑白灰</h2><p>V26扫描观察器在两个灰阶锚点之间留下了密度相关的绿色残差。V27让2049级中性曝光先完整经过5279显影、扫描光源与探测器、2K透射域孔径、Cineon映射和蓝光完成曲线，再按输出亮度查找RGB平衡。校正后立即恢复校正前的Rec.709亮度，因此黑位、对比、Gamma、局部颗粒亮度和高光位置都保持不变。最新hourly审计还完整核对了2003年5279临时专利：它只证明identifier沿文档分支在5279／5218之间变化，没有任何数值颗粒参数，因此不能改写V26乳剂。</p><div className="equation"><span>条件中性化</span><b>RGB′ = C(Y)⊙RGB · Y / Y(C(Y)⊙RGB)</b><small>C只由中性曝光标定；有颜色的像素不会被拉回灰色。</small></div><pre><code>{scanNeutralCode}</code></pre></div></section>

        <section className="validation"><span className="section-tag">V31 THREE-SCENE VALIDATION</span><h2>三个场景共同通过什么</h2><div className="validation-grid"><div><b>原始分辨率</b><p>3 × 24帧 · 5760×4320</p></div><div><b>胶片母版</b><p>12-bit ProRes 4444</p></div><div><b>正常工艺</b><p>无残余银密度项</p></div><div><b>色度策略</b><p>低频染料颜色；放映高频综合色纹理</p></div><div><b>相机原图</b><p>官方Panasonic V-709</p></div><div><b>质感</b><p>V30颗粒逐项锁定</p></div></div></section>
      </main>
      <SiteFooter />
    </>
  );
}
