"""
M1: Scorecard — страновая карточка с радарной диаграммой и динамикой.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.dashboard.data_loader import (
    load_cici_panel, load_ranking, load_monte_carlo,
    FACTOR_LABELS, FLAG_EMOJI
)
from src.model.build_panel import FACTOR_COLS


def score_to_color(score: float) -> str:
    if score >= 70:   return "#5cffb1"
    elif score >= 50: return "#ff9a3d"
    elif score >= 30: return "#ff9a3d"
    else:             return "#ff3d6b"


def make_radar_chart(row: pd.Series, row2: pd.Series | None = None) -> go.Figure:
    labels = [FACTOR_LABELS.get(f, f) for f in FACTOR_COLS]
    values = [float(row.get(f, 50)) for f in FACTOR_COLS]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(0,229,212,0.15)",
        line=dict(color="#00e5d4", width=2),
        name=str(row.get("iso3", "Primary")),
    ))

    if row2 is not None:
        values2 = [float(row2.get(f, 50)) for f in FACTOR_COLS]
        values2_closed = values2 + [values2[0]]
        fig.add_trace(go.Scatterpolar(
            r=values2_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(247,197,72,0.15)",
            line=dict(color="#f7c548", width=2),
            name=str(row2.get("iso3", "Compare")),
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="rgba(233,228,210,0.32)")),
            angularaxis=dict(tickfont=dict(size=11, color="rgba(233,228,210,0.55)")),
            bgcolor="rgba(12,16,28,0.62)",
        ),
        paper_bgcolor="#06070d",
        font=dict(color="#e9e4d2"),
        margin=dict(l=30, r=30, t=30, b=30),
        showlegend=row2 is not None,
        legend=dict(font=dict(size=10, color="#e9e4d2"), bgcolor="rgba(0,0,0,0)"),
        height=300,
    )
    return fig


def make_timeseries_chart(panel: pd.DataFrame, iso3: str) -> go.Figure:
    df = panel[panel["iso3"] == iso3].sort_values("year")
    fig = go.Figure()

    # ── Historical CICI line ──────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["cici_score"],
        mode="lines+markers",
        line=dict(color="#f7c548", width=2.5),
        marker=dict(size=5, color="#f7c548"),
        name="CICI",
        hovertemplate="%{x}: <b>%{y:.1f}</b><extra></extra>",
    ))

    # ── Feature 1: FDI Overlay on secondary y-axis ────────────────────────────
    has_fdi = (
        "fdi_inflows" in df.columns
        and df["fdi_inflows"].notna().any()
    )
    if has_fdi:
        fdi_series = df["fdi_inflows"] / 1e9  # normalise to billions USD
        fig.add_trace(go.Scatter(
            x=df["year"], y=fdi_series,
            mode="lines",
            line=dict(color="#8b5cff", dash="dash", width=1.5),
            name="FDI Inflows",
            yaxis="y2",
            hovertemplate="%{x}: <b>$%{y:.2f}B</b><extra>FDI</extra>",
        ))

    # ── Feature 2: CICI Forecast 2025–2027 ───────────────────────────────────
    years_arr = df["year"].values
    scores_arr = df["cici_score"].values.astype(float)
    valid_mask = ~np.isnan(scores_arr)
    years_valid = years_arr[valid_mask]
    scores_valid = scores_arr[valid_mask]

    if len(years_valid) >= 2:
        window_y = years_valid[-5:]
        window_s = scores_valid[-5:]
        coeffs = np.polyfit(window_y, window_s, 1)

        forecast_years = np.array([2025, 2026, 2027])
        forecast_vals = np.clip(np.polyval(coeffs, forecast_years), 0, 100)

        # Connect last historical point to forecast for visual continuity
        connect_x = [int(years_valid[-1])] + forecast_years.tolist()
        connect_y = [float(scores_valid[-1])] + forecast_vals.tolist()

        # Confidence band ±5 points
        upper = np.clip(forecast_vals + 5, 0, 100)
        lower = np.clip(forecast_vals - 5, 0, 100)
        band_x = forecast_years.tolist() + list(reversed(forecast_years.tolist()))
        band_y = upper.tolist() + list(reversed(lower.tolist()))

        fig.add_trace(go.Scatter(
            x=band_x, y=band_y,
            fill="toself",
            fillcolor="rgba(247,197,72,0.05)",
            line=dict(width=0),
            name="Forecast band",
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.add_trace(go.Scatter(
            x=connect_x, y=connect_y,
            mode="lines",
            line=dict(dash="dash", color="#f7c548", width=1.5),
            opacity=0.5,
            name="Forecast",
            hovertemplate="%{x}E: <b>%{y:.1f}</b><extra>Forecast</extra>",
        ))

        # Annotation at 2027 forecast point
        fig.add_annotation(
            x=2027, y=float(forecast_vals[-1]),
            text=f"2027E: {forecast_vals[-1]:.0f}",
            showarrow=True, arrowhead=0,
            arrowcolor="rgba(247,197,72,0.6)",
            font=dict(size=9, color="#f7c548"),
            bgcolor="rgba(6,7,13,0.75)",
            bordercolor="rgba(247,197,72,0.3)",
            xshift=4, yshift=10,
        )

    # ── Key event annotations ─────────────────────────────────────────────────
    events = {2011: "Arab Spring", 2015: "Oil shock", 2020: "COVID-19"}
    for yr, label in events.items():
        if df["year"].min() <= yr <= df["year"].max():
            fig.add_vline(x=yr, line_dash="dot", line_color="#555", line_width=1)
            fig.add_annotation(x=yr, y=df["cici_score"].max(), text=label,
                               showarrow=False, font=dict(size=9, color="#888"),
                               textangle=-90, xshift=8)

    # ── Layout ────────────────────────────────────────────────────────────────
    layout_kwargs: dict = dict(
        paper_bgcolor="#06070d", plot_bgcolor="rgba(12,16,28,0.62)",
        font=dict(color="#e9e4d2"),
        xaxis=dict(showgrid=False, color="rgba(233,228,210,0.32)"),
        yaxis=dict(
            range=[0, 100],
            gridcolor="rgba(247,197,72,0.08)",
            color="rgba(233,228,210,0.32)",
            title="CICI",
        ),
        margin=dict(l=40, r=60 if has_fdi else 20, t=20, b=30),
        height=200,
        showlegend=has_fdi,
        legend=dict(
            x=0, y=1,
            font=dict(size=9, color="rgba(233,228,210,0.55)"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
    )

    if has_fdi:
        layout_kwargs["yaxis2"] = dict(
            overlaying="y",
            side="right",
            title="FDI $B",
            color="rgba(139,92,255,0.5)",
            showgrid=False,
        )

    fig.update_layout(**layout_kwargs)
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
        paper_bgcolor="#06070d", plot_bgcolor="rgba(12,16,28,0.62)",
        font=dict(color="#e9e4d2"),
        xaxis=dict(range=[0, 100], gridcolor="rgba(247,197,72,0.08)", color="rgba(233,228,210,0.32)"),
        yaxis=dict(color="rgba(233,228,210,0.55)"),
        margin=dict(l=10, r=20, t=10, b=20),
        height=230,
        showlegend=False,
    )
    return fig


def layout() -> html.Div:
    panel = load_cici_panel()
    countries = panel[["iso3", "country"]].drop_duplicates().sort_values("country")

    options = [
        {"label": f"{FLAG_EMOJI.get(r['iso3'], '')} {r['country']}", "value": r["iso3"]}
        for _, r in countries.iterrows()
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("◆ COUNTRY SCORECARD", style={
                    "fontFamily": "var(--display)", "fontWeight": "700",
                    "fontSize": "13px", "letterSpacing": "3px",
                    "color": "var(--gold)", "textTransform": "uppercase",
                    "marginBottom": "4px",
                }),
                html.Div("Composite Investment Climate Index · 19 MENA Nations", style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--text-dim)", "letterSpacing": "2px",
                }),
            ], width=5),
            dbc.Col([
                dcc.Dropdown(
                    id="scorecard-country-selector",
                    options=options,
                    value="ARE",
                    clearable=False,
                    className="mb-2",
                )
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id="scorecard-compare-selector",
                    options=options,
                    value=None,
                    clearable=True,
                    placeholder="Compare with...",
                    className="mb-2",
                )
            ], width=3),
        ], className="mb-3 mt-2"),

        html.Div(id="scorecard-content"),
    ], className="p-3")


def build_scorecard_content(iso3: str, compare_iso3: str | None = None) -> list:
    panel = load_cici_panel()
    mc = load_monte_carlo()
    latest_year = panel["year"].max()

    row = panel[(panel["iso3"] == iso3) & (panel["year"] == latest_year)]
    if row.empty:
        return [html.P("Нет данных", className="text-muted")]
    row = row.iloc[0]

    # Optional compare row for dual radar
    row2 = None
    if compare_iso3 and compare_iso3 != iso3:
        r2 = panel[(panel["iso3"] == compare_iso3) & (panel["year"] == latest_year)]
        if not r2.empty:
            row2 = r2.iloc[0]

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

    tier = "FRONTIER" if score >= 70 else "EMERGING" if score >= 50 else "DEVELOPING" if score >= 30 else "DISTRESSED"
    tier_color = color

    return [
        # Headline panel
        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ COUNTRY PROFILE ]", className="t-panel-title"),
                html.Span(f"{latest_year}", style={"fontFamily": "var(--mono)", "fontSize": "10px", "color": "var(--text-dim)"}),
            ], className="t-panel-head"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div(iso3, style={
                            "fontFamily": "var(--mono)", "fontSize": "11px",
                            "color": "var(--gold)", "letterSpacing": "4px",
                            "border": "1px solid rgba(247,197,72,0.3)",
                            "display": "inline-block", "padding": "2px 8px",
                            "marginBottom": "8px",
                        }),
                        html.Div(f"{flag} {row['country']}", style={
                            "fontFamily": "var(--display)", "fontWeight": "700",
                            "fontSize": "28px", "color": "var(--text)", "lineHeight": "1.1",
                        }),
                        html.Div(f"#{rank} of 19 countries", style={
                            "fontFamily": "var(--mono)", "fontSize": "10px",
                            "color": "var(--text-dim)", "letterSpacing": "2px", "marginTop": "6px",
                        }),
                        html.Div(ci_str, style={
                            "fontFamily": "var(--mono)", "fontSize": "9px",
                            "color": "var(--text-dim)", "marginTop": "4px",
                        }) if ci_str else html.Span(),
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Div(f"{score:.1f}", style={
                                "fontFamily": "var(--display)", "fontWeight": "700",
                                "fontSize": "80px", "color": "var(--gold)",
                                "textShadow": "0 0 24px rgba(247,197,72,0.5)",
                                "lineHeight": "1",
                            }),
                            html.Div("/ 100", style={
                                "fontFamily": "var(--mono)", "fontSize": "12px",
                                "color": "var(--text-dim)", "marginTop": "2px",
                            }),
                            html.Div(tier, style={
                                "display": "inline-block", "marginTop": "8px",
                                "border": f"1px solid {tier_color}",
                                "fontFamily": "var(--mono)", "fontSize": "11px",
                                "letterSpacing": "2px", "color": tier_color,
                                "padding": "3px 10px",
                            }),
                        ], style={"textAlign": "right"}),
                    ], width=6),
                ], className="align-items-center"),
            ], className="t-panel-body"),
        ], className="t-panel mb-3"),

        # Factor profile panel
        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ FACTOR PROFILE ]", className="t-panel-title"),
            ], className="t-panel-head"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            figure=make_radar_chart(row, row2),
                            config={"displayModeBar": False},
                        ),
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(figure=make_factor_bars(row), config={"displayModeBar": False}),
                    ], width=6),
                ]),
            ], className="t-panel-body"),
        ], className="t-panel t-panel-accent-teal mb-3"),

        # Trend panel
        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ CICI TREND 2000–2024 + FORECAST ]", className="t-panel-title"),
            ], className="t-panel-head"),
            html.Div([
                dcc.Graph(figure=make_timeseries_chart(panel, iso3), config={"displayModeBar": False}),
            ], className="t-panel-body"),
        ], className="t-panel t-panel-accent-violet mb-3"),

        # AI Analyst panel
        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ AI ANALYST ]", className="t-panel-title"),
            ], className="t-panel-head"),
            html.Div([
                html.Button(
                    "▶ ANALYSE",
                    id="scorecard-analyse-btn",
                    n_clicks=0,
                    style={
                        "background": "transparent",
                        "border": "1px solid rgba(247,197,72,0.4)",
                        "color": "var(--gold)",
                        "fontFamily": "var(--mono)",
                        "fontSize": "10px",
                        "letterSpacing": "2px",
                        "padding": "6px 16px",
                        "cursor": "pointer",
                        "marginBottom": "14px",
                    },
                ),
                dcc.Loading(
                    id="ai-analysis-loading",
                    type="dot",
                    color="#00e5d4",
                    children=html.Div(id="ai-analysis-text"),
                ),
            ], className="t-panel-body"),
        ], className="t-panel mb-3"),
    ]
