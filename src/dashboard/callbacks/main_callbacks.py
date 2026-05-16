"""
Все Dash callbacks — интерактивность дашборда.
"""
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from src.dashboard.data_loader import load_weights, FACTOR_LABELS, FLAG_EMOJI
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS


def _build_ticker_items(df) -> list:
    """Build the list of Dash elements for the live CICI ticker bar."""
    SEPARATOR = html.Span("  ·  ", style={"color": "rgba(247,197,72,0.3)"})
    items = []
    for _, row in df.iterrows():
        iso3  = row["iso3"]
        score = float(row.get("live_cici_score", row.get("cici_score", 0)))
        delta = float(row.get("live_delta", 0))
        flag  = FLAG_EMOJI.get(iso3, "")

        if delta > 0.05:
            delta_cls   = "t-up"
            delta_str   = f"+{delta:.1f}"
        elif delta < -0.05:
            delta_cls   = "t-dn"
            delta_str   = f"{delta:.1f}"
        else:
            delta_cls   = "t-nt"
            delta_str   = f"{delta:+.1f}"

        item = html.Span([
            html.Span(f"{flag} {iso3}", style={"color": "rgba(233,228,210,0.75)"}),
            html.Span(f" {score:.1f}", style={"color": "var(--gold)", "fontWeight": "700"}),
            html.Span(f" {delta_str}", className=delta_cls),
        ], className="ticker-item")

        if items:
            items.append(SEPARATOR)
        items.append(item)

    return items


def register_callbacks(app):

    # ── Live Ticker ────────────────────────────────────────────────────────────
    @app.callback(
        Output("live-cici-ticker", "children"),
        Input("live-ticker-interval", "n_intervals"),
    )
    def update_live_ticker(_):
        try:
            from src.dashboard.live_cici import get_live_ranking
            df = get_live_ranking()
            if df.empty:
                raise ValueError("empty")
            prefix = html.Span("⟳ LIVE CICI", style={
                "fontFamily": "var(--display)",
                "fontSize": "9px",
                "letterSpacing": "2.5px",
                "color": "rgba(247,197,72,0.5)",
                "paddingRight": "16px",
                "flexShrink": "0",
            })
            return [prefix] + _build_ticker_items(df)
        except Exception:
            return html.Span(
                "⟳ LIVE CICI  —  market data unavailable",
                style={"color": "rgba(233,228,210,0.25)", "fontSize": "10px"},
            )

    # ── M1: Scorecard — обновление при смене страны или сравниваемой страны ────
    @app.callback(
        Output("scorecard-content", "children"),
        Input("scorecard-country-selector", "value"),
        Input("scorecard-compare-selector", "value"),
    )
    def update_scorecard(iso3: str, compare_iso3: str | None):
        from src.dashboard.layouts.scorecard import build_scorecard_content
        return build_scorecard_content(iso3, compare_iso3=compare_iso3)

    # ── M1: AI Analyst — генерация анализа по кнопке ──────────────────────────
    @app.callback(
        Output("ai-analysis-text", "children"),
        Input("scorecard-analyse-btn", "n_clicks"),
        Input("scorecard-country-selector", "value"),
        prevent_initial_call=True,
    )
    def run_ai_analysis(n_clicks: int, iso3: str):
        if not n_clicks:
            return ""
        from src.dashboard.ai_analyst import generate_country_analysis
        from src.dashboard.data_loader import load_cici_panel, FACTOR_LABELS

        panel = load_cici_panel()
        latest_year = panel["year"].max()
        rows = panel[(panel["iso3"] == iso3) & (panel["year"] == latest_year)]
        if rows.empty:
            return html.Div(
                "No data available for this country.",
                style={"color": "var(--text-dim)"},
            )
        row = rows.iloc[0]

        text = generate_country_analysis(iso3, row, panel, FACTOR_LABELS)
        return html.Div(
            text,
            style={
                "fontFamily": "var(--mono)",
                "fontSize": "11px",
                "color": "var(--text)",
                "lineHeight": "1.7",
                "borderLeft": "2px solid #00e5d4",
                "paddingLeft": "12px",
            },
        )

    # ── M2: Ranking — обновление при смене года ────────────────────────────────
    @app.callback(
        Output("ranking-rows-container", "children"),
        Input("ranking-year-selector", "value"),
    )
    def update_ranking(year: int):
        from src.dashboard.layouts.ranking import build_ranking_rows
        return build_ranking_rows(year)

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

    # ── M4→M1: Map click drill-down → switch to Scorecard ─────────────────────
    @app.callback(
        Output("main-tabs", "active_tab"),
        Output("scorecard-country-selector", "value"),
        Input("map-choropleth", "clickData"),
        prevent_initial_call=True,
    )
    def map_click_to_scorecard(click_data):
        if not click_data:
            raise PreventUpdate
        try:
            iso3 = click_data["points"][0]["location"]
        except (KeyError, IndexError):
            raise PreventUpdate
        return "tab-scorecard", iso3

    # ── M2: Ranking play button — toggles interval & advances year slider ─────
    @app.callback(
        Output("ranking-play-interval", "disabled"),
        Input("ranking-play-btn", "n_clicks"),
        State("ranking-play-interval", "disabled"),
        prevent_initial_call=True,
    )
    def toggle_ranking_play(n_clicks, is_disabled):
        if not n_clicks:
            raise PreventUpdate
        return not is_disabled

    @app.callback(
        Output("ranking-year-selector", "value"),
        Input("ranking-play-interval", "n_intervals"),
        State("ranking-year-selector", "value"),
        prevent_initial_call=True,
    )
    def advance_ranking_year(n_intervals, current_year):
        if current_year is None:
            return 2000
        next_year = current_year + 1
        if next_year > 2024:
            next_year = 2000
        return next_year


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
