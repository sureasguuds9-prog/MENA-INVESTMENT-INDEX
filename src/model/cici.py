"""
Расчёт Composite Investment Climate Index (CICI).

CICI = Σ (wᵢ × Fᵢ)   где Fᵢ ∈ [0, 100], Σwᵢ = 1

Принимает панель с факторами и словарь весов.
Возвращает таблицу со скорами и рейтингом.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.config import DATA_FINAL, COUNTRY_NAMES
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS


def compute_cici(
    panel: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Считает CICI для каждой строки панели (country × year).

    Args:
        panel: DataFrame с колонками F1_institutional, F2_macro, ...
        weights: словарь весов. Если None — используются baseline weights.

    Returns:
        DataFrame с добавленной колонкой 'cici_score' и 'cici_rank'.
    """
    if weights is None:
        weights = dict(BASELINE_WEIGHTS)

    df = panel.copy()

    # Нормируем веса на случай если сумма ≠ 1
    total_w = sum(weights.values())
    w = {f: v / total_w for f, v in weights.items()}

    # Считаем взвешенную сумму
    score = pd.Series(0.0, index=df.index)
    weight_used = 0.0

    for factor, weight in w.items():
        if factor not in df.columns:
            continue
        score += df[factor].fillna(df[factor].median()) * weight
        weight_used += weight

    # Если не все факторы доступны — масштабируем
    if weight_used > 0 and weight_used < 1.0:
        score = score / weight_used * 1.0

    df["cici_score"] = score.round(2)

    # Ранг внутри каждого года (1 = лучший)
    df["cici_rank"] = (
        df.groupby("year")["cici_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    return df


def build_ranking_table(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    """
    Возвращает таблицу рейтинга для конкретного года.
    Если год не задан — берёт последний доступный.
    """
    if year is None:
        year = df["year"].max()

    latest = df[df["year"] == year].copy()
    factor_cols_available = [f for f in FACTOR_COLS if f in latest.columns]

    cols = ["cici_rank", "country", "iso3", "cici_score"] + factor_cols_available
    cols = [c for c in cols if c in latest.columns]

    return (
        latest[cols]
        .sort_values("cici_rank")
        .reset_index(drop=True)
    )


def run() -> pd.DataFrame:
    print("🏆 Расчёт CICI — старт\n")

    factors_path = DATA_FINAL / "panel_factors.csv"
    if not factors_path.exists():
        raise FileNotFoundError(
            f"Не найдена панель факторов: {factors_path}\n"
            "Сначала запусти build_panel.py"
        )

    panel = pd.read_csv(factors_path)
    print(f"  Загружено: {len(panel):,} строк")

    # Пробуем загрузить регрессионные веса
    weights_path = DATA_FINAL / "factor_weights.csv"
    if weights_path.exists():
        weights_df = pd.read_csv(weights_path)
        weights = dict(zip(weights_df["factor"], weights_df["weight_regression"]))
        print(f"  Используем регрессионные веса из {weights_path.name}")
    else:
        weights = dict(BASELINE_WEIGHTS)
        print("  ℹ️  Регрессионные веса не найдены — используем baseline")

    df = compute_cici(panel, weights)

    # Сохраняем полную панель с CICI
    full_path = DATA_FINAL / "cici_panel.csv"
    df.to_csv(full_path, index=False)
    print(f"\n✅ Полная панель: {full_path}")

    # Сохраняем последний год как ranking table
    latest_year = df["year"].max()
    ranking = build_ranking_table(df, latest_year)
    ranking_path = DATA_FINAL / f"ranking_{latest_year}.csv"
    ranking.to_csv(ranking_path, index=False)
    print(f"✅ Рейтинг {latest_year}: {ranking_path}")

    # Красивый вывод топ-19
    print(f"\n🏆 MENA Investment Climate Index — Рейтинг {latest_year}")
    print("─" * 60)
    print(f"  {'#':<4} {'Страна':<22} {'CICI':>6}  {'F1':>5} {'F2':>5} {'F3':>5} {'F4':>5} {'F5':>5}")
    print("  " + "─" * 58)

    for _, row in ranking.iterrows():
        score_bar = "█" * int(row["cici_score"] / 10)
        f1 = f"{row['F1_institutional']:.0f}" if "F1_institutional" in row and pd.notna(row.get("F1_institutional")) else " — "
        f2 = f"{row['F2_macro']:.0f}" if "F2_macro" in row and pd.notna(row.get("F2_macro")) else " — "
        f3 = f"{row['F3_openness']:.0f}" if "F3_openness" in row and pd.notna(row.get("F3_openness")) else " — "
        f4 = f"{row['F4_energy']:.0f}" if "F4_energy" in row and pd.notna(row.get("F4_energy")) else " — "
        f5 = f"{row['F5_security']:.0f}" if "F5_security" in row and pd.notna(row.get("F5_security")) else " — "
        print(
            f"  {int(row['cici_rank']):<4} {row['country']:<22} "
            f"{row['cici_score']:>5.1f}  {f1:>5} {f2:>5} {f3:>5} {f4:>5} {f5:>5}"
        )

    print("─" * 60)

    return df


if __name__ == "__main__":
    run()
