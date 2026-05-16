"""
MENA Investment Index — Dash Dashboard
MVP: M1 Scorecard, M2 Ranking, M4 Map, M5 Custom Weights

Запуск: python src/dashboard/app.py
Откроется: http://127.0.0.1:8050
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from src.dashboard.layouts import scorecard, ranking, map_view, weights
from src.dashboard.callbacks.main_callbacks import register_callbacks

# ── Инициализация ──────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,          # тёмная тема
        dbc.icons.FONT_AWESOME,
    ],
    suppress_callback_exceptions=True,
    title="MENA Investment Index",
)

# ── Навбар ─────────────────────────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container([
        html.Span("🌍", style={"fontSize": "1.5rem", "marginRight": "8px"}),
        dbc.NavbarBrand("MENA Investment Climate Index", className="fw-bold"),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Scorecard",     href="#", id="nav-scorecard",  active=True)),
            dbc.NavItem(dbc.NavLink("Рейтинг",       href="#", id="nav-ranking")),
            dbc.NavItem(dbc.NavLink("Карта",         href="#", id="nav-map")),
            dbc.NavItem(dbc.NavLink("Веса",          href="#", id="nav-weights")),
        ], navbar=True, className="ms-auto"),
        html.Small("v1.0 | 19 стран | 2000–2024", className="text-muted ms-3"),
    ], fluid=True),
    color="dark",
    dark=True,
    className="mb-0",
    style={"borderBottom": "2px solid #3498db"},
)

# ── Главный layout ─────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar,

    dbc.Container([
        # Tabs навигация
        dbc.Tabs([
            dbc.Tab(
                scorecard.layout(),
                label="📋 Scorecard",
                tab_id="tab-scorecard",
            ),
            dbc.Tab(
                ranking.layout(),
                label="🏆 Рейтинг",
                tab_id="tab-ranking",
            ),
            dbc.Tab(
                map_view.layout(),
                label="🗺️ Карта",
                tab_id="tab-map",
            ),
            dbc.Tab(
                weights.layout(),
                label="⚖️ Веса",
                tab_id="tab-weights",
            ),
        ],
        id="main-tabs",
        active_tab="tab-scorecard",
        className="mt-3",
        ),
    ], fluid=True, className="px-3"),

    # Footer
    html.Footer(
        dbc.Container([
            html.Hr(style={"borderColor": "#333"}),
            dbc.Row([
                dbc.Col(html.Small([
                    "Источники: ",
                    html.Span("World Bank WDI · WGI · IMF WEO · ACLED", className="text-muted"),
                ]), width=6),
                dbc.Col(html.Small([
                    "Методология: Panel FE Regression · Monte Carlo · Backtesting",
                ], className="text-muted text-end"), width=6),
            ]),
        ], fluid=True),
        className="mt-4 mb-2",
    )
], style={"backgroundColor": "#0d1117", "minHeight": "100vh"})

# ── Callbacks ──────────────────────────────────────────────────────────────────
register_callbacks(app)

# ── Точка входа ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 MENA Investment Index Dashboard")
    print("   Открой браузер: http://127.0.0.1:8050\n")
    app.run(debug=True, port=8050)
