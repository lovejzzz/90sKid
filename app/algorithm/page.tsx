import { SiteFooter, SiteHeader } from "../components/SiteHeader";

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

export default function AlgorithmPage() {
  return (
    <>
      <SiteHeader />
      <main className="algorithm-page wrap">
        <header className="page-header"><span className="eyebrow">METHOD · CURRENT V21</span><h1>算法不是一枚滤镜。<br />它是一条成像链。</h1><p>这里公开V21模型的关键公式和真正执行的代码结构。为便于阅读，省略工程性的缓存、色彩元数据和文件编码部分。</p></header>

        <section className="pipeline"><div className="pipeline-line"><span>01<b>GH7 RAW</b><small>扩展线性RGB</small></span><i>→</i><span>02<b>虚拟曝光</b><small>V-Gamut / 光谱记录</small></span><i>→</i><span>03<b>5279显影</b><small>位点 · 染料 · DIR</small></span><i>→</i><span>04<b>观察分支</b><small>2383 或 2K DI</small></span><i>→</i><span>05<b>12-bit母版</b><small>Rec.709 1-1-1</small></span></div></section>

        <section className="method-section"><div className="method-index">01</div><div className="method-copy"><span className="section-tag">EXPOSURE</span><h2>从RAW到三条感色记录</h2><p>输入保持在线性光域，不对RAW Bayer值错误套用V-Log曲线。Panasonic官方RAW Gamut变换负责把解码后的扩展线性BT.2020映射到V-Gamut；虚拟曝光随后投向5279三条重叠的感色记录。</p><div className="equation"><span>记录曝光</span><b>E<sub>c</sub>(x,y) = Σ<sub>j</sub> M<sub>cj</sub> · RGB<sub>j</sub>(x,y)</b><small>c ∈ 红感、绿感、蓝感；M是受公开感色曲线约束的重叠响应。</small></div><div className="equation"><span>负片密度</span><b>D<sub>c</sub> = H<sub>c</sub>(log<sub>10</sub>E<sub>c</sub>)</b><small>Hc分别采样5279公开的R/G/B Status-M曲线。</small></div></div></section>

        <section className="method-section"><div className="method-index">02</div><div className="method-copy"><span className="section-tag">FINITE SITES</span><h2>快／中／慢有限位点</h2><p>每个颜色记录包含三个速度群体。逻辑斯蒂曲线给出某曝光下可显影位点的概率；二项采样保证群体完全未曝光或完全显影时随机方差自然下降。V21让青、品红、黄记录分别拥有自己的有效云尺寸、光学扩散和位点数量。</p><div className="equation"><span>激活概率</span><b>p<sub>c,k</sub> = σ((logE<sub>c</sub> − μ<sub>c,k</sub>) / w<sub>c</sub>)</b><small>k ∈ 快、中、慢；速度中心相互错开但显影区间重叠。</small></div><pre><code>{activationCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">03</div><div className="method-copy"><span className="section-tag">DYE CLOUDS</span><h2>颗粒是有限事件的光学积分</h2><p>每个群体再分成三种连续尺度近似；小型云占主导，稀疏大云提供不规则关联。样本场减去同样核函数处理的期望场，避免逐帧颗粒改变平均色调。</p><div className="equation"><span>密度方差</span><b>σ²<sub>fraction</sub> = p(1−p) / n</b><small>最终幅度再通过48µm圆孔径回标5279公开RMS曲线。</small></div><pre><code>{grainCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">04</div><div className="method-copy"><span className="section-tag">V21 · DEVELOPMENT DIR</span><h2>从后处理邻接，改为显影时的反应—扩散</h2><p>V20使用总密度生成二维DIR场。V21让九个亚层的显影事件分别释放不同尺度的抑制场；它们在平面内扩散、按有限矩阵传播到接收层，并在各颜色记录合并前反馈到密度和随机偏差。</p><div className="equation"><span>显影域耦合</span><b>ΔD<sub>c,k</sub> = β<sub>c,k</sub> Σ<sub>j,m</sub> T<sub>c,k←j,m</sub>[G<sub>σj,m</sub>＊D<sub>j,m</sub> − D<sub>j,m</sub>]</b><small>均匀区域括号项为零，因此中性H-D保持不变；边缘和颜色分离曝光才产生耦合。</small></div><pre><code>{dirCode}</code></pre></div></section>

        <section className="method-section"><div className="method-index">05</div><div className="method-copy"><span className="section-tag">SPECTRAL NEGATIVE</span><h2>染料形成与有色遮罩</h2><p>三条记录并不是理想CMY。每条5279净染料曲线含有新染料与遮罩耦合剂消耗的合成结果。总透射率由完整D-min/橙色底与带符号的净密度共同决定。</p><div className="equation"><span>负片透射率</span><b>T<sub>neg</sub>(λ) = 10<sup>−[Dmin(λ)+Σ a<sub>c</sub>ΔD<sub>c,net</sub>(λ)]</sup></b><small>印片路径保留D-min；扫描匹配路径可以在正确观察器中估计并去底。</small></div></div></section>

        <section className="method-section split-method"><div className="method-index">06</div><div className="method-copy"><span className="section-tag">THREE OBSERVERS · TWO OUTPUTS</span><h2>同一负片之后，结果开始分叉</h2><div className="method-branches"><article><b>5279 → 2383 → 氙灯</b><p>3200K印片灯穿过负片；2383三条感色层得到曝光，经过其陡峭H-D曲线形成正片染料，再用氙灯光谱和CIE观察器积分。正片MTF、细颗粒、Callier效应和投影flare属于这一支；显示适配只借用扫描分支的中性明度，不复制其色度。</p></article><article><b>5279 → Period 2K → Cineon</b><p>Status-M窄带观察器只用于解出数据表的H-D与染料量轴。成片扫描则用较宽的时期RGB探测响应积分透射光，再进行Spirit式film match、2K孔径、Cineon 0.002D/code与蓝光显示完成。</p><pre><code>{scanCode}</code></pre></article></div></div></section>

        <section className="validation"><span className="section-tag">V21 VALIDATION</span><h2>这次重排通过了什么</h2><div className="validation-grid"><div><b>平均响应</b><p>中性H-D最大误差约2.4×10⁻⁷ D</p></div><div><b>颗粒幅度</b><p>48µm孔径RMS误差约0–1.5%</p></div><div><b>空间结构</b><p>三记录独立形态仍受5279 MTF约束</p></div><div><b>颜色分离</b><p>六色阶梯的DIR变化有界</p></div><div><b>两链差异</b><p>代表帧中位色相差约4.8°</p></div><div><b>母版</b><p>5760×4320 · 12-bit · ProRes 4444</p></div></div></section>
      </main>
      <SiteFooter />
    </>
  );
}
