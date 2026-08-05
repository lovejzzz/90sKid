"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { SiteFooter, SiteHeader } from "./components/SiteHeader";
import { InteractiveImage } from "./components/InteractiveImage";
import { EmulsionFlow } from "./components/EmulsionFlow";
import { ParameterPanel } from "./components/ParameterPanel";
import { references, versions } from "./data";
import { useLanguage } from "./i18n";
import { versionEnglish } from "./versionEnglish";
import { withBasePath } from "./basePath";

export default function Home() {
  const { language, text } = useLanguage();
  const current = versions[versions.length - 1];
  const currentEnglish = versionEnglish[current.version];
  const sourceName = current.version === "V32" ? "T007" : "T002";
  const currentGallery = [
    { src: current.projection.src, alt: `${current.version} ${sourceName} 2383 projection monitor reference` },
    { src: current.bluray.src, alt: `${current.version} ${sourceName} Rec.709 Blu-ray reference` },
    ...(current.camera ? [{ src: current.camera.src, alt: `${current.version} ${sourceName} Panasonic V-709 camera baseline` }] : []),
  ];
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero" style={{ "--hero-image": `url("${withBasePath("/versions/v32-t007-projection.jpg")}")` } as CSSProperties}>
          <EmulsionFlow />
          <div className="eyebrow">KODAK VISION 500T 5279 · DIGITAL EMULSION STUDY</div>
          <h1>{text(<>颗粒不是覆盖层。<br />颗粒就是影像。</>, <>Grain is not an overlay.<br />Grain is the image.</>)}</h1>
          <p className="hero-lead">{text("我们的目标，是重建曝光、银盐位点、染料云、层间抑制、印片与扫描共同形成画面的过程。", "Our goal is to reconstruct how exposure, finite silver-halide sites, dye clouds, interlayer inhibition, printing and scanning form one image.")}</p>
          <div className="hero-actions"><Link href="/versions" className="button primary">{text("观看版本演进", "Explore the versions")}</Link><Link href="/research" className="button">{text("阅读研究", "Read the research")}</Link></div>
          <div className="hero-meta"><span><b>{versions.length}</b> {text("个已归档版本", "archived versions")}</span><span><b>{references.length}</b> {text("条核心资料", "primary references")}</span><span><b>12-bit</b> {text("5.7K主链", "5.7K pipeline")}</span></div>
        </section>

        <section className="current-section wrap">
          <div className="section-intro"><span>{text("当前基线", "CURRENT BASELINE")} · {current.version}</span><h2>{language === "en" ? currentEnglish?.title : current.title}</h2><p>{language === "en" ? currentEnglish?.summary : current.summary}</p></div>
          <div className="current-visual-layout">
            <div className={`hero-comparison ${current.camera ? "has-camera" : ""}`}>
              <figure><div className="image-title"><b>2383</b><span>REC.709 MONITOR / 1-1-1</span></div><InteractiveImage src={current.projection.src} previewSrc={current.projection.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.projection.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} 2383 projection monitor reference`} gallery={currentGallery} initialIndex={0} /><figcaption>{text("48 nit影院观察结果的Rec.709监看呈现", "Rec.709 monitor presentation of the 48-nit cinema observer")}</figcaption></figure>
              <figure><div className="image-title"><b>2K DI</b><span>REC.709 / 1-1-1 / BT.1886 DISPLAY</span></div><InteractiveImage src={current.bluray.src} previewSrc={current.bluray.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.bluray.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} Rec.709 Blu-ray reference`} gallery={currentGallery} initialIndex={1} /><figcaption>{text("时期2K扫描；BT.1886仅用于参考显示验证", "Period 2K scan; BT.1886 is used only for reference-display validation")}</figcaption></figure>
              {current.camera && <figure><div className="image-title"><b>V-709</b><span>PANASONIC OFFICIAL CAMERA BASELINE</span></div><InteractiveImage src={current.camera.src} previewSrc={current.camera.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.camera.videoSrc} sizes="(max-width: 680px) 100vw, 28vw" alt={`${current.version} ${sourceName} Panasonic V-709 camera baseline`} gallery={currentGallery} initialIndex={2} /><figcaption>{text("同一RAW的官方V-709显示基线；不进入胶片管线", "Official V-709 view of the same RAW; no film pipeline")}</figcaption></figure>}
            </div>
            <ParameterPanel groups={current.parameters} version={current.version} status={current.status} changes={current.changes} />
          </div>
        </section>

        <section className="thesis wrap">
          <div className="section-number">01</div>
          <div><span className="kicker">{text("核心命题", "CORE THESIS")}</span><h2>{text(<>噪点不是附加物。<br />随机性本身参与成像。</>, <>Noise is not an overlay.<br />Randomness participates in image formation.</>)}</h2></div>
          <div className="thesis-copy"><p>{text("数字噪点通常在画面完成后相加；彩色负片的随机性则发生在画面形成之前。有限银盐位点是否显影，会同时改变染料量、局部密度、DIR释放和邻层反应。", "Digital noise is usually added after the picture exists. Colour-negative randomness happens before the image is complete: whether finite silver-halide sites develop changes dye amount, local density, DIR release and neighbouring layers together.")}</p><p>{text("显影完成后银影会被漂白和定影移除，最终被扫描或印片观察到的是染料云。因此我们模拟的是“银盐位点播种的染料云场”，而不是永久悬浮的银颗粒。", "After development, silver is bleached and fixed away; printing and scanning observe dye clouds. We therefore simulate a dye-cloud field seeded by silver-halide events, not permanent silver specks floating over RGB.")}</p><p><b>{text("Baseline原则：", "Baseline principle: ")}</b>{text("只重建胶片、印片和扫描的成像；艺术调色留在模型之外。", "reconstruct film, printing and scanning; keep creative grading outside the model.")}</p><Link href="/algorithm">{text("查看公式与关键代码 →", "See equations and key code →")}</Link></div>
        </section>

        <section className="v21-panel wrap">
          <div><span className="eyebrow">{current.version} · MEASUREMENT-FIRST BASELINE</span><h2>{text("画面冻结之后，每一次变化都必须先回答：它能被测量吗？", "Once the image is frozen, every change must first answer: can it be measured?")}</h2></div>
          <ol>
            <li><b>{text("画面冻结", "Image frozen")}</b><span>{text("V31的5279、2383、扫描、颗粒、黑位、Gamma和综合色度边界全部不变。", "V31 negative, print, scan, grain, black, gamma and chroma boundary remain unchanged.")}</span></li>
            <li><b>{text("独立场景", "Independent scenes")}</b><span>{text("T007水面高光与细草、T031中性石面与暖色菌类使用完全相同的参数。", "T007 water highlights and fine grass, plus T031 neutral stone and warm mushrooms, use one parameter set.")}</span></li>
            <li><b>{text("可证伪门槛", "Falsifiable gates")}</b><span>{text("原生格式、高光、硬裁切、时序纹理、中性轴与OFX分块同一性都自动测量。", "Native format, highlights, clipping, temporal texture, neutral axis and OFX tile parity are measured automatically.")}</span></li>
            <li><b>{text("影院标准", "Cinema standard")}</b><span>{text("放映观察另生成ST 428-1 12-bit X′Y′Z′ DCDM序列；不再依赖含义不清的P3 ProRes标签。", "The projection observer also becomes an ST 428-1 12-bit X′Y′Z′ DCDM sequence, avoiding ambiguous P3 ProRes signalling.")}</span></li>
          </ol>
          <Link href="/research#v32" className="button">{text("阅读V32测量研究", "Read the V32 measurement study")}</Link>
        </section>

        <section className="route-grid wrap">
          <Link href="/versions"><span>ARCHIVE</span><h3>{text("版本档案", "Version archive")}</h3><p>{text(`从V4到${current.version}，逐版对照两种观看链，并记录错误和修正。`, `From V4 to ${current.version}, compare both viewing chains and retain every error and correction.`)}</p><b>{text("进入 →", "OPEN →")}</b></Link>
          <Link href="/research"><span>PAPER</span><h3>{text("研究笔记", "Research paper")}</h3><p>{text("乳剂层、遮罩、DIR、颗粒、扫描器，以及十份小时研究的证据审计。", "Emulsion layers, masking, DIR, grain, scanners and the ten-note evidence audit.")}</p><b>{text("进入 →", "OPEN →")}</b></Link>
          <Link href="/algorithm"><span>METHOD</span><h3>{text("算法说明", "Method")}</h3><p>{text("从RAW到负片、2383与Cineon的公式、流程和关键代码。", "Equations, flow and key code from RAW through the negative, 2383 and Cineon.")}</p><b>{text("进入 →", "OPEN →")}</b></Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
