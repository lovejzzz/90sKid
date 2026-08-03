import type { BranchImage, VersionEntry } from "../data";
import { refMap } from "../data";

function smallSrc(src: string) { return src.replace(/\.jpg$/, "-sm.jpg"); }

function Branch({ branch, title }: { branch: BranchImage; title: string }) {
  return (
    <figure className="branch-figure">
      <div className="branch-label"><span>{title}</span>{branch.inherited && <em>沿用 / 共用</em>}</div>
      <img
        src={branch.src}
        srcSet={`${smallSrc(branch.src)} 800w, ${branch.src} 1600w`}
        sizes="(max-width: 760px) 100vw, 50vw"
        loading="lazy"
        decoding="async"
        alt={`${title}：${branch.label}`}
      />
      <figcaption>{branch.label}</figcaption>
    </figure>
  );
}

export function VersionCard({ item, open = false }: { item: VersionEntry; open?: boolean }) {
  return (
    <article className={`version-card ${item.status === "current" ? "is-current" : ""}`} id={item.version.toLowerCase()}>
      <div className="version-heading">
        <div><span className="version-number">{item.version}</span><span className="version-era">{item.year}</span></div>
        <div><h2>{item.title}</h2><p>{item.summary}</p></div>
      </div>
      <div className="branch-grid">
        <Branch branch={item.projection} title="2383 放映" />
        <Branch branch={item.bluray} title="2K DI / 蓝光" />
      </div>
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
