import Link from "next/link";
import { SiteFooter, SiteHeader } from "./components/SiteHeader";
import { InteractiveImage } from "./components/InteractiveImage";
import { EmulsionFlow } from "./components/EmulsionFlow";
import { ParameterPanel } from "./components/ParameterPanel";
import { versions } from "./data";

export default function Home() {
  const current = versions[versions.length - 1];
  const currentGallery = [
    { src: "/versions/v26-t020-projection.jpg", alt: "V26 T020 2383放映监看参考" },
    { src: "/versions/v26-t020-bluray.jpg", alt: "V26 T020 Rec.709蓝光参考" },
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
          <div className="hero-meta"><span><b>23</b> 个已归档版本</span><span><b>33</b> 条核心资料</span><span><b>12-bit</b> 5.7K主链</span></div>
        </section>

        <section className="current-section wrap">
          <div className="section-intro"><span>当前基线 · V26</span><h2>同一振幅，不同曝光长出不同颗粒频谱</h2><p>V25修正版的颜色、黑位、对比与Gamma完全锁定。V26让快、中、慢乳剂分别拥有自己的五级染料云分布：阴影由较大的快层晶体主导，高光逐渐交给更细的慢层；两条观察链仍从同一份逐帧负片出发。</p></div>
          <div className="current-visual-layout">
            <div className="hero-comparison">
              <figure><div className="image-title"><b>2383</b><span>REC.709 MONITOR / 1-1-1</span></div><InteractiveImage src="/versions/v26-t020-projection.jpg" previewSrc="/versions/v26-t020-projection-sm.jpg" videoSrc="/versions/v26-t020-projection-live-srgb.mp4" sizes="(max-width: 680px) 100vw, 42vw" alt="V26 T020 2383放映监看参考" gallery={currentGallery} initialIndex={0} /><figcaption>48 nit影院观察结果的Rec.709监看呈现</figcaption></figure>
              <figure><div className="image-title"><b>2K DI</b><span>REC.709 / 1-1-1 / BT.1886 DISPLAY</span></div><InteractiveImage src="/versions/v26-t020-bluray.jpg" previewSrc="/versions/v26-t020-bluray-sm.jpg" videoSrc="/versions/v26-t020-bluray-live-srgb.mp4" sizes="(max-width: 680px) 100vw, 42vw" alt="V26 T020 Rec.709蓝光参考" gallery={currentGallery} initialIndex={1} /><figcaption>时期2K扫描；BT.1886仅用于参考显示验证</figcaption></figure>
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
          <div><span className="eyebrow">V26 · EXPOSURE-CONDITIONED GRAIN</span><h2>颗粒不是贴图；曝光决定哪一层参与成像</h2></div>
          <ol>
            <li><b>快／中／慢分布</b><span>三速度层不再共用同一套大、小染料云比例。</span></li>
            <li><b>曝光相关频谱</b><span>阴影快层约占61–65%颗粒功率；高光慢层约占50–59%。</span></li>
            <li><b>时间独立</b><span>每帧重新显影有限位点，最大lag-1相关约0.0074，不移动噪点贴图。</span></li>
            <li><b>基线锁定</b><span>48µm RMS、颜色、黑位、Gamma、MTF与两套观察器均不改变。</span></li>
          </ol>
          <Link href="/research#v26" className="button">阅读V26验证结果</Link>
        </section>

        <section className="route-grid wrap">
          <Link href="/versions"><span>ARCHIVE</span><h3>版本档案</h3><p>从V4到V26，逐版对照两种观看链，并记录错误和修正。</p><b>进入 →</b></Link>
          <Link href="/research"><span>PAPER</span><h3>研究笔记</h3><p>乳剂层、遮罩、DIR、颗粒、黑位、扫描器与完整引用。</p><b>进入 →</b></Link>
          <Link href="/algorithm"><span>METHOD</span><h3>算法说明</h3><p>从RAW到负片、2383与Cineon的公式、流程和关键代码。</p><b>进入 →</b></Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
