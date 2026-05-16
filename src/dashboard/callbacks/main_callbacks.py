"""
Все Dash callbacks — интерактивность дашборда.
"""
from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc
from src.dashboard.data_loader import load_weights, FACTOR_LABELS
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS


def register_callbacks(app):

    # ── M1: Scorecard — обновление при смене страны ────────────────────────────
    @app.callback(
        Output("scorecard-content", "children"),
        Input("scorecard-country-selector", "value"),
    )
    def update_scorecard(iso3: str):
        from src.dashboard.layouts.scorecard import build_scorecard_content
        return build_scorecard_content(iso3)

    # ── M2: Ranking — обновление при смене года ────────────────────────────────
    @app.callback(
        Output("ranking-table", "data"),
        Output("ranking-table", "columns"),
        Input("ranking-year-selector", "value"),
    )
    def update_ranking(year: int):
        from src.dashboard.layouts.ranking import build_ranking_table_data
        rows, cols = build_ranking_table_data(year)
        return rows, cols

    # ── M4: Map — обновление при смене года или индикатора ────────────────────
    @app.callback(
        Output("map-choropleth", "figure"),
        Input("map-year-selector", "value"),
        Input("map-factor-selector", "value"),
    )
    def update_map(year: int, factor: str):
        from src.dashboard.layouts.map_view import make_choropleth
        return make_choropleth(year=year, color_factor=factor)

    # ── M5: Custom Weights — пересчёт рейтинга при движении слайдеров ─────────
    weight_slider_ids = [f"weight-slider-{f}" for f in FACTOR_COLS]

    @app.callback(
        Output("custom-weights-ranking-chart", "figure"),
        Output("weights-sum-display", "children"),
        Output("weights-sum-warning", "children"),
        *[Input(sid, "value") for sid in weight_slider_ids],
    )
    def update_custom_ranking(*slider_values):
        from src.dashboard.layouts.weights import make_custom_ranking_chart

        raw_weights = {f: v / 100.0 for f, v in zip(FACTOR_COLS, slider_values)}
        total = sum(raw_weights.values())

        warning = None
        if abs(total - 1.0) > 0.05:
            warning = dbc.Alert(
                f"⚠️ Сумма весов = {total*100:.0f}% (нужно ~100%). Веса нормируются автоматически.",
                color="warning", className="py-1 px-2 small mb-2",
            )

        # Нормируем
        if total > 0:
            weights = {f: v / total for f, v in raw_weights.items()}
        else:
            weights = dict(BASELINE_WEIGHTS)

        sum_text = (
            f"Сумма: {total*100:.0f}% → "
            + "  ".join([f"{FACTOR_LABELS.get(f, f)}: {w*100:.0f}%" for f, w in weights.items()])
        )

        return make_custom_ranking_chart(weights), sum_text, warning

    # ── M5: Пресеты ────────────────────────────────────────────────────────────
    from src.dashboard.layouts.weights import PRESETS

    for preset_key in PRESETS:
        _register_preset_callback(app, preset_key, weight_slider_ids)

    # ── M6: Markets — сравнительный график ────────────────────────────────────
    @app.callback(
        Output("compare-chart", "figure"),
        Output("markets-last-updated", "children"),
        Input("compare-ticker-checklist", "value"),
        Input("compare-interval-selector", "value"),
        Input("markets-refresh-btn", "n_clicks"),
    )
    def update_compare_chart(tickers, interval_range, _):
        from src.dashboard.market_data import fetch_compare_data
        from src.dashboard.layouts.markets import make_compare_figure
        from datetime import datetime

        if not tickers:
            tickers = ["BTC-USD", "CL=F"]

        interval, range_ = (interval_range or "1d|1mo").split("|")
        data = fetch_compare_data(tickers, interval, range_)
        fig = make_compare_figure(data)

        updated = f"Обновлено: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}"
        return fig, updated

    # ── M6: Markets — кнопка обновить перезагружает карточки цен ─────────────
    @app.callback(
        Output("markets-price-cards", "children"),
        Input("markets-refresh-btn", "n_clicks"),
    )
    def refresh_price_cards(_):
        from src.dashboard.market_data import fetch_all_prices, TICKERS
        from src.dashboard.layouts.markets import make_price_card
        import dash_bootstrap_components as dbc

        prices = fetch_all_prices()
        return [
            dbc.Col(make_price_card(ticker, info, prices), width=12, md=6, lg=True)
            for ticker, info in TICKERS.items()
        ]

    # ── M7: News — обновление ленты при фильтрах и интервале ─────────────────
    @app.callback(
        Output("news-feed-content", "children"),
        Output("news-stats-bar", "children"),
        Output("news-last-updated", "children"),
        Input("news-country-filter", "value"),
        Input("news-impact-filter", "value"),
        Input("news-refresh-interval", "n_intervals"),
    )
    def update_news_feed(country_filter, impact_filter, _):
        from src.dashboard.news_feed import fetch_all_news
        from src.dashboard.layouts.news import make_news_card, make_stats_bar
        from datetime import datetime

        articles = fetch_all_news(country_filter=country_filter or "ALL")

        # Фильтр «только ключевые»
        if impact_filter and "moving" in impact_filter:
            articles = [a for a in articles if a.get("is_market_moving")]

        cards = [make_news_card(a) for a in articles]
        if not cards:
            from dash import html
            cards = [html.P("Нет новостей по выбранным фильтрам", className="text-muted p-3")]

        stats = make_stats_bar(articles)
        updated = f"Обновлено: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}"
        return cards, stats, updated


def _register_preset_callback(app, preset_key: str, slider_ids: list[str]):
    from src.dashboard.layouts.weights import PRESETS
    from dash import Output, Input, callback

    outputs = [Output(sid, "value", allow_duplicate=True) for sid in slider_ids]

    @app.callback(
        outputs,
        Input(f"preset-{preset_key}", "n_clicks"),
        prevent_initial_call=True,
    )
    def apply_preset(_):
        weights_dict = PRESETS.get(preset_key)
        if weights_dict is None:
            weights_dict = load_weights()
        return [round(weights_dict.get(f, BASELINE_WEIGHTS.get(f, 0.1)) * 100) for f in FACTOR_COLS]
