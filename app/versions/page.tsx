import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { VersionCard } from "../components/VersionCard";
import { versions } from "../data";

export default function VersionsPage() {
  return (
    <>
      <SiteHeader />
      <main className="archive-page wrap">
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—V25</span><h1>每一次变好，<br />也记录为什么曾经出错。</h1><p>V25继续使用两段GH7 Open Gate ProRes RAW素材，把胶片物理、影院P3、蓝光Rec.709与网页sRGB分开验证，并记录无降质加速的真实计时；早期版本缺失的分支仍会明确标注为共用或沿用。</p></header>
        <nav className="version-jump" aria-label="版本快速跳转">{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
