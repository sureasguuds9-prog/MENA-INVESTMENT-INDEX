"""
M6: Markets — рыночные данные в реальном времени.
Bitcoin, нефть WTI, золото, валюты.
Сравнительный график с автоматической цветовой палитрой.
"""
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from src.dashboard.market_data import TICKERS, COMPARE_TICKERS, INTERVAL_OPTIONS, fetch_all_prices


# Уникальные цвета для каждого тикера (автоматически)
PALETTE = [
    "#f7931a", "#2ecc71", "#ffd700", "#627eea",
    "#e74c3c", "#3498db", "#9b59b6", "#1abc9c",
    "#e67e22", "#34495e",
]


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Конвертирует hex цвет в rgba строку для Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def make_price_card(ticker: str, info: dict, price_data: dict) -> dbc.Card:
    """Карточка с текущей ценой тикера."""
    p = price_data.get(ticker, {"price": 0, "change_pct": 0, "error": True})
    price = p["price"]
    chg   = p["change_pct"]
    color = "#2ecc71" if chg >= 0 else "#e74c3c"
    arrow = "▲" if chg >= 0 else "▼"

    # Форматируем цену
    if ticker in ("EURUSD=X", "DX-Y.NYB"):
        price_str = f"{price:.4f}"
    elif price > 1000:
        price_str = f"${price:,.0f}"
    else:
        price_str = f"${price:.2f}"

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(info["emoji"], style={"fontSize": "1.5rem"}),
                html.Span(info["label"], className="ms-2 text-muted small"),
            ], className="d-flex align-items-center mb-1"),
            html.H4(price_str, className="mb-0 fw-bold",
                    style={"color": info["color"], "fontFamily": "monospace"}),
            html.Small(
                f"{arrow} {abs(chg):.2f}% за день",
                style={"color": color},
            ),
        ], className="p-2"),
    ], style={
        "backgroundColor": "#161b22",
        "border": f"1px solid {info['color']}33",
        "borderLeft": f"3px solid {info['color']}",
    }, className="mb-2")


def make_compare_figure(data: dict, interval_label: str = "") -> go.Figure:
    """Сравнительный нормированный график (база = 100)."""
    fig = go.Figure()

    for i, (ticker, df) in enumerate(data.items()):
        if df.empty:
            continue
        info = COMPARE_TICKERS.get(ticker, {})
        color = info.get("color", PALETTE[i % len(PALETTE)])
        label = info.get("label", ticker)

        last_val = df["normalized"].iloc[-1]
        chg = last_val - 100
        chg_str = f"+{chg:.1f}%" if chg >= 0 else f"{chg:.1f}%"

        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["normalized"],
            name=f"{label} ({chg_str})",
            line=dict(color=color, width=2),
            mode="lines",
            hovertemplate=(
                f"<b>{label}</b><br>"
                "%{x|%d %b %Y}<br>"
                "Норм.: %{y:.1f}<br>"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(
        y=100, line_dash="dot",
        line_color="rgba(255,255,255,0.2)",
        annotation_text="База (100)",
        annotation_font_color="rgba(255,255,255,0.4)",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left",   x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0.4)",
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            showgrid=True, gridcolor="#1e2a3a",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1e2a3a",
            zeroline=False,
            ticksuffix="",
            title="Индекс (база=100)",
        ),
        hovermode="x unified",
        height=420,
    )
    return fig


def make_single_chart(ticker: str, interval: str = "1d", range_: str = "1mo") -> go.Figure:
    """График одного актива с объёмом."""
    from src.dashboard.market_data import fetch_ticker
    df = fetch_ticker(ticker, interval, range_)
    info = TICKERS.get(ticker, {"label": ticker, "color": "#3498db", "unit": ""})

    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="Нет данных", x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#aaa", size=14))
    else:
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["close"],
            name=info["label"],
            line=dict(color=info["color"], width=2),
            fill="tozeroy",
            fillcolor=_hex_to_rgba(info["color"], 0.08),
            mode="lines",
            hovertemplate=f"<b>{info['label']}</b><br>%{{x|%d %b %Y}}<br>{info['unit']} %{{y:,.2f}}<extra></extra>",
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor="#1e2a3a", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#1e2a3a", zeroline=False),
        showlegend=False,
        height=280,
        hovermode="x unified",
    )
    return fig


def layout() -> html.Div:
    prices = fetch_all_prices()

    return html.Div([
        # ── Заголовок ──────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.H4("📈 Рынки в реальном времени", className="fw-bold mb-1"),
                html.P("Цены через Yahoo Finance · Обновление при каждом открытии страницы",
                       className="text-muted small mb-2"),
            ], width=8),
            dbc.Col([
                dbc.Button(
                    "🔄 Обновить",
                    id="markets-refresh-btn",
                    color="outline-primary",
                    size="sm",
                    className="float-end mt-1",
                ),
            ], width=4),
        ]),

        # ── Карточки с текущими ценами ─────────────────────────────────────────
        dbc.Row(
            id="markets-price-cards",
            children=[dbc.Col(make_price_card(ticker, info, prices), width=12, md=6, lg=True)
                      for ticker, info in TICKERS.items()],
            className="g-2 mb-3",
        ),

        html.Hr(style={"borderColor": "#1e2a3a"}),

        # ── Сравнительный график ───────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.H5("Сравнение активов (нормировано к 100)", className="fw-bold mb-2"),
            ], width=12, md=5),
            dbc.Col([
                dcc.Checklist(
                    id="compare-ticker-checklist",
                    options=[
                        {"label": html.Span([
                            html.Span("●", style={"color": info["color"], "marginRight": "4px"}),
                            info["label"],
                        ], style={"marginRight": "12px"}),
                         "value": ticker}
                        for ticker, info in COMPARE_TICKERS.items()
                    ],
                    value=["BTC-USD", "CL=F", "GC=F"],
                    inline=True,
                    className="small",
                    inputStyle={"marginRight": "4px"},
                    labelStyle={"marginRight": "10px", "cursor": "pointer"},
                ),
            ], width=12, md=5),
            dbc.Col([
                dcc.Dropdown(
                    id="compare-interval-selector",
                    options=[{"label": o["label"], "value": f"{o['value']}|{o['range']}"}
                             for o in INTERVAL_OPTIONS],
                    value="1d|1mo",
                    clearable=False,
                    className="small",
                ),
            ], width=12, md=2),
        ], className="align-items-center mb-2"),

        dcc.Loading(
            dcc.Graph(id="compare-chart", config={"displayModeBar": False}),
            type="circle", color="#3498db",
        ),

        html.Hr(style={"borderColor": "#1e2a3a"}),

        # ── Индивидуальные графики ─────────────────────────────────────────────
        html.H5("Детальные графики", className="fw-bold mb-3"),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("₿", style={"color": "#f7931a", "fontWeight": "bold"}),
                    html.Span(" Bitcoin / USD", className="ms-1 small text-muted"),
                ], className="mb-1"),
                dcc.Graph(
                    id="chart-btc",
                    figure=make_single_chart("BTC-USD"),
                    config={"displayModeBar": False},
                ),
            ], width=12, md=6),
            dbc.Col([
                html.Div([
                    html.Span("🛢️", style={"fontSize": "1rem"}),
                    html.Span(" Нефть WTI", className="ms-1 small text-muted"),
                ], className="mb-1"),
                dcc.Graph(
                    id="chart-oil",
                    figure=make_single_chart("CL=F"),
                    config={"displayModeBar": False},
                ),
            ], width=12, md=6),
        ], className="g-3"),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("🥇", style={"fontSize": "1rem"}),
                    html.Span(" Золото", className="ms-1 small text-muted"),
                ], className="mb-1"),
                dcc.Graph(
                    id="chart-gold",
                    figure=make_single_chart("GC=F"),
                    config={"displayModeBar": False},
                ),
            ], width=12, md=6),
            dbc.Col([
                html.Div([
                    html.Span("€", style={"color": "#3498db", "fontWeight": "bold"}),
                    html.Span(" EUR/USD", className="ms-1 small text-muted"),
                ], className="mb-1"),
                dcc.Graph(
                    id="chart-eur",
                    figure=make_single_chart("EURUSD=X"),
                    config={"displayModeBar": False},
                ),
            ], width=12, md=6),
        ], className="g-3 mt-1"),

        # Метка обновления
        html.Div(id="markets-last-updated", className="text-muted small text-end mt-2"),

    ], className="p-3")
