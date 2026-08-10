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

export default function Home() {
  const { language, text } = useLanguage();
  const current = versions[versions.length - 1];
  const currentEnglish = versionEnglish[current.version];
  const sourceName = ["V44", "V43H"].includes(current.version) ? "T020" : ["V42", "V41", "V40", "V39", "V38", "V37", "V36", "V35", "V34", "V33"].includes(current.version) ? "T031" : current.version === "V32" ? "T007" : "T002";
  const currentGallery = [
    { src: current.projection.src, alt: `${current.version} ${sourceName} 2383 projection monitor reference` },
    { src: current.bluray.src, alt: `${current.version} ${sourceName} Rec.709 Blu-ray reference` },
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
          <div className="hero-meta"><span><b>{versions.length}</b> {text("个已归档版本", "archived versions")}</span><span><b>{references.length}</b> {text("条核心资料", "primary references")}</span><span><b>12-bit</b> {text("5.7K主链", "5.7K pipeline")}</span></div>
        </section>

        <section className="current-section wrap">
          <div className="section-intro"><span>{text("当前观察器与交付修订 · 成像基线为V42", "CURRENT OBSERVER & DELIVERY REVISION · V42 IMAGE BASELINE")} · {current.version}</span><h2>{language === "en" ? currentEnglish?.title : current.title}</h2><p>{language === "en" ? currentEnglish?.summary : current.summary}</p></div>
          <div className="current-visual-layout">
            <div className={`hero-comparison ${current.camera && !current.fsd ? "has-camera" : ""}`}>
              <figure><div className="image-title"><b>2383</b><span>sRGB / MAC VIEWING COMPANION</span></div><InteractiveImage src={current.projection.src} previewSrc={current.projection.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.projection.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} 2383 projection monitor reference`} gallery={currentGallery} initialIndex={0} /><figcaption>{text("48 nit影院观察的本机sRGB观看链；专业母版为Rec.709/BT.1886", "Mac sRGB view of the 48-nit cinema observer; professional master is Rec.709/BT.1886")}</figcaption></figure>
              <figure><div className="image-title"><b>2K DI</b><span>sRGB / MAC VIEWING COMPANION</span></div><InteractiveImage src={current.bluray.src} previewSrc={current.bluray.src.replace(/\.jpg$/, "-sm.jpg")} videoSrc={current.bluray.videoSrc} sizes="(max-width: 680px) 100vw, 42vw" alt={`${current.version} ${sourceName} Rec.709 Blu-ray reference`} gallery={currentGallery} initialIndex={1} /><figcaption>{text("时期2K扫描的本机sRGB观看链；与专业母版解码到同一观察光", "Mac sRGB view of the period 2K scan; decodes to the same observer light as the professional master")}</figcaption></figure>
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
          <div><span className="eyebrow">{current.version} · OBSERVER INTEGRITY</span><h2>{text("母版不该为播放器的缩放错误负责。", "The master should not compensate for a player’s scaling error.")}</h2></div>
          <ol>
            <li><b>{text("证据诚实的观察器", "Evidence-honest observers")}</b><span>{text("放映保留2383亮度与纹理，但低频颜色继续使用已验证的正常工艺扫描参照；不凭空制造投影色差。", "Projection retains 2383 lightness and texture while low-frequency colour keeps the validated normal-process scan reference; no projection colour difference is invented.")}</span></li>
            <li><b>{text("母版保持原生", "Keep the master native")}</b><span>{text("5760×4320、12-bit母版不因网页或播放器的显示尺度而被软化。", "The 5760×4320 12-bit master is never softened for a web page or player scale.")}</span></li>
            <li><b>{text("审看必须声明尺度", "Review declares its scale")}</b><span>{text("审看版在线性观察光中按显示像素面积积分，防止锐利缩放把超Nyquist颗粒折回成粗纹理。", "Review integrates linear observer light over display pixels so sharp resize cannot fold above-Nyquist grain into coarse texture.")}</span></li>
            <li><b>{text("一幅画面权威", "One picture authority")}</b><span>{text("视频先完成编码；静帧再从最终视频同一帧生成。", "The movie is encoded first; the still is then decoded from the same final movie frame.")}</span></li>
          </ol>
          <Link href={language === "en" ? "/research#v44-en" : "/research#v44"} className="button">{text("阅读V44观察器审计", "Read the V44 observer audit")}</Link>
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
