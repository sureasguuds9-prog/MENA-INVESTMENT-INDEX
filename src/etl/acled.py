"""
ETL: ACLED (Armed Conflict Location & Event Data)
Загружает данные о конфликтах через ACLED API.
Покрывает F5: безопасность и стабильность.

Регистрация (бесплатно): https://developer.acleddata.com/
После регистрации получи API key и email, добавь в .env:
    ACLED_EMAIL=your@email.com
    ACLED_KEY=your_api_key
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

load_dotenv()

OUTPUT_DIR = DATA_RAW / "acled"

ACLED_API_URL = "https://api.acleddata.com/acled/read"

# ACLED использует ISO3 коды стран
ACLED_COUNTRY_MAP: dict[str, str] = {
    "SAU": "Saudi Arabia",
    "ARE": "United Arab Emirates",
    "QAT": "Qatar",
    "KWT": "Kuwait",
    "BHR": "Bahrain",
    "OMN": "Oman",
    "EGY": "Egypt",
    "MAR": "Morocco",
    "TUN": "Tunisia",
    "LBY": "Libya",
    "DZA": "Algeria",
    "SDN": "Sudan",
    "IRQ": "Iraq",
    "JOR": "Jordan",
    "LBN": "Lebanon",
    "SYR": "Syria",
    "YEM": "Yemen",
    "ISR": "Israel",
    "IRN": "Iran",
}


def fetch_acled_country(
    country_name: str,
    iso3: str,
    email: str,
    api_key: str,
    year_from: int,
    year_to: int,
) -> pd.DataFrame:
    """Загружает ACLED события для одной страны."""
    params = {
        "email": email,
        "key": api_key,
        "country": country_name,
        "year": f"{year_from}|{year_to}",
        "fields": "event_date|year|event_type|country|iso3|fatalities|geo_precision",
        "limit": 0,  # без лимита
        "export_type": "csv",
    }

    try:
        response = requests.get(ACLED_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            print(f"  ⚠️  ACLED API ошибка для {country_name}: {data.get('message', 'unknown')}")
            return pd.DataFrame()

        records = data.get("data", [])
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["iso3"] = iso3
        return df

    except Exception as e:
        print(f"  ⚠️  {country_name}: {e}")
        return pd.DataFrame()


def aggregate_by_year(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегирует события ACLED по стране и году.
    Создаёт индикаторы для F5: безопасность.
    """
    if df_raw.empty:
        return pd.DataFrame()

    df_raw["year"] = pd.to_numeric(df_raw["year"], errors="coerce")
    df_raw["fatalities"] = pd.to_numeric(df_raw["fatalities"], errors="coerce").fillna(0)

    agg = df_raw.groupby(["iso3", "year"]).agg(
        conflict_events_total=("event_type", "count"),
        fatalities_total=("fatalities", "sum"),
        battles_count=("event_type", lambda x: (x == "Battles").sum()),
        violence_civilians_count=("event_type", lambda x: (x == "Violence against civilians").sum()),
        protests_count=("event_type", lambda x: (x == "Protests").sum()),
    ).reset_index()

    # Логарифмируем для уменьшения влияния экстремальных значений
    import numpy as np
    agg["conflict_log"] = np.log1p(agg["conflict_events_total"])
    agg["fatalities_log"] = np.log1p(agg["fatalities_total"])

    return agg


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("⚔️  ACLED ETL — старт")

    email = os.getenv("ACLED_EMAIL")
    api_key = os.getenv("ACLED_KEY")

    if not email or not api_key:
        print("  ⚠️  ACLED credentials не найдены в .env")
        print("  📋 Инструкция:")
        print("     1. Зарегистрируйся на https://developer.acleddata.com/")
        print("     2. Создай файл .env в корне проекта:")
        print("        ACLED_EMAIL=your@email.com")
        print("        ACLED_KEY=your_api_key")
        print("  🔄 Создаю заглушку с нулями для продолжения работы...\n")
        _create_placeholder()
        return

    all_dfs: list[pd.DataFrame] = []
    print(f"   Стран: {len(ACLED_COUNTRY_MAP)} | Период: {START_YEAR}–{END_YEAR}\n")

    for iso3, country_name in ACLED_COUNTRY_MAP.items():
        print(f"  📍 {country_name}...", end=" ", flush=True)
        df = fetch_acled_country(country_name, iso3, email, api_key, START_YEAR, END_YEAR)
        if not df.empty:
            all_dfs.append(df)
            print(f"✅ {len(df):,} событий")
        else:
            print("⚠️  нет данных")

    if not all_dfs:
        print("\n❌ Данные ACLED не получены")
        _create_placeholder()
        return

    df_combined = pd.concat(all_dfs, ignore_index=True)

    raw_path = OUTPUT_DIR / "acled_raw.csv"
    df_combined.to_csv(raw_path, index=False)
    print(f"\n  Сырые данные: {raw_path} ({len(df_combined):,} событий)")

    df_agg = aggregate_by_year(df_combined)
    df_agg["country"] = df_agg["iso3"].map(COUNTRY_NAMES)
    df_agg = df_agg.sort_values(["iso3", "year"]).reset_index(drop=True)

    out_path = OUTPUT_DIR / "acled_panel.csv"
    df_agg.to_csv(out_path, index=False)

    print(f"✅ Агрегат сохранён: {out_path}")
    print(f"   Строк: {len(df_agg):,} | Стран: {df_agg['iso3'].nunique()}")

    print(f"\n📊 Топ-5 стран по числу конфликтов (суммарно):")
    top = (
        df_agg.groupby("country")["conflict_events_total"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    for country, total in top.items():
        print(f"   {country:<20} {total:>8,} событий")


def _create_placeholder() -> None:
    """Создаёт пустую панель-заглушку чтобы pipeline не падал."""
    import itertools
    rows = [
        {"iso3": iso3, "year": year, "conflict_events_total": 0,
         "fatalities_total": 0, "battles_count": 0,
         "violence_civilians_count": 0, "protests_count": 0,
         "conflict_log": 0.0, "fatalities_log": 0.0,
         "country": COUNTRY_NAMES.get(iso3, iso3)}
        for iso3, year in itertools.product(COUNTRIES, range(START_YEAR, END_YEAR + 1))
    ]
    df = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "acled_panel.csv"
    df.to_csv(out_path, index=False)
    print(f"  📄 Заглушка создана: {out_path}")
    print("  ⚠️  F5 (безопасность) будет показывать нули до подключения ACLED API")


if __name__ == "__main__":
    run()
