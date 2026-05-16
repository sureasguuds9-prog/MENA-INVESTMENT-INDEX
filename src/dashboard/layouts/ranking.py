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


def build_ranking_table_data(year: int | None = None) -> tuple[list[dict], list[dict]]:
    """Готовит данные и колонки для dash_table."""
    df = load_ranking(year)
    mc = load_monte_carlo()

    # Добавляем CI из Monte Carlo
    if not mc.empty:
        df = df.merge(
            mc[["iso3", "ci_lower_95", "ci_upper_95", "std_score"]],
            on="iso3", how="left"
        )

    rows = []
    for _, row in df.iterrows():
        flag = FLAG_EMOJI.get(row["iso3"], "")
        ci_str = (
            f"[{row['ci_lower_95']:.0f}–{row['ci_upper_95']:.0f}]"
            if "ci_lower_95" in row and pd.notna(row.get("ci_lower_95"))
            else "—"
        )
        rec = {
            "#":       int(row["cici_rank"]),
            "Страна":  f"{flag} {row['country']}",
            "CICI":    f"{row['cici_score']:.1f}",
            "95% CI":  ci_str,
        }
        for f in FACTOR_COLS:
            if f in row and pd.notna(row[f]):
                rec[FACTOR_LABELS.get(f, f)] = f"{row[f]:.0f}"
            else:
                rec[FACTOR_LABELS.get(f, f)] = "—"
        rows.append(rec)

    columns = [
        {"name": "#",      "id": "#",      "type": "numeric"},
        {"name": "Страна", "id": "Страна"},
        {"name": "CICI",   "id": "CICI",   "type": "numeric"},
        {"name": "95% CI", "id": "95% CI"},
    ] + [
        {"name": FACTOR_LABELS.get(f, f), "id": FACTOR_LABELS.get(f, f), "type": "numeric"}
        for f in FACTOR_COLS
    ]

    return rows, columns


def layout() -> html.Div:
    years = get_available_years()
    rows, columns = build_ranking_table_data()

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Рейтинг стран MENA", className="fw-bold mb-1"),
                html.P("Composite Investment Climate Index (CICI) — 0–100, выше = лучше",
                       className="text-muted small mb-3"),
            ], width=8),
            dbc.Col([
                dcc.Dropdown(
                    id="ranking-year-selector",
                    options=[{"label": str(y), "value": y} for y in reversed(years)],
                    value=years[-1],
                    clearable=False,
                    className="mb-3",
                )
            ], width=4),
        ]),

        dash_table.DataTable(
            id="ranking-table",
            columns=columns,
            data=rows,
            sort_action="native",
            filter_action="native",
            page_size=19,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#1a1a2e",
                "color": "white",
                "fontWeight": "bold",
                "fontSize": "13px",
                "border": "1px solid #333",
            },
            style_cell={
                "backgroundColor": "#16213e",
                "color": "#e0e0e0",
                "fontSize": "13px",
                "padding": "8px 12px",
                "border": "1px solid #2a2a4a",
                "fontFamily": "monospace",
            },
            style_data_conditional=[
                # Топ-5 — выделяем зелёным
                {"if": {"filter_query": "{#} <= 5"}, "backgroundColor": "#0d3b2e", "color": "#7fffb0"},
                # Последние 5 — выделяем красным
                {"if": {"filter_query": "{#} >= 15"}, "backgroundColor": "#3b0d0d", "color": "#ff9999"},
                # Чередование строк
                {"if": {"row_index": "odd"}, "backgroundColor": "#1a2a4a"},
            ],
            style_cell_conditional=[
                {"if": {"column_id": "#"},      "width": "40px", "textAlign": "center"},
                {"if": {"column_id": "CICI"},   "fontWeight": "bold", "color": "#ffd700"},
                {"if": {"column_id": "95% CI"}, "fontSize": "11px", "color": "#aaa"},
            ],
        ),

        dbc.Row([
            dbc.Col(html.Small([
                "🟢 Топ-5  ",
                html.Span("🔴 Аутсайдеры (15–19)  ", className="ms-2"),
                html.Span("Сортировка: клик по заголовку колонки", className="ms-2 text-muted"),
            ], className="text-muted mt-2")),
        ]),
    ], className="p-3")
