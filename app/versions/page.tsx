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
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("当前版本继续使用两段GH7 Open Gate ProRes RAW素材；它修正AVFoundation linear-BT.2020缓冲与Panasonic Camera LUT之间的阶段契约，同时锁定5279乳剂、颗粒、黑位、Gamma和两种观察器。", "The current release continues to use two GH7 Open Gate ProRes RAW scenes. It corrects the boundary between AVFoundation's linear-BT.2020 buffer and Panasonic's Camera LUT while locking the 5279 emulsion, grain, black, gamma and both observers.")}</p></header>
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
