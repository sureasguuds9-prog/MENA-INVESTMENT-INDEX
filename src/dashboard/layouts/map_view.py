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
        countrycolor="#555",
        showcoastlines=True,
        coastlinecolor="#444",
        showland=True,
        landcolor="#1a1a2e",
        showocean=True,
        oceancolor="#0d1b2a",
        showframe=False,
        lonaxis_range=[20, 80],
        lataxis_range=[10, 45],
        bgcolor="#0d1b2a",
    )

    fig.update_coloraxes(
        colorbar=dict(
            title=dict(text=label, font=dict(color="#e0e0e0", size=12)),
            tickfont=dict(color="#e0e0e0"),
            bgcolor="#16213e",
            bordercolor="#333",
            len=0.7,
        )
    )

    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        geo_bgcolor="#0d1b2a",
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        font=dict(color="#e0e0e0"),
    )
    return fig


def layout() -> html.Div:
    years = get_available_years()
    factor_options = [{"label": "CICI (общий)", "value": "cici_score"}] + [
        {"label": FACTOR_LABELS.get(f, f), "value": f} for f in FACTOR_COLS
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Карта MENA", className="fw-bold mb-1"),
                html.P("Инвестиционный климат по странам региона", className="text-muted small mb-3"),
            ], width=5),
            dbc.Col([
                dcc.Dropdown(
                    id="map-factor-selector",
                    options=factor_options,
                    value="cici_score",
                    clearable=False,
                    className="mb-2",
                    placeholder="Выбрать индикатор...",
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
        ]),

        dcc.Graph(
            id="map-choropleth",
            figure=make_choropleth(),
            config={"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
        ),

        # Легенда под картой
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("■ ", style={"color": "#313695"}), html.Span("75–100 Высокий  "),
                    html.Span("■ ", style={"color": "#74add1"}), html.Span("50–75 Средний  "),
                    html.Span("■ ", style={"color": "#fee090"}), html.Span("25–50 Низкий  "),
                    html.Span("■ ", style={"color": "#d73027"}), html.Span("0–25 Критический"),
                ], className="text-muted small mt-1 text-center"),
            ])
        ]),
    ], className="p-3")
