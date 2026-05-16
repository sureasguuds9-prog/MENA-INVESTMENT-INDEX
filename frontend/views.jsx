// MENA-INDEX — views (Overview + Region) with market strip + compare mode

const { useState: useStateV, useEffect: useEffectV, useMemo: useMemoV } = React;

function Delta({ value, big = false, suffix = "" }) {
  const cls = value >= 0 ? "delta delta--up" : "delta delta--down";
  return (
    <span className={cls + (big ? " delta--big" : "")}>
      {value >= 0 ? "▲" : "▼"} {Math.abs(value).toFixed(value < 1 && value > -1 ? 2 : 1)}{suffix}
    </span>
  );
}

function Panel({ title, sub, accent = "var(--gold)", children, right, className = "" }) {
  return (
    <div className={`panel ${className}`} style={{ "--panel-accent": accent }}>
      <div className="panel__head">
        <div className="panel__title-wrap">
          <span className="panel__bracket">[</span>
          <span className="panel__title">{title}</span>
          {sub && <span className="panel__sub">// {sub}</span>}
          <span className="panel__bracket">]</span>
        </div>
        {right && <div className="panel__right">{right}</div>}
      </div>
      <div className="panel__body">{children}</div>
      <div className="panel__corner panel__corner--tl"></div>
      <div className="panel__corner panel__corner--tr"></div>
      <div className="panel__corner panel__corner--bl"></div>
      <div className="panel__corner panel__corner--br"></div>
    </div>
  );
}

/** MarketStrip — top row of contextual market data per country/overview */
function MarketStrip({ region, market, lang }) {
  // For region: show USD/CCY, BRENT, GOLD, country benchmark
  // For overview: show BRENT, GOLD, DXY, UST10Y, BTC
  const items = region
    ? [
        {
          k: `USD / ${region.currency}`,
          v: region.fx > 1000 ? region.fx.toLocaleString() : region.fx.toFixed(region.fx > 10 ? 2 : 4),
          d: region.fx_d || 0,
          c: "var(--gold)",
          label_ru: `Курс USD / ${region.currency}`
        },
        {
          k: "BRENT",
          v: "$" + market.brent.v.toFixed(1),
          d: market.brent.d,
          c: "var(--amber)",
          label_ru: "Нефть Brent"
        },
        {
          k: "GOLD",
          v: "$" + market.gold.v.toLocaleString(),
          d: market.gold.d,
          c: "var(--gold-soft)",
          label_ru: "Золото · унц."
        },
        {
          k: region.benchmark.name,
          v: region.benchmark.v.toLocaleString(),
          d: region.benchmark.d,
          c: "var(--teal)",
          label_ru: "Локальный индекс"
        }
      ]
    : [
        { k: "BRENT", v: "$" + market.brent.v.toFixed(1), d: market.brent.d, c: "var(--amber)", label_ru: "Нефть Brent" },
        { k: "GOLD",  v: "$" + market.gold.v.toLocaleString(), d: market.gold.d, c: "var(--gold-soft)", label_ru: "Золото" },
        { k: "DXY",   v: market.dxy.v.toFixed(1), d: market.dxy.d, c: "var(--cyan)", label_ru: "Индекс доллара" },
        { k: "UST 10Y", v: market.ust10.v.toFixed(2) + "%", d: market.ust10.d, c: "var(--violet)", label_ru: "Доходность 10Y UST", isBp: true },
        { k: "BTC",   v: "$" + (market.btc.v / 1000).toFixed(1) + "k", d: market.btc.d, c: "var(--rose)", label_ru: "Bitcoin" }
      ];

  return (
    <div className="market-strip">
      {items.map((it, i) => (
        <div key={i} className="market-cell" style={{ "--c": it.c }}>
          <div className="market-cell__top">
            <span className="market-cell__k">{it.k}</span>
            <span className="market-cell__d" data-up={it.d >= 0}>
              {it.d >= 0 ? "▲" : "▼"} {Math.abs(it.d).toFixed(it.isBp ? 2 : 1)}{it.isBp ? "bp" : "%"}
            </span>
          </div>
          <div className="market-cell__v">{it.v}</div>
          <div className="market-cell__lbl">{lang === "ru" ? it.label_ru : ""}</div>
        </div>
      ))}
    </div>
  );
}

function OverviewView({ data, onSelect, lang }) {
  const { regions, composite, market } = data;
  return (
    <div className="view view--overview">
      <MarketStrip region={null} market={market} lang={lang} />
      <div className="overview-grid">
        <Panel
          title={lang === "ru" ? "СВОДНЫЙ ИНДЕКС MENA" : "MENA COMPOSITE INDEX"}
          sub={lang === "ru" ? `агрегат ${regions.length} регионов` : `aggregate · ${regions.length} regions`}
          accent="var(--gold)"
          className="panel--composite"
        >
          <div className="composite">
            <div className="composite__label">
              <span className="dot dot--pulse"></span>
              <span>{lang === "ru" ? "LIVE · СВОДНЫЙ" : "LIVE · AGGREGATE"}</span>
            </div>
            <div className="composite__value">
              <CountUp value={composite.value} decimals={2} />
            </div>
            <div className="composite__deltas">
              <div><span>24h</span><Delta value={composite.delta} /></div>
              <div><span>7d</span><Delta value={composite.delta_w} /></div>
              <div><span>30d</span><Delta value={composite.delta_m} /></div>
            </div>
            <div className="composite__spark">
              <Sparkline data={composite.hist} color="var(--gold)" w={520} h={70} />
            </div>
            <div className="composite__caption">
              {lang === "ru" ? "60 ПЕРИОДОВ · ВСЕ РЕГИОНЫ" : "60-PERIOD TRACE · ALL REGIONS"}
            </div>
          </div>
        </Panel>

        <Panel
          title={lang === "ru" ? "КАРТА РЕГИОНА" : "REGION MAP"}
          sub={lang === "ru" ? "клик — открыть страну" : "click country to open dashboard"}
          accent="var(--teal)"
          className="panel--map"
          right={<span className="tag" style={{ color: "var(--teal)", borderColor: "var(--teal)" }}>{regions.length} NODES · LIVE</span>}
        >
          <MenaMap regions={regions} active={null} onSelect={onSelect} lang={lang} height={520} />
        </Panel>
      </div>

      <Panel
        title={lang === "ru" ? "РАНЖИРОВАНИЕ" : "REGION RANKING"}
        sub={lang === "ru" ? `все ${regions.length} стран` : `all ${regions.length} countries`}
        accent="var(--violet)"
      >
        <div className="rank-grid">
          {regions.slice().sort((a, b) => b.index - a.index).map((r, i) => {
            const c = window.MENA_GROUP_COLOR[r.group];
            return (
              <button key={r.id} className="rank-tile" style={{ "--c": c }} onClick={() => onSelect(r.id)}>
                <span className="rank-tile__rank">#{i + 1}</span>
                <span className="rank-tile__code" style={{ color: c }}>{r.code}</span>
                <span className="rank-tile__name">{lang === "ru" ? r.name_ru : r.short_en}</span>
                <span className="rank-tile__val" style={{ color: c }}>{r.index.toFixed(1)}</span>
                <Delta value={r.delta} />
              </button>
            );
          })}
        </div>
      </Panel>
    </div>
  );
}

function AnalyticsLab({ r, regions, lang }) {
  const allMetrics = [
    { id: "gdp", label_en: "GDP Growth", label_ru: "Рост ВВП", unit: "%" },
    { id: "cpi", label_en: "Inflation", label_ru: "Инфляция", unit: "%" },
    { id: "fx",  label_en: "FX Rate · USD", label_ru: "Курс к USD", unit: "" },
    { id: "pmi", label_en: "PMI", label_ru: "PMI", unit: "" }
  ];
  const [activeMetrics, setActiveMetrics] = useStateV(allMetrics.map((m) => m.id));
  const [compareIds, setCompareIds] = useStateV([]);
  const [normalize, setNormalize] = useStateV(false);

  // Reset compare when region changes
  useEffectV(() => { setCompareIds([]); }, [r.id]);

  const toggleCompare = (id) => {
    setCompareIds((cur) =>
      cur.includes(id) ? cur.filter((x) => x !== id) : cur.length >= 5 ? cur : [...cur, id]
    );
  };
  const removeMetric = (id) => setActiveMetrics((cur) => cur.filter((m) => m !== id));
  const addMetric = (id) => setActiveMetrics((cur) => (cur.includes(id) ? cur : [...cur, id]));

  const buildSeries = (metricId) => {
    const self = {
      id: r.id,
      label: r.short_en,
      color: window.MENA_GROUP_COLOR[r.group],
      data: r.ind[metricId]
    };
    const peers = compareIds
      .map((id) => regions.find((x) => x.id === id))
      .filter(Boolean)
      .map((p) => ({
        id: p.id,
        label: p.short_en,
        color: window.MENA_GROUP_COLOR[p.group],
        data: p.ind[metricId]
      }));
    return [self, ...peers];
  };

  const hiddenMetrics = allMetrics.filter((m) => !activeMetrics.includes(m.id));
  const c = window.MENA_GROUP_COLOR[r.group];

  return (
    <Panel
      title={lang === "ru" ? "АНАЛИТИЧЕСКАЯ ЛАБОРАТОРИЯ" : "ANALYTICS LAB"}
      sub={lang === "ru"
        ? `${activeMetrics.length} графика · ${compareIds.length + 1} стран`
        : `${activeMetrics.length} charts · ${compareIds.length + 1} countries`}
      accent="var(--violet)"
      right={
        <div className="ts-controls">
          <button
            className={`seg__btn ${normalize ? "is-active" : ""}`}
            onClick={() => setNormalize((v) => !v)}
            style={normalize ? { color: "var(--violet)", borderColor: "var(--violet)", boxShadow: "inset 0 0 8px rgba(139,92,255,0.3)" } : {}}
            title={lang === "ru" ? "Нормализ. к 100" : "Normalize to 100"}
          >
            {lang === "ru" ? "= 100" : "= 100"}
          </button>
          {compareIds.length > 0 && (
            <button className="seg__btn" onClick={() => setCompareIds([])}>
              {lang === "ru" ? "ОЧИСТИТЬ" : "CLEAR"}
            </button>
          )}
        </div>
      }
    >
      <div className="lab-chips">
        <div className="lab-chips__label">
          <span>{lang === "ru" ? "СТРАНЫ НА ГРАФИКАХ" : "COUNTRIES ON CHARTS"}</span>
          <span className="lab-chips__hint">
            {lang === "ru" ? "клик — добавить/убрать (макс. 5)" : "click to toggle overlay (max 5)"}
          </span>
        </div>
        <div className="lab-chips__row">
          <div className="compare-chip is-on lab-chip--anchor" style={{ "--c": c }} title={lang === "ru" ? "Закреплено" : "Locked anchor"}>
            <span className="compare-chip__dot" style={{ background: c }}></span>
            <span className="compare-chip__code">{r.code}</span>
            <span className="compare-chip__name">{r.short_en}</span>
            <span className="lab-chip__lock">⚓</span>
          </div>
          {regions.filter((p) => p.id !== r.id).map((p) => {
            const pc = window.MENA_GROUP_COLOR[p.group];
            const on = compareIds.includes(p.id);
            return (
              <button
                key={p.id}
                className={`compare-chip ${on ? "is-on" : ""}`}
                onClick={() => toggleCompare(p.id)}
                style={{ "--c": pc }}
              >
                <span className="compare-chip__dot" style={{ background: pc }}></span>
                <span className="compare-chip__code">{p.code}</span>
                <span className="compare-chip__name">{p.short_en}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="lab-grid">
        {activeMetrics.map((mid) => {
          const m = allMetrics.find((x) => x.id === mid);
          const series = buildSeries(mid);
          return (
            <div key={mid} className="lab-chart">
              <div className="lab-chart__head">
                <span className="lab-chart__title">
                  <span className="lab-chart__dot"></span>
                  {lang === "ru" ? m.label_ru : m.label_en}
                  {m.unit && <span className="lab-chart__unit">{m.unit}</span>}
                </span>
                <button
                  className="lab-chart__close"
                  onClick={() => removeMetric(mid)}
                  aria-label="remove"
                  title={lang === "ru" ? "Убрать график" : "Remove chart"}
                >×</button>
              </div>
              <CompareChart
                series={series}
                normalize={normalize && series.length > 1}
                h={210}
                label=""
              />
              {series.length > 1 && (
                <div className="lab-chart__legend">
                  {series.map((s) => (
                    <span key={s.id} className="lab-chart__legend-item">
                      <span className="lab-chart__legend-dot" style={{ background: s.color, boxShadow: `0 0 6px ${s.color}` }}></span>
                      <span style={{ color: s.color }}>{s.label}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {hiddenMetrics.length > 0 && (
          <div className="lab-add">
            <div className="lab-add__title">+ {lang === "ru" ? "ДОБАВИТЬ ГРАФИК" : "ADD CHART"}</div>
            <div className="lab-add__opts">
              {hiddenMetrics.map((m) => (
                <button key={m.id} className="lab-add__btn" onClick={() => addMetric(m.id)}>
                  <span className="lab-add__btn-plus">＋</span>
                  {lang === "ru" ? m.label_ru : m.label_en}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}

function RegionView({ r, regions, lang, onSelect, data }) {
  const c = window.MENA_GROUP_COLOR[r.group];

  const headline = [
    { k: lang === "ru" ? "Рост ВВП" : "GDP Growth", v: r.gdp_growth.toFixed(1) + "%", t: r.gdp_growth > 2 ? "up" : "neutral" },
    { k: lang === "ru" ? "Инфляция" : "Inflation",  v: r.inflation.toFixed(1) + "%",  t: r.inflation > 5 ? "alert" : "stable" },
    { k: "PMI", v: r.pmi.toFixed(1), t: r.pmi > 50 ? "up" : "down" },
    { k: lang === "ru" ? "Риск" : "Risk", v: r.risk, t: r.risk > 60 ? "alert" : r.risk > 35 ? "neutral" : "up" }
  ];

  const myRank = regions.slice().sort((a, b) => b.index - a.index).findIndex((p) => p.id === r.id) + 1;

  return (
    <div className="view view--region" style={{ "--c": c }}>
      <MarketStrip region={r} market={data.market} lang={lang} />

      <div className="region-hero">
        <div className="region-hero__id">
          <span className="region-hero__code" style={{ color: c, borderColor: c }}>{r.code}</span>
          <div className="region-hero__name">
            <div className="region-hero__name-en">{r.name_en}</div>
            <div className="region-hero__name-ru">{r.name_ru}</div>
          </div>
          <span className="region-hero__tier" style={{ color: c }}>TIER {r.tier}</span>
        </div>

        <div className="region-hero__core">
          <div className="region-hero__big" style={{ color: c, textShadow: `0 0 24px ${c}` }}>
            <CountUp value={r.index} decimals={2} />
          </div>
          <div className="region-hero__meta">
            <div className="region-hero__delta-wrap">
              <Delta value={r.delta} big />
              <span className="region-hero__delta-label">24h · INDEX SCORE</span>
            </div>
            <div className="region-hero__rank">
              <span>{lang === "ru" ? "РАНГ" : "RANK"}</span>
              <strong>#{myRank}<span className="region-hero__rank-of">/{regions.length}</span></strong>
            </div>
            <div className="region-hero__rank">
              <span>{lang === "ru" ? "ГРУППА" : "GROUP"}</span>
              <strong style={{ color: c, fontSize: 16 }}>{r.group}</strong>
            </div>
          </div>
        </div>

        <div className="region-hero__stats">
          <div><span>{lang === "ru" ? "Столица" : "Capital"}</span><strong>{lang === "ru" ? r.capital_ru : r.capital}</strong></div>
          <div><span>{lang === "ru" ? "Население" : "Population"}</span><strong>{r.pop}</strong></div>
          <div><span>GDP</span><strong>{r.gdp}</strong></div>
          <div><span>{lang === "ru" ? "Резервы" : "Reserves"}</span><strong>{r.reserves}</strong></div>
          <div><span>CDS 5Y</span><strong>{r.cds ? r.cds + " bps" : "—"}</strong></div>
          <div><span>{lang === "ru" ? "Зав. нефть" : "Oil dep"}</span><strong>{r.oil_dep}%</strong></div>
        </div>
      </div>

      <div className="region-kpi-strip">
        {headline.map((s, i) => (
          <div key={i} className="kpi" data-type={s.t}>
            <div className="kpi__k">{s.k}</div>
            <div className="kpi__v">{s.v}</div>
            <div className="kpi__indicator"></div>
          </div>
        ))}
      </div>

      <AnalyticsLab r={r} regions={regions} lang={lang} />

      <div className="region-main-grid">
        <Panel
          title={lang === "ru" ? "СОБЫТИЯ" : "LIVE EVENTS"}
          sub={lang === "ru" ? "оперативная лента" : "intel feed"}
          accent="var(--cyan)"
        >
          <div className="feed feed--region">
            {r.events.map((e, i) => (
              <div key={i} className="feed__item">
                <span className="feed__t">{e.t}</span>
                <span className="feed__tag" data-tag={e.tag}>{e.tag}</span>
                <span className="feed__txt">{lang === "ru" ? e.ru : e.en}</span>
              </div>
            ))}
            <div className="feed__item feed__item--more">
              {r.tags.map((t) => <span key={t} className="region-card__tag">{t}</span>)}
            </div>
          </div>
        </Panel>

        <Panel
          title={lang === "ru" ? "ПЕРИФЕРИЯ" : "PEER RANK"}
          sub={lang === "ru" ? `группа · ${r.group}` : `group · ${r.group}`}
          accent="var(--teal)"
        >
          <div className="peers">
            {regions.filter((p) => p.group === r.group).slice().sort((a, b) => b.index - a.index).map((p, i) => {
              const pc = window.MENA_GROUP_COLOR[p.group];
              const max = Math.max(...regions.map((x) => x.index));
              const pct = (p.index / max) * 100;
              const isMe = p.id === r.id;
              return (
                <div key={p.id} className={`peer ${isMe ? "is-me" : ""}`} onClick={() => onSelect(p.id)}>
                  <span className="peer__rank">#{i + 1}</span>
                  <span className="peer__code" style={{ color: pc }}>{p.short_en}</span>
                  <div className="peer__bar">
                    <div className="peer__fill" style={{ width: `${pct}%`, background: pc, boxShadow: `0 0 8px ${pc}` }}></div>
                  </div>
                  <span className="peer__val" style={{ color: pc }}>{p.index.toFixed(1)}</span>
                  <Delta value={p.delta} />
                </div>
              );
            })}
          </div>
        </Panel>
      </div>
    </div>
  );
}

Object.assign(window, { OverviewView, RegionView, Panel, Delta });
