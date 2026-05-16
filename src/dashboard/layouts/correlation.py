"""
M8: Correlation — factor correlation heatmap + box-plot distribution.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd

from src.dashboard.data_loader import load_cici_panel, FACTOR_LABELS
from src.model.build_panel import FACTOR_COLS


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# Short axis labels matching FACTOR_COLS order
SHORT_LABELS = ["Inst.", "Macro", "Open.", "Energy", "Sec.", "H.Cap.", "Fin."]

# Colors cycling through the terminal palette for the box plots
BOX_COLORS = ["#f7c548", "#00e5d4", "#8b5cff", "#ff5d8f", "#ff9a3d", "#5cffb1", "#4dd0e1"]

# Custom diverging colorscale: red(-1) → black(0) → teal(+1)
DIVERGING_SCALE = [
    [0.0,  "#ff3d6b"],
    [0.5,  "#06070d"],
    [1.0,  "#00e5d4"],
]

_DARK_LAYOUT = dict(
    paper_bgcolor="#06070d",
    plot_bgcolor="rgba(12,16,28,0.62)",
    font=dict(family="'JetBrains Mono', monospace", color="#e9e4d2"),
    margin=dict(l=8, r=8, t=8, b=8),
)


def make_correlation_heatmap() -> go.Figure:
    """7×7 Pearson correlation heatmap of FACTOR_COLS for the latest year."""
    panel = load_cici_panel()
    latest_year = panel["year"].max()
    df = panel[panel["year"] == latest_year][FACTOR_COLS].dropna()

    corr = df.corr().round(2)

    # Build annotation text matrix
    annotations = []
    for i, row_label in enumerate(FACTOR_COLS):
        for j, col_label in enumerate(FACTOR_COLS):
            val = corr.loc[row_label, col_label]
            annotations.append(
                dict(
                    x=SHORT_LABELS[j],
                    y=SHORT_LABELS[i],
                    text=f"{val:.2f}",
                    showarrow=False,
                    font=dict(
                        size=10,
                        color="#e9e4d2" if abs(val) < 0.7 else "#06070d",
                    ),
                )
            )

    fig = go.Figure(
        go.Heatmap(
            z=corr.values.tolist(),
            x=SHORT_LABELS,
            y=SHORT_LABELS,
            colorscale=DIVERGING_SCALE,
            zmin=-1,
            zmax=1,
            colorbar=dict(
                tickfont=dict(size=9, color="#e9e4d2"),
                outlinecolor="rgba(247,197,72,0.2)",
                outlinewidth=1,
                thickness=10,
                len=0.85,
            ),
            hovertemplate="%{y} × %{x}<br>r = %{z:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        **_DARK_LAYOUT,
        height=420,
        annotations=annotations,
        xaxis=dict(
            tickfont=dict(size=10, color="rgba(247,197,72,0.8)"),
            gridcolor="rgba(247,197,72,0.05)",
        ),
        yaxis=dict(
            tickfont=dict(size=10, color="rgba(247,197,72,0.8)"),
            gridcolor="rgba(247,197,72,0.05)",
            autorange="reversed",
        ),
    )
    return fig


def make_factor_boxplot() -> go.Figure:
    """Box plots showing the distribution of each factor across 19 countries."""
    panel = load_cici_panel()
    latest_year = panel["year"].max()
    df = panel[panel["year"] == latest_year][FACTOR_COLS].dropna()

    fig = go.Figure()
    for i, (col, color) in enumerate(zip(FACTOR_COLS, BOX_COLORS)):
        fig.add_trace(
            go.Box(
                y=df[col].tolist(),
                name=SHORT_LABELS[i],
                marker=dict(color=color, size=5, opacity=0.85),
                line=dict(color=color, width=1.5),
                fillcolor=_hex_to_rgba(color, 0.12),
                boxmean=True,
                hovertemplate="%{y:.1f}<extra>" + SHORT_LABELS[i] + "</extra>",
            )
        )

    fig.update_layout(
        **_DARK_LAYOUT,
        height=280,
        showlegend=False,
        xaxis=dict(
            tickfont=dict(size=10, color="rgba(247,197,72,0.8)"),
            gridcolor="rgba(247,197,72,0.05)",
        ),
        yaxis=dict(
            title=dict(text="Score (0–100)", font=dict(size=9, color="rgba(233,228,210,0.4)")),
            tickfont=dict(size=9, color="rgba(233,228,210,0.5)"),
            gridcolor="rgba(247,197,72,0.06)",
            range=[0, 100],
        ),
    )
    return fig


def _panel_header(label: str) -> html.Div:
    return html.Div(
        html.Span(label, style={
            "fontFamily": "var(--display)",
            "fontSize": "10px",
            "fontWeight": "600",
            "letterSpacing": "3px",
            "color": "var(--gold)",
            "textShadow": "0 0 8px rgba(247,197,72,0.4)",
            "textTransform": "uppercase",
        }),
        style={
            "padding": "10px 16px",
            "borderBottom": "1px solid var(--border)",
            "background": "linear-gradient(180deg, rgba(247,197,72,0.06), transparent)",
        },
    )


def layout() -> html.Div:
    return html.Div([
        # Tab heading
        html.Div([
            html.Span("◆ ", style={"color": "var(--teal)"}),
            html.Span("FACTOR CORRELATION", style={"letterSpacing": "4px"}),
        ], style={
            "fontFamily": "var(--display)",
            "fontWeight": "700",
            "fontSize": "15px",
            "color": "var(--gold)",
            "textShadow": "0 0 12px rgba(247,197,72,0.45)",
            "padding": "18px 0 10px",
            "letterSpacing": "2px",
        }),

        # Correlation matrix panel
        html.Div([
            html.Div([
                html.Div(className="t-panel-corner t-panel-corner-tl"),
                html.Div(className="t-panel-corner t-panel-corner-tr"),
                html.Div(className="t-panel-corner t-panel-corner-bl"),
                html.Div(className="t-panel-corner t-panel-corner-br"),
            ]),
            _panel_header("[ CORRELATION MATRIX ]"),
            html.Div([
                dcc.Graph(
                    figure=make_correlation_heatmap(),
                    config={"displayModeBar": False},
                    style={"width": "100%"},
                ),
                html.Div(
                    "Pearson correlation across all 19 countries, latest year",
                    style={
                        "fontFamily": "var(--mono)",
                        "fontSize": "10px",
                        "color": "var(--text-dim)",
                        "letterSpacing": "1.5px",
                        "padding": "6px 0 4px",
                        "textAlign": "center",
                    },
                ),
            ], style={"padding": "12px 16px 16px"}),
        ], className="t-panel", style={"marginBottom": "16px"}),

        # Factor distribution panel
        html.Div([
            html.Div([
                html.Div(className="t-panel-corner t-panel-corner-tl"),
                html.Div(className="t-panel-corner t-panel-corner-tr"),
                html.Div(className="t-panel-corner t-panel-corner-bl"),
                html.Div(className="t-panel-corner t-panel-corner-br"),
            ]),
            _panel_header("[ FACTOR DISTRIBUTION ]"),
            html.Div([
                dcc.Graph(
                    figure=make_factor_boxplot(),
                    config={"displayModeBar": False},
                    style={"width": "100%"},
                ),
            ], style={"padding": "12px 16px 16px"}),
        ], className="t-panel t-panel-accent-teal"),

    ], style={"paddingBottom": "32px"})
