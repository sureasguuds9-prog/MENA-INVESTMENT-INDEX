"""
Панельная регрессия Fixed Effects: FDI ~ F1 + F2 + ... + F7.

Цель: получить коэффициенты β, нормировать их в веса факторов.
Модель: Two-Way Fixed Effects (country FE + year FE).
Библиотека: linearmodels.panel.PanelOLS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.config import DATA_FINAL
from src.model.build_panel import BASELINE_WEIGHTS

FACTOR_COLS = [
    "F1_institutional",
    "F2_macro",
    "F3_openness",
    "F4_energy",
    "F5_security",
    "F6_human_capital",
    "F7_financial",
]

TARGET = "fdi_pct_gdp"


def load_panel() -> pd.DataFrame:
    path = DATA_FINAL / "panel_factors.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Файл не найден: {path}\n"
            "Сначала запусти: python -m src.model.build_panel"
        )
    df = pd.read_csv(path)
    print(f"  Загружено: {len(df):,} строк, {df['iso3'].nunique()} стран")
    return df


def prepare_regression_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Подготавливает данные для PanelOLS:
    - Убирает строки без target
    - Устанавливает MultiIndex (entity, time)
    - Требует минимум 2 наблюдения на страну
    """
    df = df.copy()

    # Убираем строки без FDI (target)
    df = df.dropna(subset=[TARGET])

    # Убираем страны с менее чем 5 наблюдениями
    counts = df.groupby("iso3")[TARGET].count()
    valid_countries = counts[counts >= 5].index
    df = df[df["iso3"].isin(valid_countries)]

    # Для факторов с пропусками — заполняем медианой страны
    for f in FACTOR_COLS:
        if f in df.columns:
            df[f] = df.groupby("iso3")[f].transform(
                lambda s: s.fillna(s.median())
            )
            # Если всё ещё NaN — глобальная медиана
            df[f] = df[f].fillna(df[f].median())

    # PanelOLS требует MultiIndex (entity, time)
    df = df.set_index(["iso3", "year"])

    print(f"  После очистки: {len(df):,} строк, {df.index.get_level_values(0).nunique()} стран")
    return df


def run_panel_ols(df: pd.DataFrame) -> dict:
    """
    Запускает Two-Way Fixed Effects регрессию.
    Возвращает dict с результатами и весами факторов.
    """
    try:
        from linearmodels.panel import PanelOLS
        import warnings
        warnings.filterwarnings("ignore")

        available_factors = [f for f in FACTOR_COLS if f in df.columns]
        print(f"  Факторов в модели: {len(available_factors)}: {available_factors}")

        model = PanelOLS(
            dependent=df[TARGET],
            exog=df[available_factors],
            entity_effects=True,
            time_effects=True,
            drop_absorbed=True,
        )
        result = model.fit(cov_type="clustered", cluster_entity=True)
        return {"success": True, "result": result, "factors": available_factors}

    except ImportError:
        print("  ⚠️  linearmodels не установлен — использую OLS через statsmodels")
        return run_ols_fallback(df)
    except Exception as e:
        print(f"  ⚠️  PanelOLS ошибка: {e} — использую OLS fallback")
        return run_ols_fallback(df)


def run_ols_fallback(df: pd.DataFrame) -> dict:
    """OLS fallback если linearmodels недоступен."""
    import statsmodels.formula.api as smf

    available_factors = [f for f in FACTOR_COLS if f in df.columns]
    df_reset = df.reset_index()
    formula = f"{TARGET} ~ " + " + ".join(available_factors) + " + C(iso3)"

    result = smf.ols(formula, data=df_reset).fit()
    return {"success": True, "result": result, "factors": available_factors, "fallback": True}


def extract_weights(reg_output: dict) -> dict[str, float]:
    """
    Извлекает коэффициенты β и нормирует их в веса.
    wᵢ = |βᵢ| / Σ|βᵢ|

    Если регрессия не дала значимых коэффициентов — возвращает baseline weights.
    """
    result = reg_output["result"]
    factors = reg_output["factors"]
    is_fallback = reg_output.get("fallback", False)

    try:
        if is_fallback:
            # statsmodels result
            params = result.params
            betas = {f: params.get(f, 0.0) for f in factors}
        else:
            # linearmodels result
            params = result.params
            betas = {f: params[f] for f in factors if f in params.index}

        # Берём абсолютные значения
        abs_betas = {f: abs(b) for f, b in betas.items()}
        total = sum(abs_betas.values())

        if total == 0:
            print("  ⚠️  Все коэффициенты = 0, используем baseline weights")
            return dict(BASELINE_WEIGHTS)

        # Нормируем
        regression_weights = {f: abs_betas[f] / total for f in factors}

        # Добавляем факторы которых нет в регрессии с baseline весом
        for f in FACTOR_COLS:
            if f not in regression_weights:
                regression_weights[f] = BASELINE_WEIGHTS.get(f, 0.05)

        # Финальная нормировка
        total_all = sum(regression_weights.values())
        regression_weights = {f: w / total_all for f, w in regression_weights.items()}

        return regression_weights

    except Exception as e:
        print(f"  ⚠️  Не удалось извлечь коэффициенты ({e}), используем baseline")
        return dict(BASELINE_WEIGHTS)


def print_regression_summary(reg_output: dict, weights: dict[str, float]) -> None:
    result = reg_output["result"]
    factors = reg_output["factors"]
    is_fallback = reg_output.get("fallback", False)

    print("\n" + "─" * 55)
    print("  РЕЗУЛЬТАТЫ РЕГРЕССИИ")
    print("─" * 55)

    try:
        if is_fallback:
            r2 = result.rsquared
            params = result.params
            pvalues = result.pvalues
        else:
            r2 = result.rsquared
            params = result.params
            pvalues = result.pvalues

        print(f"  R² = {r2:.3f}")
        print(f"  Модель: {'OLS + country dummies (fallback)' if is_fallback else 'Two-Way Fixed Effects'}")
        print()
        print(f"  {'Фактор':<25} {'β':>8}  {'p-value':>8}  {'Вес':>8}  {'Знач.'}")
        print("  " + "─" * 53)

        for f in factors:
            beta = params.get(f, float("nan"))
            pval = pvalues.get(f, float("nan")) if hasattr(pvalues, "get") else float("nan")
            weight = weights.get(f, 0)
            sig = "***" if pval < 0.01 else ("**" if pval < 0.05 else ("*" if pval < 0.10 else ""))
            print(f"  {f:<25} {beta:>8.3f}  {pval:>8.3f}  {weight:>7.1%}  {sig}")

    except Exception as e:
        print(f"  (не удалось вывести детали: {e})")

    print("─" * 55)
    print()
    print("  ИТОГОВЫЕ ВЕСА ФАКТОРОВ:")
    print()
    for f in FACTOR_COLS:
        w = weights.get(f, 0)
        bar = "█" * int(w * 100 / 5)
        baseline_w = BASELINE_WEIGHTS.get(f, 0)
        delta = w - baseline_w
        delta_str = f"({'+' if delta >= 0 else ''}{delta:.1%})"
        print(f"  {f:<25} {bar:<20} {w:.1%} {delta_str}")


def run() -> dict[str, float]:
    """
    Полный цикл регрессии. Возвращает словарь весов.
    """
    print("📈 Панельная регрессия — старт\n")

    df_raw = load_panel()
    df = prepare_regression_data(df_raw)
    reg_output = run_panel_ols(df)
    weights = extract_weights(reg_output)
    print_regression_summary(reg_output, weights)

    # Сохраняем веса
    weights_df = pd.DataFrame([
        {"factor": f, "weight_regression": w, "weight_baseline": BASELINE_WEIGHTS.get(f, 0)}
        for f, w in weights.items()
    ])
    weights_path = DATA_FINAL / "factor_weights.csv"
    weights_df.to_csv(weights_path, index=False)
    print(f"\n✅ Веса сохранены: {weights_path}")

    return weights


if __name__ == "__main__":
    run()
