import { useState } from "react";
import Header from "./components/Header";
import OverallCard from "./components/OverallCard";
import StatsBar from "./components/StatsBar";
import NewsList from "./components/NewsList";
import HistoryList from "./components/HistoryList";
import { useAnalysis } from "./useAnalysis";
import { fmtCost } from "./utils";

export default function App() {
  const { result, history, running, error, startRun, openRun } = useAnalysis();
  const [minRelevance, setMinRelevance] = useState(3);

  const items = result?.items || [];
  const hasItems = items.length > 0;

  return (
    <>
      <Header
        minRelevance={minRelevance}
        onChangeRelevance={setMinRelevance}
        onRefresh={() => startRun(minRelevance)}
        running={running}
      />

      <main>
        {error && <div className="err">Lỗi: {error}</div>}

        {hasItems && <OverallCard overall={result.overall} />}
        {hasItems && <StatsBar items={items} />}

        {running && (
          <div id="loading">
            <div className="spinner" />
            <span>
              Đang thu thập tin & gọi Claude phân tích... (có thể mất 30–120 giây)
            </span>
          </div>
        )}

        {!running && !hasItems && (
          <div id="empty">
            Chưa có dữ liệu. Bấm <b>Thu thập &amp; Phân tích</b> để bắt đầu.
          </div>
        )}

        {hasItems && <NewsList items={items} />}

        {hasItems && (
          <p className="meta footer">
            Cập nhật:{" "}
            {result.finished_at
              ? new Date(result.finished_at).toLocaleString("vi-VN")
              : "—"}
            {result.cost_usd ? `  •  Chi phí Claude: ${fmtCost(result.cost_usd)}` : ""}
          </p>
        )}

        <HistoryList history={history} onOpen={openRun} />
      </main>
    </>
  );
}
