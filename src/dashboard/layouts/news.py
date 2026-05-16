"""
M7: Live News Feed — живая лента новостей MENA.
Ключевые новости, влияющие на индекс, подсвечиваются цветом.
"""
from dash import html, dcc
import dash_bootstrap_components as dbc
from src.dashboard.news_feed import fetch_all_news, IMPACT_COLORS, KEYWORD_CATEGORIES
from src.dashboard.data_loader import FLAG_EMOJI

CATEGORY_LABELS = {
    "oil":      ("🛢️", "Нефть",      "warning"),
    "conflict": ("⚔️", "Конфликт",   "danger"),
    "economy":  ("💰", "Экономика",  "success"),
    "politics": ("🏛️", "Политика",  "info"),
    "nuclear":  ("☢️", "Ядерный",   "danger"),
}

COUNTRY_OPTIONS = [
    {"label": "🌍 Все страны MENA", "value": "ALL"},
    {"label": "🇸🇦 Saudi Arabia",  "value": "SAU"},
    {"label": "🇦🇪 UAE",           "value": "ARE"},
    {"label": "🇮🇷 Iran",          "value": "IRN"},
    {"label": "🇮🇱 Israel",        "value": "ISR"},
    {"label": "🇮🇶 Iraq",          "value": "IRQ"},
    {"label": "🇪🇬 Egypt",         "value": "EGY"},
    {"label": "🇱🇧 Lebanon",       "value": "LBN"},
    {"label": "🇾🇪 Yemen",         "value": "YEM"},
    {"label": "🇸🇾 Syria",         "value": "SYR"},
    {"label": "🇶🇦 Qatar",         "value": "QAT"},
    {"label": "🇲🇦 Morocco",       "value": "MAR"},
    {"label": "🇱🇾 Libya",         "value": "LBY"},
]


def make_category_badge(cat: str) -> html.Span:
    emoji, label, color = CATEGORY_LABELS.get(cat, ("📌", cat, "secondary"))
    return dbc.Badge(
        f"{emoji} {label}",
        color=color,
        className="me-1",
        style={"fontSize": "10px"},
    )


def make_impact_badge(impact_type: str, impact_label: str) -> html.Span:
    cfg = IMPACT_COLORS.get(impact_type, {})
    return dbc.Badge(
        f"⚡ {impact_label}",
        color=cfg.get("badge", "secondary"),
        className="me-1 fw-bold",
        style={"fontSize": "11px"},
    )


def make_country_flags(countries: list[str]) -> html.Span:
    flags = " ".join(FLAG_EMOJI.get(c, "") for c in countries[:4])
    return html.Span(flags, style={"fontSize": "14px"})


def make_news_card(article: dict) -> html.Div:
    impact_type = article.get("impact_type")
    is_moving   = article.get("is_market_moving", False)

    moving_cls = ""
    if is_moving:
        moving_cls = {"danger": "moving", "warning": "moving warning", "success": "moving success", "info": "moving info"}.get(impact_type, "moving")

    cats = article.get("categories", [])
    tag_cat = cats[0] if cats else "info"
    tag_label = {"oil": "ENERGY", "conflict": "CONFLICT", "economy": "ECONOMY", "politics": "POLICY", "nuclear": "NUCLEAR"}.get(tag_cat, "NEWS")

    impact_label = article.get("impact_label", "")
    display_tag = f"⚡ {impact_label}" if is_moving and impact_label else tag_label

    return html.Div([
        html.Span(article["pub_str"], className="t-feed-time"),
        html.Span(display_tag, className=f"t-feed-tag {tag_cat}"),
        html.Div([
            html.A(article["title"], href=article["url"], target="_blank", className="t-feed-txt"),
            html.Div(
                " ".join(FLAG_EMOJI.get(c, "") for c in article.get("countries", [])[:3]),
                style={"fontSize": "12px", "marginTop": "2px"},
            ),
        ]),
    ], className=f"t-feed-item {moving_cls}")


def make_impact_legend() -> dbc.Card:
    """Легенда подсветки."""
    return dbc.Card([
        dbc.CardBody([
            html.P("Влияние на индекс:", className="small fw-bold mb-2 text-muted"),
            *[
                html.Div([
                    html.Span("●", style={"color": cfg["border"], "marginRight": "6px", "fontSize": "16px"}),
                    html.Span(cfg["label"], className="small text-muted"),
                ], className="mb-1")
                for itype, cfg in IMPACT_COLORS.items()
            ],
            html.Hr(style={"borderColor": "#333", "margin": "8px 0"}),
            html.P("Серая граница = нейтральная новость", className="small text-muted mb-0"),
        ], className="p-2"),
    ], style={"backgroundColor": "#111", "border": "1px solid #222"})


def make_stats_bar(articles: list[dict]) -> html.Div:
    """Строка статистики по ленте."""
    total = len(articles)
    moving = sum(1 for a in articles if a.get("is_market_moving"))
    danger = sum(1 for a in articles if a.get("impact_type") == "danger")
    positive = sum(1 for a in articles if a.get("impact_type") == "success")

    return dbc.Row([
        dbc.Col(html.Div([
            html.Span(f"{total}", className="fw-bold", style={"fontSize": "1.3rem"}),
            html.Span(" новостей", className="text-muted small ms-1"),
        ]), width="auto"),
        dbc.Col(html.Div([
            html.Span(f"{moving}", className="fw-bold text-warning", style={"fontSize": "1.3rem"}),
            html.Span(" ключевых", className="text-muted small ms-1"),
        ]), width="auto"),
        dbc.Col(html.Div([
            html.Span(f"{danger}", className="fw-bold text-danger", style={"fontSize": "1.3rem"}),
            html.Span(" риска", className="text-muted small ms-1"),
        ]), width="auto"),
        dbc.Col(html.Div([
            html.Span(f"{positive}", className="fw-bold text-success", style={"fontSize": "1.3rem"}),
            html.Span(" позитивных", className="text-muted small ms-1"),
        ]), width="auto"),
    ], className="g-3 mb-3 align-items-center")


def layout() -> html.Div:
    articles = fetch_all_news()

    return html.Div([
        # ── Заголовок + фильтры ────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.H4("📰 Live News Feed", className="fw-bold mb-1"),
                html.P(
                    "BBC Middle East · Al Jazeera · Обновление каждые 5 минут",
                    className="text-muted small mb-0",
                ),
            ], width=12, md=5),
            dbc.Col([
                dcc.Dropdown(
                    id="news-country-filter",
                    options=COUNTRY_OPTIONS,
                    value="ALL",
                    clearable=False,
                    placeholder="Фильтр по стране...",
                ),
            ], width=12, md=4),
            dbc.Col([
                dbc.Checklist(
                    id="news-impact-filter",
                    options=[{"label": " Только ключевые", "value": "moving"}],
                    value=[],
                    switch=True,
                    className="small mt-2",
                ),
            ], width=12, md=3),
        ], className="mb-3"),

        # ── Статистика ────────────────────────────────────────────────────────
        html.Div(id="news-stats-bar", children=make_stats_bar(articles)),

        # ── Основной контент ──────────────────────────────────────────────────
        dbc.Row([
            # Лента новостей
            dbc.Col([
                dcc.Loading(
                    html.Div(id="news-feed-content",
                             children=[make_news_card(a) for a in articles]),
                    type="circle",
                    color="#3498db",
                ),
            ], width=12, md=9),

            # Боковая панель
            dbc.Col([
                make_impact_legend(),

                html.Div(className="mt-3"),

                dbc.Card([
                    dbc.CardHeader("Топ категорий", className="small fw-bold py-2"),
                    dbc.CardBody([
                        _make_category_stats(articles),
                    ], className="p-2"),
                ], style={"backgroundColor": "#111", "border": "1px solid #222"}),

                html.Div(className="mt-3"),

                dbc.Card([
                    dbc.CardHeader("Топ стран", className="small fw-bold py-2"),
                    dbc.CardBody([
                        _make_country_stats(articles),
                    ], className="p-2"),
                ], style={"backgroundColor": "#111", "border": "1px solid #222"}),

            ], width=12, md=3),
        ]),

        # Автообновление каждые 5 минут
        dcc.Interval(id="news-refresh-interval", interval=5 * 60 * 1000, n_intervals=0),
        html.Div(id="news-last-updated", className="text-muted small text-end mt-2"),

    ], className="p-3")


def _make_category_stats(articles: list[dict]) -> html.Div:
    from collections import Counter
    cats = Counter(c for a in articles for c in a.get("categories", []))
    rows = []
    for cat, count in cats.most_common(5):
        emoji, label, color = CATEGORY_LABELS.get(cat, ("📌", cat, "secondary"))
        rows.append(html.Div([
            html.Span(f"{emoji} {label}", className="small"),
            dbc.Badge(str(count), color=color, className="float-end small"),
        ], className="mb-1"))
    return html.Div(rows)


def _make_country_stats(articles: list[dict]) -> html.Div:
    from collections import Counter
    from src.dashboard.data_loader import FLAG_EMOJI
    from src.config import COUNTRY_NAMES
    countries = Counter(c for a in articles for c in a.get("countries", []))
    rows = []
    for iso3, count in countries.most_common(6):
        flag = FLAG_EMOJI.get(iso3, "")
        name = COUNTRY_NAMES.get(iso3, iso3)
        rows.append(html.Div([
            html.Span(f"{flag} {name}", className="small"),
            dbc.Badge(str(count), color="secondary", className="float-end small"),
        ], className="mb-1"))
    return html.Div(rows if rows else [html.Span("—", className="text-muted small")])
