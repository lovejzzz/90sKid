import type { Language } from "../i18n";
import Link from "next/link";
import { currentEngineCandidate, currentResearchCycle, currentVisualRelease, nextVisualRelease, researchChapters, researchLedger } from "../researchLedger";

const statusCopy = {
  image: { zh: "成像发布", en: "IMAGE RELEASE" },
  audit: { zh: "研究审计", en: "RESEARCH AUDIT" },
  rejected: { zh: "候选拒绝", en: "CANDIDATE REJECTED" },
  boundary: { zh: "证据边界", en: "EVIDENCE BOUNDARY" },
} as const;

export function ResearchStatus({ language }: { language: Language }) {
  const zh = language === "zh";
  return (
    <section className="research-status" aria-label={zh ? "当前研究状态" : "Current research status"}>
      <div><span>{zh ? "当前视觉发布" : "CURRENT VISUAL RELEASE"}</span><b>{currentVisualRelease}</b><small>{zh ? "网站中已经有可核对媒体的最近版本" : "latest release with reviewable media on this site"}</small></div>
      <div><span>{zh ? "研究周期" : "RESEARCH CYCLE"}</span><b>{currentResearchCycle}</b><small>{zh ? "按主题整理；实验编号只留在证据附录" : "organized by topic; experiment IDs live in the evidence appendix"}</small></div>
      <div><span>{zh ? "下一视觉发布" : "NEXT VISUAL RELEASE"}</span><b>{nextVisualRelease}</b><small>{zh ? "只在新增测量或可验证修正出现后编号" : "numbered only after new measurement or a verifiable correction"}</small></div>
    </section>
  );
}

export function ResearchLedger({ language, compact = false }: { language: Language; compact?: boolean }) {
  const zh = language === "zh";
  const chapters = compact ? researchChapters.slice(-2) : researchChapters;
  return (
    <section className={`audit-ledger${compact ? " is-compact" : ""}`} id={compact ? "latest-audits" : "audit-ledger"}>
      <header>
        <span className="section-tag">{zh ? "研究周期 05 · 四条主线" : "RESEARCH CYCLE 05 · FOUR THEMATIC THREADS"}</span>
        <h2>{zh ? "研究按问题组织，不再让一句结论冒充一个胶片版本。" : "Research is organized by questions—not by making every finding look like a film version."}</h2>
        <p>{zh ? `网站当前可观看版本为${currentVisualRelease}。下一版为${nextVisualRelease}：只在出现新的测量或可验证修正后编号。当前引擎为${currentEngineCandidate}；旧V46—V86编号仍作为脚本、报告和失败实验的不可变证据ID。` : `The current reviewable release is ${currentVisualRelease}. The next release is ${nextVisualRelease}: it will be numbered only after a new measurement or verifiable correction. The current engine is ${currentEngineCandidate}. Legacy V46–V86 numbers remain immutable evidence IDs for scripts, reports and failed experiments.`}</p>
      </header>
      <div className="audit-ledger-grid">
        {chapters.map((chapter, chapterIndex) => (
          <article key={chapter.id} id={compact ? undefined : chapter.id} className="audit-entry status-audit research-chapter">
            <div><b>{String(chapterIndex + 1).padStart(2, "0")}</b><span>{zh ? `${chapter.evidenceIds.length}条证据` : `${chapter.evidenceIds.length} EVIDENCE NOTES`}</span></div>
            <h3>{zh ? chapter.titleZh : chapter.titleEn}</h3>
            <p>{zh ? chapter.summaryZh : chapter.summaryEn}</p>
            <p><b>{zh ? "当前结论：" : "CURRENT CONCLUSION: "}</b>{zh ? chapter.conclusionZh : chapter.conclusionEn}</p>
            {!compact && <details><summary>{zh ? "展开可追溯实验附录" : "Open traceable experiment appendix"}</summary><div className="research-evidence-list">{chapter.evidenceIds.map((id) => { const entry = researchLedger.find((candidate) => candidate.version === id); return entry ? <section key={id} id={`${chapter.id}-${id.toLowerCase()}`}><div><b>{id}</b><span>{zh ? statusCopy[entry.status].zh : statusCopy[entry.status].en}</span></div><h4>{zh ? entry.titleZh : entry.titleEn}</h4><p>{zh ? entry.summaryZh : entry.summaryEn}</p></section> : null; })}</div></details>}
          </article>
        ))}
      </div>
      {compact && <Link className="button" href="/research#audit-ledger">{zh ? "查看四个研究主题与证据附录" : "Read the four research threads and evidence appendix"}</Link>}
    </section>
  );
}
