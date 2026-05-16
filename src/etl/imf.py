"""
ETL: IMF World Economic Outlook (WEO)
Загружает макро-прогнозы и исторические данные через IMF WEO bulk download.
Покрывает F2: макроэкономическая стабильность.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
import pandas as pd
import io
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

OUTPUT_DIR = DATA_RAW / "imf"

# IMF WEO коды → наши названия колонок
WEO_SUBJECTS: dict[str, str] = {
    "NGDP_RPCH":  "gdp_growth_imf",      # Real GDP growth (%)
    "PCPIPCH":    "inflation_imf",        # Inflation (average CPI %)
    "GGXWDG_NGDP": "gross_debt_pct_gdp", # General govt gross debt (% of GDP)
    "BCA_NGDPD":  "current_account_pct", # Current account balance (% of GDP)
    "LUR":        "unemployment_rate",    # Unemployment rate (%)
    "NGDPDPC":    "gdp_per_capita_imf",  # GDP per capita (current USD)
}

# Маппинг ISO3 → IMF country code (числовой)
# IMF использует собственные коды стран
IMF_COUNTRY_CODES: dict[str, str] = {
    "SAU": "456", "ARE": "466", "QAT": "453", "KWT": "443",
    "BHR": "419", "OMN": "449", "EGY": "469", "MAR": "686",
    "TUN": "744", "LBY": "672", "DZA": "612", "SDN": "732",
    "IRQ": "433", "JOR": "439", "LBN": "446", "SYR": "463",
    "YEM": "474", "ISR": "436", "IRN": "429",
}

# Обратный маппинг
IMF_CODE_TO_ISO3 = {v: k for k, v in IMF_COUNTRY_CODES.items()}

WEO_URL = "https://www.imf.org/external/pubs/ft/weo/2024/02/weodata/WEOOct2024all.xls"


def download_weo() -> pd.DataFrame:
    """Скачивает IMF WEO bulk файл и возвращает DataFrame."""
    print("  📥 Скачиваю IMF WEO bulk файл (~15MB)...")

    headers = {"User-Agent": "Mozilla/5.0 (research project)"}
    response = requests.get(WEO_URL, headers=headers, timeout=120)
    response.raise_for_status()

    # WEO файл — tab-separated, encoding latin-1
    df = pd.read_csv(
        io.StringIO(response.content.decode("latin-1")),
        sep="\t",
        low_memory=False,
    )
    return df


def parse_weo(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Парсит сырой WEO датафрейм в панельный формат."""
    # Нужные колонки: WEO Country Code, Subject Descriptor, WEO Subject Code, + годы
    year_cols = [str(y) for y in range(START_YEAR, END_YEAR + 1) if str(y) in df_raw.columns]

    # Фильтруем по нужным subject codes
    mask_subjects = df_raw["WEO Subject Code"].isin(WEO_SUBJECTS.keys())
    # Фильтруем по нужным странам
    target_imf_codes = set(IMF_COUNTRY_CODES.values())
    mask_countries = df_raw["WEO Country Code"].astype(str).isin(target_imf_codes)

    df_filtered = df_raw[mask_subjects & mask_countries].copy()

    if df_filtered.empty:
        print("  ⚠️  Фильтрация WEO вернула пустой датафрейм — проверь коды стран/индикаторов")
        return pd.DataFrame()

    records: list[dict] = []

    for _, row in df_filtered.iterrows():
        imf_code = str(int(float(row["WEO Country Code"])))
        iso3 = IMF_CODE_TO_ISO3.get(imf_code)
        if not iso3:
            continue

        subject_code = row["WEO Subject Code"]
        col_name = WEO_SUBJECTS[subject_code]

        for year_str in year_cols:
            raw_val = str(row.get(year_str, "")).strip()
            # IMF использует запятые как разделитель тысяч и "n/a" для пропусков
            raw_val = raw_val.replace(",", "").replace("--", "").replace("n/a", "")
            try:
                value = float(raw_val)
            except ValueError:
                value = None

            records.append({
                "iso3": iso3,
                "year": int(year_str),
                col_name: value,
            })

    df_long = pd.DataFrame(records)

    # Pivot: каждый subject → отдельная колонка
    df_pivot = df_long.pivot_table(
        index=["iso3", "year"],
        columns=None,
        values=list(WEO_SUBJECTS.values()),
        aggfunc="first",
    ).reset_index() if not df_long.empty else pd.DataFrame()

    # Более надёжный способ через groupby
    all_cols = list(WEO_SUBJECTS.values())
    df_panel = (
        df_long
        .groupby(["iso3", "year"])[all_cols]
        .first()
        .reset_index()
    )

    df_panel["country"] = df_panel["iso3"].map(COUNTRY_NAMES)
    return df_panel.sort_values(["iso3", "year"]).reset_index(drop=True)


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("💰 IMF WEO ETL — старт")

    try:
        df_raw = download_weo()
    except Exception as e:
        print(f"  ❌ Ошибка скачивания WEO: {e}")
        print("  💡 Скачай файл вручную: https://www.imf.org/en/Publications/WEO/weo-database/2024/October")
        print(f"     Сохрани как: {OUTPUT_DIR / 'WEOOct2024all.xls'}")
        return

    print(f"  ✅ Скачано: {len(df_raw):,} строк, {len(df_raw.columns)} колонок")

    # Сохраняем сырой файл
    raw_path = OUTPUT_DIR / "weo_raw.csv"
    df_raw.to_csv(raw_path, index=False, encoding="utf-8")

    df_panel = parse_weo(df_raw)

    if df_panel.empty:
        print("  ❌ Не удалось распарсить WEO данные")
        return

    out_path = OUTPUT_DIR / "imf_weo_panel.csv"
    df_panel.to_csv(out_path, index=False)

    print(f"\n✅ Сохранено: {out_path}")
    print(f"   Строк: {len(df_panel):,} | Стран: {df_panel['iso3'].nunique()} | Лет: {df_panel['year'].nunique()}")

    indicator_cols = [c for c in df_panel.columns if c not in ("iso3", "year", "country")]
    coverage = df_panel[indicator_cols].notna().mean() * 100
    print(f"\n📊 Покрытие по индикаторам:")
    for col, pct in coverage.items():
        bar = "█" * int(pct / 5)
        print(f"   {col:<30} {bar:<20} {pct:.1f}%")


if __name__ == "__main__":
    run()
