"""
Monte Carlo Sensitivity Analysis.

Запускает N симуляций с рандомными весами вблизи baseline.
Цель: оценить устойчивость рейтинга стран к выбору весов.
Выход: bootstrap 95% CI для CICI каждой страны и матрица ранговой устойчивости.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.config import DATA_FINAL
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS
from src.model.cici import compute_cici

N_SIMULATIONS = 5_000
NOISE_LEVEL = 0.3    # ±30% от базового веса
RANDOM_SEED = 42


def sample_weights(
    baseline: dict[str, float],
    noise: float = NOISE_LEVEL,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Генерирует случайные веса с равномерным шумом вокруг baseline."""
    if rng is None:
        rng = np.random.default_rng()

    factors = list(baseline.keys())
    base_vals = np.array([baseline[f] for f in factors])

    # Умножаем на случайный множитель из [1-noise, 1+noise]
    multipliers = rng.uniform(1 - noise, 1 + noise, size=len(factors))
    raw = base_vals * multipliers

    # Зануляем отрицательные (если шум большой)
    raw = np.clip(raw, 0, None)

    # Нормируем в сумму 1
    total = raw.sum()
    if total == 0:
        raw = base_vals.copy()
        total = raw.sum()

    return dict(zip(factors, raw / total))


def run(n: int = N_SIMULATIONS) -> dict:
    print(f"🎲 Monte Carlo Sensitivity Analysis")
    print(f"   Симуляций: {n:,} | Шум: ±{NOISE_LEVEL*100:.0f}%\n")

    panel_path = DATA_FINAL / "panel_factors.csv"
    if not panel_path.exists():
        raise FileNotFoundError(f"Нет панели: {panel_path}")

    panel = pd.read_csv(panel_path)

    # Пробуем регрессионные веса как baseline
    weights_path = DATA_FINAL / "factor_weights.csv"
    if weights_path.exists():
        w_df = pd.read_csv(weights_path)
        baseline = dict(zip(w_df["factor"], w_df["weight_regression"]))
    else:
        baseline = dict(BASELINE_WEIGHTS)

    latest_year = panel["year"].max()
    panel_latest = panel[panel["year"] == latest_year].copy()
    countries = panel_latest["iso3"].tolist()

    rng = np.random.default_rng(RANDOM_SEED)

    # Матрица результатов: строки = симуляции, колонки = страны
    scores_matrix = np.zeros((n, len(countries)))
    ranks_matrix  = np.zeros((n, len(countries)), dtype=int)

    print(f"  Запускаю {n:,} симуляций...", end=" ", flush=True)

    for i in range(n):
        w = sample_weights(baseline, rng=rng)
        df_sim = compute_cici(panel_latest.copy(), w)
        df_sim = df_sim.set_index("iso3")

        for j, iso3 in enumerate(countries):
            if iso3 in df_sim.index:
                scores_matrix[i, j] = df_sim.loc[iso3, "cici_score"]
                ranks_matrix[i, j]  = df_sim.loc[iso3, "cici_rank"]

    print(f"готово ✅")

    # Считаем статистики
    ci_lower = np.percentile(scores_matrix, 2.5, axis=0)
    ci_upper = np.percentile(scores_matrix, 97.5, axis=0)
    mean_scores = scores_matrix.mean(axis=0)
    std_scores  = scores_matrix.std(axis=0)
    median_rank = np.median(ranks_matrix, axis=0).astype(int)

    # Ранговая устойчивость: % симуляций где страна в топ-5
    top5_pct = (ranks_matrix <= 5).mean(axis=0) * 100

    results_df = pd.DataFrame({
        "iso3":           countries,
        "mean_score":     mean_scores.round(2),
        "ci_lower_95":    ci_lower.round(2),
        "ci_upper_95":    ci_upper.round(2),
        "std_score":      std_scores.round(2),
        "median_rank":    median_rank,
        "top5_pct":       top5_pct.round(1),
    })

    # Добавляем названия стран
    from src.config import COUNTRY_NAMES
    results_df["country"] = results_df["iso3"].map(COUNTRY_NAMES)
    results_df = results_df.sort_values("mean_score", ascending=False).reset_index(drop=True)
    results_df.insert(0, "rank_stable", range(1, len(results_df) + 1))

    # Сохраняем
    out_path = DATA_FINAL / "monte_carlo_results.csv"
    results_df.to_csv(out_path, index=False)

    print(f"\n✅ Результаты: {out_path}")
    _print_mc_summary(results_df)

    return {"results": results_df, "scores_matrix": scores_matrix, "ranks_matrix": ranks_matrix}


def _print_mc_summary(df: pd.DataFrame) -> None:
    print(f"\n📊 Устойчивость рейтинга (Monte Carlo 95% CI, {N_SIMULATIONS:,} симуляций)")
    print("─" * 72)
    print(f"  {'#':<4} {'Страна':<22} {'Ср. CICI':>8}  {'95% CI':>16}  {'±':>5}  {'Top-5%':>6}")
    print("  " + "─" * 70)

    for _, row in df.iterrows():
        ci_str = f"[{row['ci_lower_95']:.1f} – {row['ci_upper_95']:.1f}]"
        std_str = f"±{row['std_score']:.1f}"
        top5 = f"{row['top5_pct']:.0f}%"
        print(
            f"  {int(row['rank_stable']):<4} {row['country']:<22} "
            f"{row['mean_score']:>8.1f}  {ci_str:>16}  {std_str:>5}  {top5:>6}"
        )

    print("─" * 72)
    print()

    # Флагаем нестабильные позиции (широкий CI)
    unstable = df[df["std_score"] > 10]
    if not unstable.empty:
        print(f"  ⚠️  Нестабильные позиции (std > 10): {', '.join(unstable['country'].tolist())}")
        print("      Их рейтинг сильно зависит от выбора весов — интерпретировать с осторожностью")


if __name__ == "__main__":
    run()
