// MENA-INDEX — real MENA map with 16 featured countries

const { useEffect: useEffectM, useState: useStateM } = React;

// ISO 3166-1 numeric → region id (matches data.js)
const FEATURED_IDS = {
  784: "uae",
  682: "ksa",
  634: "qa",
  414: "kw",
  48:  "bh",
  512: "om",
  376: "il",
  400: "jo",
  422: "lb",
  368: "iq",
  364: "ir",
  792: "tr",
  818: "eg",
  504: "ma",
  12:  "dz",
  788: "tn"
};

// Group accent colors (countries inherit from their group)
const GROUP_COLOR = {
  GCC: "#f7c548",
  LEVANT: "#4dd0e1",
  ANATOLIA: "#8b5cff",
  NAFRICA: "#ff5d8f"
};

// Per-country accent (variations on group color for differentiation in charts)
const ACCENT = {
  uae: "#f7c548",
  ksa: "#00e5d4",
  qa:  "#ffb37c",
  kw:  "#ffd96b",
  bh:  "#bfa45a",
  om:  "#dca35a",
  il:  "#4dd0e1",
  jo:  "#7ad6ff",
  lb:  "#a6e9ff",
  iq:  "#5a93bf",
  ir:  "#a877ff",
  tr:  "#6e3dff",
  eg:  "#ff9a3d",
  ma:  "#ff5d8f",
  dz:  "#ff7da9",
  tn:  "#d65a9c"
};

const CONTEXT_IDS = new Set([
  // featured will render in their own pass
  434, 729, 887, 732, 275, 760, 762, 706
]);

let _topoCache = null;
let _topoPromise = null;
function loadTopo() {
  if (_topoCache) return Promise.resolve(_topoCache);
  if (_topoPromise) return _topoPromise;
  _topoPromise = fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json")
    .then((r) => r.json())
    .then((t) => { _topoCache = t; return t; });
  return _topoPromise;
}

function MenaMap({ regions, active, onSelect, lang, height = 540 }) {
  const [topo, setTopo] = useStateM(null);
  const [hover, setHover] = useStateM(null);

  useEffectM(() => {
    let alive = true;
    loadTopo().then((t) => alive && setTopo(t)).catch((e) => console.error("map", e));
    return () => { alive = false; };
  }, []);

  const W = 1100;
  const H = height;

  if (!topo || !window.topojson || !window.d3) {
    return (
      <div className="map-loading" style={{ height: H }}>
        <div className="map-loading__inner">
          <div className="map-loading__bar"><div></div></div>
          <span>ACQUIRING SATELLITE FEED…</span>
        </div>
      </div>
    );
  }

  const fc = window.topojson.feature(topo, topo.objects.countries);
  const all = fc.features;
  const projection = window.d3.geoMercator()
    .center([28, 28])
    .scale(620)
    .translate([W / 2, H / 2 + 30]);
  const pathGen = window.d3.geoPath(projection);

  const contextFeatures = [];
  const featuredFeatures = [];
  all.forEach((f) => {
    const id = +f.id;
    if (FEATURED_IDS[id]) featuredFeatures.push(f);
    else if (CONTEXT_IDS.has(id)) contextFeatures.push(f);
  });

  const regionById = {};
  regions.forEach((r) => (regionById[r.id] = r));

  return (
    <div className="mena-map">
      <svg viewBox={`0 0 ${W} ${H}`} className="mena-map__svg">
        <defs>
          <pattern id="map-grid-real" patternUnits="userSpaceOnUse" width="40" height="40">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(247,197,72,0.05)" strokeWidth="0.8" />
          </pattern>
          <radialGradient id="map-bg-glow" cx="50%" cy="55%" r="55%">
            <stop offset="0%" stopColor="rgba(247,197,72,0.08)" />
            <stop offset="100%" stopColor="rgba(247,197,72,0)" />
          </radialGradient>
        </defs>

        <rect x="0" y="0" width={W} height={H} fill="url(#map-grid-real)" />
        <rect x="0" y="0" width={W} height={H} fill="url(#map-bg-glow)" />

        {[15, 20, 25, 30, 35, 40].map((lat) => {
          const pts = [];
          for (let lon = -20; lon <= 70; lon += 5) {
            const [x, y] = projection([lon, lat]);
            pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
          }
          return <polyline key={"lat" + lat} points={pts.join(" ")} fill="none" stroke="rgba(247,197,72,0.05)" strokeDasharray="2 4" />;
        })}
        {[-10, 0, 10, 20, 30, 40, 50, 60].map((lon) => {
          const pts = [];
          for (let lat = 10; lat <= 45; lat += 5) {
            const [x, y] = projection([lon, lat]);
            pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
          }
          return <polyline key={"lon" + lon} points={pts.join(" ")} fill="none" stroke="rgba(247,197,72,0.05)" strokeDasharray="2 4" />;
        })}

        {contextFeatures.map((f) => (
          <path
            key={"ctx-" + f.id}
            d={pathGen(f)}
            fill="rgba(247,197,72,0.03)"
            stroke="rgba(247,197,72,0.16)"
            strokeWidth="0.5"
          />
        ))}

        {featuredFeatures.map((f) => {
          const id = +f.id;
          const regionId = FEATURED_IDS[id];
          const r = regionById[regionId];
          if (!r) return null;
          const c = GROUP_COLOR[r.group] || ACCENT[regionId];
          const isActive = active === regionId;
          const isHover = hover === regionId;
          return (
            <path
              key={"feat-" + id}
              d={pathGen(f)}
              fill={isActive || isHover ? c + "55" : c + "22"}
              stroke={c}
              strokeWidth={isActive ? 2.2 : isHover ? 1.6 : 1}
              style={{
                cursor: "pointer",
                filter: `drop-shadow(0 0 ${isActive ? 10 : 4}px ${c})`,
                transition: "fill 180ms, stroke-width 180ms"
              }}
              onMouseEnter={() => setHover(regionId)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect && onSelect(regionId)}
            />
          );
        })}

        {/* Pulsing pin per featured country (always visible) */}
        {regions.map((r) => {
          const [x, y] = projection([r.lon, r.lat]);
          const c = GROUP_COLOR[r.group];
          const isActive = active === r.id;
          const isHover = hover === r.id;
          const showLabel = isActive || isHover;
          return (
            <g key={"pin-" + r.id}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHover(r.id)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect && onSelect(r.id)}>
              <circle cx={x} cy={y} r="10" fill="none" stroke={c} strokeOpacity="0.3">
                <animate attributeName="r" from="6" to="18" dur="2.4s" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" from="0.5" to="0" dur="2.4s" repeatCount="indefinite" />
              </circle>
              <circle cx={x} cy={y} r={isActive ? 5 : 3.5} fill={c}
                style={{ filter: `drop-shadow(0 0 8px ${c})` }} />
              {/* Country code chip */}
              <g transform={`translate(${x + 6}, ${y - 8})`}>
                <rect x="0" y="0" width="22" height="14" fill="rgba(8,10,18,0.92)" stroke={c} strokeOpacity="0.7" />
                <text x="11" y="10" textAnchor="middle" fill={c} fontFamily="JetBrains Mono" fontSize="9" fontWeight="700" letterSpacing="1">
                  {r.code}
                </text>
              </g>
              {/* Hover/active full label */}
              {showLabel && (
                <g transform={`translate(${x + 32}, ${y + 4})`}>
                  <rect x="0" y="-12" width="118" height="36" fill="rgba(8,10,18,0.95)" stroke={c} strokeWidth="1.2" style={{ filter: `drop-shadow(0 0 8px ${c})` }} />
                  <text x="8" y="2" fill={c} fontFamily="Chakra Petch" fontSize="11" fontWeight="700" letterSpacing="2">{r.short_en} · {r.code}</text>
                  <text x="8" y="18" fill="rgba(255,255,255,0.9)" fontFamily="JetBrains Mono" fontSize="12" fontWeight="700">{r.index.toFixed(1)}</text>
                  <text x="58" y="18" fill={r.delta >= 0 ? "#5cffb1" : "#ff3d6b"} fontFamily="JetBrains Mono" fontSize="11">{r.delta >= 0 ? "▲" : "▼"}{Math.abs(r.delta).toFixed(1)}</text>
                </g>
              )}
            </g>
          );
        })}

        <g stroke="rgba(247,197,72,0.55)" strokeWidth="1.2" fill="none">
          <path d="M 6 6 L 6 22 M 6 6 L 22 6" />
          <path d={`M ${W - 6} 6 L ${W - 6} 22 M ${W - 6} 6 L ${W - 22} 6`} />
          <path d={`M 6 ${H - 6} L 6 ${H - 22} M 6 ${H - 6} L 22 ${H - 6}`} />
          <path d={`M ${W - 6} ${H - 6} L ${W - 6} ${H - 22} M ${W - 6} ${H - 6} L ${W - 22} ${H - 6}`} />
        </g>

        {/* Group legend */}
        <g transform={`translate(20, ${H - 32})`} fontFamily="JetBrains Mono" fontSize="9">
          {[
            { c: "#f7c548", l: "GCC" },
            { c: "#4dd0e1", l: "LEVANT" },
            { c: "#8b5cff", l: "ANATOLIA" },
            { c: "#ff5d8f", l: "N.AFRICA" }
          ].map((g, i) => (
            <g key={g.l} transform={`translate(${i * 96}, 0)`}>
              <rect x="0" y="-7" width="9" height="9" fill={g.c} style={{ filter: `drop-shadow(0 0 4px ${g.c})` }} />
              <text x="14" y="1" fill={g.c} letterSpacing="2">{g.l}</text>
            </g>
          ))}
        </g>

        <text x={W - 20} y={H - 14} textAnchor="end" fill="rgba(247,197,72,0.4)" fontFamily="JetBrains Mono" fontSize="9" letterSpacing="2">
          MERCATOR · {regions.length} FEATURED · {lang === "ru" ? "клик — детали" : "click to inspect"}
        </text>
      </svg>
    </div>
  );
}

window.MenaMap = MenaMap;
window.MENA_ACCENT = ACCENT;
window.MENA_GROUP_COLOR = GROUP_COLOR;
