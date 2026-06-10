import { BIAS } from "../constants";

export default function NotificationBanner({ notice, onDismiss, onView }) {
  if (!notice) return null;
  const bias = BIAS[notice.overall?.bias] || BIAS.neutral;

  return (
    <div className="notice">
      <span className="notice-dot" style={{ background: bias.color }} />
      <span className="notice-text">
        🔔 Phát hiện <b>{notice.new_count}</b> tin mới — xu hướng tổng thể:{" "}
        <b style={{ color: bias.color }}>{bias.label}</b>
      </span>
      <button className="notice-view" onClick={onView}>
        Xem ngay
      </button>
      <button className="notice-close" onClick={onDismiss} aria-label="Đóng">
        ✕
      </button>
    </div>
  );
}
