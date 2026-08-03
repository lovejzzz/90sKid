import Link from "next/link";

const links = [
  ["/", "概览"],
  ["/versions", "版本档案"],
  ["/research", "研究"],
  ["/algorithm", "算法"],
];

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand" aria-label="5279 Emulsion Project 首页">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><b>5279</b><small>EMULSION PROJECT</small></span>
      </Link>
      <nav aria-label="主导航">
        {links.map(([href, label]) => <Link key={href} href={href}>{label}</Link>)}
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div><b>5279 Emulsion Project</b><span>从GH7 ProRes RAW重建35mm彩色负片的形成过程</span></div>
      <p>这是一份持续修订的研究记录。公开资料约束模型；未公开的5279内部配方只作有边界的结构推断。</p>
    </footer>
  );
}
