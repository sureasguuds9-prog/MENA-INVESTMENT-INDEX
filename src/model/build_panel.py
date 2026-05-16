"""
Сборка финальной панели для модели.

Объединяет данные из всех источников:
  - World Bank WDI  → F2, F3, F4, F6, F7 + FDI (target)
  - WGI             → F1 (институциональное качество)
  - IMF WEO         → F2 (макро, если есть)
  - ACLED           → F5 (конфликты)

Затем собирает 7 факторных индексов и нормализует всё в [0, 100].
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW, DATA_FINAL
from src.model.normalize import normalize_all, clip_outliers, INVERT_INDICATORS


# ── Маппинг: исходный индикатор → фактор ──────────────────────────────────────

FACTOR_COMPONENTS: dict[str, list[str]] = {
    "F1_institutional": [
        "control_of_corruption",   # WGI scores 0-100
        "govt_effectiveness",
        "rule_of_law",
        "regulatory_quality",
        "voice_accountability",
        "political_stability",
    ],
    "F2_macro": [
        "gdp_growth",
        "inflation_cpi",
        "govt_debt_pct_gdp",
        "gdp_per_capita",
    ],
    "F3_openness": [
        "trade_pct_gdp",
    ],
    "F4_energy": [
        "natural_res_rents",
        "electricity_access",
    ],
    "F5_security": [
        "political_stability",          # из WGI
        "conflict_log",                 # из ACLED (нули если нет ключа)
        "fatalities_log",
    ],
    "F6_human_capital": [
        "literacy_rate",
        "labor_participation",
    ],
    "F7_financial": [
        "market_cap",
        "domestic_credit",
    ],
}

# Базовые веса (prior до регрессии)
BASELINE_WEIGHTS: dict[str, float] = {
    "F1_institutional": 0.25,
    "F2_macro":         0.20,
    "F3_openness":      0.18,
    "F4_energy":        0.15,
    "F5_security":      0.12,
    "F6_human_capital": 0.05,
    "F7_financial":     0.05,
}


# Алиасы для импорта из других модулей
FACTOR_COLS: list[str] = list(FACTOR_COMPONENTS.keys())


def load_source(path: Path, label: str) -> pd.DataFrame | None:
    """Загружает CSV, логирует статус."""
    if not path.exists():
        print(f"  ⚠️  {label}: файл не найден ({path.name}) — пропускаю")
        return None
    df = pd.read_csv(path, low_memory=False)
    print(f"  ✅ {label}: {len(df):,} строк")
    return df


def merge_sources() -> pd.DataFrame:
    """Объединяет все источники в одну панель по (iso3, year)."""
    print("\n📦 Загружаю источники данных...")

    wb   = load_source(DATA_RAW / "worldbank" / "worldbank_raw.csv",  "World Bank")
    wgi  = load_source(DATA_RAW / "wgi"       / "wgi_panel.csv",      "WGI")
    acled = load_source(DATA_RAW / "acled"    / "acled_panel.csv",    "ACLED")
    imf  = load_source(DATA_RAW / "imf"       / "imf_weo_panel.csv",  "IMF WEO")

    # Стартуем с полной сеткой country × year
    grid = pd.MultiIndex.from_product(
        [COUNTRIES, range(START_YEAR, END_YEAR + 1)],
        names=["iso3", "year"],
    ).to_frame(index=False)

    panel = grid.copy()

    for df, key_cols in [
        (wb,    ["iso3", "year"]),
        (wgi,   ["iso3", "year"]),
        (acled, ["iso3", "year"]),
        (imf,   ["iso3", "year"]),
    ]:
        if df is None:
            continue
        # Убираем дублирующие служебные колонки перед мержем
        drop_cols = [c for c in ["country"] if c in df.columns]
        df = df.drop(columns=drop_cols)
        panel = panel.merge(df, on=key_cols, how="left")

    panel["country"] = panel["iso3"].map(COUNTRY_NAMES)
    return panel


def build_factor_scores(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Для каждого фактора F1–F7:
    1. Обрезает выбросы (1–99 перцентиль)
    2. Нормализует каждый компонент в [0, 100]
    3. Берёт среднее доступных компонентов → factor score
    """
    print("\n⚙️  Строю факторные индексы...")

    all_component_cols: list[str] = []
    for components in FACTOR_COMPONENTS.values():
        all_component_cols.extend(components)

    available = [c for c in all_component_cols if c in panel.columns]

    # Клипим выбросы для числовых колонок
    for col in available:
        if panel[col].notna().sum() > 10:
            panel[col] = clip_outliers(panel[col])

    # Нормализуем все компоненты
    panel = normalize_all(panel, available)

    # Собираем факторы как среднее нормализованных компонентов
    for factor, components in FACTOR_COMPONENTS.items():
        norm_cols = [f"{c}_norm" for c in components if f"{c}_norm" in panel.columns]
        if not norm_cols:
            print(f"  ⚠️  {factor}: нет данных — заполняю 50 (нейтрально)")
            panel[factor] = 50.0
            continue

        panel[factor] = panel[norm_cols].mean(axis=1)
        coverage = panel[factor].notna().mean() * 100
        print(f"  {factor}: {len(norm_cols)} компонентов, покрытие {coverage:.0f}%")

    return panel


def fill_missing(panel: pd.DataFrame, factor_cols: list[str]) -> pd.DataFrame:
    """
    Заполняет пропуски в факторных индексах:
    1. Линейная интерполяция внутри страны (по времени)
    2. Если осталось — медиана страны
    3. Если осталось — медиана субрегиона
    """
    print("\n🔧 Заполняю пропуски...")

    for factor in factor_cols:
        before = panel[factor].isna().sum()
        # Интерполяция по времени внутри страны
        panel[factor] = (
            panel.groupby("iso3")[factor]
            .transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
        )
        # Медиана страны
        panel[factor] = panel.groupby("iso3")[factor].transform(
            lambda s: s.fillna(s.median())
        )
        after = panel[factor].isna().sum()
        if before > 0:
            print(f"  {factor}: было {before} NaN → осталось {after}")

    return panel


def run() -> pd.DataFrame:
    DATA_FINAL.mkdir(parents=True, exist_ok=True)
    print("🏗️  Build Panel — старт")

    panel = merge_sources()
    factor_cols = list(FACTOR_COMPONENTS.keys())

    panel = build_factor_scores(panel)
    panel = fill_missing(panel, factor_cols)

    # Сохраняем промежуточный файл с факторами
    factors_path = DATA_FINAL / "panel_factors.csv"
    save_cols = ["iso3", "country", "year"] + factor_cols + ["fdi_pct_gdp", "fdi_usd"]
    save_cols = [c for c in save_cols if c in panel.columns]
    panel[save_cols].to_csv(factors_path, index=False)

    print(f"\n✅ Панель с факторами: {factors_path}")
    print(f"   Строк: {len(panel):,} | Стран: {panel['iso3'].nunique()} | Лет: {panel['year'].nunique()}")

    # Краткая сводка по факторам
    print(f"\n📊 Средние факторные индексы (все страны, все годы):")
    for f in factor_cols:
        if f in panel.columns:
            mean_val = panel[f].mean()
            bar = "█" * int(mean_val / 5)
            print(f"  {f:<25} {bar:<20} {mean_val:.1f}")

    return panel


if __name__ == "__main__":
    run()
