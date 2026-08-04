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
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("当前版本继续使用两段GH7 Open Gate ProRes RAW素材，锁定负片、颗粒和放映基线，只修改有独立证据支持的扫描灰轴；缺失的早期分支仍明确标注为共用或沿用。", "The current release continues to use two GH7 Open Gate ProRes RAW scenes. It locks the negative, grain and projection baseline, changing only the scan gray axis supported by independent diagnostics. Missing early branches remain explicitly marked as shared or retained.")}</p></header>
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
