"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { SiteFooter, SiteHeader } from "./components/SiteHeader";
import { InteractiveImage } from "./components/InteractiveImage";
import { EmulsionFlow } from "./components/EmulsionFlow";
import { ParameterPanel } from "./components/ParameterPanel";
import { ResearchLedger, ResearchStatus } from "./components/ResearchLedger";
import { versions } from "./data";
import { useLanguage } from "./i18n";
import { currentResearchCycle, currentVisualRelease, nextVisualRelease } from "./researchLedger";
import { versionEnglish } from "./versionEnglish";

export default function Home() {
  const { language, text } = useLanguage();
  const current = versions[versions.length - 1];
  const currentEnglish = versionEnglish[current.version];
  const sourceName = ["V47", "V46", "V45", "V44", "V43H"].includes(current.version) ? "T020" : ["V42", "V41", "V40", "V39", "V38", "V37", "V36", "V35", "V34", "V33"].includes(current.version) ? "T031" : current.version === "V32" ? "T007" : "T002";
  const currentGallery = [
    { src: current.projection.src, alt: `${current.version} ${sourceName} 2383 projection monitor reference` },
    { src: current.bluray.src, alt: `${current.version} ${sourceName} scan / DI observer master` },
    ...(current.fsd ? [{ src: current.fsd.src, alt: `${current.version} ${sourceName} FSD finite-site density control` }] : []),
    ...(current.camera ? [{ src: current.camera.src, alt: `${current.version} ${sourceName} Panasonic V-709 camera baseline` }] : []),
  ];
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero" style={{ "--hero-image": `url("${current.projection.src}")` } as CSSProperties}>
          <EmulsionFlow />
          <div className="eyebrow">KODAK VISION 500T 5279 · DIGITAL EMULSION STUDY</div>
          <h1>{text(<>颗粒不是覆盖层。<br />颗粒就是影像。</>, <>Grain is not an overlay.<br />Grain is the image.</>)}</h1>
          <p className="hero-lead">{text("我们的目标，是重建曝光、银盐位点、染料云、层间抑制、印片与扫描共同形成画面的过程。", "Our goal is to reconstruct how exposure, finite silver-halide sites, dye clouds, interlayer inhibition, printing and scanning form one image.")}</p>
          <div className="hero-actions"><Link href="/versions" className="button primary">{text("观看版本演进", "Explore the versions")}</Link><Link href="/research" className="button">{text("阅读研究", "Read the research")}</Link></div>
          <div className="hero-meta"><span><b>{currentVisualRelease}</b> {text("当前视觉发布", "current visual release")}</span><span><b>{currentResearchCycle}</b> {text("研究周期", "research cycle")}</span><span><b>12-bit</b> {text("5.7K内部母版", "5.7K internal master")}</span></div>
        </section>

        <div className="wrap home-research-status"><ResearchStatus language={language} /></div>

        <section className="current-section wrap">
          <div className="section-intro"><span>{text("当前视觉发布", "CURRENT VISUAL RELEASE")} · {currentVisualRelease}<br />{text("下一视觉发布", "NEXT VISUAL RELEASE")} · {nextVisualRelease}<br />{text("研究周期", "RESEARCH CYCLE")} · {currentResearchCycle}</span><h2>{language === "en" ? currentEnglish?.title : current.title}</h2><p>{language === "en" ? currentEnglish?.summary : current.summary}<br /><br />{text("V47是同一V46确定性观察器上的银盐组织对照；V46仍是物理5279分支。旧内部V47—V86标签继续作为不可变实验ID保留。", "V47 is a silver-halide morphology comparator on the same V46 deterministic observers; V46 remains the physical 5279 branch. Legacy internal V47–V86 labels remain immutable experiment IDs.")}</p></div>
          <div className="current-visual-layout">
            <div className={`hero-comparison ${current.camera && !current.fsd ? "has-camera" : ""}`}>
              <figure><div className="image-title"><b>2383</b><span>sRGB / MAC VIEWING COMPANION</span></div><InteractiveImage src={current.projection.src} previewSrc={current.projection.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.projection.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} 2383 projection monitor reference`} gallery={currentGallery} initialIndex={0} /><figcaption>{text("48 nit影院观察的本机sRGB观看链；专业母版为Rec.709/BT.1886", "Mac sRGB view of the 48-nit cinema observer; professional master is Rec.709/BT.1886")}</figcaption></figure>
              <figure><div className="image-title"><b>SCAN / DI</b><span>sRGB / MAC VIEWING COMPANION</span></div><InteractiveImage src={current.bluray.src} previewSrc={current.bluray.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.bluray.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} scan / DI observer master`} gallery={currentGallery} initialIndex={1} /><figcaption>{text("扫描／DI观察母版的本机sRGB观看链；不是蓝光或UHD压片成品", "Mac sRGB view of the scan / DI observer master; not a Blu-ray or UHD disc encode")}</figcaption></figure>
              {current.fsd && <figure><div className="image-title"><b>FSD</b><span>FINITE-SITE DENSITY CONTROL</span></div><InteractiveImage src={current.fsd.src} previewSrc={current.fsd.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.fsd.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} FSD finite-site density control`} gallery={currentGallery} initialIndex={2} /><figcaption>{text("共享确定性观察均值的独立有限密度路线；不并入物理5279", "Independent finite-density route sharing the deterministic observer mean; not part of physical 5279")}</figcaption></figure>}
              {current.camera && <figure><div className="image-title"><b>V-709</b><span>PANASONIC OFFICIAL CAMERA BASELINE</span></div><InteractiveImage src={current.camera.src} previewSrc={current.camera.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.camera.videoSrc} sizes="(max-width: 680px) 100vw, 28vw" alt={`${current.version} ${sourceName} Panasonic V-709 camera baseline`} gallery={currentGallery} initialIndex={2 + (current.fsd ? 1 : 0)} /><figcaption>{text("同一RAW的官方V-709显示基线；不进入胶片管线", "Official V-709 view of the same RAW; no film pipeline")}</figcaption></figure>}
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
          <div><span className="eyebrow">{current.version} · LATEST PUBLISHED VISUAL WITNESS</span><h2>{text("标准观察者改变观察，而不改写乳剂。", "A standard observer changes observation—not the emulsion.")}</h2></div>
          <ol>
            <li><b>{text("官方1 nm观察者", "Official 1 nm observer")}</b><span>{text("用CIE发布的1931 2°逐纳米数据积分2383，不再用解析近似代替标准表。", "Integrate 2383 through the CIE-published 1931 2° one-nanometre table instead of an analytical approximation.")}</span></li>
            <li><b>{text("母版保持原生", "Keep the master native")}</b><span>{text("5760×4320、12-bit母版不因网页或播放器的显示尺度而被软化。", "The 5760×4320 12-bit master is never softened for a web page or player scale.")}</span></li>
            <li><b>{text("审看必须声明尺度", "Review declares its scale")}</b><span>{text("审看版在线性观察光中按显示像素面积积分，防止锐利缩放把超Nyquist颗粒折回成粗纹理。", "Review integrates linear observer light over display pixels so sharp resize cannot fold above-Nyquist grain into coarse texture.")}</span></li>
            <li><b>{text("一幅画面权威", "One picture authority")}</b><span>{text("视频先完成编码；静帧再从最终视频同一帧生成。", "The movie is encoded first; the still is then decoded from the same final movie frame.")}</span></li>
          </ol>
          <Link href="/research#silver-efex-internals" className="button">{text("阅读V47银盐组织研究", "Read the V47 morphology study")}</Link>
        </section>

        <div className="wrap"><ResearchLedger language={language} compact /></div>

        <section className="route-grid wrap">
          <Link href="/versions"><span>VISUAL ARCHIVE</span><h3>{text("视觉版本档案", "Visual version archive")}</h3><p>{text(`从V4到${current.version}保留真实媒体对照；研究版本不伪造截图。`, `Real media comparisons are retained from V4 to ${current.version}; research-only revisions do not fabricate imagery.`)}</p><b>{text("进入 →", "OPEN →")}</b></Link>
          <Link href="/research"><span>RESEARCH CYCLE · {currentResearchCycle}</span><h3>{text("研究笔记", "Research paper")}</h3><p>{text("材料测量、多层随机性、2383放映与扫描／交付四条研究主线；小实验保留在可追溯附录。", "Four research threads—material measurement, multilayer randomness, 2383 projection, and scan/delivery—with small experiments retained in a traceable appendix.")}</p><b>{text("进入 →", "OPEN →")}</b></Link>
          <Link href="/algorithm"><span>METHOD</span><h3>{text("算法说明", "Method")}</h3><p>{text("从RAW到负片、2383与Cineon的公式、流程和关键代码。", "Equations, flow and key code from RAW through the negative, 2383 and Cineon.")}</p><b>{text("进入 →", "OPEN →")}</b></Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
