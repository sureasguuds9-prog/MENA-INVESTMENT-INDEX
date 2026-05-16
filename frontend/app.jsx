// MENA-INDEX — app shell with grouped horizontal tab nav

const { useState: useStateA, useEffect: useEffectA, useRef: useRefA } = React;

function Clock() {
  const [now, setNow] = useStateA(new Date());
  useEffectA(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const pad = (n) => String(n).padStart(2, "0");
  const utc = `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
  const date = `${now.getUTCFullYear()}.${pad(now.getUTCMonth() + 1)}.${pad(now.getUTCDate())}`;
  return (
    <div className="clock">
      <span className="clock__date">{date}</span>
      <span className="clock__time">UTC {utc}</span>
    </div>
  );
}

function Brand() {
  return (
    <div className="brand">
      <div className="brand__mark">
        <svg viewBox="0 0 40 40" width="34" height="34">
          <defs>
            <linearGradient id="bg-mark" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#f7c548" />
              <stop offset="100%" stopColor="#ff5d8f" />
            </linearGradient>
          </defs>
          <polygon points="20,3 35,12 35,28 20,37 5,28 5,12" fill="none" stroke="url(#bg-mark)" strokeWidth="1.5" />
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
  );
}

function TabBar({ regions, groups, active, onSelect, lang }) {
  const scrollerRef = useRefA(null);

  // Order regions by their group order in `groups`
  const groupOrder = groups.reduce((acc, g, i) => ({ ...acc, [g.id]: i }), {});
  const grouped = groups.map((g) => ({
    ...g,
    regions: regions.filter((r) => r.group === g.id)
  }));

  // Auto-scroll active tab into view
  useEffectA(() => {
    const el = scrollerRef.current?.querySelector(".tab.is-active");
    if (el) el.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }, [active]);

  return (
    <div className="tabbar-wrap">
      <div className="tabbar" ref={scrollerRef}>
        <button
          className={`tab tab--overview ${active === "overview" ? "is-active" : ""}`}
          onClick={() => onSelect("overview")}
        >
          <span className="tab__icon">◆</span>
          <span className="tab__col">
            <span className="tab__en">{lang === "ru" ? "ОБЗОР" : "OVERVIEW"}</span>
            <span className="tab__ru">{lang === "ru" ? "вся MENA" : "all regions"}</span>
          </span>
        </button>

        {grouped.map((g, gi) => (
          <React.Fragment key={g.id}>
            <div className="tabbar__group-sep" style={{ "--c": g.color }}>
              <span className="tabbar__group-label" style={{ color: g.color }}>
                {lang === "ru" ? g.label_ru : g.label_en}
              </span>
            </div>
            {g.regions.map((r) => {
              const c = g.color;
              const isActive = active === r.id;
              return (
                <button
                  key={r.id}
                  className={`tab ${isActive ? "is-active" : ""}`}
                  onClick={() => onSelect(r.id)}
                  style={{ "--c": c }}
                >
                  <span className="tab__code">{r.code}</span>
                  <span className="tab__col">
                    <span className="tab__en">{r.short_en}</span>
                    <span className="tab__ru">{lang === "ru" ? r.name_ru : r.name_en}</span>
                  </span>
                  <span className="tab__metric">
                    <span className="tab__val" style={{ color: c }}>{r.index.toFixed(1)}</span>
                    <span className={`tab__delta ${r.delta >= 0 ? "up" : "down"}`}>
                      {r.delta >= 0 ? "▲" : "▼"}{Math.abs(r.delta).toFixed(1)}
                    </span>
                  </span>
                </button>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function Header({ lang, setLang, regionCount }) {
  return (
    <header className="header">
      <Brand />
      <div className="header__right">
        <div className="status">
          <span className="dot dot--pulse"></span>
          <span>STREAM · {regionCount}/{regionCount} NODES</span>
        </div>
        <div className="lang-toggle">
          <button className={lang === "en" ? "is-active" : ""} onClick={() => setLang("en")}>EN</button>
          <button className={lang === "ru" ? "is-active" : ""} onClick={() => setLang("ru")}>РУ</button>
        </div>
        <Clock />
      </div>
    </header>
  );
}

function App() {
  const data = window.MENA_DATA;
  const [active, setActive] = useStateA(() => {
    try { return localStorage.getItem("mena_view") || "overview"; } catch (e) { return "overview"; }
  });
  const [lang, setLang] = useStateA(() => {
    try { return localStorage.getItem("mena_lang") || "en"; } catch (e) { return "en"; }
  });

  // If saved active is a region that no longer exists, reset
  useEffectA(() => {
    if (active !== "overview" && !data.regions.find((r) => r.id === active)) {
      setActive("overview");
    }
  }, []);

  useEffectA(() => { try { localStorage.setItem("mena_view", active); } catch (e) {} }, [active]);
  useEffectA(() => { try { localStorage.setItem("mena_lang", lang); } catch (e) {} }, [lang]);

  useEffectA(() => { window.scrollTo({ top: 0, behavior: "smooth" }); }, [active]);

  const region = active === "overview" ? null : data.regions.find((r) => r.id === active);
  const screenLabel = active === "overview"
    ? "01 Overview"
    : `${String(data.regions.findIndex((r) => r.id === active) + 2).padStart(2, "0")} ${region.short_en}`;

  return (
    <div className="app" data-screen-label={screenLabel}>
      <div className="scanlines"></div>
      <div className="grain"></div>
      <Header lang={lang} setLang={setLang} regionCount={data.regions.length} />
      <TabBar regions={data.regions} groups={data.groups} active={active} onSelect={setActive} lang={lang} />
      <main className="main">
        {active === "overview"
          ? <OverviewView data={data} onSelect={setActive} lang={lang} />
          : <RegionView r={region} regions={data.regions} lang={lang} onSelect={setActive} data={data} />}
      </main>
      <footer className="footer">
        <span>MENA-INDEX · MTX-7 · 2026.Q2 · {data.regions.length} countries</span>
        <span>// illustrative figures — not investment advice</span>
        <span>{lang === "ru" ? "источник · NE 50m · jsdelivr" : "src · NE 50m · jsdelivr"}</span>
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
