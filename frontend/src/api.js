// Lớp giao tiếp với backend FastAPI.

export async function fetchLatest() {
  const r = await fetch("/api/runs/latest");
  if (!r.ok) return null;
  return r.json(); // có thể là null
}

export async function fetchRun(id) {
  const r = await fetch(`/api/runs/${id}`);
  if (!r.ok) throw new Error("Không lấy được run");
  return r.json();
}

export async function fetchHistory(limit = 15) {
  const r = await fetch(`/api/history?limit=${limit}`);
  if (!r.ok) return [];
  return r.json();
}

export async function createRun(minRelevance) {
  const r = await fetch(`/api/runs?min_relevance=${minRelevance}`, {
    method: "POST",
  });
  if (!r.ok) throw new Error("Không tạo được run");
  const { run_id } = await r.json();
  return run_id;
}

// Mở SSE để nhận cập nhật realtime của một run.
// onUpdate(run) gọi mỗi khi có dữ liệu; onEnd() khi kết thúc.
export function streamRun(id, { onUpdate, onEnd }) {
  const es = new EventSource(`/api/runs/${id}/stream`);
  es.onmessage = (e) => {
    try {
      onUpdate(JSON.parse(e.data));
    } catch {
      /* bỏ qua frame không phải JSON */
    }
  };
  es.addEventListener("end", () => {
    es.close();
    onEnd?.();
  });
  es.onerror = () => {
    es.close();
    onEnd?.();
  };
  return () => es.close();
}

// Mở SSE để nhận thông báo khi tự động thu thập phát hiện tin mới.
// onNotify(notification) gọi mỗi khi có thông báo mới.
export function streamNotifications(onNotify) {
  const es = new EventSource("/api/notifications/stream");
  es.onmessage = (e) => {
    try {
      onNotify(JSON.parse(e.data));
    } catch {
      /* bỏ qua frame không phải JSON */
    }
  };
  return () => es.close();
}
