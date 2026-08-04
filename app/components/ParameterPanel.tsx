"use client";

import type { ParameterGroup, VersionEntry } from "../data";
import { useLanguage } from "../i18n";

type Props = {
  groups?: ParameterGroup[];
  version: string;
  status?: VersionEntry["status"];
  changes?: string[];
};

export function ParameterPanel({ groups, version, status, changes = [] }: Props) {
  const { language, text } = useLanguage();
  const available = groups && groups.length > 0;
  return (
    <aside className="parameter-panel" aria-label={text(`${version}参数面板`, `${version} parameter panel`)}>
      <header>
        <div><span>PARAMETERS</span><b>{version}</b></div>
        <em>{available ? text("完整快照", "FULL SNAPSHOT") : text("历史记录", "HISTORICAL")}</em>
      </header>
      <div className="parameter-scroll">
        {available ? groups.map((group) => (
          <section key={group.title}>
            <h3>{language === "en" ? (group.titleEn ?? group.title) : group.title}</h3>
            <dl>{group.items.map((item) => (
              <div key={`${group.title}-${item.label}`}>
                <dt>{language === "en" ? (item.labelEn ?? item.label) : item.label}</dt>
                <dd>{language === "en" ? (item.valueEn ?? item.value) : item.value}{(language === "en" ? item.noteEn : item.note) && <small>{language === "en" ? item.noteEn : item.note}</small>}</dd>
              </div>
            ))}</dl>
          </section>
        )) : (
          <section>
            <h3>{text("可确认的版本参数", "CONFIRMED VERSION PARAMETERS")}</h3>
            <dl>
              <div><dt>{text("版本", "Version")}</dt><dd>{version}</dd></div>
              <div><dt>{text("阶段", "Stage")}</dt><dd>{status === "prototype" ? text("结构原型", "Structural prototype") : text("校准版本", "Calibration release")}</dd></div>
              <div><dt>{text("测试源", "Source")}</dt><dd>GH7 Open Gate ProRes RAW</dd></div>
              <div><dt>{text("参考画幅", "Reference frame")}</dt><dd>5760 × 4320 · 4:3</dd></div>
            </dl>
            <h3>{text("当版启用项", "ENABLED IN THIS RELEASE")}</h3>
            <ul>{changes.map((change) => <li key={change}>{change}</li>)}</ul>
            <p className="parameter-warning">{text("早期实验没有保存可复现的完整数值快照，因此不补写推测参数。V22起保留完整参数。", "Early experiments did not preserve reproducible numerical snapshots, so missing parameters are not reconstructed from guesses. Complete snapshots begin with V22.")}</p>
          </section>
        )}
      </div>
    </aside>
  );
}
