"""
M5: Custom Weights — слайдеры для настройки весов факторов в реальном времени.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
from src.dashboard.data_loader import load_weights, load_ranking, FACTOR_LABELS, FLAG_EMOJI
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS


PRESETS: dict[str, dict[str, float]] = {
    "balanced": {
        "F1_institutional": 0.25, "F2_macro": 0.20, "F3_openness": 0.18,
        "F4_energy": 0.15, "F5_security": 0.12, "F6_human_capital": 0.05, "F7_financial": 0.05,
    },
    "energy": {
        "F1_institutional": 0.10, "F2_macro": 0.10, "F3_openness": 0.10,
        "F4_energy": 0.50, "F5_security": 0.10, "F6_human_capital": 0.05, "F7_financial": 0.05,
    },
    "tech": {
        "F1_institutional": 0.30, "F2_macro": 0.20, "F3_openness": 0.20,
        "F4_energy": 0.05, "F5_security": 0.10, "F6_human_capital": 0.10, "F7_financial": 0.05,
    },
    "risk": {
        "F1_institutional": 0.20, "F2_macro": 0.15, "F3_openness": 0.10,
        "F4_energy": 0.10, "F5_security": 0.35, "F6_human_capital": 0.05, "F7_financial": 0.05,
    },
    "regression": None,  # заполняется динамически
}

PRESET_LABELS = {
    "balanced":  "⚖️ Balanced",
    "energy":    "⛽ Energy Investor",
    "tech":      "💻 Tech Investor",
    "risk":      "🛡️ Risk-Averse",
    "regression": "📊 Regression (авто)",
}


def make_custom_ranking_chart(weights: dict[str, float]) -> go.Figure:
    from src.model.cici import compute_cici
    panel_path = __import__("src.config", fromlist=["DATA_FINAL"]).DATA_FINAL / "panel_factors.csv"
    import pandas as pd
    panel = pd.read_csv(panel_path)
    latest = panel[panel["year"] == panel["year"].max()].copy()
    result = compute_cici(latest, weights).sort_values("cici_score", ascending=True)

    colors = ["#2ecc71" if s >= 60 else ("#f39c12" if s >= 40 else "#e74c3c")
              for s in result["cici_score"]]
    flags = [FLAG_EMOJI.get(iso, "") for iso in result["iso3"]]
    labels = [f"{f} {c}" for f, c in zip(flags, result["country"])]

    fig = go.Figure(go.Bar(
        x=result["cici_score"],
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}" for s in result["cici_score"]],
        textposition="outside",
        textfont=dict(size=11, color="#ddd"),
        hovertemplate="%{y}: <b>%{x:.1f}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(range=[0, 105], gridcolor="#2a2a4a", color="#aaa", title="CICI"),
        yaxis=dict(color="#ddd", tickfont=dict(size=11)),
        margin=dict(l=10, r=60, t=10, b=20),
        height=560,
        showlegend=False,
    )
    return fig


def layout() -> html.Div:
    current_weights = load_weights()

    sliders = []
    for f in FACTOR_COLS:
        w = current_weights.get(f, BASELINE_WEIGHTS.get(f, 0.1))
        label = FACTOR_LABELS.get(f, f)
        sliders.append(
            dbc.Row([
                dbc.Col(html.Label(label, className="small text-muted"), width=4),
                dbc.Col(
                    dcc.Slider(
                        id=f"weight-slider-{f}",
                        min=0, max=50, step=1,
                        value=round(w * 100),
                        marks={0: "0%", 25: "25%", 50: "50%"},
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="mb-0",
                    ), width=6,
                ),
                dbc.Col(
                    html.Span(f"{w*100:.0f}%", id=f"weight-display-{f}",
                              className="small fw-bold text-warning"),
                    width=2,
                ),
            ], className="mb-2 align-items-center")
        )

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Настройка весов", className="fw-bold mb-1"),
                html.P("Измени веса факторов — рейтинг пересчитается мгновенно",
                       className="text-muted small mb-3"),
            ], width=7),
            dbc.Col([
                html.Label("Пресеты:", className="small text-muted"),
                dbc.ButtonGroup([
                    dbc.Button(PRESET_LABELS[p], id=f"preset-{p}", size="sm",
                               color="secondary", outline=True, className="me-1")
                    for p in PRESETS
                ], className="flex-wrap"),
            ], width=5),
        ]),

        dbc.Row([
            # Слайдеры
            dbc.Col([
                html.Div(id="weights-sum-warning"),
                *sliders,
                html.Hr(style={"borderColor": "#333"}),
                html.Div(id="weights-sum-display", className="small text-muted"),
            ], width=4),

            # Рейтинг по кастомным весам
            dbc.Col([
                html.P("Рейтинг с текущими весами:", className="text-muted small fw-bold mb-1"),
                dcc.Graph(
                    id="custom-weights-ranking-chart",
                    figure=make_custom_ranking_chart(current_weights),
                    config={"displayModeBar": False},
                ),
            ], width=8),
        ]),
    ], className="p-3")
