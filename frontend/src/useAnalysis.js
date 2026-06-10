import { useCallback, useEffect, useState } from "react";
import * as api from "./api";

// Hook trung tâm: nạp dữ liệu, chạy phân tích mới (SSE), tải lịch sử.
export function useAnalysis() {
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const loadHistory = useCallback(async () => {
    setHistory(await api.fetchHistory(15));
  }, []);

  const loadLatest = useCallback(async () => {
    const latest = await api.fetchLatest();
    if (latest) setResult(latest);
  }, []);

  const openRun = useCallback(async (id) => {
    try {
      setResult(await api.fetchRun(id));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const startRun = useCallback(
    async (minRelevance) => {
      setError(null);
      setRunning(true);
      try {
        const runId = await api.createRun(minRelevance);
        api.streamRun(runId, {
          onUpdate: (run) => {
            if (run.status === "done") setResult(run);
            else if (run.status === "error") setError(run.error || "Lỗi không rõ");
          },
          onEnd: () => {
            setRunning(false);
            loadHistory();
          },
        });
      } catch (e) {
        setError(e.message);
        setRunning(false);
      }
    },
    [loadHistory]
  );

  useEffect(() => {
    loadLatest();
    loadHistory();
  }, [loadLatest, loadHistory]);

  // Lắng nghe thông báo tin mới từ vòng tự động thu thập.
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    const close = api.streamNotifications((note) => {
      setNotice(note);
      loadHistory();
      // Nếu đang xem run mới nhất (không phải lịch sử cũ), cập nhật luôn.
      api.fetchLatest().then((latest) => {
        if (latest && latest.id === note.run_id) setResult(latest);
      });

      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("BTC News Impact Analyzer", {
          body: `Có ${note.new_count} tin mới • Xu hướng: ${note.overall.bias}`,
        });
      }
    });
    return close;
  }, [loadHistory]);

  return { result, history, running, error, notice, dismissNotice: () => setNotice(null), startRun, openRun };
}
