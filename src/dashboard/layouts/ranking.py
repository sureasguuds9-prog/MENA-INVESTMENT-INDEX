"""
M2: Ranking Table — сравнительный рейтинг всех 19 стран.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import pandas as pd
from src.dashboard.data_loader import (
    load_ranking, load_monte_carlo, get_available_years,
    FACTOR_LABELS, FLAG_EMOJI
)
from src.model.build_panel import FACTOR_COLS


def _score_color(score: float) -> str:
    if score >= 70:   return "#5cffb1"
    elif score >= 50: return "#f7c548"
    elif score >= 30: return "#ff9a3d"
    else:             return "#ff3d6b"


def _tier(score: float) -> str:
    if score >= 70:   return "FRONTIER"
    elif score >= 50: return "EMERGING"
    elif score >= 30: return "DEVELOPING"
    else:             return "DISTRESSED"


def build_ranking_rows(year: int | None = None) -> list[dict]:
    df = load_ranking(year)
    mc = load_monte_carlo()
    if not mc.empty:
        df = df.merge(mc[["iso3", "ci_lower_95", "ci_upper_95"]], on="iso3", how="left")

    rows = []
    for _, row in df.sort_values("cici_rank").iterrows():
        flag  = FLAG_EMOJI.get(row["iso3"], "")
        score = float(row["cici_score"])
        rank  = int(row["cici_rank"])
        color = _score_color(score)
        tier  = _tier(score)

        ci_str = ""
        if "ci_lower_95" in row and pd.notna(row.get("ci_lower_95")):
            ci_str = f"[{row['ci_lower_95']:.0f}–{row['ci_upper_95']:.0f}]"

        factor_spans = []
        for f in FACTOR_COLS:
            val = row.get(f)
            if pd.notna(val):
                fc = _score_color(float(val))
                factor_spans.append(html.Div([
                    html.Span(FACTOR_LABELS.get(f, f)[:3].upper(),
                              style={"fontFamily": "var(--mono)", "fontSize": "8px",
                                     "color": "var(--text-dim)", "letterSpacing": "1px",
                                     "display": "block"}),
                    html.Span(f"{val:.0f}", style={"color": fc, "fontFamily": "var(--mono)",
                                                    "fontSize": "13px", "fontWeight": "700"}),
                ], style={"textAlign": "center", "minWidth": "36px"}))

        rows.append(html.Div([
            # Rank badge
            html.Div(f"#{rank:02d}", style={
                "fontFamily": "var(--mono)", "fontWeight": "700", "fontSize": "18px",
                "color": color if rank <= 5 else ("var(--text-dim)" if rank >= 15 else "var(--text-mute)"),
                "minWidth": "48px", "textAlign": "center", "flexShrink": "0",
            }),
            # Flag + country
            html.Div([
                html.Div(f"{flag} {row['country']}", style={
                    "fontFamily": "var(--display)", "fontWeight": "600",
                    "fontSize": "14px", "color": "var(--text)",
                }),
                html.Div(row["iso3"], style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--gold)", "letterSpacing": "3px", "marginTop": "2px",
                }),
            ], style={"flex": "1", "minWidth": "140px"}),
            # Score
            html.Div([
                html.Span(f"{score:.1f}", style={
                    "fontFamily": "var(--display)", "fontWeight": "700",
                    "fontSize": "22px", "color": color,
                    "textShadow": f"0 0 10px {color}66",
                }),
                html.Div(tier, style={
                    "fontFamily": "var(--mono)", "fontSize": "8px",
                    "color": color, "letterSpacing": "2px", "marginTop": "2px",
                    "border": f"1px solid {color}66", "padding": "1px 5px",
                    "display": "inline-block",
                }),
                html.Div(ci_str, style={
                    "fontFamily": "var(--mono)", "fontSize": "8px",
                    "color": "var(--text-dim)", "marginTop": "3px",
                }) if ci_str else html.Span(),
            ], style={"textAlign": "right", "minWidth": "90px", "flexShrink": "0"}),
            # Factor bars
            html.Div(factor_spans, style={
                "display": "flex", "gap": "8px", "alignItems": "center",
                "flexWrap": "wrap", "justifyContent": "flex-end", "flex": "2",
            }),
        ], style={
            "display": "flex", "alignItems": "center", "gap": "16px",
            "padding": "10px 16px",
            "borderBottom": "1px solid rgba(247,197,72,0.07)",
            "background": ("rgba(92,255,177,0.04)" if rank <= 5
                           else "rgba(255,61,107,0.04)" if rank >= 15 else "transparent"),
            "transition": "background 0.15s",
        }, className="t-rank-row"))

    return rows


def layout() -> html.Div:
    years = get_available_years()
    min_year = min(years) if years else 2000
    max_year = max(years) if years else 2024
    default_year = max_year

    slider_marks = {
        y: {
            "label": str(y),
            "style": {"color": "#f7c548", "fontFamily": "var(--mono)", "fontSize": "10px"},
        }
        for y in [2000, 2005, 2010, 2015, 2020, 2024]
        if min_year <= y <= max_year
    }

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("◆ COUNTRY RANKING", style={
                    "fontFamily": "var(--display)", "fontWeight": "700",
                    "fontSize": "13px", "letterSpacing": "3px",
                    "color": "var(--gold)", "textTransform": "uppercase",
                    "marginBottom": "4px",
                }),
                html.Div("Composite Investment Climate Index · 0–100, higher = better", style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--text-dim)", "letterSpacing": "2px",
                }),
            ], width=5),
            dbc.Col([
                # Play button + animated interval
                html.Div([
                    html.Button(
                        "▶ PLAY",
                        id="ranking-play-btn",
                        n_clicks=0,
                        style={
                            "background": "transparent",
                            "border": "1px solid rgba(247,197,72,0.4)",
                            "color": "var(--gold)",
                            "fontFamily": "var(--mono)",
                            "fontSize": "10px",
                            "letterSpacing": "2px",
                            "padding": "5px 14px",
                            "cursor": "pointer",
                            "marginRight": "12px",
                            "flexShrink": "0",
                        },
                    ),
                    dcc.Slider(
                        id="ranking-year-selector",
                        min=min_year,
                        max=max_year,
                        step=1,
                        value=default_year,
                        marks=slider_marks,
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode="drag",
                    ),
                    dcc.Interval(
                        id="ranking-play-interval",
                        interval=800,
                        disabled=True,
                        n_intervals=0,
                    ),
                ], style={"display": "flex", "alignItems": "center", "paddingTop": "6px"}),
            ], width=7),
        ], className="mb-3 mt-2"),

        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ RANKING TABLE ]", className="t-panel-title"),
                html.Span("sort by CICI score", style={"fontFamily": "var(--mono)", "fontSize": "9px", "color": "var(--text-dim)"}),
            ], className="t-panel-head"),
            html.Div(
                html.Div(id="ranking-rows-container", children=build_ranking_rows()),
                className="t-panel-body", style={"padding": "0"},
            ),
        ], className="t-panel"),

        html.Div([
            html.Span("◉ FRONTIER ≥70  ", style={"color": "#5cffb1", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ EMERGING ≥50  ", style={"color": "#f7c548", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ DEVELOPING ≥30  ", style={"color": "#ff9a3d", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ DISTRESSED <30", style={"color": "#ff3d6b", "fontFamily": "var(--mono)", "fontSize": "10px"}),
        ], style={"marginTop": "12px", "paddingLeft": "4px"}),
    ], className="p-3")
