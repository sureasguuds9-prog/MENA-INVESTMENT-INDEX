"""
ETL: World Bank WDI
Загружает макроэкономические и торговые индикаторы для 19 стран MENA.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import wbgapi
import pandas as pd
from tqdm import tqdm
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

OUTPUT_DIR = DATA_RAW / "worldbank"

# Индикаторы World Bank WDI
INDICATORS: dict[str, str] = {
    "NY.GDP.MKTP.CD":       "gdp_usd",           # F2: GDP (current USD)
    "NY.GDP.PCAP.CD":       "gdp_per_capita",     # F2: GDP per capita
    "NY.GDP.MKTP.KD.ZG":    "gdp_growth",         # F2: GDP growth (annual %)
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",       # TARGET: FDI net inflows (% of GDP)
    "BX.KLT.DINV.CD.WD":    "fdi_usd",            # TARGET: FDI net inflows (USD)
    "NE.TRD.GNFS.ZS":       "trade_pct_gdp",      # F3: Trade (% of GDP)
    "FP.CPI.TOTL.ZG":       "inflation_cpi",      # F2: Inflation (CPI, annual %)
    "GC.DOD.TOTL.GD.ZS":    "govt_debt_pct_gdp",  # F2: Central govt debt (% of GDP)
    "IC.BUS.EASE.XQ":       "ease_business",      # F3: Ease of Doing Business rank
    "NY.GDP.TOTL.RT.ZS":    "natural_res_rents",  # F4: Total natural resources rents (% of GDP)
    "EG.ELC.ACCS.ZS":       "electricity_access", # F4: Access to electricity (%)
    "SE.ADT.LITR.ZS":       "literacy_rate",      # F6: Literacy rate, adult (%)
    "SL.TLF.CACT.ZS":       "labor_participation",# F6: Labor force participation (%)
    "FS.AST.DOMS.GD.ZS":    "domestic_credit",    # F7: Domestic credit (% of GDP)
    "CM.MKT.LCAP.GD.ZS":    "market_cap",         # F7: Market cap of listed companies (% of GDP)
}


def fetch_indicator(indicator_code: str, col_name: str) -> pd.DataFrame:
    """Загружает один индикатор для всех стран MENA."""
    try:
        df = wbgapi.data.DataFrame(
            series=indicator_code,
            economy=COUNTRIES,
            time=range(START_YEAR, END_YEAR + 1),
            labels=False,
        )
        # wbgapi возвращает: строки=страны, столбцы=годы (YR2000, YR2001...)
        df = df.reset_index()
        df = df.rename(columns={"economy": "iso3"})

        # Разворачиваем из wide в long
        year_cols = [c for c in df.columns if str(c).startswith("YR") or str(c).isdigit()]
        df_long = df.melt(
            id_vars="iso3",
            value_vars=year_cols,
            var_name="year",
            value_name=col_name,
        )
        df_long["year"] = df_long["year"].astype(str).str.replace("YR", "").astype(int)
        df_long = df_long.dropna(subset=[col_name])
        return df_long[["iso3", "year", col_name]]

    except Exception as e:
        print(f"  ⚠️  {indicator_code} ({col_name}): {e}")
        return pd.DataFrame(columns=["iso3", "year", col_name])


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🌍 World Bank ETL — старт")
    print(f"   Стран: {len(COUNTRIES)} | Индикаторов: {len(INDICATORS)} | Период: {START_YEAR}–{END_YEAR}\n")

    all_dfs: list[pd.DataFrame] = []

    for code, name in tqdm(INDICATORS.items(), desc="Загрузка индикаторов"):
        df = fetch_indicator(code, name)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        print("❌ Данные не получены")
        return

    # Объединяем все индикаторы в одну панельную таблицу
    from functools import reduce
    panel = reduce(
        lambda left, right: pd.merge(left, right, on=["iso3", "year"], how="outer"),
        all_dfs,
    )

    # Добавляем название страны
    panel["country"] = panel["iso3"].map(COUNTRY_NAMES)

    # Сортируем
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

    # Сохраняем
    out_path = OUTPUT_DIR / "worldbank_raw.csv"
    panel.to_csv(out_path, index=False)

    print(f"\n✅ Сохранено: {out_path}")
    print(f"   Строк: {len(panel):,} | Стран: {panel['iso3'].nunique()} | Лет: {panel['year'].nunique()}")
    print(f"\n📊 Покрытие по индикаторам:")

    indicator_cols = [c for c in panel.columns if c not in ("iso3", "year", "country")]
    coverage = panel[indicator_cols].notna().mean() * 100
    for col, pct in coverage.items():
        bar = "█" * int(pct / 5)
        print(f"   {col:<25} {bar:<20} {pct:.1f}%")


if __name__ == "__main__":
    run()
