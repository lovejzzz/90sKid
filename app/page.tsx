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
  const sourceName = current.version === "V34" || current.version === "V33" ? "T031" : current.version === "V32" ? "T007" : "T002";
  const currentGallery = [
    { src: current.projection.src, alt: `${current.version} ${sourceName} 2383 projection monitor reference` },
    { src: current.bluray.src, alt: `${current.version} ${sourceName} Rec.709 Blu-ray reference` },
    ...(current.camera ? [{ src: current.camera.src, alt: `${current.version} ${sourceName} Panasonic V-709 camera baseline` }] : []),
  ];
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero" style={{ "--hero-image": `url("${withBasePath("/versions/v34-t031-projection.jpg")}")` } as CSSProperties}>
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
          <div><span className="eyebrow">{current.version} · EVIDENCE-FIRST BASELINE</span><h2>{text("每一个物理效应，只能在成像链里拥有一个明确位置。", "Every physical effect gets one explicit place in the image-formation chain.")}</h2></div>
          <ol>
            <li><b>{text("MTF只算一次", "MTF once")}</b><span>{text("处理后5279 MTF已经包含显影邻接；V34移除后来重复的确定性DIR锐度。", "Processed-stock 5279 MTF already includes developer adjacency; V34 removes the later deterministic duplicate.")}</span></li>
            <li><b>{text("母版只编码一次", "One encode per master")}</b><span>{text("V31综合色边界在线性Rec.709内存中完成；放映与扫描不再经过中间ProRes往返。", "The V31 chroma boundary runs in linear Rec.709 memory; neither observer takes an intermediate ProRes round trip.")}</span></li>
            <li><b>{text("不可识别就不动", "Unknown means frozen")}</b><span>{text("没有5279 NPS或分色楔实测，就不重调颗粒形态、层间DIR或绿色中和。", "Without 5279 NPS or separation-wedge measurements, grain morphology, interimage DIR and green neutralization stay frozen.")}</span></li>
            <li><b>{text("稳定性优先", "Stability first")}</b><span>{text("48 GiB机器保留一个原生worker；会产生大量swap的并行方案即使更快也不进入baseline。", "The 48-GiB Mac keeps one native worker; a faster scheme that creates heavy swap does not enter the baseline.")}</span></li>
          </ol>
          <Link href="/research#v34" className="button">{text("阅读V34管线审计", "Read the V34 pipeline audit")}</Link>
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
