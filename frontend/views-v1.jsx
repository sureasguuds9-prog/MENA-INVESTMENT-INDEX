// MENA-INDEX — main views (Overview + Region)

const { useState: useStateV, useEffect: useEffectV, useMemo: useMemoV } = React;

function Tag({ children, color = "var(--gold)" }) {
  return (
    <span className="tag" style={{ color, borderColor: color }}>
      {children}
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

function Delta({ value, big = false }) {
  const cls = value >= 0 ? "delta delta--up" : "delta delta--down";
  return (
    <span className={cls + (big ? " delta--big" : "")}>
      {value >= 0 ? "▲" : "▼"} {Math.abs(value).toFixed(2)}
    </span>
  );
}

function RegionCard({ r, onClick, lang }) {
  const accentMap = {
    uae: "#f7c548",
    ksa: "#00e5d4",
    qa: "#8b5cff",
    il: "#4dd0e1",
    eg: "#ff9a3d",
    ma: "#ff5d8f"
  };
  const c = accentMap[r.id];
  return (
    <div className="region-card" style={{ "--c": c }} onClick={onClick}>
      <div className="region-card__head">
        <div className="region-card__code">
          <span className="region-card__flag" style={{ background: c }}></span>
          {r.code}
        </div>
        <Tag color={c}>{r.tier}</Tag>
      </div>
      <div className="region-card__name">
        <div className="region-card__name-en">{r.name_en}</div>
        <div className="region-card__name-ru">{r.name_ru}</div>
      </div>
      <div className="region-card__index">
        <div className="region-card__value" style={{ color: c }}>
          <CountUp value={r.index} decimals={1} />
        </div>
        <div className="region-card__delta">
          <Delta value={r.delta} />
          <span className="region-card__delta-label">24h</span>
        </div>
      </div>
      <div className="region-card__spark">
        <Sparkline data={r.hist} color={c} w={300} h={50} />
      </div>
      <div className="region-card__meta">
        <div>
          <span className="region-card__k">GDP</span>
          <span className="region-card__v">{r.gdp}</span>
        </div>
        <div>
          <span className="region-card__k">CPI</span>
          <span className="region-card__v">{r.inflation}%</span>
        </div>
        <div>
          <span className="region-card__k">RISK</span>
          <span className="region-card__v" style={{ color: r.risk > 50 ? "var(--alert)" : c }}>
            {r.risk}
          </span>
        </div>
      </div>
      <div className="region-card__tags">
        {r.tags.map((t) => (
          <span key={t} className="region-card__tag">{t}</span>
        ))}
      </div>
      <div className="region-card__arrow">→</div>
    </div>
  );
}

function OverviewView({ data, onSelect, lang }) {
  const { regions, composite, corr } = data;
  const labels = regions.reduce((acc, r) => ({ ...acc, [r.id]: r.short_en }), {});
  return (
    <div className="view view--overview">
      <div className="view__top-grid">
        <Panel title="MENA COMPOSITE INDEX" sub="агрегированный индекс" accent="var(--gold)" className="panel--hero"
          right={<Tag>LIVE · MTX-7</Tag>}>
          <div className="hero">
            <div className="hero__left">
              <div className="hero__label">
                <span>COMPOSITE</span>
                <span>{lang === "ru" ? "СВОДНЫЙ" : "AGGREGATE"}</span>
              </div>
              <div className="hero__value">
                <CountUp value={composite.value} decimals={2} />
              </div>
              <div className="hero__deltas">
                <div><span className="hero__dk">24h</span> <Delta value={composite.delta} /></div>
                <div><span className="hero__dk">7d</span> <Delta value={composite.delta_w} /></div>
                <div><span className="hero__dk">30d</span> <Delta value={composite.delta_m} /></div>
              </div>
              <div className="hero__legend">
                {composite.components.map((c) => (
                  <BarRow
                    key={c.k}
                    label={c.k}
                    value={c.v}
                    max={100}
                    color={c.t === "up" ? "var(--gold)" : c.t === "down" ? "var(--alert)" : "var(--teal)"}
                  />
                ))}
              </div>
            </div>
            <div className="hero__right">
              <AreaChart data={composite.hist} color="var(--gold)" label="60-PERIOD COMPOSITE TRACE" h={260} />
            </div>
          </div>
        </Panel>

        <Panel title="GEO RISK MATRIX" sub="радар риска" accent="var(--alert)">
          <div className="risk-stack">
            <RadialGauge value={48} label="GEO·RISK" sub="MODERATE / СРЕД." color="var(--alert)" size={170} />
            <div className="risk-stack__list">
              {regions
                .slice()
                .sort((a, b) => b.risk - a.risk)
                .map((r) => (
                  <div key={r.id} className="risk-row" onClick={() => onSelect(r.id)}>
                    <span className="risk-row__code">{r.code}</span>
                    <div className="risk-row__bar">
                      <div
                        className="risk-row__fill"
                        style={{
                          width: `${r.risk}%`,
                          background: r.risk > 60 ? "var(--alert)" : r.risk > 35 ? "var(--amber)" : "var(--teal)"
                        }}
                      ></div>
                    </div>
                    <span className="risk-row__val">{r.risk}</span>
                  </div>
                ))}
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="REGION TOPOLOGY" sub="региональная топология" accent="var(--gold)"
        right={<Tag color="var(--teal)">6 NODES · SYNCED</Tag>}>
        <MenaMap regions={regions} active={null} onSelect={onSelect} lang={lang} />
      </Panel>

      <Panel title="REGION GRID" sub="6 узлов · выбери для деталей" accent="var(--teal)"
        right={<span className="tag-row">
          <Tag color="var(--gold)">GCC</Tag>
          <Tag color="var(--amber)">N.AFRICA</Tag>
          <Tag color="var(--cyan)">LEVANT</Tag>
        </span>}>
        <div className="region-grid">
          {regions.map((r) => (
            <RegionCard key={r.id} r={r} onClick={() => onSelect(r.id)} lang={lang} />
          ))}
        </div>
      </Panel>

      <div className="view__bottom-grid">
        <Panel title="CORRELATION MATRIX" sub="кросс-корреляция 90d" accent="var(--violet)">
          <Heatmap matrix={corr} labels={labels} />
          <div className="legend-strip">
            <span><span className="dot" style={{ background: "hsla(45,80%,55%,0.8)" }}></span> HIGH (&gt; 0.6)</span>
            <span><span className="dot" style={{ background: "hsla(175,80%,45%,0.8)" }}></span> MED (0.3–0.6)</span>
            <span><span className="dot" style={{ background: "hsla(290,80%,45%,0.8)" }}></span> LOW (&lt; 0.3)</span>
          </div>
        </Panel>

        <Panel title="INTEL FEED" sub="оперативная лента" accent="var(--cyan)"
          right={<Tag color="var(--cyan)">{lang === "ru" ? "ОБНОВЛ. 12с" : "12s AGO"}</Tag>}>
          <div className="feed">
            {regions.flatMap((r) =>
              r.events.slice(0, 2).map((e, i) => (
                <div key={r.id + i} className="feed__item" onClick={() => onSelect(r.id)}>
                  <span className="feed__t">{e.t}</span>
                  <span className="feed__code">{r.code}</span>
                  <span className="feed__tag" data-tag={e.tag}>{e.tag}</span>
                  <span className="feed__txt">{lang === "ru" ? e.ru : e.en}</span>
                </div>
              ))
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function RegionView({ r, lang, onSelect, regions }) {
  const accentMap = {
    uae: "#f7c548",
    ksa: "#00e5d4",
    qa: "#8b5cff",
    il: "#4dd0e1",
    eg: "#ff9a3d",
    ma: "#ff5d8f"
  };
  const c = accentMap[r.id];
  const [timeframe, setTimeframe] = useStateV("12M");
  const [metric, setMetric] = useStateV("gdp");
  const metrics = [
    { id: "gdp", label_en: "GDP Growth", label_ru: "Рост ВВП", suffix: "%" },
    { id: "cpi", label_en: "Inflation", label_ru: "Инфляция", suffix: "%" },
    { id: "fx", label_en: "FX Rate", label_ru: "Курс", suffix: "" },
    { id: "pmi", label_en: "PMI", label_ru: "PMI", suffix: "" }
  ];
  const peerRanking = regions
    .slice()
    .sort((a, b) => b.index - a.index)
    .map((p, i) => ({ ...p, rank: i + 1 }));
  const myRank = peerRanking.find((p) => p.id === r.id).rank;

  return (
    <div className="view view--region" style={{ "--c": c }}>
      <Panel title={`${r.short_en} · ${r.code} · ${r.name_en.toUpperCase()}`} sub={r.name_ru} accent={c}
        className="panel--hero" right={<Tag color={c}>TIER {r.tier} · LIVE</Tag>}>
        <div className="region-hero">
          <div className="region-hero__left">
            <div className="region-hero__big" style={{ color: c, textShadow: `0 0 20px ${c}` }}>
              <CountUp value={r.index} decimals={2} />
            </div>
            <div className="region-hero__sub">
              <span>INDEX SCORE</span>
              <span>· RANK #{myRank} / {regions.length}</span>
            </div>
            <div className="region-hero__deltas">
              <div><span>24h</span> <Delta value={r.delta} big /></div>
              <div><span>CAP</span> <strong>{r.capital}</strong></div>
              <div><span>POP</span> <strong>{r.pop}</strong></div>
              <div><span>GDP</span> <strong>{r.gdp}</strong></div>
              <div><span>CCY</span> <strong>{r.currency} · {r.fx}</strong></div>
              <div><span>RES</span> <strong>{r.reserves}</strong></div>
            </div>
            <div className="region-hero__tags">
              {r.tags.map((t) => <span key={t} className="region-card__tag">{t}</span>)}
            </div>
          </div>
          <div className="region-hero__right">
            <AreaChart data={r.hist} color={c} label={`24M INDEX TRACE · ${r.short_en}`} h={260} />
          </div>
        </div>
      </Panel>

      <div className="region-kpi-grid">
        {r.sub.map((s) => (
          <div key={s.k} className="kpi" data-type={s.t}>
            <div className="kpi__k">{s.k}</div>
            <div className="kpi__v">{s.v}</div>
            <div className="kpi__indicator" data-type={s.t}></div>
          </div>
        ))}
      </div>

      <div className="region-mid-grid">
        <Panel title="INDICATOR TIME-SERIES" sub="временной ряд показателей" accent={c}
          right={
            <div className="seg">
              {metrics.map((m) => (
                <button
                  key={m.id}
                  className={`seg__btn ${metric === m.id ? "is-active" : ""}`}
                  onClick={() => setMetric(m.id)}
                  style={metric === m.id ? { color: c, borderColor: c } : {}}
                >
                  {lang === "ru" ? m.label_ru : m.label_en}
                </button>
              ))}
            </div>
          }
        >
          <AreaChart data={r.ind[metric]} color={c} label={metric.toUpperCase() + " · 24 PERIODS"} h={240} />
          <div className="seg seg--inline">
            {["1M", "3M", "6M", "12M", "24M", "ALL"].map((tf) => (
              <button
                key={tf}
                className={`seg__btn ${timeframe === tf ? "is-active" : ""}`}
                onClick={() => setTimeframe(tf)}
                style={timeframe === tf ? { color: c, borderColor: c } : {}}
              >
                {tf}
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="RISK PROFILE" sub="профиль риска" accent="var(--alert)">
          <div className="region-risk">
            <RadialGauge
              value={r.risk}
              label={lang === "ru" ? "РИСК" : "RISK"}
              sub={r.risk > 60 ? "ELEVATED" : r.risk > 35 ? "MODERATE" : "LOW"}
              color={r.risk > 60 ? "var(--alert)" : r.risk > 35 ? "var(--amber)" : "var(--teal)"}
              size={170}
            />
            <div className="region-risk__list">
              <BarRow label="CDS 5Y" value={r.cds} max={700} color="var(--alert)" suffix=" bp" />
              <BarRow label={lang === "ru" ? "Зав. нефть" : "Oil Dep"} value={r.oil_dep} max={100} color="var(--amber)" suffix="%" />
              <BarRow label={lang === "ru" ? "Инфляция" : "Inflation"} value={r.inflation} max={20} color="var(--rose)" suffix="%" />
              <BarRow label="PMI" value={r.pmi} max={70} color={r.pmi > 50 ? "var(--teal)" : "var(--alert)"} />
              <BarRow label={lang === "ru" ? "Рост ВВП" : "GDP Growth"} value={r.gdp_growth} max={8} color="var(--gold)" suffix="%" />
            </div>
          </div>
        </Panel>
      </div>

      <div className="region-bottom-grid">
        <Panel title="PEER COMPARISON" sub="сравнение с регионом" accent="var(--teal)">
          <div className="peers">
            {peerRanking.map((p) => {
              const pc = accentMap[p.id];
              const max = Math.max(...regions.map((x) => x.index));
              const pct = (p.index / max) * 100;
              const isMe = p.id === r.id;
              return (
                <div key={p.id} className={`peer ${isMe ? "is-me" : ""}`} onClick={() => onSelect(p.id)}>
                  <span className="peer__rank">#{p.rank}</span>
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

        <Panel title="LIVE EVENTS" sub="лента событий" accent={c}>
          <div className="feed feed--region">
            {r.events.map((e, i) => (
              <div key={i} className="feed__item">
                <span className="feed__t">{e.t}</span>
                <span className="feed__tag" data-tag={e.tag}>{e.tag}</span>
                <span className="feed__txt">{lang === "ru" ? e.ru : e.en}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

Object.assign(window, { OverviewView, RegionView, Panel, Tag, Delta });
