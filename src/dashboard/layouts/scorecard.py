"""
M1: Scorecard — страновая карточка с радарной диаграммой и динамикой.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.data_loader import (
    load_cici_panel, load_ranking, load_monte_carlo,
    FACTOR_LABELS, FLAG_EMOJI
)
from src.model.build_panel import FACTOR_COLS


def score_to_color(score: float) -> str:
    if score >= 70:   return "#2ecc71"
    elif score >= 50: return "#f39c12"
    elif score >= 30: return "#e67e22"
    else:             return "#e74c3c"


def make_radar_chart(row: pd.Series) -> go.Figure:
    labels = [FACTOR_LABELS.get(f, f) for f in FACTOR_COLS]
    values = [float(row.get(f, 50)) for f in FACTOR_COLS]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(52, 152, 219, 0.25)",
        line=dict(color="#3498db", width=2),
        name="CICI",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#aaa")),
            angularaxis=dict(tickfont=dict(size=11, color="#ddd")),
            bgcolor="#16213e",
        ),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        margin=dict(l=30, r=30, t=30, b=30),
        showlegend=False,
        height=300,
    )
    return fig


def make_timeseries_chart(panel: pd.DataFrame, iso3: str) -> go.Figure:
    df = panel[panel["iso3"] == iso3].sort_values("year")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["cici_score"],
        mode="lines+markers",
        line=dict(color="#3498db", width=2.5),
        marker=dict(size=5),
        name="CICI",
        hovertemplate="%{x}: <b>%{y:.1f}</b><extra></extra>",
    ))
    # Аннотации ключевых событий
    events = {2011: "Arab Spring", 2015: "Oil shock", 2020: "COVID-19"}
    for yr, label in events.items():
        if df["year"].min() <= yr <= df["year"].max():
            fig.add_vline(x=yr, line_dash="dot", line_color="#555", line_width=1)
            fig.add_annotation(x=yr, y=df["cici_score"].max(), text=label,
                               showarrow=False, font=dict(size=9, color="#888"),
                               textangle=-90, xshift=8)
    fig.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(showgrid=False, color="#aaa"),
        yaxis=dict(range=[0, 100], gridcolor="#2a2a4a", color="#aaa", title="CICI"),
        margin=dict(l=40, r=20, t=20, b=30),
        height=200,
        showlegend=False,
    )
    return fig


def make_factor_bars(row: pd.Series) -> go.Figure:
    labels = [FACTOR_LABELS.get(f, f) for f in FACTOR_COLS]
    values = [float(row.get(f, 0)) for f in FACTOR_COLS]
    colors = [score_to_color(v) for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}" for v in values],
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="%{y}: <b>%{x:.1f}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(range=[0, 100], gridcolor="#2a2a4a", color="#aaa"),
        yaxis=dict(color="#ddd"),
        margin=dict(l=10, r=20, t=10, b=20),
        height=230,
        showlegend=False,
    )
    return fig


def layout() -> html.Div:
    panel = load_cici_panel()
    countries = panel[["iso3", "country"]].drop_duplicates().sort_values("country")
    latest_year = panel["year"].max()

    options = [
        {"label": f"{FLAG_EMOJI.get(r['iso3'], '')} {r['country']}", "value": r["iso3"]}
        for _, r in countries.iterrows()
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Страновая карточка", className="fw-bold mb-1"),
                html.P("Детальный профиль инвестиционного климата", className="text-muted small mb-3"),
            ], width=8),
            dbc.Col([
                dcc.Dropdown(
                    id="scorecard-country-selector",
                    options=options,
                    value="ARE",
                    clearable=False,
                    className="mb-2",
                )
            ], width=4),
        ]),

        html.Div(id="scorecard-content"),
    ], className="p-3")


def build_scorecard_content(iso3: str) -> list:
    panel = load_cici_panel()
    mc = load_monte_carlo()
    latest_year = panel["year"].max()

    row = panel[(panel["iso3"] == iso3) & (panel["year"] == latest_year)]
    if row.empty:
        return [html.P("Нет данных", className="text-muted")]
    row = row.iloc[0]

    flag = FLAG_EMOJI.get(iso3, "")
    score = row["cici_score"]
    rank = int(row["cici_rank"])
    color = score_to_color(score)

    # CI из Monte Carlo
    ci_str = ""
    if not mc.empty:
        mc_row = mc[mc["iso3"] == iso3]
        if not mc_row.empty:
            lo = mc_row.iloc[0]["ci_lower_95"]
            hi = mc_row.iloc[0]["ci_upper_95"]
            ci_str = f"95% CI: [{lo:.1f} – {hi:.1f}]"

    return [
        # Хэдлайн
        dbc.Row([
            dbc.Col([
                html.H2(f"{flag} {row['country']}", className="fw-bold mb-0"),
                html.P(f"Рейтинг {latest_year}", className="text-muted small"),
            ], width=6),
            dbc.Col([
                html.Div([
                    html.Span(f"{score:.1f}", style={"fontSize": "3rem", "fontWeight": "bold", "color": color}),
                    html.Span(" / 100", style={"color": "#888", "fontSize": "1.2rem"}),
                    html.Div(f"#{rank} из 19  {ci_str}", className="text-muted small mt-1"),
                ], className="text-end"),
            ], width=6),
        ], className="mb-3 align-items-center"),

        # Радар + барс
        dbc.Row([
            dbc.Col([
                html.P("Профиль факторов", className="text-muted small fw-bold mb-1"),
                dcc.Graph(figure=make_radar_chart(row), config={"displayModeBar": False}),
            ], width=6),
            dbc.Col([
                html.P("Факторные индексы (0–100)", className="text-muted small fw-bold mb-1"),
                dcc.Graph(figure=make_factor_bars(row), config={"displayModeBar": False}),
            ], width=6),
        ]),

        # Динамика
        dbc.Row([
            dbc.Col([
                html.P("Динамика CICI 2000–2024", className="text-muted small fw-bold mb-1"),
                dcc.Graph(figure=make_timeseries_chart(panel, iso3), config={"displayModeBar": False}),
            ], width=12),
        ]),
    ]
