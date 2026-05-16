"""
ETL: ACLED (Armed Conflict Location & Event Data)
Загружает данные о конфликтах через ACLED OAuth API.
Покрывает F5: безопасность и стабильность.

.env должен содержать:
    ACLED_EMAIL=your@email.com
    ACLED_REFRESH_TOKEN=def502...  (из первичного логина на acleddata.com)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import requests
import pandas as pd
import itertools
from dotenv import load_dotenv
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

load_dotenv()

OUTPUT_DIR = DATA_RAW / "acled"

ACLED_API_URL    = "https://acleddata.com/api/acled/read"
ACLED_TOKEN_URL  = "https://acleddata.com/oauth/token"
ACLED_CLIENT_ID  = "acled"

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


def get_access_token(refresh_token: str) -> str | None:
    """Получает новый access token через refresh token."""
    try:
        resp = requests.post(
            ACLED_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": ACLED_CLIENT_ID,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        new_refresh = data.get("refresh_token")

        # Обновляем refresh_token в .env если он изменился
        if new_refresh and new_refresh != refresh_token:
            _update_env_refresh_token(new_refresh)

        return token
    except Exception as e:
        print(f"  ⚠️  Не удалось получить access token: {e}")
        return None


def _update_env_refresh_token(new_token: str) -> None:
    """Обновляет ACLED_REFRESH_TOKEN в .env файле."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return
    lines = env_path.read_text().splitlines()
    new_lines = []
    for line in lines:
        if line.startswith("ACLED_REFRESH_TOKEN="):
            new_lines.append(f"ACLED_REFRESH_TOKEN={new_token}")
        else:
            new_lines.append(line)
    env_path.write_text("\n".join(new_lines) + "\n")


def fetch_acled_country(country_name: str, iso3: str, access_token: str) -> pd.DataFrame:
    """Загружает ACLED события для одной страны за весь период."""
    params = {
        "country": country_name,
        "year": f"{START_YEAR}|{END_YEAR}",
        "fields": "event_date|year|event_type|country|iso3|fatalities",
        "limit": 0,
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(ACLED_API_URL, params=params, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()

        if data.get("message") == "Access denied":
            print(f"  ⛔  Access denied — аккаунт не одобрен для API")
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
    """Агрегирует события ACLED по стране и году."""
    if df_raw.empty:
        return pd.DataFrame()

    import numpy as np
    df_raw["year"] = pd.to_numeric(df_raw["year"], errors="coerce")
    df_raw["fatalities"] = pd.to_numeric(df_raw["fatalities"], errors="coerce").fillna(0)

    agg = df_raw.groupby(["iso3", "year"]).agg(
        conflict_events_total=("event_type", "count"),
        fatalities_total=("fatalities", "sum"),
        battles_count=("event_type", lambda x: (x == "Battles").sum()),
        violence_civilians_count=("event_type", lambda x: (x == "Violence against civilians").sum()),
        protests_count=("event_type", lambda x: (x == "Protests").sum()),
    ).reset_index()

    agg["conflict_log"]   = np.log1p(agg["conflict_events_total"])
    agg["fatalities_log"] = np.log1p(agg["fatalities_total"])

    return agg


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("⚔️  ACLED ETL — старт")

    refresh_token = os.getenv("ACLED_REFRESH_TOKEN")

    if not refresh_token:
        print("  ⚠️  ACLED_REFRESH_TOKEN не найден в .env")
        print("  🔄 Создаю заглушку...")
        _create_placeholder()
        return

    print("  🔑 Получаю access token...")
    access_token = get_access_token(refresh_token)

    if not access_token:
        print("  ❌ Не удалось получить access token — создаю заглушку")
        _create_placeholder()
        return

    print(f"  ✅ Token получен | Стран: {len(ACLED_COUNTRY_MAP)} | Период: {START_YEAR}–{END_YEAR}\n")

    all_dfs: list[pd.DataFrame] = []
    access_denied = False

    for iso3, country_name in ACLED_COUNTRY_MAP.items():
        print(f"  📍 {country_name}...", end=" ", flush=True)
        df = fetch_acled_country(country_name, iso3, access_token)

        if not df.empty:
            all_dfs.append(df)
            print(f"✅ {len(df):,} событий")
        else:
            # Проверяем не отказ ли в доступе
            if not access_denied:
                test = _test_access(access_token)
                if not test:
                    access_denied = True
                    print(f"\n  ⛔  Аккаунт не одобрен ACLED для API доступа.")
                    print("  📧 Проверь почту sureasguuds9@gmail.com — должно прийти письмо от ACLED")
                    print("  🌐 Или зайди на acleddata.com/user и прими Terms of Use")
                    print("  🔄 Создаю заглушку и продолжаю...")
                    _create_placeholder()
                    return
            print("⚠️  нет данных")

    if not all_dfs:
        print("\n❌ Данные ACLED не получены — создаю заглушку")
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

    top = (
        df_agg.groupby("country")["conflict_events_total"]
        .sum().sort_values(ascending=False).head(5)
    )
    print(f"\n📊 Топ-5 стран по конфликтам:")
    for country, total in top.items():
        print(f"   {country:<20} {total:>8,} событий")


def _test_access(access_token: str) -> bool:
    """Быстрая проверка что API доступ одобрен."""
    try:
        resp = requests.get(
            ACLED_API_URL,
            params={"country": "Egypt", "year": "2020", "limit": "1"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        data = resp.json()
        return data.get("message") != "Access denied"
    except Exception:
        return False


def _create_placeholder() -> None:
    rows = [
        {
            "iso3": iso3, "year": year,
            "conflict_events_total": 0, "fatalities_total": 0,
            "battles_count": 0, "violence_civilians_count": 0,
            "protests_count": 0, "conflict_log": 0.0, "fatalities_log": 0.0,
            "country": COUNTRY_NAMES.get(iso3, iso3),
        }
        for iso3, year in itertools.product(COUNTRIES, range(START_YEAR, END_YEAR + 1))
    ]
    df = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "acled_panel.csv"
    df.to_csv(out_path, index=False)
    print(f"  📄 Заглушка создана: {out_path}")
    print("  ⚠️  F5 (безопасность) будет нулевым до одобрения ACLED API доступа")


if __name__ == "__main__":
    run()
