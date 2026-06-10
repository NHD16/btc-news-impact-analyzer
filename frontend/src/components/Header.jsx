import { RELEVANCE_OPTIONS } from "../constants";

export default function Header({ minRelevance, onChangeRelevance, onRefresh, running }) {
  return (
    <header>
      <h1>
        <span className="logo">₿</span> BTC News Impact Analyzer
      </h1>
      <div className="controls">
        <label className="meta">
          Lọc độ liên quan:{" "}
          <select
            value={minRelevance}
            onChange={(e) => onChangeRelevance(Number(e.target.value))}
            disabled={running}
          >
            {RELEVANCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <button className="primary" onClick={onRefresh} disabled={running}>
          🔄 Thu thập & Phân tích
        </button>
      </div>
    </header>
  );
}
