"""
MENA Investment Index — Terminal Dashboard
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output
from datetime import datetime, timezone

from src.dashboard.layouts import scorecard, ranking, map_view, weights, markets, news
from src.dashboard.callbacks.main_callbacks import register_callbacks

TERMINAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: #06070d; --bg-deep: #03040a;
  --bg-panel: rgba(12,16,28,0.72);
  --bg-panel-solid: #0a0e1c;
  --border: rgba(247,197,72,0.18);
  --border-strong: rgba(247,197,72,0.5);
  --text: #e9e4d2;
  --text-mute: rgba(233,228,210,0.55);
  --text-dim: rgba(233,228,210,0.32);
  --gold: #f7c548; --gold-soft: #ffd76b;
  --teal: #00e5d4; --cyan: #4dd0e1;
  --violet: #8b5cff; --rose: #ff5d8f;
  --amber: #ff9a3d; --alert: #ff3d6b; --green: #5cffb1;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
  --display: 'Chakra Petch', 'Inter', system-ui, sans-serif;
  --body: 'Inter', system-ui, sans-serif;
}

* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: var(--bg); color: var(--text);
  font-family: var(--body);
  overflow-x: hidden; min-height: 100vh;
}
body {
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(247,197,72,0.07), transparent 60%),
    radial-gradient(1000px 500px at -10% 110%, rgba(139,92,255,0.06), transparent 60%),
    radial-gradient(800px 400px at 50% 50%, rgba(0,229,212,0.03), transparent 70%),
    var(--bg);
}
body::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(247,197,72,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(247,197,72,0.04) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(ellipse at center, rgba(0,0,0,0.9), transparent 80%);
}
.scanlines {
  position: fixed; inset: 0; pointer-events: none; z-index: 9000;
  background: repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0, rgba(0,0,0,0) 2px, rgba(0,0,0,0.12) 3px, rgba(0,0,0,0) 4px);
  mix-blend-mode: multiply; opacity: 0.4;
}

/* HEADER */
.term-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 28px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(8,10,18,0.8), rgba(8,10,18,0.4));
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  position: relative; z-index: 100;
}
.term-header::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold) 30%, var(--rose) 70%, transparent);
  opacity: 0.4;
}
.term-brand { display: flex; align-items: center; gap: 12px; }
.term-brand-title {
  font-family: var(--display); font-weight: 700;
  font-size: 20px; letter-spacing: 4px; color: var(--gold);
  text-shadow: 0 0 12px rgba(247,197,72,0.5); line-height: 1;
}
.term-brand-title span { color: var(--rose); }
.term-brand-sub {
  font-family: var(--mono); font-size: 9px;
  color: var(--text-dim); letter-spacing: 2.5px;
  text-transform: uppercase; margin-top: 3px;
}
.term-status {
  display: flex; align-items: center; gap: 7px;
  font-family: var(--mono); font-size: 10px;
  color: var(--teal); letter-spacing: 2px;
}
.dot-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--alert); box-shadow: 0 0 8px var(--alert);
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.3)} }
.term-clock {
  font-family: var(--mono); font-size: 11px;
  color: var(--gold); letter-spacing: 1.5px;
}
.term-right { display: flex; align-items: center; gap: 20px; }

/* TABS */
.term-tabs .nav-tabs { border-bottom: 1px solid var(--border); background: rgba(6,8,14,0.85); gap: 4px; padding: 8px 16px 0; }
.term-tabs .nav-link {
  font-family: var(--display) !important; font-weight: 600 !important;
  font-size: 11px !important; letter-spacing: 2px !important;
  text-transform: uppercase !important;
  color: var(--text-mute) !important;
  background: rgba(8,10,18,0.6) !important;
  border: 1px solid var(--border) !important;
  border-bottom: none !important;
  padding: 8px 16px !important;
  transition: all 180ms !important;
  position: relative; overflow: hidden;
}
.term-tabs .nav-link::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--gold); opacity: 0.3; transition: opacity 180ms;
}
.term-tabs .nav-link:hover { color: var(--text) !important; border-color: var(--gold) !important; }
.term-tabs .nav-link:hover::before { opacity: 0.8; }
.term-tabs .nav-link.active {
  color: var(--gold) !important;
  background: linear-gradient(180deg, rgba(247,197,72,0.12), rgba(8,10,18,0.4)) !important;
  border-color: var(--gold) !important;
  box-shadow: 0 0 16px -4px var(--gold), 0 0 0 1px var(--gold) !important;
}
.term-tabs .nav-link.active::before { opacity: 1; box-shadow: 0 0 8px var(--gold); height: 3px; }
.term-tabs .tab-content { padding-top: 4px; }

/* PANELS */
.t-panel {
  position: relative;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  backdrop-filter: blur(8px);
  box-shadow: 0 20px 60px -20px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
  margin-bottom: 16px;
}
.t-panel::before {
  content: ""; position: absolute; top: -1px; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0.55;
}
.t-panel-accent-teal::before { background: linear-gradient(90deg, transparent, var(--teal), transparent); }
.t-panel-accent-violet::before { background: linear-gradient(90deg, transparent, var(--violet), transparent); }
.t-panel-accent-amber::before { background: linear-gradient(90deg, transparent, var(--amber), transparent); }
.t-panel-corner {
  position: absolute; width: 10px; height: 10px; border-color: var(--gold); opacity: 0.7;
}
.t-panel-corner-tl { top:-1px;left:-1px; border-top:1.5px solid;border-left:1.5px solid; }
.t-panel-corner-tr { top:-1px;right:-1px; border-top:1.5px solid;border-right:1.5px solid; }
.t-panel-corner-bl { bottom:-1px;left:-1px; border-bottom:1.5px solid;border-left:1.5px solid; }
.t-panel-corner-br { bottom:-1px;right:-1px; border-bottom:1.5px solid;border-right:1.5px solid; }
.t-panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(247,197,72,0.06), transparent);
}
.t-panel-title {
  font-family: var(--display); font-size: 11px; font-weight: 600;
  letter-spacing: 3px; color: var(--gold);
  text-shadow: 0 0 8px rgba(247,197,72,0.4);
  text-transform: uppercase;
}
.t-panel-title span { color: var(--text-dim); }
.t-panel-body { padding: 16px; }

/* KPI CARDS */
.t-kpi {
  position: relative;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  padding: 12px 14px 10px;
  overflow: hidden;
}
.t-kpi::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--gold); opacity: 0.5; box-shadow: 0 0 8px var(--gold);
}
.t-kpi.green::before { background: var(--green); box-shadow: 0 0 8px var(--green); }
.t-kpi.alert::before { background: var(--alert); box-shadow: 0 0 8px var(--alert); animation: blink 1.6s infinite; }
.t-kpi.teal::before  { background: var(--teal);  box-shadow: 0 0 8px var(--teal); }
.t-kpi.amber::before { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
.t-kpi.violet::before{ background: var(--violet);box-shadow: 0 0 8px var(--violet); }
.t-kpi-k { font-family: var(--mono); font-size: 9px; color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase; }
.t-kpi-v { font-family: var(--display); font-weight: 700; font-size: 28px; color: var(--gold); margin-top: 4px; line-height: 1; }
.t-kpi-v.green { color: var(--green); text-shadow: 0 0 8px rgba(92,255,177,0.4); }
.t-kpi-v.alert { color: var(--alert); }
.t-kpi-v.teal  { color: var(--teal); }
.t-kpi-v.amber { color: var(--amber); }
.t-kpi-v.violet{ color: var(--violet); }

/* MARKET CELLS */
.t-market-cell {
  position: relative;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  padding: 10px 14px 12px;
  overflow: hidden;
  transition: border-color 200ms;
}
.t-market-cell:hover { border-color: var(--gold); }
.t-market-cell-bar {
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  opacity: 0.6; box-shadow: 0 0 8px currentColor;
}
.t-market-cell-key { font-family: var(--mono); font-size: 10px; letter-spacing: 2px; font-weight: 700; }
.t-market-cell-price { font-family: var(--display); font-weight: 700; font-size: 22px; color: var(--text); margin-top: 4px; }
.t-market-cell-delta { font-family: var(--mono); font-size: 10px; }
.t-market-cell-delta.up   { color: var(--green); }
.t-market-cell-delta.down { color: var(--alert); }

/* RANK TILES */
.t-rank-tile {
  display: grid;
  grid-template-columns: 28px 36px 1fr auto;
  gap: 10px; align-items: center;
  padding: 10px 12px;
  background: rgba(8,10,18,0.55);
  border: 1px solid var(--border);
  position: relative;
  transition: all 160ms;
  margin-bottom: 4px;
  cursor: default;
}
.t-rank-tile::before {
  content: ""; position: absolute; top: 0; left: 0; width: 2px; height: 100%;
  background: var(--gold); opacity: 0.4;
}
.t-rank-tile:hover { transform: translateX(3px); border-color: var(--gold); }
.t-rank-tile:hover::before { opacity: 1; box-shadow: 0 0 6px var(--gold); }
.t-rank-tile.top { --c: var(--green); }
.t-rank-tile.top::before { background: var(--green); }
.t-rank-tile.bottom::before { background: var(--alert); }
.t-rank-num { font-family: var(--mono); font-size: 12px; color: var(--text-dim); }
.t-rank-code { font-family: var(--mono); font-weight: 700; font-size: 12px; letter-spacing: 1.5px; color: var(--gold); }
.t-rank-name { font-family: var(--body); font-size: 12px; color: var(--text-mute); }
.t-rank-val { font-family: var(--display); font-weight: 700; font-size: 18px; color: var(--gold); text-shadow: 0 0 6px rgba(247,197,72,0.4); }

/* FEED (news) */
.t-feed-item {
  display: grid; grid-template-columns: 52px 70px 1fr;
  gap: 10px; align-items: start;
  padding: 10px 4px;
  border-bottom: 1px dashed var(--border);
  font-size: 12px; position: relative;
}
.t-feed-item.moving { border-left: 3px solid var(--alert); padding-left: 8px; }
.t-feed-item.moving.success { border-left-color: var(--green); }
.t-feed-item.moving.warning { border-left-color: var(--amber); }
.t-feed-item.moving.info    { border-left-color: var(--teal); }
.t-feed-time { font-family: var(--mono); font-size: 10px; color: var(--text-dim); }
.t-feed-tag {
  font-family: var(--mono); font-size: 9px; padding: 2px 6px;
  letter-spacing: 1.5px; border: 1px solid var(--border); color: var(--gold);
  white-space: nowrap; align-self: start;
}
.t-feed-tag.oil     { color: var(--amber); border-color: var(--amber); }
.t-feed-tag.conflict{ color: var(--alert); border-color: var(--alert); }
.t-feed-tag.economy { color: var(--teal);  border-color: var(--teal); }
.t-feed-tag.politics{ color: var(--violet);border-color: var(--violet); }
.t-feed-tag.nuclear { color: var(--rose);  border-color: var(--rose); animation: blink 1.6s infinite; }
.t-feed-txt { color: var(--text); line-height: 1.4; }
.t-feed-txt a { color: inherit; text-decoration: none; }
.t-feed-txt a:hover { color: var(--gold); }

/* BAR */
.t-bar-wrap { height: 5px; background: rgba(247,197,72,0.07); border: 1px solid var(--border); overflow: hidden; }
.t-bar-fill  { height: 100%; background: var(--gold); transition: width 0.8s cubic-bezier(.2,.7,.2,1); }
.t-bar-fill.green  { background: var(--green); }
.t-bar-fill.amber  { background: var(--amber); }
.t-bar-fill.alert  { background: var(--alert); }

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }
::selection { background: rgba(247,197,72,0.35); color: #0a0e1c; }

/* Dash overrides */
.container-fluid { position: relative; z-index: 1; }
.nav-tabs { flex-wrap: nowrap; overflow-x: auto; }
Select__control, .Select-control { background: var(--bg-panel-solid) !important; border-color: var(--border) !important; color: var(--text) !important; }
.dropdown .Select-menu-outer { background: var(--bg-panel-solid) !important; border-color: var(--border) !important; }
.VirtualizedSelectOption { color: var(--text) !important; }
"""

INDEX_STRING = """<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<style>""" + TERMINAL_CSS + """</style>
</head>
<body>
<div class="scanlines"></div>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>"""

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="MENA · INDEX · Terminal",
    index_string=INDEX_STRING,
)

# ── Header ──────────────────────────────────────────────────────────────────
header = html.Div([
    # Brand
    html.Div([
        html.Div("◆", style={
            "fontSize": "28px", "color": "#f7c548",
            "textShadow": "0 0 8px rgba(247,197,72,0.6)",
            "flexShrink": "0", "lineHeight": "1",
        }),
        html.Div([
            html.Div([
                html.Span("MENA", style={"color": "var(--gold)", "letterSpacing": "4px"}),
                html.Span("·", style={"color": "var(--rose)", "margin": "0 4px"}),
                html.Span("INDEX", style={"color": "var(--gold)", "letterSpacing": "4px"}),
            ], className="term-brand-title"),
            html.Div("macro intelligence terminal", className="term-brand-sub"),
        ]),
    ], className="term-brand"),

    # Right side
    html.Div([
        html.Div([
            html.Span(className="dot-pulse"),
            html.Span("STREAM · 19/19 NODES"),
        ], className="term-status"),
        html.Div(id="term-clock", className="term-clock", children="UTC 00:00:00"),
    ], className="term-right"),
], className="term-header")

# ── Tabs ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    header,
    dbc.Container([
        dbc.Tabs([
            dbc.Tab(scorecard.layout(), label="◆ SCORECARD", tab_id="tab-scorecard"),
            dbc.Tab(ranking.layout(),   label="▲ RANKING",   tab_id="tab-ranking"),
            dbc.Tab(map_view.layout(),  label="◉ MAP",       tab_id="tab-map"),
            dbc.Tab(weights.layout(),   label="⚖ WEIGHTS",   tab_id="tab-weights"),
            dbc.Tab(markets.layout(),   label="∿ MARKETS",   tab_id="tab-markets"),
            dbc.Tab(news.layout(),      label="◈ NEWS",      tab_id="tab-news"),
        ], id="main-tabs", active_tab="tab-scorecard", className="term-tabs mt-2"),
    ], fluid=True, className="px-3 pb-4"),

    dcc.Interval(id="clock-interval", interval=1000, n_intervals=0),
], style={"minHeight": "100vh"})

register_callbacks(app)

@app.callback(Output("term-clock", "children"), Input("clock-interval", "n_intervals"))
def update_clock(_):
    now = datetime.now(timezone.utc)
    return f"UTC {now.strftime('%H:%M:%S')}"

# ── Flask routes for React SPA ────────────────────────────────────────────
from flask import send_from_directory

FRONTEND_DIR = str(Path(__file__).parent.parent.parent / "frontend")

@app.server.route("/terminal")
def serve_terminal():
    return send_from_directory(FRONTEND_DIR, "MENA-INDEX.html")

@app.server.route("/terminal/<path:filename>")
def serve_terminal_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == "__main__":
    try:
        from src.dashboard.generate_frontend_data import run as gen_data
        gen_data()
    except Exception as e:
        print(f"  ⚠️  frontend/data.js: {e}")
    print("\n🚀 MENA · INDEX · Terminal")
    print("   Dashboard: http://127.0.0.1:8050")
    print("   Terminal:  http://127.0.0.1:8050/terminal\n")
    app.run(debug=True, port=8050)
