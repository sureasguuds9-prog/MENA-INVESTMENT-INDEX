// MENA-INDEX — stylized MENA region map (hex-coordinate flat projection)

function MenaMap({ regions, active, onSelect, lang }) {
  // Map lat/lon (approx) to SVG coords. Map area: longitude -10..56, latitude 15..38
  const W = 720;
  const H = 320;
  const lonMin = -12;
  const lonMax = 58;
  const latMin = 14;
  const latMax = 38;
  const x = (lon) => ((lon - lonMin) / (lonMax - lonMin)) * W;
  const y = (lat) => H - ((lat - latMin) / (latMax - latMin)) * H;

  // Simplified coastline / outline anchors
  const outline =
    "M 35 240 L 60 220 L 95 215 L 120 230 L 150 240 L 180 250 L 210 240 L 240 230 L 270 220 L 305 215 L 340 220 L 370 215 L 405 210 L 440 205 L 475 200 L 510 195 L 545 195 L 585 200 L 620 210 L 660 220 L 695 230 L 700 290 L 660 295 L 610 290 L 555 285 L 490 280 L 420 278 L 355 275 L 290 268 L 230 255 L 175 250 L 125 252 L 80 260 L 40 270 Z";

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
      <defs>
        <radialGradient id="map-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(247,197,72,0.18)" />
          <stop offset="100%" stopColor="rgba(247,197,72,0)" />
        </radialGradient>
        <pattern id="map-hatch" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(247,197,72,0.08)" strokeWidth="0.8" />
        </pattern>
        <pattern id="map-grid" patternUnits="userSpaceOnUse" width="48" height="32">
          <path d="M 48 0 L 0 0 0 32" fill="none" stroke="rgba(247,197,72,0.05)" strokeWidth="0.8" />
        </pattern>
      </defs>

      <rect x="0" y="0" width={W} height={H} fill="url(#map-grid)" />

      {/* Lat/lon graticule */}
      {[20, 25, 30, 35].map((lat) => (
        <line key={lat} x1="0" x2={W} y1={y(lat)} y2={y(lat)} stroke="rgba(247,197,72,0.07)" strokeDasharray="2 6" />
      ))}
      {[-10, 0, 10, 20, 30, 40, 50].map((lon) => (
        <line key={lon} x1={x(lon)} x2={x(lon)} y1="0" y2={H} stroke="rgba(247,197,72,0.07)" strokeDasharray="2 6" />
      ))}

      {/* Coastline / region mass */}
      <path d={outline} fill="url(#map-hatch)" stroke="rgba(247,197,72,0.35)" strokeWidth="1" />

      {/* Connection lines between regions */}
      {regions.map((a, i) =>
        regions.slice(i + 1).map((b) => (
          <line
            key={a.id + b.id}
            x1={x(a.lon)}
            y1={y(a.lat)}
            x2={x(b.lon)}
            y2={y(b.lat)}
            stroke={active && (active === a.id || active === b.id) ? "rgba(247,197,72,0.4)" : "rgba(247,197,72,0.1)"}
            strokeDasharray="3 5"
            strokeWidth="0.8"
          />
        ))
      )}

      {/* Region nodes */}
      {regions.map((r) => {
        const isActive = active === r.id;
        const cx = x(r.lon);
        const cy = y(r.lat);
        const accentMap = {
          uae: "#f7c548",
          ksa: "#00e5d4",
          qa: "#8b5cff",
          il: "#4dd0e1",
          eg: "#ff9a3d",
          ma: "#ff5d8f"
        };
        const c = accentMap[r.id] || "#f7c548";
        return (
          <g key={r.id} style={{ cursor: "pointer" }} onClick={() => onSelect && onSelect(r.id)}>
            {/* Pulsing rings */}
            <circle cx={cx} cy={cy} r="18" fill="none" stroke={c} strokeOpacity="0.3">
              <animate attributeName="r" from="12" to="28" dur="2.4s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" from="0.5" to="0" dur="2.4s" repeatCount="indefinite" />
            </circle>
            <circle cx={cx} cy={cy} r={isActive ? 14 : 10} fill={c} opacity={isActive ? 0.3 : 0.18} />
            <circle cx={cx} cy={cy} r={isActive ? 7 : 5} fill={c}
              style={{ filter: `drop-shadow(0 0 8px ${c})` }} />

            {/* Label box */}
            <g transform={`translate(${cx + 14}, ${cy - 22})`}>
              <rect x="0" y="0" width="86" height="34" fill="rgba(8,10,20,0.85)" stroke={c} strokeOpacity={isActive ? 0.9 : 0.4} />
              <text x="6" y="13" fill={c} fontFamily="Chakra Petch" fontSize="11" fontWeight="700" letterSpacing="1.5">
                {r.short_en} · {r.code}
              </text>
              <text x="6" y="26" fill="rgba(255,255,255,0.7)" fontFamily="JetBrains Mono" fontSize="10">
                {r.index.toFixed(1)} {r.delta >= 0 ? "▲" : "▼"} {Math.abs(r.delta).toFixed(1)}
              </text>
            </g>
          </g>
        );
      })}

      {/* Scan corners */}
      <g stroke="rgba(247,197,72,0.6)" strokeWidth="1.2" fill="none">
        <path d="M 4 4 L 4 18 M 4 4 L 18 4" />
        <path d={`M ${W - 4} 4 L ${W - 4} 18 M ${W - 4} 4 L ${W - 18} 4`} />
        <path d={`M 4 ${H - 4} L 4 ${H - 18} M 4 ${H - 4} L 18 ${H - 4}`} />
        <path d={`M ${W - 4} ${H - 4} L ${W - 4} ${H - 18} M ${W - 4} ${H - 4} L ${W - 18} ${H - 4}`} />
      </g>

      <text x={W - 10} y={H - 10} textAnchor="end" fill="rgba(247,197,72,0.4)" fontFamily="JetBrains Mono" fontSize="9" letterSpacing="2">
        MENA · 12.3°N–37.4°N
      </text>
    </svg>
  );
}

window.MenaMap = MenaMap;
