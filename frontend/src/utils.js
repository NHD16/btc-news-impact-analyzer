// Định dạng mốc thời gian ISO sang giờ UTC+7 + thời gian tương đối (tính theo UTC 0).
export function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  // Hiệu của hai mốc tuyệt đối (epoch ms) → luôn tính theo UTC 0, độc lập múi giờ.
  const diff = (Date.now() - d.getTime()) / 1000; // giây
  let rel;
  if (diff < 0) rel = "sắp tới";
  else if (diff < 60) rel = "vừa xong";
  else if (diff < 3600) rel = `${Math.floor(diff / 60)} phút trước`;
  else if (diff < 86400) rel = `${Math.floor(diff / 3600)} giờ trước`;
  else rel = `${Math.floor(diff / 86400)} ngày trước`;
  const abs = d.toLocaleString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  });
  return `${abs} UTC+7 (${rel})`;
}

export function fmtCost(usd) {
  if (usd == null) return "";
  return `$${Number(usd).toFixed(4)}`;
}
