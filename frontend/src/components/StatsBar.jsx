export default function StatsBar({ items }) {
  const up = items.filter((i) => i.btc_direction === "up").length;
  const down = items.filter((i) => i.btc_direction === "down").length;
  const high = items.filter((i) => i.impact === "high").length;

  const stats = [
    { n: items.length, label: "Tin phân tích", color: undefined },
    { n: up, label: "Dự báo TĂNG", color: "var(--good)" },
    { n: down, label: "Dự báo GIẢM", color: "var(--bad)" },
    { n: high, label: "Tác động CAO", color: "var(--accent)" },
  ];

  return (
    <div className="stats">
      {stats.map((s) => (
        <div className="stat" key={s.label}>
          <div className="n" style={{ color: s.color }}>
            {s.n}
          </div>
          <div className="l">{s.label}</div>
        </div>
      ))}
    </div>
  );
}
