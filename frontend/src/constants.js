// Ánh xạ nhãn hiển thị cho hướng giá, mức tác động, xu hướng tổng thể.

export const DIR = {
  up: { label: "BTC ▲ TĂNG", cls: "up" },
  down: { label: "BTC ▼ GIẢM", cls: "down" },
  flat: { label: "BTC ◆ ĐI NGANG", cls: "flat" },
};

export const IMPACT = {
  high: "Tác động CAO",
  medium: "Tác động TB",
  low: "Tác động thấp",
};

export const BIAS = {
  bullish: { label: "BULLISH 🐂", color: "var(--good)" },
  bearish: { label: "BEARISH 🐻", color: "var(--bad)" },
  neutral: { label: "NEUTRAL", color: "var(--flat)" },
};

export const RELEVANCE_OPTIONS = [
  { value: 1, label: "Tất cả" },
  { value: 3, label: "Trung bình+" },
  { value: 5, label: "Cao (chỉ tin quan trọng)" },
  { value: 8, label: "Rất cao" },
];
