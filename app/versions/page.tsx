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
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("V31以T002、T020、T032三段原分辨率素材验证正常ECN-2/ECP-2D工艺的综合色度—明暗解耦：保留V30质感与官方LAD，只移除意外的留银判别特征。每个例子继续并列相机、放映和时期扫描。", "V31 tests normal-process chroma/tone decoupling across T002, T020 and T032 at native resolution. It retains V30 texture and official LAD while removing an accidental retained-silver discriminator; every example still compares camera, projection and period scan.")}</p></header>
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
