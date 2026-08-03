import Link from "next/link";
import { SiteFooter, SiteHeader } from "./components/SiteHeader";
import { InteractiveImage } from "./components/InteractiveImage";
import { EmulsionFlow } from "./components/EmulsionFlow";
import { ParameterPanel } from "./components/ParameterPanel";
import { versions } from "./data";

export default function Home() {
  const current = versions[versions.length - 1];
  const currentGallery = [
    { src: "/versions/v24-t020-projection.jpg", alt: "V24 T020 2383氙灯放映效果" },
    { src: "/versions/v24-t020-bluray.jpg", alt: "V24 T020 2K DI蓝光效果" },
  ];
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero">
          <EmulsionFlow />
          <div className="eyebrow">KODAK VISION 500T 5279 · DIGITAL EMULSION STUDY</div>
          <h1>不是给数码影像<br />贴一层颗粒。</h1>
          <p className="hero-lead">我们的目标，是重建曝光、银盐位点、染料云、层间抑制、印片与扫描共同形成画面的过程。</p>
          <div className="hero-actions"><Link href="/versions" className="button primary">观看版本演进</Link><Link href="/research" className="button">阅读研究</Link></div>
          <div className="hero-meta"><span><b>21</b> 个已归档版本</span><span><b>30</b> 条核心资料</span><span><b>12-bit</b> 5.7K主链</span></div>
        </section>

        <section className="current-section wrap">
          <div className="section-intro"><span>当前基线 · V24</span><h2>同一张负片，两种历史上真实存在的结果</h2><p>左侧经过5279负片、分析染料反演、2383正片和氙灯投影；右侧经过负片扫描、Cineon/2K DI与蓝光完成。V24把V23的早期CCD／16mm倾向拆成空间频谱与综合色颗粒两个问题，在平均颜色完全不动的前提下重新逼近35mm。</p></div>
          <div className="current-visual-layout">
            <div className="hero-comparison">
              <figure><div className="image-title"><b>2383</b><span>PRINT / XENON</span></div><InteractiveImage src="/versions/v24-t020-projection.jpg" previewSrc="/versions/v24-t020-projection-sm.jpg" videoSrc="/versions/v24-t020-projection-live-srgb.mp4" sizes="(max-width: 680px) 100vw, 42vw" alt="V24 T020 2383氙灯放映效果" gallery={currentGallery} initialIndex={0} /><figcaption>35mm细颗粒频谱、综合色积分、分析染料与2383氙灯链</figcaption></figure>
              <figure><div className="image-title"><b>2K DI</b><span>SPIRIT / BLU-RAY</span></div><InteractiveImage src="/versions/v24-t020-bluray.jpg" previewSrc="/versions/v24-t020-bluray-sm.jpg" videoSrc="/versions/v24-t020-bluray-live-srgb.mp4" sizes="(max-width: 680px) 100vw, 42vw" alt="V24 T020 2K DI蓝光效果" gallery={currentGallery} initialIndex={1} /><figcaption>同一乳剂经时期2K孔径与更强综合色颗粒积分完成</figcaption></figure>
            </div>
            <ParameterPanel groups={current.parameters} version={current.version} status={current.status} changes={current.changes} />
          </div>
        </section>

        <section className="thesis wrap">
          <div className="section-number">01</div>
          <div><span className="kicker">核心命题</span><h2>噪点不是附加物。<br />随机性本身参与成像。</h2></div>
          <div className="thesis-copy"><p>数字噪点通常在画面完成后相加；彩色负片的随机性则发生在画面形成之前。有限银盐位点是否显影，会同时改变染料量、局部密度、DIR释放和邻层反应。</p><p>显影完成后银影会被漂白和定影移除，最终被扫描或印片观察到的是染料云。因此我们模拟的是“银盐位点播种的染料云场”，而不是永久悬浮的银颗粒。</p><p><b>Baseline原则：</b>只重建胶片、印片和扫描的成像；艺术调色留在模型之外。</p><Link href="/algorithm">查看公式与关键代码 →</Link></div>
        </section>

        <section className="v21-panel wrap">
          <div><span className="eyebrow">V24 · 35MM TEXTURE SEPARATION</span><h2>保留沸腾，去掉“数码彩噪”的识别线索</h2></div>
          <ol>
            <li><b>空间频谱重分配</b><span>减少大染料云和总体相关尺度，降低像16mm一样成团的低频纹理。</span></li>
            <li><b>综合色／明度分离</b><span>只积分综合色颗粒；明度颗粒与逐帧随机性完整保留。</span></li>
            <li><b>平均颜色锁定</b><span>候选与V23的平均画面最大绝对差为0，色相、饱和度和黑白灰没有偷调。</span></li>
            <li><b>官方幅度守恒</b><span>均匀曝光的5279 48µm RMS误差保持在约0.6–1.4%。</span></li>
          </ol>
          <Link href="/research#v24" className="button">阅读V24验证结果</Link>
        </section>

        <section className="route-grid wrap">
          <Link href="/versions"><span>ARCHIVE</span><h3>版本档案</h3><p>从V4到V24，逐版对照两种观看链，并记录错误和修正。</p><b>进入 →</b></Link>
          <Link href="/research"><span>PAPER</span><h3>研究笔记</h3><p>乳剂层、遮罩、DIR、颗粒、黑位、扫描器与完整引用。</p><b>进入 →</b></Link>
          <Link href="/algorithm"><span>METHOD</span><h3>算法说明</h3><p>从RAW到负片、2383与Cineon的公式、流程和关键代码。</p><b>进入 →</b></Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
