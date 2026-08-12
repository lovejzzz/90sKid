"use client";

import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { ResearchStatus } from "../components/ResearchLedger";
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
# V40在随机DIR完成后，对处理负片总残差回标48µm RMS`;

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

const observerCode = `# V40：专业母版是唯一画面权威，伴随版共享其实际压缩结构
professional = prores4444_xq(pow(Lobs, 1/2.4))
Lmaster      = pow(decode(professional), 2.4)
quicktime    = prores4444_xq(srgb_oetf(Lmaster))
still        = frame(quicktime, 12)   # no second OETF inversion
web_video    = encode_srgb(quicktime) # same first frame and transfer
# EOTF(professional) ≈ EOTF(quicktime) ≈ Lmaster`;

const densityFormationCode = `# V39：图像结构停留在其被测量的密度域
Dneg_mean = mtf_5279(develop_5279(exposure))
Dneg_real = Dneg_mean + finite_site_density - mean_density
scan = spirit_2k_observe(Dneg_real)

Dprint_mean = mtf_2383(expose_2383(Dneg_mean))
Dprint_real = Dprint_mean + mtf_2383(expose_2383(Dneg_real) - expose_2383(Dneg_mean))
Dprint_real += finite_2383_dye_cloud_density
projection = xenon_observe(Dprint_real)
# 没有display RGB grain overlay`;

const v40BoundaryCode = `# V40：只在公开数据真正测量的位置约束随机性
D5279 = mtf_5279(Dmean) + calibrate_post_process_RMS(delta_after_DIR)
delta_visible = observer_integrate_luma_and_opponent(D5279 - Dmean)

# 2383公开资料没有分记录协方差/NPS：不虚构随机印片颗粒
D2383 = mtf_2383(expose_2383(D5279))
projection = xenon_observe(D2383)

# V40末端适配器只保留scan低频染料综合色与projection明度
projection = final_adapter(scan_low_chroma, projection_luma, opponent_hf=0)

# 同时检查综合色能量和缺少3×3邻域支持的孤立原色脉冲
assert dark_opponent_p9999 <= 0.035
assert isolated_primary_impulses_gt_0_06_per_million <= 5`;

const v41ColourCode = `# V41：色卡只估计误差方向；12.5%保守步长且严格保持场景亮度
xyz_d50 = bradford_d65_to_d50(bt2020_to_xyz(scene_linear))
chroma  = xyz_d50 - neutral_axis(xyz_d50)
corrected = chroma + 0.125 * (cross_group_matrix @ chroma - chroma)
scene_v41 = restore_exact_d65_luminance(corrected)

# 有符号中间值只有在三条组合记录曝光全部非负时才安全
signed_records = film_basis_signed @ record_sensitivity.T
records = where(all(signed_records >= 0), signed_records,
                film_basis_clipped @ record_sensitivity.T)`;

const v43hCode = `# V43H只覆盖未测量的候选项；V42其余常量冻结
negative_nps = preserve_rms_48um(
    redistribute_spatial_spectrum(scale=0.72, five_size_classes=True))
spirit = lerp(v42_broad_observer, bounded_candidate, weight=0.25)

# 2383只允许弱共模密度；没有独立RGB印片脉冲
delta_print = 0.06 * (binomial(900, p) / 900 - p)
print_light = mean_print_light * 10 ** (-delta_print[..., None])

projection, scan, deterministic = observe_once(realized_negative)
fsd = independent_fsd(deterministic, N=176, sigma=0.597)`;

const v44Code = `# V44回到已接受的V42成像Profile
negative = form_v42_5279(raw)
projection_light = observe_2383_xenon(negative)
scan             = observe_period_2k(negative)
projection = normal_process_monitor(projection_light,
                                    low_frequency_chroma=scan)

# 原生5.7K母版保持画面权威
master_light = bt1886_decode(decode(prores_xq_master))
review_light = pixel_area_integrate(master_light, width=1920)
review       = prores_xq(srgb_encode(review_light))
still        = decode_frame(review, middle_frame)`;

const v45Code = `# 只替换2383的标准观察者；其余V44/V42参数冻结
lambda_nm, xyz_bar = load_cie_1931_2deg_official_1nm()
dye_1nm   = linear_interp(kodak_2383_dye_graph_20nm, lambda_nm)
xenon_1nm = linear_interp(kodak_xenon_graph_20nm, lambda_nm)
T = 10 ** (-(dye_amount_cmy @ dye_1nm.T))
XYZ = trapz(T * xenon_1nm * xyz_bar, dx=1nm)

# profile、标准表和193³运行晶格共同接受SHA-256门禁
assert lattice == build_from(profile="v45", observer=xyz_bar)`;

const parallelCode = `# 固定8条带和固定SeedSequence；worker数只改变调度，不改变样本
for stripe in fixed_row_stripes(8):
    rng = Generator(SeedSequence([frame_record_layer_class_seed, stripe.index]))
    developed[stripe] = rng.binomial(site_count, p[stripe])
# 1 worker 与 8 workers：5760×4320 max_abs_delta == 0`;

const productionCode = `# V35 Production：完整uint32随机字，不先缩成24-bit float
threshold = floor(float32(probability) * 2**32)
developed += philox_u32(counter(frame, record, population,
                                size_class, x, y, lane)) < threshold
# 每帧45个身份必须唯一；Archive仍保留V34 NumPy/CPU实现`;

const stablePhaseCode = `# V37：位点仍由frame参与Philox identity，每一帧都是新乳剂
sampled_phase = rng.uniform(0, 2*pi)       # 继续消耗以保持Archive序列
class_id = record * 15 + population * 5 + size_class
phase = 2*pi * frac((class_id + 0.5) * golden_ratio) + pi/6
offset = 0.38 * [cos(phase), sin(phase)]
# 只有数值积分相位稳定；grain sites从不跨帧复用`;

const scanNeutralCode = `# V27: 在完整扫描链上预计算2049级中性曝光，而不是猜一项全局品红
scale_y, scale_rgb = build_spirit_neutral_scale(samples=2049)
rgb_balanced = rgb * interpolate(scale_y, scale_rgb, rec709_luma(rgb))
y_before = rec709_luma(rgb)
y_after  = rec709_luma(rgb_balanced)
rgb_v27  = compress_unit_gamut(rgb_balanced * y_before / max(y_after, 1e-8))
# 2383分支不调用此函数；V26负片、颗粒、DIR和扫描2K孔径保持不变`;

const v81BoundCode = `# V81：这是可行域，不是新的5279参数
joint_max = minimum(p_i, p_j)
rho_max = (joint_max - p_i*p_j) / sqrt(p_i*(1-p_i)*p_j*(1-p_j))

# 有界共享事件族：严格保持每条Bernoulli边缘
if bernoulli(alpha):
    u = shared_uniform()
    x_i, x_j = (u < p_i), (u < p_j)
else:
    x_i, x_j = (uniform() < p_i), (uniform() < p_j)

assert requested_rho <= rho_max
# alpha未知；V81没有把它加入当前V72成像发布`;

const v82JointCode = `# V82：三条pair joint必须共享一个合法的P(111)
t_min = max(0, q_rg+q_rb-p_r, q_rg+q_gb-p_g, q_rb+q_gb-p_b)
t_max = min(q_rg, q_rb, q_gb,
            1-p_r-p_g-p_b+q_rg+q_rb+q_gb)
assert t_min <= t_max

# PSD只约束二阶矩；仍要重建并检查全部8个Bernoulli单元
cells = rgb_bernoulli_cells(p_rgb, q_pairs, t)
assert min(cells) >= 0 and sum(cells) == 1`;

const v83TransferCode = `# V83：按当前V72真实阶段顺序计算，不重写历史
S_shared(f, E, alpha) = finite_site_cross_power(p_rgb, alpha)
D_raw(f) = stochastic_DIR(f, E) @ S_shared(f, E, alpha)

# 当前增益在DIR之后作用，但分母仍是独立、DIR前预测
g_rgb = sigma_kodak_48um / sqrt(var_pre_DIR_independent)
D_formed = mean_density + g_rgb * D_raw

assert max_relative_48um_error <= 0.010762
# 闭合边缘不等于识别联合统计；alpha仍未知`;

const v84EnergyCode = `# V84：边缘RMS固定，观察器能量仍随协方差改变
var_record = diag(Sigma_D)              # Kodak 48 um约束
var_observer = w.T @ Sigma_D @ w        # 放映／扫描实际看见

# T020配对裁切，alpha 0 -> 1
projection_luma *= 1.538
projection_opponent *= 0.837
scan_luma *= 1.432
scan_opponent *= 0.816

assert deterministic_mean_is_bit_exact
promote_alpha = False`;

export default function AlgorithmPage() {
  const { language } = useLanguage();
  if (language === "en") return <><SiteHeader /><AlgorithmEnglish /><SiteFooter /></>;
  return (
    <>
      <SiteHeader />
      <main className="algorithm-page wrap">
        <header className="page-header"><span className="eyebrow">METHOD · V47 VISUAL RELEASE / RESEARCH CYCLE 06</span><h1>算法不是一枚滤镜。<br />它是一条成像链。</h1><p>V46继续作为物理5279分支。当前可观看的V47增加经受控Silver Efex测量约束的SHM形态对照：多尺度群体、局部非均质、团簇、空洞与厚尾共同形成有限密度。两条路线明确分离，避免把形态旁证伪装成5279测量。</p></header>

        <ResearchStatus language="zh" />

        <section className="method-section"><div className="method-index">V47</div><div className="method-copy"><span className="section-tag">CONTROLLED SHM · MULTISCALE · THICK-TAIL</span><h2>如果银盐组织不是Gaussian，只匹配强度就不够</h2><p>0.45、0.90与1.80原生像素的三个独立各向同性群体，由慢变化占有场在局部重新分配。二阶Hermite群体形成不对称团簇／空洞，三阶Hermite群体形成受控Nik 8 Tri-X导出中实测的正厚尾。标准化后的组织进入N=1250逆二项CDF，因此它参与形成密度，而不是成为后期覆盖层。</p><div className="equation"><span>SHM形成</span><b>Z″=Z+a(Z²−1)+0.020(Z³−3Z)　→　G=F⁻¹<sub>Binomial(1250,Y)</sub>(Φ(Z″))/1250</b><small>RMS、lag-1、偏度、峰度、局部频谱变化、综合色不变性与逐格更新全部是发布门槛。</small></div></div></section>

        <section className="method-section"><div className="method-index">V46</div><div className="method-copy"><span className="section-tag">PUBLIC RELEASE · ENDPOINT HOLD · EXACT NNLS</span><h2>随机性不越过测量端点，光谱逆解不依赖裁零近似</h2><p>V46在Kodak颗粒曲线支持之外保持完整有限事件状态，消除激活概率趋零时的巨密度尾部。Status-M三记录到净染料／遮罩密度通过精确非负主动集求解；129³基础晶格负责平滑区域，5³精确microbrick只覆盖真实帧会触发的主动集边界与插值风险。三段真实素材最坏印片密度误差为0.0005094 D。</p><div className="equation"><span>认证边界</span><b>max |D<sub>adaptive</sub>−D<sub>exact</sub>| = 0.0005094 D &lt; 0.001 D</b><small>放映和扫描共享同一负片印片密度；未知记录间协方差仍保持未知。</small></div></div></section>

        <section className="method-section"><div className="method-index">V86</div><div className="method-copy"><span className="section-tag">PSD ENVELOPE · ONE-SIGMA SECANT · DIRECT SPECTRAL CROSS-CHECK</span><h2>先把“未知的层间统计”与“已经算错的阴影精度”分开</h2><p>固定Kodak三条48 µm RMS后，我们在所有正半定3×3相关矩阵上求线性Rec.709观察器外包络。共同事件降低综合色，却把亮度颗粒提高到独立记录的约1.48—1.67倍；它不能被叫作免费去彩噪。随后用V61联合光谱方程直接重算每个中性点与±1σ扰动，发现29³ runtime光谱LUT在−3 logE最坏偏离0.013987 D，而−2.5到0 logE低于0.000366 D。</p><div className="equation"><span>V87必须关闭的共同误差</span><b>max |D<sub>29³</sub>−D<sub>direct spectral</sub>| = 0.013987 D @ −3 logE</b><small>先把阴影误差压到0.001 D以下，再讨论联合协方差；V86不改变像素。</small></div></div></section>
        <section className="method-section"><div className="method-index">V85</div><div className="method-copy"><span className="section-tag">SOURCE PDF · VECTOR RE-EXTRACTION · STATUS-M DOMAIN</span><h2>不能通过伪造一条已测边缘，修复一个未知的联合分布</h2><p>我们重新渲染2003官方PDF并从矢量对象提取R/G/B路径、12个Sigma-D刻度与曝光轴。结果与V50/V72最大只差2.9×10<sup>−6</sup> D；0—4到−4—0平移也通过。ISO 10505要求彩色负片RMS使用Status-M光谱乘积，因此V61联合光谱逆解同样保留。蓝记录较大的边缘是公开证据，Kodak没有发布的是记录间协方差与交叉频谱。</p><div className="equation"><span>现在真正未知的量</span><b>已知diag(Σ<sub>D</sub>)　+　未知非对角项　→　未知观察器颗粒</b><small>V85不改变像素；下一步计算物理合法的观察器范围，而不是凭顺眼选择相关性。</small></div></div></section>

        <section className="method-section"><div className="method-index">V84</div><div className="method-copy"><span className="section-tag">PAIRED REAL RAW · TWO OBSERVERS · SCALE-INTEGRATED ENERGY</span><h2>固定三个对角线，不能固定投影机和扫描器看到的颗粒</h2><p>V84用T020的原生576²裁切和严格配对的有限事件比较α=0/.25/.5/1。确定性均值逐像素相同，三条48 µm边缘几乎不变；但α=1让放映亮度RMS上升53.8%、扫描上升43.2%，总RGB颗粒上升约四分之一。综合色虽下降，颗粒没有消失，只被重新分配。α=1被拒为默认值，.25/.50只保留诊断。</p><pre><code>{v84EnergyCode}</code></pre><div className="equation"><span>为什么边缘门禁仍不够</span><b>diag(Σ)固定　≠　wᵀΣw固定</b><small>下一步回查官方蓝记录RMS的图例、Status-M坐标和可见色彩映射，而不是用一个顺眼的α遮盖问题。</small></div></div></section>

        <section className="method-section"><div className="method-index">V83</div><div className="method-copy"><span className="section-tag">EXACT CROSS-SPECTRUM · STOCHASTIC DIR · DIRECT FINITE-SITE CHECK</span><h2>先按代码实际发生的顺序算，再判断研究叙述是否正确</h2><p>完整Profile复核发现，V72继承的是DIR后残差校准，不是我们一度写下的DIR前染料产率校准。V83把45组生产空间核、三种DIR扩散和48 µm孔径写成完整交叉频谱，并用真实有限Bernoulli／多项式事件直接验证。全部α和曝光端点的边缘RMS误差不超过1.076%，但α=0与α=1可以分别产生近零与约0.7—0.95的记录相关；官方边缘曲线无法替我们选择。</p><pre><code>{v83TransferCode}</code></pre><div className="equation"><span>本次真正得到的边界</span><b>marginal RMS compatible ≠ joint colour structure identified</b><small>V83不改变V72像素；下一步只允许做明确标注的共享事件不确定性对照，并同时检查协方差、尾部和尺度积分。</small></div></div></section>

        <section className="method-section"><div className="method-index">V82</div><div className="method-copy"><span className="section-tag">THREE-RECORD BERNOULLI POLYTOPE · EIGHT-CELL GATE</span><h2>一张合法的相关矩阵，仍然可能不是一份合法的彩色乳剂</h2><p>三条记录对可以各自通过Fréchet界，3×3相关矩阵也可以正半定，但八种RGB激活状态中仍可能至少一个必须为负概率。V82在60个曝光／群体三元组上测试7,500组独立pair-alpha：3,462组无联合解，其中1,484组是PSD假通过。因此未来采样器不能暴露三个互相独立的相关滑杆。</p><pre><code>{v82JointCode}</code></pre><div className="equation"><span>三记录可行区间</span><b>max(0,q<sub>RG</sub>+q<sub>RB</sub>−p<sub>R</sub>,…) ≤ P(111) ≤ min(q<sub>RG</sub>,q<sub>RB</sub>,q<sub>GB</sub>,1−Σp+Σq)</b><small>V81单一共用α家族在全部测试点通过八状态门禁，但α仍没有5279测量，因此不改变V72像素。</small></div></div></section>

        <section className="method-section"><div className="method-index">V81</div><div className="method-copy"><span className="section-tag">SHARED FINITE EVENTS · EXACT FEASIBILITY BOUND</span><h2>先证明随机耦合在数学上可行，再讨论它看起来像不像胶片</h2><p>V80证明成像后混合三条密度会破坏有限非负边界。V81因此把候选移回激活阶段：共享均匀变量可以保持每条Bernoulli边缘精确不变，但允许的相关上限由两条激活概率共同决定。对180个记录／群体／曝光组合，ρ=0.99只在13个中可行。α仍没有5279实测依据，所以当前V72像素不变。</p><pre><code>{v81BoundCode}</code></pre><div className="equation"><span>精确正相关上界</span><b>ρ<sub>max</sub>=[min(p<sub>i</sub>,p<sub>j</sub>)−p<sub>i</sub>p<sub>j</sub>] / √[p<sub>i</sub>(1−p<sub>i</sub>)p<sub>j</sub>(1−p<sub>j</sub>)]</b><small>这是概率恒等式，不是5279测量；未来候选还必须回闭48 µm RMS、密度界、综合色尾部、CPU/Metal身份和双观察器。</small></div></div></section>

        <section className="method-section"><div className="method-index">V45</div><div className="method-copy"><span className="section-tag">OFFICIAL CIE 1931 2° · 1 NM</span><h2>提升标准观察者，不借机改变胶片</h2><p>V45把同一组Kodak 2383染料与氙灯20 nm图表线性插值到1 nm，并通过CIE官方逐纳米综合色函数执行380–780 nm梯形积分。Status-A逆解、LAD、2383 H-D、V31正常工艺颜色边界和完整V42负片形成都被冻结。无染料白点变化低于4×10⁻⁷，证明它不是隐藏白平衡。</p><pre><code>{v45Code}</code></pre><div className="equation"><span>单变量版本</span><b>V45 = V44 + official CIE 1 nm observer</b><small>20 nm Kodak图表仍是材料信息上限；插值不会被描述成新的1 nm胶片测量。</small></div></div></section>

        <section className="pipeline"><div className="pipeline-line"><span>01<b>GH7 RAW</b><small>扩展线性RGB</small></span><i>→</i><span>02<b>虚拟曝光</b><small>V-Gamut / 光谱记录</small></span><i>→</i><span>03<b>5279显影</b><small>位点 · 染料 · DIR</small></span><i>→</i><span>04<b>观察分支</b><small>2383 或 2K DI</small></span><i>→</i><span>05<b>显示交付</b><small>BT.1886母版 / sRGB观看版</small></span></div></section>

        <section className="method-section"><div className="method-index">V44</div><div className="method-copy"><span className="section-tag">GATED OBSERVERS · SCALE-DECLARED REVIEW</span><h2>不能为了补偿播放器未知的缩放方式，反过来修改乳剂</h2><p>公开48µm RMS不能识别V43H猜测的NPS，公开资料也不支持它的Spirit与2383颗粒候选，因此V44恢复V42成像。完全直接的解析放映颜色没有通过暗部综合色门禁，所以保留V31正常工艺监看边界：2383拥有亮度和纹理，时期扫描只提供低频染料色度。原生5.7K、12-bit母版保持完整，审看版明确对1920像素栅格中的线性观察光做面积积分。</p><pre><code>{v44Code}</code></pre><div className="equation"><span>显示采样边界</span><b>L<sub>review</sub>=A<sub>pixel</sub>[EOTF<sub>BT.1886</sub>(V<sub>master</sub>)]</b><small>面积积分在线性观察光中完成，之后才编码sRGB；静帧从最终视频反解。</small></div></div></section>

        <section className="method-section"><div className="method-index">V43H</div><div className="method-copy"><span className="section-tag">HYPOTHESIS EDITION · ISOLATED / REVERSIBLE</span><h2>补全未知，不等于把猜测写成测量</h2><p>V43H冻结V42的RAW解释、颜色、H-D、DIR、MTF、48µm RMS、黑位与Gamma，只测试三个有资料方向但没有直接数值测量的中心候选：更细密的35mm空间频谱、向时期Spirit合成观察器移动25%，以及弱小、光谱中性的2383共模密度纹理。放映和扫描共享同一份实现负片；FSD只读取同次光谱积分返回的确定性均值，仍是一条独立对照。</p><pre><code>{v43hCode}</code></pre><div className="equation"><span>版本边界</span><b>V43H = V42 + isolated hypotheses</b><small>每个新自由度都能单独关闭；V42不会被实验Profile改写。</small></div></div></section>

        <section className="method-section"><div className="method-index">V42</div><div className="method-copy"><span className="section-tag">RESEARCH-CONFORMANT ENGINE · ONE PICTURE AUTHORITY</span><h2>这是V41研究成果的可执行收口，不是另一条“V2”画面风格</h2><p>V42不增加调色，也不声称取得新的5279材料测量。它把V37稳定积分相位、V40处理后颗粒度边界与无虚构2383随机颗粒、V41的12.5%色卡约束逐项做成运行门槛；Production默认使用经验证的Philox-u32 Bernoulli Metal实现，并要求每帧45个随机身份完整且无重复。两条12-bit BT.1886母版先落盘，sRGB观看版、截图与网页素材只能从实际母版反解生成；音频与时间码按V29边界保留。</p><div className="equation"><span>版本含义</span><b>V42 image model = V41 accepted baseline</b><small>版本号前进是因为引擎、审计与交付契约成为正式发布的一部分，而不是因为创造了新的审美外观。</small></div></div></section>

        <section className="method-section"><div className="method-index">V41</div><div className="method-copy"><span className="section-tag">T003 FIT · T005 HOLDOUT · LUMINANCE PRESERVED</span><h2>修正一个很可能存在的误差，同时把证据不足的幅度留作未知</h2><p>T003与未参与拟合的T005在合成色和自然色上重复同一色相／色度残差方向。全量矩阵和25%候选都在最终2383画面中过强，因此生产版只保留12.5%；不修改白平衡、曝光、黑位、对比或Gamma。中间广色域分量不再一律硬裁，但只有组合后的三条5279记录曝光全部非负时才保留有符号值。</p><pre><code>{v41ColourCode}</code></pre><div className="equation"><span>证据边界</span><b>Direction identified · magnitude provisional</b><small>两个同条件户外素材允许迈出保守一步，不允许宣称完整GH7相机标定。</small></div></div></section>

        <section className="method-section"><div className="method-index">V40</div><div className="method-copy"><span className="section-tag">MEASURED RANDOMNESS · BOUNDED COLOUR TAILS</span><h2>密度仍是画面，但未知的随机自由度不能假装成胶片</h2><p>V39把图像结构移回密度域，却把Kodak处理后48µm RMS反演成DIR前各速度层产额，并为2383建立没有分记录协方差或NPS证据的独立Poisson颗粒。边际RMS可以正确，最终暗部仍会出现稀疏原色尖峰。V40把5279颗粒度约束放回公开测量的处理后边界，让两条观察器共同积分明度与综合色高频；2383只保留有资料支持的确定性密度与MTF。不是在显示端降彩噪，而是从源头停止生成未识别的彩色随机项。</p><pre><code>{v40BoundaryCode}</code></pre><div className="equation"><span>发布条件</span><b>RMS + Covariance + Tail + Observer</b><small>三段、两分支、全部144个交付帧必须在原生5760×4320通过。</small></div></div></section>

        <section className="method-section"><div className="method-index">V39</div><div className="method-copy"><span className="section-tag">WITHDRAWN · DENSITY-FORMATION EXPERIMENT</span><h2>先形成一份真实密度，再让扫描器或印片观察它</h2><p>V39正确指出MTF和颗粒应在密度材料中形成，却错误地把处理后RMS当作DIR前约束，并虚构了独立2383三记录颗粒。此段保留为错误记录，不能作为当前算法说明。</p><pre><code>{densityFormationCode}</code></pre><div className="equation"><span>仍然成立的部分</span><b>D<sub>5279,real</sub>=MTF<sub>5279</sub>(D<sub>mean</sub>)+δD<sub>sites</sub></b><small>密度域位置正确；随机项的识别边界在V40修正。</small></div></div></section>

        <section className="method-section"><div className="method-index">V39</div><div className="method-copy"><span className="section-tag">ONE MASTER LIGHT · TWO EXPLICIT DELIVERIES</span><h2>编码可以不同，但解码后必须回到同一份母版光</h2><p>V38解决了摄影机OETF与显示EOTF混用，却仍从浮点Lobs独立压缩两份ProRes。V39的细密度结构让两次有损压缩产生可测分叉。因此V39先生成12-bit BT.1886专业母版，再从该实际母版反解Lmaster，以ProRes 4444 XQ生成sRGB本机观看版；JPEG与网页只继承后者。P3和HDR不用于制造未经证据支持的鲜艳度或亮度。</p><pre><code>{observerCode}</code></pre><div className="equation"><span>交付不变量</span><b>EOTF<sub>BT.1886</sub>(V<sub>master</sub>) ≈ EOTF<sub>sRGB</sub>(V<sub>Mac</sub>) ≈ L<sub>master</sub></b><small>三个原生24帧场景全部通过；最坏通道平均线性光误差0.001092，小于0.0015门槛。</small></div></div></section>

        <section className="method-section"><div className="method-index">V37</div><div className="method-copy"><span className="section-tag">INDEPENDENT SITES · STABLE INTEGRATION</span><h2>每一格胶片都更新，但成像算子不应该整幅跳动</h2><p>V36的乳剂位点本来已经逐帧独立，却又为每个记录层与速度层抽取一个全场亚像素相位，让双线性积分核每帧一起转向。V37保留frame参与Philox身份，只把15组尺寸类相位固定为黄金比例分布并整体旋转30°。因此颗粒不会被时间平滑、跟随运动或冻结；被删除的是额外的数值呼吸。</p><pre><code>{stablePhaseCode}</code></pre><div className="equation"><span>时间边界</span><b>G<sub>t</sub> ⟂ G<sub>t+1</sub>　·　K<sub>integration,t</sub>=K<sub>integration</sub></b><small>随机乳剂逐帧独立；积分核的统计传递在时间上稳定。</small></div></div></section>

        <section className="method-section"><div className="method-index">V35</div><div className="method-copy"><span className="section-tag">AUDITABLE PRODUCTION GRAPH</span><h2>随机实现可以独立，但每一个身份都必须可追溯</h2><p>Production不要求重现V34 PCG64的同一颗颗粒，但必须保持有限二项分布、48µm RMS、NPS、层间统计与时序独立。V35用完整Philox uint32随机字直接比较float32概率的2³²定点阈值；帧、记录层、速度层、尺寸类与全局像素坐标共同定义身份。异步Metal与CPU期望滤波重叠，45次/帧调用自动去重并写入provenance。</p><pre><code>{productionCode}</code></pre><div className="equation"><span>概率表示边界</span><b>|p<sub>u32</sub>−p<sub>float32</sub>| &lt; 2<sup>−32</sup></b><small>三个素材实测最大2.269×10⁻¹⁰；V34仍是Archive字节级参考。</small></div></div></section>

        <section className="method-section"><div className="method-index">V34</div><div className="method-copy"><span className="section-tag">PROCESSED MTF · SINGLE GENERATION</span><h2>总响应只计算一次，成片也只编码一次</h2><p>5279官方MTF来自处理后的胶片，并已经包含显影邻接的中频提升。V34保留这条总MTF，关闭后来重复加入的确定性层内DIR邻接；层间interimage与随机颗粒耦合仍在显影域。两条观察器随后在线性Rec.709中完成V31综合色边界，再分别进入唯一一次交付编码。</p><div className="equation"><span>确定性结构</span><b>MTF<sub>out</sub>=MTF<sub>Kodak, ECN-2</sub></b><small>不再乘以第二条DIR acutance响应。</small></div><div className="equation"><span>单世代输出</span><b>Proj<sub>master</sub>=Encode(A(Proj<sub>lin</sub>,Scan<sub>lin</sub>))</b><small>扫描母版直接Encode(Scanlin)；没有中间ProRes往返。</small></div></div></section>

        <section className="method-section"><div className="method-index">00</div><div className="method-copy"><span className="section-tag">V33 · INPUT / TONE / DELIVERY CONTRACT</span><h2>把相机见证、胶片曝光与技术中和拆成三个边界</h2><p>T002、T007与T031使用同一冻结胶片模型。相机见证固定0.00 stop，胶片输入明确为+0.45 stop；Technical Neutral关闭。验证器测量原生12-bit 1-1-1、硬黑、toe、p05–p95对比、32级单调色调映射和有效log-luma power。</p><div className="equation"><span>曝光边界</span><b>Camera=V709(RAW)　·　Film=5279(RAW·2<sup>0.45</sup>)</b><small>白平衡或tint校正若被灰卡授权，只能位于5279之前。</small></div><div className="equation"><span>黑场门槛</span><b>Black = fraction(Y′<sub>709</sub> ≤ 1/1023)</b><small>黑场、toe和gamma分别报告，不再由一个主观“更浓”判断代替。</small></div></div></section>

        <section className="method-section"><div className="method-index">01</div><div className="method-copy"><span className="section-tag">V28 · RAW INPUT CONTRACT</span><h2>从解码后的线性BT.2020到三条感色记录</h2><p>AVFoundation交付的是已经白平衡、去马赛克并标记为extended-linear BT.2020/D65的RGB，不是等待再次套Camera LUT的Bayer数据。V28只做线性BT.2020→XYZ D65→V-Gamut原色变换，不重复白平衡或非线性相机分离；虚拟曝光随后投向5279三条重叠感色记录。</p><div className="equation"><span>输入原色变换</span><b>RGB<sub>V-Gamut</sub> = M<sub>XYZ→V</sub> · M<sub>2020→XYZ</sub> · RGB<sub>decoded</sub></b><small>所有矩阵在线性光域执行；V-Log不是ProRes RAW解码曲线。</small></div><div className="equation"><span>记录曝光</span><b>E<sub>c</sub>(x,y) = Σ<sub>j</sub> M<sub>cj</sub> · RGB<sub>j</sub>(x,y)</b><small>c ∈ 红感、绿感、蓝感；M是受公开感色曲线约束的重叠响应。</small></div><div className="equation"><span>负片密度</span><b>D<sub>c</sub> = H<sub>c</sub>(log<sub>10</sub>E<sub>c</sub>)</b><small>Hc分别采样5279公开的R/G/B Status-M曲线。</small></div></div></section>

        <section className="method-section"><div className="method-index">02</div><div className="method-copy"><span className="section-tag">FINITE SITES</span><h2>快／中／慢有限位点</h2><p>每个颜色记录包含三个速度群体。逻辑斯蒂曲线给出某曝光下可显影位点的概率；二项采样保证群体完全未曝光或完全显影时随机方差自然下降。V21让青、品红、黄记录分别拥有自己的有效云尺寸、光学扩散和位点数量。</p><div className="equation"><span>激活概率</span><b>p<sub>c,k</sub> = σ((logE<sub>c</sub> − μ<sub>c,k</sub>) / w<sub>c</sub>)</b><small>k ∈ 快、中、慢；速度中心相互错开但显影区间重叠。</small></div><pre><code>{activationCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">03</div><div className="method-copy"><span className="section-tag">V26 · EXPOSURE-CONDITIONED DYE CLOUDS · V40 BOUNDARY</span><h2>颗粒是有限事件的多尺度光学积分</h2><p>每个快／中／慢群体再分成五种尺寸类别，作为连续染料云分布的数值求积。快层保留稍宽的大云尾部，慢层提高小云比例；三层激活概率随曝光交叉，阴影、中间调与高光自然形成不同空间频谱。V40不再逐层反演公开颗粒度，而是在随机DIR完成后，对最终处理负片通过48µm圆孔径校准。</p><div className="equation"><span>密度方差</span><b>σ²<sub>fraction</sub> = p(1−p) / n</b><small>有限位点决定形态；48µm RMS只在其公开测量的处理后边界约束最终密度残差。</small></div><pre><code>{cloudCode}</code></pre><pre><code>{grainCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">04</div><div className="method-copy"><span className="section-tag">V21 · DEVELOPMENT DIR</span><h2>从后处理邻接，改为显影时的反应—扩散</h2><p>V20使用总密度生成二维DIR场。V21让九个亚层的显影事件分别释放不同尺度的抑制场；它们在平面内扩散、按有限矩阵传播到接收层，并在各颜色记录合并前反馈到密度和随机偏差。</p><div className="equation"><span>显影域耦合</span><b>ΔD<sub>c,k</sub> = β<sub>c,k</sub> Σ<sub>j,m</sub> T<sub>c,k←j,m</sub>[G<sub>σj,m</sub>＊D<sub>j,m</sub> − D<sub>j,m</sub>]</b><small>均匀区域括号项为零，因此中性H-D保持不变；边缘和颜色分离曝光才产生耦合。</small></div><pre><code>{dirCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">05</div><div className="method-copy"><span className="section-tag">SPECTRAL NEGATIVE</span><h2>染料形成与有色遮罩</h2><p>三条记录并不是理想CMY。每条5279净染料曲线含有新染料与遮罩耦合剂消耗的合成结果。总透射率由完整D-min/橙色底与带符号的净密度共同决定。</p><div className="equation"><span>负片透射率</span><b>T<sub>neg</sub>(λ) = 10<sup>−[Dmin(λ)+Σ a<sub>c</sub>ΔD<sub>c,net</sub>(λ)]</sup></b><small>印片路径保留D-min；扫描匹配路径可以在正确观察器中估计并去底。</small></div></div></section>

        <section className="method-section"><div className="method-index">06</div><div className="method-copy"><span className="section-tag">V22 · ANALYTICAL PRINT DYES</span><h2>Status-A测到的密度，不能再当一次染料量</h2><p>状态密度计看到的是三种正片染料在指定光谱权重下共同形成的积分密度。V21把三条Status-A主曲线输出再次乘以CMY染料光谱，等于重复计算旁带吸收。V22逐曝光反解分析染料量，再在LAD附近施加层间曝光耦合，最后经过2383的非线性正片曲线。</p><div className="equation"><span>Status-A积分</span><b>D<sub>A,k</sub> = −log<sub>10</sub>[Σ<sub>λ</sub>10<sup>−Σj a<sub>j</sub>d<sub>j</sub>(λ)</sup>W<sub>k</sub>(λ) / Σ<sub>λ</sub>W<sub>k</sub>(λ)]</b><small>由三条主曲线数值反演a<sub>j</sub>，而不是把D<sub>A,k</sub>直接当a<sub>j</sub>。</small></div><div className="equation"><span>层间曝光</span><b>E′<sub>print</sub> = M(E<sub>print</sub> − E<sub>LAD</sub>) + E<sub>LAD</sub></b><small>LAD锚点不动；矩阵只描述锚点附近不同记录的互感方向。</small></div><pre><code>{printCode}</code></pre></div></section>

        <section className="method-section split-method"><div className="method-index">07</div><div className="method-copy"><span className="section-tag">THREE OBSERVERS · TWO OUTPUTS</span><h2>同一负片之后，结果开始分叉</h2><div className="method-branches"><article><b>5279 → 2383 → 氙灯</b><p>3200K印片灯穿过负片；2383三条感色层得到曝光，经过其陡峭H-D曲线形成正片染料，再用氙灯光谱和CIE观察器积分。正片MTF、Callier效应和投影flare属于这一支；2383随机颗粒因缺少协方差/NPS证据在V40暂不声称。</p></article><article><b>5279 → Scan / DI → Cineon</b><p>Status-M只负责数据表测量轴。扫描观察器用较宽的时期RGB探测响应积分透射光，再进行Spirit式film match、扫描孔径与Cineon 0.002D/code映射。这里终止于扫描／DI母版；蓝光或UHD的缩放、色度抽样、位深与压缩是后续独立交付层。</p><pre><code>{scanCode}</code></pre></article></div></div></section>

        <section className="method-section"><div className="method-index">08</div><div className="method-copy"><span className="section-tag">V30 · OFFICIAL LAD COLOUR ANCHOR</span><h2>用Kodak通道密度锚定2383，不让供应商LUT定义胶片颜色</h2><p>V30把2383的打印中性点从简化的相等密度改为H-61B官方目标1.09/1.06/1.03 D。供应商D60 LUT与数字化染料曲线的残差仍保留作研究记录，但它们没有足够证据支配最终色相或饱和度，因此显示权重为零。</p><div className="equation"><span>官方LAD与证据权重</span><b>D<sub>LAD</sub>=[1.09,1.06,1.03]　·　w<sub>D60</sub>=w<sub>hue</sub>=w<sub>sat</sub>=0</b><small>这是物理校准修正，不是减蓝或减饱和的创作调色。</small></div></div></section>

        <section className="method-section"><div className="method-index">08B</div><div className="method-copy"><span className="section-tag">V31 历史 · V40 最终适配器修正</span><h2>2383可以改变明暗，但不能因此把染料颜色当成银影抽走</h2><p>V30把综合色度写成C/L，再以更陡的2383中性曲线替换L；暗部因此同时失去绝对综合色度，与完整亮度颗粒叠加后接近留银。V31修正了低频颜色边界，但最终适配器又在观察器已经积分一次之后，重新加入了完整的放映高频综合色残差。V40删除这条重复路径：Period 2K只提供克制的低频OKLab a/b染料颜色，放映分支提供逐像素精确线性亮度，不再二次加入综合色高频项。这是工艺边界修正，不是增艳，也不是显示空间降噪。</p><div className="equation"><span>V40最终观察边界</span><b>ab<sub>out</sub>=G<sub>σ</sub>＊ab<sub>scan</sub>　·　Y<sub>out</sub>=Y<sub>proj</sub></b><small>σ=0.72px@2K；色域围绕目标Y压缩。5279、2383黑位、Gamma与密度域颗粒形成参数全部不变。</small></div></div></section>

        <section className="method-section"><div className="method-index">09</div><div className="method-copy"><span className="section-tag">V24 · COLOUR-GRAIN SEPARATION</span><h2>输出链观察颗粒，但不重新调色</h2><p>三条独立染料记录经过光谱观察会生成较强综合色纹理。V24在signed grain delta中分离Rec.709明度与综合色分量：明度纹理原样保留，综合色纹理分别按2383投影和Period 2K扫描孔径积分。确定性mean RGB不进入这一步，因此平均色相、饱和度和黑白灰严格不动。</p><pre><code>{colourGrainCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">10</div><div className="method-copy"><span className="section-tag">V40 · OUTPUT OBSERVERS</span><h2>观看条件、显示线性光与文件传递函数必须分开</h2><p>48 nit影院条件留在2383观察模型中，Period 2K完成态留在扫描观察器中。两者输出的都是display-linear Rec.709光。专业视频使用ProRes 4444 XQ与inverse BT.1886 gamma 2.4编码；当前Mac默认模式的直接观看版从实际母版派生，同样使用ProRes 4444 XQ，但采用明确的sRGB传递。XDR若切换到HDTV Video参考模式，应以专业母版为准。</p><pre><code>{observerCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">11</div><div className="method-copy"><span className="section-tag">EXACT ACCELERATION</span><h2>缓存固定颜色，复用平均负片，并行独立银盐事件</h2><p>193³格点继续缓存固定的分析染料与2383颜色物理。V25另删除每帧一次重复的确定性负片显影，并把45组二项抽样切成固定种子条带。分辨率、粒层数量、随机分布、光学积分和48µm回标都不变。</p><pre><code>{outputLutCode}</code></pre><pre><code>{parallelCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">12</div><div className="method-copy"><span className="section-tag">V26 · NPS + TEMPORAL VALIDATION</span><h2>“有机”必须能被空间与时间测量</h2><p>V26分别计算阴影、中间调和高光的径向密度噪声功率谱，并统计三速度层的贡献。它不把一张噪点纹理做平移或循环：帧号进入每个颜色记录、速度层和粒径级的固定随机种子，每一帧形成独立显影事件。</p><div className="equation"><span>时间独立约束</span><b>|corr(δD<sub>t</sub>, δD<sub>t+1</sub>)| → 0</b><small>四帧均匀场、三记录的最大绝对lag-1相关为0.0074；最大平均密度漂移0.00015D。</small></div></div></section>

        <section className="method-section"><div className="method-index">13</div><div className="method-copy"><span className="section-tag">V27 · FULL NEUTRAL-SCALE SCAN CALIBRATION</span><h2>只修扫描RGB比例，不重新塑造黑白灰</h2><p>V26扫描观察器在两个灰阶锚点之间留下了密度相关的绿色残差。V27让2049级中性曝光先完整经过5279显影、扫描光源与探测器、2K透射域孔径、Cineon映射和当时的Rec.709完成曲线，再按输出亮度查找RGB平衡。校正后立即恢复校正前的Rec.709亮度，因此黑位、对比、Gamma、局部颗粒亮度和高光位置都保持不变。这里描述扫描／DI观察器，不再把它误称为已经经过影碟压缩的蓝光成片。最新hourly审计还完整核对了2003年5279临时专利：它只证明identifier沿文档分支在5279／5218之间变化，没有任何数值颗粒参数，因此不能改写V26乳剂。</p><div className="equation"><span>条件中性化</span><b>RGB′ = C(Y)⊙RGB · Y / Y(C(Y)⊙RGB)</b><small>C只由中性曝光标定；有颜色的像素不会被拉回灰色。</small></div><pre><code>{scanNeutralCode}</code></pre></div></section>

        <section className="validation"><span className="section-tag">V40 THREE-SCENE · EVERY-FRAME VALIDATION</span><h2>三个场景共同通过什么</h2><div className="validation-grid"><div><b>原始分辨率</b><p>3 × 24帧 · 5760×4320</p></div><div><b>双12-bit交付</b><p>BT.1886母版 + sRGB观看版</p></div><div><b>彩色尾部</b><p>144帧原生审计</p></div><div><b>时间结构</b><p>独立位点 · 稳定积分</p></div><div><b>显示叠加</b><p>颗粒0层</p></div><div><b>颜色边界</b><p>冻结V38，无艺术调色</p></div></div></section>
      </main>
      <SiteFooter />
    </>
  );
}
