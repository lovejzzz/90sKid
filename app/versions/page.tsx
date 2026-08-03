import { SiteFooter, SiteHeader } from "../components/SiteHeader";
import { VersionCard } from "../components/VersionCard";
import { versions } from "../data";

export default function VersionsPage() {
  return (
    <>
      <SiteHeader />
      <main className="archive-page wrap">
        <header className="page-header"><span className="eyebrow">VERSION ARCHIVE · V4—V24</span><h1>每一次变好，<br />也记录为什么曾经出错。</h1><p>V24继续使用两段GH7 Open Gate ProRes RAW素材，把35mm颗粒频谱与综合色纹理独立验证；早期版本尚未拆分放映和蓝光路径，缺失分支会明确标注为共用实验图或沿用上一版。</p></header>
        <nav className="version-jump" aria-label="版本快速跳转">{versions.map((v) => <a key={v.version} href={`#${v.version.toLowerCase()}`}>{v.version}</a>)}</nav>
        <div className="archive-list">{[...versions].reverse().map((item, i) => <VersionCard key={item.version} item={item} open={i === 0} />)}</div>
      </main>
      <SiteFooter />
    </>
  );
}
