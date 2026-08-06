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
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—{latest}</span><h1>{text(<>每一次变好，<br />也记录为什么曾经出错。</>, <>Every improvement records<br />why the earlier result was wrong.</>)}</h1><p>{text("V37保留逐帧独立的乳剂位点，只移除整幅采样核每帧转向造成的数值呼吸；颜色、密度、锐度与颗粒尺度全部保持V36基线。", "V37 preserves independent emulsion sites on every frame and removes only the numerical breathing caused by whole-field sampling rotation; colour, density, sharpness and grain scale remain at the V36 baseline.")}</p></header>
        <nav className="version-jump" aria-label={text("版本快速跳转", "Jump to version")}>{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
