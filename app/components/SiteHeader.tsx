"use client";

import Link from "next/link";
import { useLanguage } from "../i18n";

const links = [
  ["/", "概览", "Overview"],
  ["/versions", "版本档案", "Versions"],
  ["/research", "研究", "Research"],
  ["/algorithm", "算法", "Method"],
];

export function SiteHeader() {
  const { language, setLanguage, text } = useLanguage();
  return (
    <header className="site-header">
      <Link href="/" className="brand" aria-label={text("5279 Emulsion Project 首页", "5279 Emulsion Project home")}>
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><b>5279</b><small>EMULSION PROJECT</small></span>
      </Link>
      <div className="header-actions">
        <nav aria-label={text("主导航", "Main navigation")}>
          {links.map(([href, zh, en]) => <Link key={href} href={href}>{language === "zh" ? zh : en}</Link>)}
        </nav>
        <div className="language-switch" role="group" aria-label={text("语言切换", "Language switcher")}>
          <button type="button" className={language === "zh" ? "is-active" : ""} aria-pressed={language === "zh"} onClick={() => setLanguage("zh")}>中文</button>
          <span>/</span>
          <button type="button" className={language === "en" ? "is-active" : ""} aria-pressed={language === "en"} onClick={() => setLanguage("en")}>EN</button>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  const { text } = useLanguage();
  return (
    <footer className="site-footer">
      <div><b>5279 Emulsion Project</b><span>{text("从GH7 ProRes RAW重建35mm彩色负片的形成过程", "Reconstructing 35 mm colour-negative image formation from GH7 ProRes RAW")}</span></div>
      <p>{text("这是一份持续修订的研究记录。公开资料约束模型；未公开的5279内部配方只作有边界的结构推断。", "This is a living research record. Public measurements constrain the model; undisclosed 5279 chemistry is represented only by bounded structural hypotheses.")}</p>
    </footer>
  );
}
