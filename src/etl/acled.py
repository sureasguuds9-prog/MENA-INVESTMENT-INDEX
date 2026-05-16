"""
ETL: Security & Conflict Indicators (замена ACLED)
Использует открытые данные World Bank без регистрации:
  - VC.IHR.PSRC.P5  : убийства на 100k населения
  - MS.MIL.XPND.GD.ZS : военные расходы % ВВП
Покрывает F5: безопасность и стабильность.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
import itertools
import wbgapi as wb
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

OUTPUT_DIR = DATA_RAW / "acled"

WB_SECURITY_INDICATORS = {
    "VC.IHR.PSRC.P5":    "homicide_rate",      # убийства на 100k
    "MS.MIL.XPND.GD.ZS": "military_exp_pct",   # военные расходы % ВВП
}


def fetch_wb_security() -> pd.DataFrame:
    """Загружает security-индикаторы из World Bank WDI."""
    dfs = []
    for code, col in WB_SECURITY_INDICATORS.items():
        try:
            raw = wb.data.DataFrame(
                code,
                economy=COUNTRIES,
                time=range(START_YEAR, END_YEAR + 1),
                labels=False,
            )
            # wide → long
            long = raw.reset_index().melt(id_vars="economy", var_name="year", value_name=col)
            long = long.rename(columns={"economy": "iso3"})
            long["year"] = long["year"].astype(str).str.replace("YR", "").astype(int)
            long = long.dropna(subset=[col])
            dfs.append(long[["iso3", "year", col]])
            print(f"  ✅ {code} ({col}): {long['iso3'].nunique()} стран, {long['year'].nunique()} лет")
        except Exception as e:
            print(f"  ⚠️  {code}: {e}")

    if not dfs:
        return pd.DataFrame()

    from functools import reduce
    panel = reduce(lambda l, r: pd.merge(l, r, on=["iso3", "year"], how="outer"), dfs)
    return panel


def build_conflict_proxies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Строит конфликтные прокси для совместимости с build_panel.py:
      conflict_log    = log(homicide_rate + 1)   — прокси насилия
      fatalities_log  = military_exp_pct          — прокси нестабильности
      conflict_events_total = homicide_rate (raw)
      fatalities_total      = military_exp_pct * 10 (scaled)
    """
    df = df.copy()

    # Заполняем пропуски медианой по стране → глобальной медианой
    for col in ["homicide_rate", "military_exp_pct"]:
        if col in df.columns:
            df[col] = df.groupby("iso3")[col].transform(lambda s: s.fillna(s.median()))
            df[col] = df[col].fillna(df[col].median())

    df["conflict_log"]            = np.log1p(df.get("homicide_rate", 0))
    df["fatalities_log"]          = df.get("military_exp_pct", 0).fillna(0)
    df["conflict_events_total"]   = df.get("homicide_rate", 0).fillna(0)
    df["fatalities_total"]        = df.get("military_exp_pct", 0).fillna(0) * 10
    df["battles_count"]           = 0
    df["violence_civilians_count"] = 0
    df["protests_count"]          = 0

    return df


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🛡️  Security ETL — старт (World Bank, без регистрации)")
    print(f"   Индикаторов: {len(WB_SECURITY_INDICATORS)} | Период: {START_YEAR}–{END_YEAR}\n")

    df = fetch_wb_security()

    if df.empty:
        print("❌ Данные не получены — создаю заглушку")
        _create_placeholder()
        return

    df = build_conflict_proxies(df)

    # Дополняем до полной панели (все страны × все годы)
    full_idx = pd.DataFrame(
        list(itertools.product(COUNTRIES, range(START_YEAR, END_YEAR + 1))),
        columns=["iso3", "year"],
    )
    df = full_idx.merge(df, on=["iso3", "year"], how="left")

    # Финальный fillna нулями для совместимости
    for col in ["conflict_log", "fatalities_log", "conflict_events_total",
                "fatalities_total", "battles_count", "violence_civilians_count", "protests_count"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
        else:
            df[col] = 0

    df["country"] = df["iso3"].map(COUNTRY_NAMES)
    df = df.sort_values(["iso3", "year"]).reset_index(drop=True)

    out_path = OUTPUT_DIR / "acled_panel.csv"
    df.to_csv(out_path, index=False)

    print(f"\n✅ Сохранено: {out_path}")
    print(f"   Строк: {len(df):,} | Стран: {df['iso3'].nunique()}")

    coverage = df[["homicide_rate", "military_exp_pct"]].notna().mean() * 100
    print(f"\n📊 Покрытие:")
    for col, pct in coverage.items():
        bar = "█" * int(pct / 5)
        print(f"   {col:<25} {bar:<20} {pct:.1f}%")


def _create_placeholder() -> None:
    rows = [
        {
            "iso3": iso3, "year": year,
            "homicide_rate": None, "military_exp_pct": None,
            "conflict_events_total": 0, "fatalities_total": 0,
            "battles_count": 0, "violence_civilians_count": 0,
            "protests_count": 0, "conflict_log": 0.0, "fatalities_log": 0.0,
            "country": COUNTRY_NAMES.get(iso3, iso3),
        }
        for iso3, year in itertools.product(COUNTRIES, range(START_YEAR, END_YEAR + 1))
    ]
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "acled_panel.csv", index=False)
    print(f"  📄 Заглушка создана: {OUTPUT_DIR / 'acled_panel.csv'}")


if __name__ == "__main__":
    run()
