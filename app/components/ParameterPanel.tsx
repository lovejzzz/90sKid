import type { ParameterGroup, VersionEntry } from "../data";

type Props = {
  groups?: ParameterGroup[];
  version: string;
  status?: VersionEntry["status"];
  changes?: string[];
};

export function ParameterPanel({ groups, version, status, changes = [] }: Props) {
  const available = groups && groups.length > 0;
  return (
    <aside className="parameter-panel" aria-label={`${version}参数面板`}>
      <header>
        <div><span>PARAMETERS</span><b>{version}</b></div>
        <em>{available ? "完整快照" : "历史记录"}</em>
      </header>
      <div className="parameter-scroll">
        {available ? groups.map((group) => (
          <section key={group.title}>
            <h3>{group.title}</h3>
            <dl>{group.items.map((item) => (
              <div key={`${group.title}-${item.label}`}>
                <dt>{item.label}</dt>
                <dd>{item.value}{item.note && <small>{item.note}</small>}</dd>
              </div>
            ))}</dl>
          </section>
        )) : (
          <section>
            <h3>可确认的版本参数</h3>
            <dl>
              <div><dt>版本</dt><dd>{version}</dd></div>
              <div><dt>阶段</dt><dd>{status === "prototype" ? "结构原型" : "校准版本"}</dd></div>
              <div><dt>测试源</dt><dd>GH7 Open Gate ProRes RAW</dd></div>
              <div><dt>参考画幅</dt><dd>5760 × 4320 · 4:3</dd></div>
            </dl>
            <h3>当版启用项</h3>
            <ul>{changes.map((change) => <li key={change}>{change}</li>)}</ul>
            <p className="parameter-warning">早期实验没有保存可复现的完整数值快照，因此不补写推测参数。V22起保留完整参数。</p>
          </section>
        )}
      </div>
    </aside>
  );
}
