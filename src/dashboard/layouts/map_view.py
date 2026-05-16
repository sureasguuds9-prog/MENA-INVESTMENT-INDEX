"""
M4: Choropleth Map — интерактивная карта MENA с CICI score.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.data_loader import (
    load_cici_panel, load_ranking, get_available_years,
    FACTOR_LABELS, FLAG_EMOJI, SCORE_COLOR_SCALE
)
from src.model.build_panel import FACTOR_COLS


def make_choropleth(year: int | None = None, color_factor: str = "cici_score") -> go.Figure:
    panel = load_cici_panel()
    if year is None:
        year = panel["year"].max()

    df = panel[panel["year"] == year].copy()

    label = "CICI" if color_factor == "cici_score" else FACTOR_LABELS.get(color_factor, color_factor)

    # Hover текст
    df["hover"] = df.apply(lambda r: (
        f"<b>{FLAG_EMOJI.get(r['iso3'], '')} {r['country']}</b><br>"
        f"CICI: <b>{r['cici_score']:.1f}</b>  (#{int(r['cici_rank'])})<br>"
        + "<br>".join([
            f"{FACTOR_LABELS.get(f, f)}: {r[f]:.0f}"
            for f in FACTOR_COLS if f in r and pd.notna(r[f])
        ])
    ), axis=1)

    fig = px.choropleth(
        df,
        locations="iso3",
        color=color_factor,
        hover_name="country",
        custom_data=["hover"],
        color_continuous_scale=SCORE_COLOR_SCALE,
        range_color=[0, 100],
        scope="world",
        fitbounds="locations",
    )

    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        marker_line_color="#333",
        marker_line_width=0.5,
    )

    # Показываем только регион MENA
    fig.update_geos(
        visible=False,
        resolution=50,
        showcountries=True,
        countrycolor="rgba(247,197,72,0.2)",
        showcoastlines=True,
        coastlinecolor="rgba(0,229,212,0.15)",
        showland=True,
        landcolor="#0a0e1c",
        showocean=True,
        oceancolor="#03040a",
        showframe=False,
        lonaxis_range=[20, 80],
        lataxis_range=[10, 45],
        bgcolor="#03040a",
    )

    fig.update_coloraxes(
        colorbar=dict(
            title=dict(text=label, font=dict(color="rgba(233,228,210,0.55)", size=11)),
            tickfont=dict(color="rgba(233,228,210,0.32)", size=9),
            bgcolor="rgba(12,16,28,0.8)",
            bordercolor="rgba(247,197,72,0.2)",
            len=0.7,
        )
    )

    fig.update_layout(
        paper_bgcolor="#06070d",
        geo_bgcolor="#03040a",
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        font=dict(color="#e9e4d2"),
    )
    return fig


def layout() -> html.Div:
    years = get_available_years()
    factor_options = [{"label": "CICI (composite)", "value": "cici_score"}] + [
        {"label": FACTOR_LABELS.get(f, f), "value": f} for f in FACTOR_COLS
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("◆ MENA MAP", style={
                    "fontFamily": "var(--display)", "fontWeight": "700",
                    "fontSize": "13px", "letterSpacing": "3px",
                    "color": "var(--gold)", "textTransform": "uppercase",
                    "marginBottom": "4px",
                }),
                html.Div("Investment climate index by country", style={
                    "fontFamily": "var(--mono)", "fontSize": "9px",
                    "color": "var(--text-dim)", "letterSpacing": "2px",
                }),
            ], width=5),
            dbc.Col([
                dcc.Dropdown(
                    id="map-factor-selector",
                    options=factor_options,
                    value="cici_score",
                    clearable=False,
                    className="mb-2",
                    placeholder="Select indicator...",
                )
            ], width=4),
            dbc.Col([
                dcc.Dropdown(
                    id="map-year-selector",
                    options=[{"label": str(y), "value": y} for y in reversed(years)],
                    value=years[-1],
                    clearable=False,
                    className="mb-2",
                )
            ], width=3),
        ], className="mb-3 mt-2"),

        html.Div([
            html.Div(className="t-panel-corner t-panel-corner-tl"),
            html.Div(className="t-panel-corner t-panel-corner-tr"),
            html.Div(className="t-panel-corner t-panel-corner-bl"),
            html.Div(className="t-panel-corner t-panel-corner-br"),
            html.Div([
                html.Span("[ CHOROPLETH ]", className="t-panel-title"),
            ], className="t-panel-head"),
            html.Div([
                dcc.Graph(
                    id="map-choropleth",
                    figure=make_choropleth(),
                    config={"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
                ),
            ], className="t-panel-body", style={"padding": "0"}),
        ], className="t-panel t-panel-accent-teal"),

        html.Div([
            html.Span("◉ FRONTIER ≥70  ", style={"color": "#5cffb1", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ EMERGING ≥50  ", style={"color": "#f7c548", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ DEVELOPING ≥30  ", style={"color": "#ff9a3d", "fontFamily": "var(--mono)", "fontSize": "10px"}),
            html.Span("◉ DISTRESSED <30", style={"color": "#ff3d6b", "fontFamily": "var(--mono)", "fontSize": "10px"}),
        ], style={"marginTop": "12px", "paddingLeft": "4px", "textAlign": "center"}),
    ], className="p-3")
