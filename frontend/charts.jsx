// MENA-INDEX — chart components (SVG, React)

const { useMemo, useEffect, useState, useRef } = React;

function path(points, w, h, padX = 4, padY = 4) {
  if (!points.length) return "";
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const xs = (i) => padX + (i / (points.length - 1)) * (w - padX * 2);
  const ys = (v) => h - padY - ((v - min) / range) * (h - padY * 2);
  return points.map((v, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(2)},${ys(v).toFixed(2)}`).join(" ");
}

function areaPath(points, w, h, padX = 4, padY = 4) {
  if (!points.length) return "";
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const xs = (i) => padX + (i / (points.length - 1)) * (w - padX * 2);
  const ys = (v) => h - padY - ((v - min) / range) * (h - padY * 2);
  const line = points.map((v, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(2)},${ys(v).toFixed(2)}`).join(" ");
  return `${line} L${xs(points.length - 1).toFixed(2)},${h} L${xs(0).toFixed(2)},${h} Z`;
}

function Sparkline({ data, w = 120, h = 32, color = "var(--gold)", fill = true, glow = true, animate = true }) {
  const id = useMemo(() => "sl_" + Math.random().toString(36).slice(2, 8), []);
  const ref = useRef(null);
  useEffect(() => {
    if (!animate || !ref.current) return;
    const len = ref.current.getTotalLength();
    ref.current.style.strokeDasharray = len;
    ref.current.style.strokeDashoffset = len;
    requestAnimationFrame(() => {
      ref.current.style.transition = "stroke-dashoffset 1.2s ease-out";
      ref.current.style.strokeDashoffset = 0;
    });
  }, [data]);
  return (
    <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.45" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={areaPath(data, w, h)} fill={`url(#${id})`} />}
      <path
        ref={ref}
        d={path(data, w, h)}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ filter: glow ? `drop-shadow(0 0 4px ${color})` : "none" }}
      />
    </svg>
  );
}

function AreaChart({ data, w = 640, h = 220, color = "var(--gold)", label = "" }) {
  const id = useMemo(() => "ac_" + Math.random().toString(36).slice(2, 8), []);
  const min = Math.min(...data);
  const max = Math.max(...data);
  const padX = 36;
  const padY = 24;
  const xs = (i) => padX + (i / (data.length - 1)) * (w - padX * 2);
  const ys = (v) => h - padY - ((v - min) / (max - min || 1)) * (h - padY * 2);
  const grid = 4;
  const ticks = Array.from({ length: grid + 1 }, (_, i) => min + (i / grid) * (max - min));
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: h, display: "block", overflow: "visible" }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.45" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
        <pattern id={id + "_grid"} width="48" height="32" patternUnits="userSpaceOnUse">
          <path d="M 48 0 L 0 0 0 32" fill="none" stroke="rgba(255,215,100,0.04)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect x={padX} y={padY} width={w - padX * 2} height={h - padY * 2} fill={`url(#${id + "_grid"})`} />
      {ticks.map((t, i) => (
        <g key={i}>
          <line
            x1={padX}
            x2={w - padX}
            y1={ys(t)}
            y2={ys(t)}
            stroke="rgba(255,215,100,0.08)"
            strokeDasharray="2 4"
          />
          <text x={6} y={ys(t) + 3} fill="rgba(255,215,100,0.4)" fontSize="9" fontFamily="JetBrains Mono">
            {t.toFixed(1)}
          </text>
        </g>
      ))}
      <path d={areaPath(data, w, h, padX, padY)} fill={`url(#${id})`} />
      <path
        d={path(data, w, h, padX, padY)}
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ filter: `drop-shadow(0 0 6px ${color})` }}
      />
      {data.map((v, i) =>
        i === data.length - 1 ? (
          <g key={i}>
            <circle cx={xs(i)} cy={ys(v)} r="3.5" fill={color} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
            <circle cx={xs(i)} cy={ys(v)} r="8" fill="none" stroke={color} strokeOpacity="0.4">
              <animate attributeName="r" from="4" to="14" dur="1.6s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" from="0.6" to="0" dur="1.6s" repeatCount="indefinite" />
            </circle>
          </g>
        ) : null
      )}
      {label && (
        <text x={padX} y={14} fill={color} fontSize="10" fontFamily="JetBrains Mono" letterSpacing="2">
          {label.toUpperCase()}
        </text>
      )}
    </svg>
  );
}

function RadialGauge({ value, max = 100, label = "RISK", sub = "", color = "var(--gold)", size = 180 }) {
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const startA = -210;
  const endA = 30;
  const span = endA - startA;
  const pct = Math.min(1, Math.max(0, value / max));
  const valA = startA + span * pct;
  const polar = (a) => {
    const rad = (a * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  function arc(a1, a2) {
    const [x1, y1] = polar(a1);
    const [x2, y2] = polar(a2);
    const large = a2 - a1 > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
  }
  const ticks = Array.from({ length: 25 }, (_, i) => startA + (i / 24) * span);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
      <path d={arc(startA, endA)} fill="none" stroke="rgba(255,215,100,0.1)" strokeWidth="10" strokeLinecap="round" />
      <path
        d={arc(startA, valA)}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 8px ${color})` }}
      />
      {ticks.map((a, i) => {
        const [x1, y1] = polar(a);
        const inner = r - (i % 4 === 0 ? 16 : 8);
        const rad = (a * Math.PI) / 180;
        const x2 = cx + inner * Math.cos(rad);
        const y2 = cy + inner * Math.sin(rad);
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={a <= valA ? color : "rgba(255,215,100,0.18)"}
            strokeWidth={i % 4 === 0 ? 1.5 : 0.8}
            strokeOpacity={a <= valA ? 1 : 0.5}
          />
        );
      })}
      <text x={cx} y={cy - 8} textAnchor="middle" fontFamily="Chakra Petch" fontSize={size * 0.28} fill={color}
        style={{ filter: `drop-shadow(0 0 6px ${color})` }}>
        {Math.round(value)}
      </text>
      <text x={cx} y={cy + 16} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="10" fill="rgba(255,215,100,0.6)" letterSpacing="3">
        {label}
      </text>
      {sub && (
        <text x={cx} y={cy + 32} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="9" fill="rgba(255,255,255,0.4)">
          {sub}
        </text>
      )}
    </svg>
  );
}

function BarRow({ label, value, max, color = "var(--gold)", suffix = "" }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="bar-row">
      <div className="bar-row__label">{label}</div>
      <div className="bar-row__track">
        <div
          className="bar-row__fill"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 10px ${color}` }}
        ></div>
      </div>
      <div className="bar-row__value" style={{ color }}>{value}{suffix}</div>
    </div>
  );
}

function Heatmap({ matrix, labels }) {
  const ids = Object.keys(matrix);
  const cell = 44;
  return (
    <div className="heatmap">
      <div className="heatmap__grid" style={{ gridTemplateColumns: `60px repeat(${ids.length}, ${cell}px)` }}>
        <div></div>
        {ids.map((c) => (
          <div key={c} className="heatmap__head">{labels[c]}</div>
        ))}
        {ids.map((r) => (
          <React.Fragment key={r}>
            <div className="heatmap__head heatmap__head--row">{labels[r]}</div>
            {ids.map((c) => {
              const v = matrix[r][c];
              const isDiag = r === c;
              const intensity = v;
              const hue = v > 0.6 ? 45 : v > 0.3 ? 175 : 290;
              return (
                <div
                  key={c}
                  className="heatmap__cell"
                  style={{
                    background: isDiag
                      ? "rgba(247,197,72,0.12)"
                      : `hsla(${hue}, 80%, ${30 + intensity * 25}%, ${0.18 + intensity * 0.6})`,
                    color: intensity > 0.5 ? "#fff" : "rgba(255,255,255,0.7)",
                    boxShadow: intensity > 0.7 ? `inset 0 0 8px hsla(${hue},90%,60%,0.5)` : "none"
                  }}
                >
                  {isDiag ? "—" : v.toFixed(2)}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function CountUp({ value, decimals = 1, prefix = "", suffix = "", duration = 900 }) {
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);
  useEffect(() => {
    const from = fromRef.current;
    const start = performance.now();
    let raf;
    function step(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (value - from) * eased);
      if (t < 1) raf = requestAnimationFrame(step);
      else fromRef.current = value;
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return <span>{prefix}{display.toFixed(decimals)}{suffix}</span>;
}

function CompareChart({ series, w = 800, h = 280, normalize = false, label = "" }) {
  // series: [{id, label, color, data}]
  if (!series || !series.length) return null;
  const padX = 44;
  const padY = 28;

  // Optionally normalize each series to index = 100 at first point
  const processed = series.map((s) => {
    if (!normalize) return s;
    const first = s.data[0] || 1;
    return { ...s, data: s.data.map((v) => (v / first) * 100) };
  });

  const allValues = processed.flatMap((s) => s.data);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || 1;
  const n = processed[0].data.length;
  const xs = (i) => padX + (i / (n - 1)) * (w - padX * 2);
  const ys = (v) => h - padY - ((v - min) / range) * (h - padY * 2);
  const grid = 4;
  const ticks = Array.from({ length: grid + 1 }, (_, i) => min + (i / grid) * range);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: h, display: "block", overflow: "visible" }}>
      <defs>
        <pattern id="cc_grid" width="48" height="32" patternUnits="userSpaceOnUse">
          <path d="M 48 0 L 0 0 0 32" fill="none" stroke="rgba(247,197,72,0.04)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect x={padX} y={padY} width={w - padX * 2} height={h - padY * 2} fill="url(#cc_grid)" />
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={padX} x2={w - padX} y1={ys(t)} y2={ys(t)} stroke="rgba(247,197,72,0.08)" strokeDasharray="2 4" />
          <text x={6} y={ys(t) + 3} fill="rgba(247,197,72,0.4)" fontSize="9" fontFamily="JetBrains Mono">
            {normalize ? t.toFixed(0) : t.toFixed(1)}
          </text>
        </g>
      ))}
      {processed.map((s, si) => {
        const d = s.data.map((v, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join(" ");
        const last = s.data[s.data.length - 1];
        return (
          <g key={s.id}>
            <path d={d} fill="none" stroke={s.color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"
              style={{ filter: `drop-shadow(0 0 5px ${s.color})` }} />
            <circle cx={xs(n - 1)} cy={ys(last)} r="3.5" fill={s.color}
              style={{ filter: `drop-shadow(0 0 6px ${s.color})` }} />
            <text x={xs(n - 1) + 8} y={ys(last) + 4} fill={s.color} fontFamily="JetBrains Mono" fontSize="10" fontWeight="700" letterSpacing="1">
              {s.label}
            </text>
          </g>
        );
      })}
      {label && (
        <text x={padX} y={16} fill="rgba(247,197,72,0.8)" fontSize="10" fontFamily="JetBrains Mono" letterSpacing="2">
          {label.toUpperCase()}{normalize ? " · INDEX=100" : ""}
        </text>
      )}
    </svg>
  );
}

Object.assign(window, { Sparkline, AreaChart, RadialGauge, BarRow, Heatmap, CountUp, CompareChart });
