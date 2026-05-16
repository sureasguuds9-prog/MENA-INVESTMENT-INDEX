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

    colors = ["#5cffb1" if s >= 70 else ("#f7c548" if s >= 50 else ("#ff9a3d" if s >= 30 else "#ff3d6b"))
              for s in result["cici_score"]]
    flags = [FLAG_EMOJI.get(iso, "") for iso in result["iso3"]]
    labels = [f"{f} {c}" for f, c in zip(flags, result["country"])]

    fig = go.Figure(go.Bar(
        x=result["cici_score"],
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}" for s in result["cici_score"]],
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="%{y}: <b>%{x:.1f}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#06070d", plot_bgcolor="rgba(12,16,28,0.62)",
        font=dict(color="#e9e4d2"),
        xaxis=dict(range=[0, 105], gridcolor="rgba(247,197,72,0.08)",
                   color="rgba(233,228,210,0.32)", title="CICI"),
        yaxis=dict(color="rgba(233,228,210,0.55)", tickfont=dict(size=11)),
        margin=dict(l=10, r=40, t=10, b=20),
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
            html.Div([
                html.Div([
                    html.Span(label, style={
                        "fontFamily": "var(--mono)", "fontSize": "10px",
                        "color": "var(--text-mute)", "letterSpacing": "1px",
                    }),
                    html.Span(f"{w*100:.0f}%", id=f"weight-display-{f}", style={
                        "fontFamily": "var(--mono)", "fontWeight": "700",
                        "fontSize": "12px", "color": "var(--gold)",
                    }),
                ], style={"display": "flex", "justifyContent": "space-between",
                          "marginBottom": "4px"}),
                dcc.Slider(
                    id=f"weight-slider-{f}",
                    min=0, max=50, step=1,
                    value=round(w * 100),
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": False},
                    className="mb-0",
                ),
            ], style={"marginBottom": "16px"})
        )

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("◆ FACTOR WEIGHTS", style={
                    "fontFamily": "var(--display)", "fontWeight": "700",
                    "fontSize": "13px", "letterSpacing": "3px",
                    "color": "var(--gold)", "textTransform": "uppercase",
                    "marginBottom": "4px",
                }),
                html.Div("Adjust factor weights — ranking recalculates instantly", style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--text-dim)", "letterSpacing": "2px",
                }),
            ], width=7),
            dbc.Col([
                html.Div("PRESETS:", style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--text-dim)", "letterSpacing": "2px",
                    "marginBottom": "6px",
                }),
                html.Div([
                    html.Button(
                        PRESET_LABELS[p],
                        id=f"preset-{p}",
                        style={
                            "fontFamily": "var(--mono)", "fontSize": "10px",
                            "background": "transparent", "border": "1px solid rgba(247,197,72,0.3)",
                            "color": "var(--gold)", "padding": "4px 10px",
                            "cursor": "pointer", "marginRight": "4px", "marginBottom": "4px",
                            "letterSpacing": "1px",
                        }
                    )
                    for p in PRESETS
                ], style={"display": "flex", "flexWrap": "wrap"}),
            ], width=5),
        ], className="mb-4 mt-2"),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div(className="t-panel-corner t-panel-corner-tl"),
                    html.Div(className="t-panel-corner t-panel-corner-tr"),
                    html.Div(className="t-panel-corner t-panel-corner-bl"),
                    html.Div(className="t-panel-corner t-panel-corner-br"),
                    html.Div([
                        html.Span("[ WEIGHT CONFIG ]", className="t-panel-title"),
                    ], className="t-panel-head"),
                    html.Div([
                        html.Div(id="weights-sum-warning", style={"marginBottom": "8px"}),
                        *sliders,
                        html.Div(style={"borderTop": "1px solid rgba(247,197,72,0.1)", "margin": "8px 0"}),
                        html.Div(id="weights-sum-display", style={
                            "fontFamily": "var(--mono)", "fontSize": "10px",
                            "color": "var(--text-dim)",
                        }),
                    ], className="t-panel-body"),
                ], className="t-panel"),
            ], width=4),

            dbc.Col([
                html.Div([
                    html.Div(className="t-panel-corner t-panel-corner-tl"),
                    html.Div(className="t-panel-corner t-panel-corner-tr"),
                    html.Div(className="t-panel-corner t-panel-corner-bl"),
                    html.Div(className="t-panel-corner t-panel-corner-br"),
                    html.Div([
                        html.Span("[ CUSTOM RANKING ]", className="t-panel-title"),
                    ], className="t-panel-head"),
                    html.Div([
                        dcc.Graph(
                            id="custom-weights-ranking-chart",
                            figure=make_custom_ranking_chart(current_weights),
                            config={"displayModeBar": False},
                        ),
                    ], className="t-panel-body"),
                ], className="t-panel t-panel-accent-teal"),
            ], width=8),
        ]),
    ], className="p-3")
