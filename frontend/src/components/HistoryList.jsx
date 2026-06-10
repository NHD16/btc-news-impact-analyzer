import { BIAS } from "../constants";
import { fmtTime, fmtCost } from "../utils";

function statusLabel(h) {
  if (h.status === "done") return (BIAS[h.bias] || BIAS.neutral).label;
  if (h.status === "running") return "⏳ đang chạy";
  return "⚠️ lỗi";
}

export default function HistoryList({ history, onOpen }) {
  return (
    <div className="history">
      <h2>🕘 Lịch sử phân tích</h2>
      {history.length === 0 ? (
        <span className="meta">Chưa có lịch sử.</span>
      ) : (
        history.map((h) => (
          <div className="hrow" key={h.id} onClick={() => onOpen(h.id)}>
            <span className={`hbias ${h.bias}`}>{statusLabel(h)}</span>
            <span className="meta">{fmtTime(h.started_at)}</span>
            <span className="meta">{h.item_count} tin</span>
            <span className="meta">{fmtCost(h.cost_usd)}</span>
          </div>
        ))
      )}
    </div>
  );
}
