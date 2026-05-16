"""
ETL: IMF DataMapper API
Загружает макро-данные через официальный IMF JSON API (без авторизации).
Покрывает F2: макроэкономическая стабильность.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
import pandas as pd
from functools import reduce
from tqdm import tqdm
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

OUTPUT_DIR = DATA_RAW / "imf"

IMF_API = "https://www.imf.org/external/datamapper/api/v1/{indicator}/{countries}"

# IMF DataMapper коды → наши названия колонок
IMF_INDICATORS: dict[str, str] = {
    "NGDP_RPCH":   "gdp_growth_imf",       # Real GDP growth (%)
    "PCPIPCH":     "inflation_imf",         # Inflation, avg CPI (%)
    "GGXWDG_NGDP": "gross_debt_pct_gdp",   # Gross govt debt (% of GDP)
    "BCA_NGDPD":   "current_account_pct",  # Current account (% of GDP)
    "LUR":         "unemployment_rate",     # Unemployment rate (%)
    "NGDPDPC":     "gdp_per_capita_imf",   # GDP per capita (current USD)
}


def fetch_indicator(code: str, col_name: str) -> pd.DataFrame:
    """Загружает один индикатор для всех 19 стран через IMF DataMapper API."""
    countries_str = "/".join(COUNTRIES)
    url = IMF_API.format(indicator=code, countries=countries_str)

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        country_data = data.get("values", {}).get(code, {})
        if not country_data:
            return pd.DataFrame(columns=["iso3", "year", col_name])

        records = []
        for iso3, year_dict in country_data.items():
            if iso3 not in COUNTRIES:
                continue
            for year_str, value in year_dict.items():
                try:
                    year = int(year_str)
                    if START_YEAR <= year <= END_YEAR and value is not None:
                        records.append({"iso3": iso3, "year": year, col_name: float(value)})
                except (ValueError, TypeError):
                    pass

        return pd.DataFrame(records) if records else pd.DataFrame(columns=["iso3", "year", col_name])

    except Exception as e:
        print(f"  ⚠️  {code} ({col_name}): {e}")
        return pd.DataFrame(columns=["iso3", "year", col_name])


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("💰 IMF DataMapper ETL — старт")
    print(f"   Индикаторов: {len(IMF_INDICATORS)} | Период: {START_YEAR}–{END_YEAR}\n")

    all_dfs: list[pd.DataFrame] = []

    for code, name in tqdm(IMF_INDICATORS.items(), desc="Загрузка IMF"):
        df = fetch_indicator(code, name)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        print("❌ Данные IMF не получены")
        return

    panel = reduce(
        lambda l, r: pd.merge(l, r, on=["iso3", "year"], how="outer"),
        all_dfs,
    )
    panel["country"] = panel["iso3"].map(COUNTRY_NAMES)
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

    out_path = OUTPUT_DIR / "imf_weo_panel.csv"
    panel.to_csv(out_path, index=False)

    print(f"\n✅ Сохранено: {out_path}")
    print(f"   Строк: {len(panel):,} | Стран: {panel['iso3'].nunique()}")

    indicator_cols = [c for c in panel.columns if c not in ("iso3", "year", "country")]
    coverage = panel[indicator_cols].notna().mean() * 100
    print(f"\n📊 Покрытие:")
    for col, pct in coverage.items():
        bar = "█" * int(pct / 5)
        print(f"   {col:<25} {bar:<20} {pct:.1f}%")


if __name__ == "__main__":
    run()
