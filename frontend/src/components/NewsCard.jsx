import { DIR, IMPACT } from "../constants";
import { fmtTime } from "../utils";

const sentimentColor = (s) =>
  s === "good" ? "var(--good)" : s === "bad" ? "var(--bad)" : "var(--flat)";

export default function NewsCard({ item, isNew }) {
  const d = DIR[item.btc_direction] || DIR.flat;
  return (
    <div className={`card ${d.cls}`}>
      <div className="top">
        <h3>
          {item.link ? (
            <a href={item.link} target="_blank" rel="noopener noreferrer">
              {item.title}
            </a>
          ) : (
            item.title
          )}
        </h3>
        <div className="badges">
          {isNew && <span className="b new">MỚI</span>}
          <span className={`b ${d.cls}`}>{d.label}</span>
          <span className={`b ${item.impact}`}>{IMPACT[item.impact] || item.impact}</span>
        </div>
      </div>

      <div className="reason">{item.reason}</div>

      <div className="src">
        <span>📰 {item.source}</span>
        <span title="Thời điểm tin xuất hiện">🕒 {fmtTime(item.published)}</span>
        <span>
          Tin:{" "}
          <b style={{ color: sentimentColor(item.sentiment) }}>{item.sentiment}</b>
        </span>
        <span>
          Tự tin:{" "}
          <span className="conf">
            <i style={{ width: `${Number(item.confidence) || 0}%` }} />
          </span>{" "}
          {Number(item.confidence) || 0}%
        </span>
        {(item.keywords || []).slice(0, 5).map((k) => (
          <span className="kw" key={k}>
            {k}
          </span>
        ))}
      </div>
    </div>
  );
}
