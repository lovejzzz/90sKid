"use client";

import type { BranchImage, VersionEntry } from "../data";
import { refMap } from "../data";
import { useLanguage } from "../i18n";
import { translateBranchLabel, versionEnglish } from "../versionEnglish";
import { InteractiveImage, type GalleryItem } from "./InteractiveImage";
import { ParameterPanel } from "./ParameterPanel";

function smallSrc(src: string) { return src.replace(/\.jpg$/, "-sm.jpg"); }

function branchAlt(branch: BranchImage, title: string, english = false) { return `${title}: ${english ? translateBranchLabel(branch.label) : branch.label}`; }

function Branch({ branch, title, gallery, galleryIndex, english }: { branch: BranchImage; title: string; gallery: GalleryItem[]; galleryIndex: number; english: boolean }) {
  return (
    <figure className="branch-figure">
      <div className="branch-label"><span>{title}</span>{branch.inherited && <em>{english ? "RETAINED / SHARED" : "沿用 / 共用"}</em>}</div>
      <InteractiveImage
        src={branch.src}
        previewSrc={smallSrc(branch.src)}
        videoSrc={branch.videoSrc}
        sizes="(max-width: 760px) 100vw, 50vw"
        alt={branchAlt(branch, title)}
        gallery={gallery}
        initialIndex={galleryIndex}
      />
      <figcaption>{english ? translateBranchLabel(branch.label) : branch.label}</figcaption>
    </figure>
  );
}

export function VersionCard({ item, open = false }: { item: VersionEntry; open?: boolean }) {
  const { language, text } = useLanguage();
  const english = language === "en";
  const copy = english ? versionEnglish[item.version] : undefined;
  const title = copy?.title ?? item.title;
  const year = english && item.status !== "current" && copy?.year === "CURRENT BASELINE"
    ? "ARCHIVED CALIBRATION"
    : (copy?.year ?? item.year);
  const summary = copy?.summary ?? item.summary;
  const changes = copy?.changes ?? item.changes;
  const errors = copy?.errors ?? item.errors;
  const discoveries = copy?.discoveries ?? item.discoveries;
  const primaryBranchCount = 2 + (item.fsd ? 1 : 0) + (item.camera ? 1 : 0);
  const trialBaseIndex = (trialIndex: number) => primaryBranchCount + (
    item.additionalTrials?.slice(0, trialIndex).reduce(
      (sum, trial) => sum + 2 + (trial.fsd ? 1 : 0) + (trial.camera ? 1 : 0),
      0,
    ) ?? 0
  );
  const gallery: GalleryItem[] = [
    { src: item.projection.src, alt: branchAlt(item.projection, english ? "2383 projection" : "2383 放映", english) },
    { src: item.bluray.src, alt: branchAlt(item.bluray, english ? "2K DI / Blu-ray" : "2K DI / 蓝光", english) },
    ...(item.fsd ? [{ src: item.fsd.src, alt: branchAlt(item.fsd, english ? "FSD finite-site density" : "FSD 有限密度", english) }] : []),
    ...(item.camera ? [{ src: item.camera.src, alt: branchAlt(item.camera, english ? "Camera baseline" : "相机原图", english) }] : []),
    ...(item.additionalTrials?.flatMap((trial) => [
      { src: trial.projection.src, alt: branchAlt(trial.projection, english ? "2383 projection" : "2383 放映", english) },
      { src: trial.bluray.src, alt: branchAlt(trial.bluray, english ? "2K DI / Blu-ray" : "2K DI / 蓝光", english) },
      ...(trial.fsd ? [{ src: trial.fsd.src, alt: branchAlt(trial.fsd, english ? "FSD finite-site density" : "FSD 有限密度", english) }] : []),
      ...(trial.camera ? [{ src: trial.camera.src, alt: branchAlt(trial.camera, english ? "Camera baseline" : "相机原图", english) }] : []),
    ]) ?? []),
  ];
  return (
    <article className={`version-card ${item.status === "current" ? "is-current" : ""} ${item.status === "hypothesis" ? "is-hypothesis" : ""}`} id={item.version.toLowerCase()}>
      <div className="version-heading">
        <div><span className="version-number">{item.version}</span><span className="version-era">{year}</span></div>
        <div><h2>{title}</h2><p>{summary}</p></div>
      </div>
      <div className="version-visual-layout">
        <div className={`branch-grid ${item.camera && !item.fsd ? "has-camera" : ""}`}>
          <Branch branch={item.projection} title={text("2383 放映", "2383 PROJECTION")} gallery={gallery} galleryIndex={0} english={english} />
          <Branch branch={item.bluray} title={text("2K DI / 蓝光", "2K DI / BLU-RAY")} gallery={gallery} galleryIndex={1} english={english} />
          {item.fsd && <Branch branch={item.fsd} title={text("FSD 有限密度", "FSD FINITE-SITE DENSITY")} gallery={gallery} galleryIndex={2} english={english} />}
          {item.camera && <Branch branch={item.camera} title={text("相机原图", "CAMERA BASELINE")} gallery={gallery} galleryIndex={2 + (item.fsd ? 1 : 0)} english={english} />}
        </div>
        <ParameterPanel groups={item.parameters} version={item.version} status={item.status} changes={changes} />
      </div>
      {item.additionalTrials?.map((trial, trialIndex) => (
        <section className="source-trial" key={trial.name}>
          <header><div><span>ADDITIONAL SOURCE</span><b>{trial.name}</b></div><p>{english ? (copy?.trialNote ?? trial.note) : trial.note}</p></header>
          <div className={`branch-grid ${trial.camera && !trial.fsd ? "has-camera" : ""}`}>
            <Branch branch={trial.projection} title={text("2383 放映", "2383 PROJECTION")} gallery={gallery} galleryIndex={trialBaseIndex(trialIndex)} english={english} />
            <Branch branch={trial.bluray} title={text("2K DI / 蓝光", "2K DI / BLU-RAY")} gallery={gallery} galleryIndex={trialBaseIndex(trialIndex) + 1} english={english} />
            {trial.fsd && <Branch branch={trial.fsd} title={text("FSD 有限密度", "FSD FINITE-SITE DENSITY")} gallery={gallery} galleryIndex={trialBaseIndex(trialIndex) + 2} english={english} />}
            {trial.camera && <Branch branch={trial.camera} title={text("相机原图", "CAMERA BASELINE")} gallery={gallery} galleryIndex={trialBaseIndex(trialIndex) + 2 + (trial.fsd ? 1 : 0)} english={english} />}
          </div>
        </section>
      ))}
      {item.pipelineComparisons && (
        <section className="pipeline-comparisons">
          <header className="pipeline-comparisons-intro">
            <span>{text("受控管线对比", "CONTROLLED PIPELINE COMPARISON")}</span>
            <h3>{text("三种密度形成，同一个观察边界", "Three density models, one observer boundary")}</h3>
            <p>{text(`这不是三个调色预设。物理5279是${item.version}主模型；FSD是由Silver Efex研究启发的有限位点对照；确定性基线关闭随机密度。`, `These are not three grades. Physical 5279 is the ${item.version} model; FSD is a finite-site control informed by the Silver Efex study; the deterministic baseline disables stochastic density.`)}</p>
          </header>
          {item.pipelineComparisons.map((comparison) => {
            const comparisonGallery: GalleryItem[] = comparison.outputs.map((output) => ({
              src: output.branch.src,
              alt: branchAlt(output.branch, english ? output.titleEn : output.title, english),
            }));
            return (
              <section className="pipeline-comparison-set" key={comparison.name}>
                <header><b>{comparison.name}</b><p>{english ? comparison.noteEn : comparison.note}</p></header>
                <div className="pipeline-comparison-grid">
                  {comparison.outputs.map((output, outputIndex) => (
                    <Branch
                      key={output.titleEn}
                      branch={output.branch}
                      title={english ? output.titleEn : output.title}
                      gallery={comparisonGallery}
                      galleryIndex={outputIndex}
                      english={english}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </section>
      )}
      <details open={open}>
        <summary>{text("完整 Changelog", "Full changelog")}</summary>
        <div className="change-grid">
          <section><h3>{text("本版改进", "Improvements")}</h3><ul>{changes.map((x) => <li key={x}>{x}</li>)}</ul></section>
          <section className="error-list"><h3>{text("当时的错误 / 局限", "Errors / limitations")}</h3><ul>{errors.map((x) => <li key={x}>{x}</li>)}</ul></section>
          <section><h3>{text("由此得到的新发现", "What we learned")}</h3><ul>{discoveries.map((x) => <li key={x}>{x}</li>)}</ul></section>
        </div>
        <div className="inline-refs">{text("证据：", "Evidence: ")}{item.refs.map((id) => {
          const ref = refMap[id];
          return <a key={id} href={ref.url} target="_blank" rel="noreferrer">[{id.slice(1)}] {ref.title}</a>;
        })}</div>
      </details>
    </article>
  );
}
