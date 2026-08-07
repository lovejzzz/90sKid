"use client";

import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { VersionCard } from "../components/VersionCard";
import { versions } from "../data";
import { useLanguage } from "../i18n";

export default function VersionsPage() {
  const { text } = useLanguage();
  const latest = versions[versions.length - 1].version;
  return (
    <>
      <SiteHeader />
      <main className="archive-page wrap">
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("V41用T003指出色度残差方向，再以T005独立复核；只采用12.5%的保守修正，并保持V40的颗粒、黑位、对比与Gamma。", "V41 estimates a chroma-residual direction from T003, confirms it on the independent T005, then retains only a conservative 12.5% step while freezing V40 grain, black, contrast and gamma.")}</p></header>
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
