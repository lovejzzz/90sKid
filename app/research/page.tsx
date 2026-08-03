import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { references } from "../data";

function Cite({ ids }: { ids: string[] }) { return <sup className="cite">{ids.map((id) => <a key={id} href={`#ref-${id}`}>{id.slice(1)}</a>)}</sup>; }

export default function ResearchPage() {
  return (
    <>
      <SiteHeader />
      <main className="paper-page wrap">
        <header className="paper-header"><span className="eyebrow">RESEARCH NOTE · REVISION 2026.08</span><h1>从银盐位点到电影画面：<br />5279数码乳剂重建研究</h1><p className="abstract"><b>摘要</b>　本项目尝试从数码RAW重建Kodak VISION 500T 5279的成像过程，而不是复刻一组静态LUT。模型覆盖有限感光位点、彩色染料云、分层速度、DIR层间效应、5279光谱遮罩、2383印片和时期2K扫描。结论按“5279直接数据 / 同期柯达机制 / 有边界推断”分级。</p><div className="paper-byline"><span>持续研究记录</span><span>方法 · 实验 · 错误复盘</span></div></header>

        <div className="paper-layout">
          <aside className="paper-toc"><b>目录</b><a href="#premise">1　研究命题</a><a href="#layers">2　多层乳剂</a><a href="#grain">3　颗粒与染料云</a><a href="#mask">4　有色遮罩</a><a href="#dir">5　DIR层间效应</a><a href="#scanner">6　扫描器耦合</a><a href="#black">7　黑位与高光</a><a href="#v21">8　V21计划</a><a href="#limitations">9　边界</a><a href="#references">引用</a></aside>
          <article className="paper-body">
            <section id="premise"><div className="section-tag">01 · PREMISE</div><h2>研究命题</h2><p>数码相机先形成规则像素采样，噪声通常被视作需要移除或后加的信号扰动。胶片的微观随机性发生得更早：光子是否使某个卤化银晶体形成可显影潜影，会决定随后是否生成染料。因此“颗粒”与图像密度并不是两个完全独立的对象。<Cite ids={["R2", "R3", "R13"]} /></p><blockquote>画面不是先存在，再长出颗粒；画面密度就是大量离散显影事件经过光学观察后的统计结果。</blockquote><p>这不意味着数码无法逼近胶片。关键是不要在显示空间模拟表面噪声，而要在曝光和显影域重新采样有限事件，再让印片或扫描器观察它们。</p></section>

            <section id="layers"><div className="section-tag">02 · LAYERS</div><h2>一条颜色记录内部仍有多个速度层</h2><p>彩色负片至少包含蓝、绿、红感光记录，分别生成黄、品红、青染料。每条记录又可以由快、中、慢乳剂组成，以覆盖暗部、中间调和高光。较快群体通常依赖更大的有效晶体，较慢群体更细密；三者的显影区间彼此重叠。<Cite ids={["R2", "R7", "R15"]} /></p><div className="layer-diagram" aria-label="乳剂层示意"><div className="coat">保护层 / UV</div><div className="blue"><b>蓝感记录</b><span>快 · 中 · 慢 → 黄染料</span></div><div className="filter">黄色滤光层</div><div className="green"><b>绿感记录</b><span>快 · 中 · 慢 → 品红染料</span></div><div className="inter">中间层 / 清除剂</div><div className="red"><b>红感记录</b><span>快 · 中 · 慢 → 青染料</span></div><div className="base">片基 + rem-jet</div></div><p>V14—V20让三个颜色记录共用一套代表性粒径。同期Kodak示例证明，实际的青、品红、黄记录可以拥有明显不同、甚至非单调的晶体结构。V21将把这种自由度放开，但最终必须回到5279公开的R/G/B RMS颗粒和MTF曲线，而不能把专利示例冒充5279秘方。<Cite ids={["R1", "R11"]} /></p></section>

            <section id="grain"><div className="section-tag">03 · GRAIN</div><h2>最终看到的是染料云，不是留下的银影</h2><p>曝光后的卤化银被彩色显影剂还原成金属银；显影剂同时氧化并与成色剂反应，在同一位置生成不溶染料。随后漂白把金属银转回银盐，定影将银盐移走。处理完成的彩色负片留下的是染料图像和过程存留的有色遮罩。<Cite ids={["R2", "R3", "R15"]} /></p><div className="process-strip"><span>曝光</span><i>→</i><span>潜影位点</span><i>→</i><span>银显影 + 染料生成</span><i>→</i><span>漂白 / 定影移银</span><i>→</i><b>染料云图像</b></div><p>因此“银盐沸腾感”更准确的算法表达，是每一帧重新采样受曝光约束的有限显影位点；染料云的大小、重叠、亚像素位置和光学积分决定可见颗粒。随机样本改变，条件均值必须不漂移。</p><div className="equation"><span>有限位点</span><b>Var(f) = p(1 − p) / n</b><small>未曝光时p≈0、完全显影时p≈1，方差都下降；转换区间最大。</small></div></section>

            <section id="mask"><div className="section-tag">04 · MASK</div><h2>橙色底是局部颜色校正留下的常数项</h2><p>真实青、品红染料存在不希望的旁带吸收。红感层中的品红色遮罩耦合剂会在生成青染料时被消耗；青染料增加造成的绿/蓝旁带吸收，与品红耦合剂减少造成的密度下降在波段平均上互相补偿。绿感层的黄色遮罩耦合剂执行类似功能。<Cite ids={["R1", "R2", "R3"]} /></p><p>所以5279数据表中“D-mins subtracted”的染料曲线是净密度变化：新染料吸收加上遮罩耦合剂被消耗的反向变化。局部负值具有物理意义。把它裁成正值，或在光谱染料之外再加一遍橙色遮罩，都会造成明显色偏。</p><div className="equation"><span>净光谱密度</span><b>ΔD<sub>net</sub>(λ) = D<sub>dye</sub>(λ) − D<sub>mask consumed</sub>(λ)</b><small>形状不可能逐波长完美抵消；残余光谱误差构成片种色彩性格。</small></div></section>

            <section id="dir"><div className="section-tag">05 · DIR</div><h2>DIR把局部清晰度和饱和度变成同一个化学问题</h2><p>显影抑制剂释放型成色剂会在显影处释放抑制剂。抑制剂既能在本层扩散形成边缘邻接效应，提高中频MTF；也能迁移到相邻颜色记录，改变中性曝光和颜色分离曝光之间的gamma关系。中间层、清除剂和带电聚合物会限制或反射这种迁移。<Cite ids={["R6", "R11"]} /></p><p>这意味着饱和度不是全局HSV旋钮。Kodak同期实验用“颜色分离曝光gamma / 中性曝光gamma”衡量层间色彩效应；同一种DIR在不同层位可以增加或降低饱和度。</p><div className="equation"><span>颜色分离饱和度指标</span><b>S<sub>c</sub> ≈ γ<sub>separation,c</sub> / γ<sub>neutral,c</sub></b><small>它随颜色、曝光、邻域和层位置变化。</small></div><p>V20仍在总密度形成后计算二维抑制场。V21会让每个快/中/慢群体在显影时释放抑制剂，先扩散和抑制邻层，再合并密度。</p></section>

            <section id="scanner"><div className="section-tag">06 · SCANNER</div><h2>Status-M测量器不等于时期Telecine</h2><p>5279数据表的H-D和颗粒是Status-M测量结果；真正的Telecine拥有自己的光源、滤光器和探测器响应。Kodak 1994年的扫描相关专利指出，典型Telecine红通道在远离青染料峰值的位置读数，同时会接收到品红染料长波尾部。结果是红调制不足、串色，并需要电子增益，进一步放大噪声。<Cite ids={["R11", "R12"]} /></p><p>更重要的是，Kodak会直接改变负片红记录相对绿记录的反差，使Telecine在独立通道校正之前就接近R/G反差一致。底片与扫描器从设计阶段已经耦合。</p><div className="observer-grid"><div><b>Status-M</b><span>窄带标准密度</span><small>只用于匹配数据表</small></div><div><b>Period 2K</b><span>宽带探测器 + 光学film match</span><small>形成DI / Cineon</small></div><div><b>2383 Print</b><span>印片灯 + 正片感色层</span><small>形成放映正片</small></div></div><p>《霹雳娇娃2》使用5279负片、2K数字中间片并由EFILM完成后期，是极有价值的2003完成态参考。但它还包含创作调色、2K系统限制和后来家庭媒体转换，因此不能直接当作未调色的5279测量。<Cite ids={["R9", "R10"]} /></p></section>

            <section id="black"><div className="section-tag">07 · TONE</div><h2>黑位、高光、颗粒和曲线斜率必须一起校准</h2><p>降低整体负片反差可以减少扫描噪声，却也可能让中间调发平，并不能自动改善暗部可见性。同期Kodak实验通过改变toe与中段斜率的比例，在较低测量噪声下保持中间调并改善阴影细节。<Cite ids={["R12"]} /></p><p>放映黑由2383最大密度、投影杂散光和银幕亮度共同限定；蓝光黑是扫描、Cineon映射、显示OETF和母版黑锚点的共同决定。两者不能通过同一条lift/gamma/gain曲线互相追平。</p></section>

            <section id="v21"><div className="section-tag">08 · NEXT</div><h2>V21的可验证目标</h2><ol className="research-plan"><li><b>重新数字化公开曲线</b><span>给H-D、MTF、RMS颗粒和光谱曲线加入读图不确定区间。</span></li><li><b>颜色记录独立形态</b><span>分别拟合青、品红、黄记录的快中慢粒径和容量。</span></li><li><b>反应—扩散DIR</b><span>在亚层显影阶段生成抑制剂，加入横向扩散、层间传播、阻隔与清除。</span></li><li><b>七组阶梯验证</b><span>同时测量中性、红、绿、蓝、青、品红、黄的gamma和局部边缘。</span></li><li><b>三个观察器</b><span>Status-M、时期2K扫描、5279→2383印片完全分离。</span></li><li><b>最后才渲染实拍</b><span>诊断楔通过后，再输出5.7K 12-bit放映和蓝光版本。</span></li></ol></section>

            <section id="limitations"><div className="section-tag">09 · LIMITS</div><h2>我们知道什么，也明确不知道什么</h2><ul><li><b>直接知道：</b>5279公开的曲线、RMS颗粒、MTF、感色和净染料密度。</li><li><b>机制上知道：</b>Kodak同期多层乳剂、DIR、遮罩、Telecine补偿和ECN-2过程。</li><li><b>仍在推断：</b>5279每一亚层的真实晶体尺寸、涂布量、DIR化合物与扩散常数。</li><li><b>无法由RGB恢复：</b>原始场景的连续光谱、镜头内部光谱透过率和真实化学批次。</li></ul><p>网站中所有推断都会保留来源等级。模型追求的是受测量约束的物理近似，不宣称破解Kodak未公开配方。</p></section>
          </article>
        </div>

        <section id="references" className="references"><div className="section-tag">REFERENCES</div><h2>引用与资料</h2><ol>{references.map((ref) => <li id={`ref-${ref.id}`} key={ref.id}><span>{ref.id.slice(1).padStart(2, "0")}</span><div><a href={ref.url} target="_blank" rel="noreferrer">{ref.title}</a><small>{ref.type}</small></div></li>)}</ol></section>
      </main>
      <SiteFooter />
    </>
  );
}
