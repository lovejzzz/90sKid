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
        <header className="page-header"><span className="eyebrow">PUBLIC VISUAL ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("这里只记录真正生成了可比较图像或视频的视觉版本。当前V49把随机性放回负片密度形成；V48保留为显示RGB残差错误的可复现对照。", "Only releases with comparable image or movie evidence appear here. Current V49 returns randomness to negative-density formation; V48 remains a reproducible witness of the display-RGB residual error.")}</p></header>
        <ResearchStatus language={language} />
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
