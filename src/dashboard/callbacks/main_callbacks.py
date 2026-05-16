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
