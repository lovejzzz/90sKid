import type { BranchImage, VersionEntry } from "../data";
import { refMap } from "../data";
import { InteractiveImage, type GalleryItem } from "./InteractiveImage";
import { ParameterPanel } from "./ParameterPanel";

function smallSrc(src: string) { return src.replace(/\.jpg$/, "-sm.jpg"); }

function branchAlt(branch: BranchImage, title: string) { return `${title}：${branch.label}`; }

function Branch({ branch, title, gallery, galleryIndex }: { branch: BranchImage; title: string; gallery: GalleryItem[]; galleryIndex: number }) {
  return (
    <figure className="branch-figure">
      <div className="branch-label"><span>{title}</span>{branch.inherited && <em>沿用 / 共用</em>}</div>
      <InteractiveImage
        src={branch.src}
        previewSrc={smallSrc(branch.src)}
        videoSrc={branch.videoSrc}
        sizes="(max-width: 760px) 100vw, 50vw"
        alt={branchAlt(branch, title)}
        gallery={gallery}
        initialIndex={galleryIndex}
      />
      <figcaption>{branch.label}</figcaption>
    </figure>
  );
}

export function VersionCard({ item, open = false }: { item: VersionEntry; open?: boolean }) {
  const gallery: GalleryItem[] = [
    { src: item.projection.src, alt: branchAlt(item.projection, "2383 放映") },
    { src: item.bluray.src, alt: branchAlt(item.bluray, "2K DI / 蓝光") },
    ...(item.additionalTrials?.flatMap((trial) => [
      { src: trial.projection.src, alt: branchAlt(trial.projection, "2383 放映") },
      { src: trial.bluray.src, alt: branchAlt(trial.bluray, "2K DI / 蓝光") },
    ]) ?? []),
  ];
  return (
    <article className={`version-card ${item.status === "current" ? "is-current" : ""}`} id={item.version.toLowerCase()}>
      <div className="version-heading">
        <div><span className="version-number">{item.version}</span><span className="version-era">{item.year}</span></div>
        <div><h2>{item.title}</h2><p>{item.summary}</p></div>
      </div>
      <div className="version-visual-layout">
        <div className="branch-grid">
          <Branch branch={item.projection} title="2383 放映" gallery={gallery} galleryIndex={0} />
          <Branch branch={item.bluray} title="2K DI / 蓝光" gallery={gallery} galleryIndex={1} />
        </div>
        <ParameterPanel groups={item.parameters} version={item.version} status={item.status} changes={item.changes} />
      </div>
      {item.additionalTrials?.map((trial, trialIndex) => (
        <section className="source-trial" key={trial.name}>
          <header><div><span>ADDITIONAL SOURCE</span><b>{trial.name}</b></div><p>{trial.note}</p></header>
          <div className="branch-grid">
            <Branch branch={trial.projection} title="2383 放映" gallery={gallery} galleryIndex={2 + trialIndex * 2} />
            <Branch branch={trial.bluray} title="2K DI / 蓝光" gallery={gallery} galleryIndex={3 + trialIndex * 2} />
          </div>
        </section>
      ))}
      <details open={open}>
        <summary>完整 Changelog</summary>
        <div className="change-grid">
          <section><h3>本版改进</h3><ul>{item.changes.map((x) => <li key={x}>{x}</li>)}</ul></section>
          <section className="error-list"><h3>当时的错误 / 局限</h3><ul>{item.errors.map((x) => <li key={x}>{x}</li>)}</ul></section>
          <section><h3>由此得到的新发现</h3><ul>{item.discoveries.map((x) => <li key={x}>{x}</li>)}</ul></section>
        </div>
        <div className="inline-refs">证据：{item.refs.map((id) => {
          const ref = refMap[id];
          return <a key={id} href={ref.url} target="_blank" rel="noreferrer">[{id.slice(1)}] {ref.title}</a>;
        })}</div>
      </details>
    </article>
  );
}
