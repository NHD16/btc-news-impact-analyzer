import { BIAS } from "../constants";

export default function OverallCard({ overall }) {
  if (!overall) return null;
  const b = BIAS[overall.bias] || BIAS.neutral;
  return (
    <div className="overall">
      <div className="gauge">
        <div className="bias" style={{ color: b.color }}>
          {b.label}
        </div>
        <div className="lbl">Xu hướng BTC</div>
      </div>
      <div className="summary">{overall.summary}</div>
    </div>
  );
}
