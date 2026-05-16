"""
Backtesting модели CICI.

Схема:
  - Обучение регрессии на 2000–2018
  - Прогноз FDI на 2019–2023 через CICI score
  - Метрики: RMSE, MAE, Spearman rank correlation

Цель по ТЗ: Spearman ρ > 0.75
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from scipy import stats
from src.config import DATA_FINAL
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS
from src.model.cici import compute_cici

TRAIN_END  = 2018
TEST_START = 2019
TEST_END   = 2023


def run() -> dict:
    print("🔬 Backtesting — старт")
    print(f"   Train: 2000–{TRAIN_END} | Test: {TEST_START}–{TEST_END}\n")

    panel_path = DATA_FINAL / "panel_factors.csv"
    if not panel_path.exists():
        raise FileNotFoundError(f"Нет панели: {panel_path}")

    panel = pd.read_csv(panel_path)

    if "fdi_pct_gdp" not in panel.columns:
        print("  ⚠️  Нет колонки fdi_pct_gdp — backtesting невозможен")
        return {}

    # Разбиваем на train/test
    train = panel[panel["year"] <= TRAIN_END].copy()
    test  = panel[(panel["year"] >= TEST_START) & (panel["year"] <= TEST_END)].copy()

    print(f"  Train: {len(train):,} строк | Test: {len(test):,} строк")

    # ── Шаг 1: Регрессия на train ──────────────────────────────────────────────
    weights = _fit_weights_on_train(train)

    # ── Шаг 2: Считаем CICI на test ───────────────────────────────────────────
    test_with_cici = compute_cici(test, weights)

    # ── Шаг 3: Корреляция CICI ~ реальный FDI ─────────────────────────────────
    valid = test_with_cici.dropna(subset=["fdi_pct_gdp", "cici_score"])

    if len(valid) < 10:
        print("  ⚠️  Недостаточно данных для оценки (нужно ≥ 10 строк с FDI)")
        return {}

    actual  = valid["fdi_pct_gdp"].values
    pred    = valid["cici_score"].values

    # Spearman (ранговая корреляция — главная метрика рейтинга)
    spearman_r, spearman_p = stats.spearmanr(actual, pred)

    # Pearson (линейная)
    pearson_r, pearson_p = stats.pearsonr(actual, pred)

    # RMSE / MAE (масштаб условный — CICI в [0,100], FDI в % ВВП)
    # Нормализуем actual в [0,100] для сопоставимости
    act_norm = (actual - actual.min()) / (actual.max() - actual.min()) * 100
    rmse = np.sqrt(np.mean((act_norm - pred) ** 2))
    mae  = np.mean(np.abs(act_norm - pred))

    # Ранговая точность по годам
    yearly_spearman = _yearly_spearman(valid)

    metrics = {
        "spearman_r":   round(spearman_r, 3),
        "spearman_p":   round(spearman_p, 4),
        "pearson_r":    round(pearson_r, 3),
        "pearson_p":    round(pearson_p, 4),
        "rmse":         round(rmse, 2),
        "mae":          round(mae, 2),
        "n_obs":        len(valid),
        "yearly":       yearly_spearman,
    }

    _print_backtest_results(metrics)

    # Сохраняем
    out_df = pd.DataFrame([{k: v for k, v in metrics.items() if k != "yearly"}])
    out_df.to_csv(DATA_FINAL / "backtest_metrics.csv", index=False)

    yearly_df = pd.DataFrame(yearly_spearman)
    yearly_df.to_csv(DATA_FINAL / "backtest_yearly.csv", index=False)

    print(f"\n✅ Метрики: {DATA_FINAL / 'backtest_metrics.csv'}")

    return metrics


def _fit_weights_on_train(train: pd.DataFrame) -> dict[str, float]:
    """Быстрая оценка весов через OLS на обучающей выборке."""
    try:
        import statsmodels.formula.api as smf

        available = [f for f in FACTOR_COLS if f in train.columns]
        train_clean = train.dropna(subset=["fdi_pct_gdp"] + available)

        if len(train_clean) < 20:
            print("  ⚠️  Мало данных для регрессии на train — используем baseline")
            return dict(BASELINE_WEIGHTS)

        formula = "fdi_pct_gdp ~ " + " + ".join(available) + " + C(iso3)"
        result = smf.ols(formula, data=train_clean).fit()

        betas = {f: abs(result.params.get(f, 0)) for f in available}
        total = sum(betas.values())

        if total == 0:
            return dict(BASELINE_WEIGHTS)

        weights = {f: betas[f] / total for f in available}
        # Добавляем пропущенные с baseline
        for f in FACTOR_COLS:
            if f not in weights:
                weights[f] = BASELINE_WEIGHTS.get(f, 0.05)
        total_all = sum(weights.values())
        return {f: w / total_all for f, w in weights.items()}

    except Exception as e:
        print(f"  ⚠️  Регрессия на train упала ({e}) — baseline")
        return dict(BASELINE_WEIGHTS)


def _yearly_spearman(df: pd.DataFrame) -> list[dict]:
    """Считает Spearman ρ отдельно для каждого тестового года."""
    results = []
    for year in sorted(df["year"].unique()):
        yr = df[df["year"] == year].dropna(subset=["fdi_pct_gdp", "cici_score"])
        if len(yr) < 5:
            continue
        rho, p = stats.spearmanr(yr["fdi_pct_gdp"], yr["cici_score"])
        results.append({"year": year, "spearman_r": round(rho, 3), "p_value": round(p, 4), "n": len(yr)})
    return results


def _print_backtest_results(metrics: dict) -> None:
    target_met = "✅" if metrics["spearman_r"] >= 0.75 else "❌"

    print("\n" + "─" * 50)
    print("  РЕЗУЛЬТАТЫ BACKTESTING")
    print("─" * 50)
    print(f"  Наблюдений:          {metrics['n_obs']}")
    print(f"  Spearman ρ:          {metrics['spearman_r']:>6.3f}  (p={metrics['spearman_p']:.4f})  {target_met} (цель ≥ 0.75)")
    print(f"  Pearson r:           {metrics['pearson_r']:>6.3f}  (p={metrics['pearson_p']:.4f})")
    print(f"  RMSE (норм.):        {metrics['rmse']:>6.2f}")
    print(f"  MAE  (норм.):        {metrics['mae']:>6.2f}")
    print("─" * 50)

    if metrics.get("yearly"):
        print("\n  Spearman ρ по годам:")
        for yr in metrics["yearly"]:
            sig = "✅" if yr["spearman_r"] >= 0.75 else ("🟡" if yr["spearman_r"] >= 0.5 else "❌")
            print(f"    {yr['year']}: ρ = {yr['spearman_r']:.3f}  (n={yr['n']})  {sig}")


if __name__ == "__main__":
    run()
