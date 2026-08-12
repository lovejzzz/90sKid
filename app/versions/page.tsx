"use client";

import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { VersionCard } from "../components/VersionCard";
import { ResearchStatus } from "../components/ResearchLedger";
import { versions } from "../data";
import { useLanguage } from "../i18n";

export default function VersionsPage() {
  const { language, text } = useLanguage();
  const latest = versions[versions.length - 1].version;
  return (
    <>
      <SiteHeader />
      <main className="archive-page wrap">
        <header className="page-header"><span className="eyebrow">PUBLIC VISUAL ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("这里只记录真正生成了可比较图像或视频的视觉版本，当前为V46。材料、算法与交付研究按主题归档；旧内部V46—V86实验编号仍留在Research中，作为不可变的历史证据ID。", "Only releases with comparable image or movie evidence appear here. V46 is current. Material, algorithm and delivery research is organized by topic; legacy internal V46–V86 experiment numbers remain immutable evidence IDs in Research.")}</p></header>
        <ResearchStatus language={language} />
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
