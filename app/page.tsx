import Link from "next/link";
import { SiteFooter, SiteHeader } from "./components/SiteHeader";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero">
          <div className="eyebrow">KODAK VISION 500T 5279 · DIGITAL EMULSION STUDY</div>
          <h1>不是给数码影像<br />贴一层颗粒。</h1>
          <p className="hero-lead">我们的目标，是重建曝光、银盐位点、染料云、层间抑制、印片与扫描共同形成画面的过程。</p>
          <div className="hero-actions"><Link href="/versions" className="button primary">观看版本演进</Link><Link href="/research" className="button">阅读研究</Link></div>
          <div className="hero-meta"><span><b>19</b> 个已归档版本</span><span><b>20</b> 条核心资料</span><span><b>12-bit</b> 5.7K主链</span></div>
        </section>

        <section className="current-section wrap">
          <div className="section-intro"><span>当前基线 · V22</span><h2>同一张负片，两种历史上真实存在的结果</h2><p>左侧经过5279负片、分析染料反演、2383正片和氙灯投影；右侧经过负片扫描、Cineon/2K DI与蓝光完成。两者共享同一帧乳剂随机实现，但拥有各自的观察器、黑位和颜色。</p></div>
          <div className="hero-comparison">
            <figure><div className="image-title"><b>2383</b><span>PRINT / XENON</span></div><img src="/versions/v22-projection.jpg" alt="V22 2383氙灯放映效果" /><figcaption>分析染料、LAD层间耦合、典型影院flare与相对色度观看适配</figcaption></figure>
            <figure><div className="image-title"><b>2K DI</b><span>SPIRIT / BLU-RAY</span></div><img src="/versions/v22-bluray.jpg" alt="V22 2K DI蓝光效果" /><figcaption>宽带时期扫描观察器、Cineon密度与2K积分蓝光完成</figcaption></figure>
          </div>
        </section>

        <section className="thesis wrap">
          <div className="section-number">01</div>
          <div><span className="kicker">核心命题</span><h2>噪点不是附加物。<br />随机性本身参与成像。</h2></div>
          <div className="thesis-copy"><p>数字噪点通常在画面完成后相加；彩色负片的随机性则发生在画面形成之前。有限银盐位点是否显影，会同时改变染料量、局部密度、DIR释放和邻层反应。</p><p>显影完成后银影会被漂白和定影移除，最终被扫描或印片观察到的是染料云。因此我们模拟的是“银盐位点播种的染料云场”，而不是永久悬浮的银颗粒。</p><Link href="/algorithm">查看公式与关键代码 →</Link></div>
        </section>

        <section className="v21-panel wrap">
          <div><span className="eyebrow">V22 · IMPLEMENTED &amp; VALIDATED</span><h2>把胶片化学与显示器观看分开</h2></div>
          <ol>
            <li><b>先反解分析染料量</b><span>Status-A积分密度不再被重复当作CMY染料量。</span></li>
            <li><b>LAD锚定层间耦合</b><span>在正片H-D之前处理互感曝光，并保持LAD中性锚点。</span></li>
            <li><b>D60只提供相对色度</b><span>减去厂商变换自身的中性响应，避免绝对白点染色。</span></li>
            <li><b>保持测试而非主观选图</b><span>六色中位色相误差7.94°→1.46°，饱和度全部落在七套厂商变换包络内。</span></li>
          </ol>
          <Link href="/research#v22" className="button">阅读V22验证结果</Link>
        </section>

        <section className="route-grid wrap">
          <Link href="/versions"><span>ARCHIVE</span><h3>版本档案</h3><p>从V4到V22，逐版对照两种观看链，并记录错误和修正。</p><b>进入 →</b></Link>
          <Link href="/research"><span>PAPER</span><h3>研究笔记</h3><p>乳剂层、遮罩、DIR、颗粒、黑位、扫描器与完整引用。</p><b>进入 →</b></Link>
          <Link href="/algorithm"><span>METHOD</span><h3>算法说明</h3><p>从RAW到负片、2383与Cineon的公式、流程和关键代码。</p><b>进入 →</b></Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
