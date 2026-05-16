// MENA-INDEX — main app shell

const { useState: useStateA, useEffect: useEffectA, useMemo: useMemoA } = React;

function Clock() {
  const [now, setNow] = useStateA(new Date());
  useEffectA(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const pad = (n) => String(n).padStart(2, "0");
  const utc = `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
  const local = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  const date = `${now.getUTCFullYear()}.${pad(now.getUTCMonth() + 1)}.${pad(now.getUTCDate())}`;
  return (
    <div className="clock">
      <div className="clock__row">
        <span className="clock__k">UTC</span>
        <span className="clock__v">{utc}</span>
      </div>
      <div className="clock__row">
        <span className="clock__k">LOC</span>
        <span className="clock__v">{local}</span>
      </div>
      <div className="clock__date">{date}</div>
    </div>
  );
}

function Ticker({ items, lang }) {
  const repeated = [...items, ...items, ...items];
  return (
    <div className="ticker">
      <div className="ticker__label">
        <span className="dot dot--pulse"></span>
        MENA·LIVE
      </div>
      <div className="ticker__lane">
        <div className="ticker__track">
          {repeated.map((it, i) => (
            <span key={i} className="ticker__item">
              <span className="ticker__tag" data-tag={it.tag}>{it.tag}</span>
              <span className="ticker__txt">{lang === "ru" ? it.ru : it.en}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function Sidebar({ regions, active, onSelect, lang }) {
  const accentMap = {
    uae: "#f7c548",
    ksa: "#00e5d4",
    qa: "#8b5cff",
    il: "#4dd0e1",
    eg: "#ff9a3d",
    ma: "#ff5d8f"
  };
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="brand">
          <div className="brand__mark">
            <svg viewBox="0 0 40 40" width="36" height="36">
              <defs>
                <linearGradient id="bg1" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#f7c548" />
                  <stop offset="100%" stopColor="#ff5d8f" />
                </linearGradient>
              </defs>
              <polygon points="20,3 35,12 35,28 20,37 5,28 5,12" fill="none" stroke="url(#bg1)" strokeWidth="1.5" />
              <polygon points="20,9 30,15 30,25 20,31 10,25 10,15" fill="none" stroke="#f7c548" strokeOpacity="0.5" strokeWidth="1" />
              <circle cx="20" cy="20" r="3.5" fill="#f7c548" />
              <circle cx="20" cy="20" r="6" fill="none" stroke="#f7c548" strokeOpacity="0.4" />
            </svg>
          </div>
          <div className="brand__text">
            <div className="brand__title">MENA<span>·</span>INDEX</div>
            <div className="brand__sub">macro intelligence terminal</div>
          </div>
        </div>
      </div>

      <div className="sidebar__section">
        <div className="sidebar__heading">
          <span>// VIEWS</span>
          <span>v2.4.1</span>
        </div>
        <button
          className={`nav-item nav-item--overview ${active === "overview" ? "is-active" : ""}`}
          onClick={() => onSelect("overview")}
        >
          <span className="nav-item__hex">◆</span>
          <span className="nav-item__txt">
            <span className="nav-item__en">OVERVIEW</span>
            <span className="nav-item__ru">Обзор · MENA</span>
          </span>
          <span className="nav-item__indicator"></span>
        </button>
      </div>

      <div className="sidebar__section">
        <div className="sidebar__heading">
          <span>// REGIONS / РЕГИОНЫ</span>
          <span>6</span>
        </div>
        {regions.map((r) => {
          const c = accentMap[r.id];
          return (
            <button
              key={r.id}
              className={`nav-item ${active === r.id ? "is-active" : ""}`}
              onClick={() => onSelect(r.id)}
              style={{ "--c": c }}
            >
              <span className="nav-item__code">{r.code}</span>
              <span className="nav-item__txt">
                <span className="nav-item__en">{r.short_en} · {r.name_en}</span>
                <span className="nav-item__ru">{r.name_ru}</span>
              </span>
              <span className="nav-item__val" style={{ color: c }}>{r.index.toFixed(1)}</span>
              <span className={`nav-item__delta ${r.delta >= 0 ? "up" : "down"}`}>
                {r.delta >= 0 ? "▲" : "▼"}{Math.abs(r.delta).toFixed(1)}
              </span>
            </button>
          );
        })}
      </div>

      <div className="sidebar__footer">
        <div className="sidebar__status">
          <span className="dot dot--pulse"></span>
          <span>FEED · STREAMING</span>
        </div>
        <div className="sidebar__status sidebar__status--mute">
          <span>NODES 6/6 · LAT 42ms</span>
        </div>
      </div>
    </aside>
  );
}

function Header({ active, lang, setLang, data }) {
  const region = active === "overview" ? null : data.regions.find((r) => r.id === active);
  return (
    <header className="header">
      <div className="header__left">
        <div className="header__breadcrumb">
          <span className="header__crumb">MENA-INDEX</span>
          <span className="header__sep">/</span>
          <span className="header__crumb header__crumb--active">
            {region ? `${region.code} · ${lang === "ru" ? region.name_ru : region.name_en}` : (lang === "ru" ? "ОБЗОР" : "OVERVIEW")}
          </span>
        </div>
        <div className="header__mission">
          <span className="header__mission-k">MISSION</span>
          <span className="header__mission-v">MENA-MTX · 2026.05.16 · SHIFT-α</span>
        </div>
      </div>
      <div className="header__center">
        <div className="header__metrics">
          <div className="hm">
            <span className="hm__k">BRENT</span>
            <span className="hm__v">$82.4</span>
            <span className="hm__d up">+0.7%</span>
          </div>
          <div className="hm">
            <span className="hm__k">DXY</span>
            <span className="hm__v">104.2</span>
            <span className="hm__d down">−0.2%</span>
          </div>
          <div className="hm">
            <span className="hm__k">GOLD</span>
            <span className="hm__v">$2,418</span>
            <span className="hm__d up">+0.4%</span>
          </div>
          <div className="hm">
            <span className="hm__k">10Y UST</span>
            <span className="hm__v">4.32%</span>
            <span className="hm__d down">−2bp</span>
          </div>
          <div className="hm">
            <span className="hm__k">BTC</span>
            <span className="hm__v">$67,140</span>
            <span className="hm__d up">+1.2%</span>
          </div>
        </div>
      </div>
      <div className="header__right">
        <div className="lang-toggle">
          <button className={lang === "en" ? "is-active" : ""} onClick={() => setLang("en")}>EN</button>
          <button className={lang === "ru" ? "is-active" : ""} onClick={() => setLang("ru")}>RU</button>
        </div>
        <Clock />
      </div>
    </header>
  );
}

function App() {
  const data = window.MENA_DATA;
  const initial = (() => {
    try {
      return localStorage.getItem("mena_view") || "overview";
    } catch (e) {
      return "overview";
    }
  })();
  const [active, setActive] = useStateA(initial);
  const initLang = (() => {
    try {
      return localStorage.getItem("mena_lang") || "en";
    } catch (e) {
      return "en";
    }
  })();
  const [lang, setLang] = useStateA(initLang);

  useEffectA(() => {
    try { localStorage.setItem("mena_view", active); } catch (e) {}
  }, [active]);
  useEffectA(() => {
    try { localStorage.setItem("mena_lang", lang); } catch (e) {}
  }, [lang]);

  const region = active === "overview" ? null : data.regions.find((r) => r.id === active);
  const screenLabel = active === "overview" ? "01 Overview" :
    `${String(data.regions.findIndex(r => r.id === active) + 2).padStart(2, "0")} ${region.short_en}`;

  return (
    <div className="app" data-screen-label={screenLabel}>
      <div className="scanlines"></div>
      <div className="grain"></div>
      <Header active={active} lang={lang} setLang={setLang} data={data} />
      <div className="app__body">
        <Sidebar regions={data.regions} active={active} onSelect={setActive} lang={lang} />
        <main className="main" key={active}>
          {active === "overview" ? (
            <OverviewView data={data} onSelect={setActive} lang={lang} />
          ) : (
            <RegionView r={region} regions={data.regions} lang={lang} onSelect={setActive} />
          )}
        </main>
      </div>
      <Ticker items={data.ticker} lang={lang} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
