"""
ETL: World Governance Indicators (WGI)
Загружает 6 измерений качества управления через World Bank API.
Покрывает F1: институциональное качество.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
import pandas as pd
from tqdm import tqdm
from src.config import COUNTRIES, COUNTRY_NAMES, START_YEAR, END_YEAR, DATA_RAW

OUTPUT_DIR = DATA_RAW / "wgi"

# WGI индикаторы — правильные коды через source=3
# Scores в диапазоне 0–100 (удобно для нормализации)
WGI_INDICATORS: dict[str, str] = {
    "GOV_WGI_CC.SC":  "control_of_corruption",   # Control of Corruption score (0-100)
    "GOV_WGI_GE.SC":  "govt_effectiveness",       # Government Effectiveness score
    "GOV_WGI_PV.SC":  "political_stability",      # Political Stability score
    "GOV_WGI_RL.SC":  "rule_of_law",              # Rule of Law score
    "GOV_WGI_RQ.SC":  "regulatory_quality",       # Regulatory Quality score
    "GOV_WGI_VA.SC":  "voice_accountability",     # Voice & Accountability score
}

# Дублируем как "rank" для совместимости с остальным кодом
WGI_RANK_INDICATORS: dict[str, str] = {
    "GOV_WGI_CC.SC":  "control_of_corruption_rank",
    "GOV_WGI_GE.SC":  "govt_effectiveness_rank",
    "GOV_WGI_PV.SC":  "political_stability_rank",
    "GOV_WGI_RL.SC":  "rule_of_law_rank",
    "GOV_WGI_RQ.SC":  "regulatory_quality_rank",
    "GOV_WGI_VA.SC":  "voice_accountability_rank",
}

ALL_INDICATORS = {**WGI_INDICATORS}


WGI_DATA_URL = "https://api.worldbank.org/v2/sources/3/country/{country}/series/{series}/data"


def fetch_wgi_indicator(code: str, col_name: str) -> pd.DataFrame:
    """
    Загружает один WGI индикатор для всех стран MENA.
    Использует WB source=3 endpoint: /sources/3/country/{iso}/series/{code}/data
    """
    records: list[dict] = []

    for iso3 in COUNTRIES:
        url = WGI_DATA_URL.format(country=iso3, series=code)
        page = 1
        try:
            while True:
                resp = requests.get(
                    url,
                    params={"format": "json", "per_page": 100, "page": page},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                total_pages = int(data.get("pages", 1))

                source_block = data.get("source", {})
                items = source_block.get("data", []) if isinstance(source_block, dict) else []

                for item in items:
                    var_list = item.get("variable", [])
                    year_val = None
                    for v in var_list:
                        if v.get("concept") == "Time":
                            raw_id = str(v.get("id", "")).replace("YR", "")
                            try:
                                year_val = int(raw_id)
                            except ValueError:
                                pass

                    value = item.get("value")
                    if year_val and value is not None:
                        try:
                            records.append({
                                "iso3": iso3,
                                "year": year_val,
                                col_name: float(value),
                            })
                        except (ValueError, TypeError):
                            pass

                if page >= total_pages:
                    break
                page += 1

        except Exception:
            pass

    if not records:
        return pd.DataFrame(columns=["iso3", "year", col_name])

    df = pd.DataFrame(records)
    df = df[df["year"].between(START_YEAR, END_YEAR)]
    return df


def compute_composite_governance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет составной индекс институционального качества (F1).
    Среднее арифметическое перцентильных рангов 6 измерений WGI.
    """
    rank_cols = list(WGI_RANK_INDICATORS.values())
    available = [c for c in rank_cols if c in df.columns]

    if available:
        df["institutional_quality_index"] = df[available].mean(axis=1)

    return df


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("🏛️  WGI ETL — старт")
    print(f"   Индикаторов: {len(ALL_INDICATORS)} | Период: {START_YEAR}–{END_YEAR}\n")

    all_dfs: list[pd.DataFrame] = []

    for code, name in tqdm(ALL_INDICATORS.items(), desc="Загрузка WGI"):
        df = fetch_wgi_indicator(code, name)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        print("❌ Данные WGI не получены")
        return

    from functools import reduce
    panel = reduce(
        lambda left, right: pd.merge(left, right, on=["iso3", "year"], how="outer"),
        all_dfs,
    )

    panel = compute_composite_governance(panel)
    panel["country"] = panel["iso3"].map(COUNTRY_NAMES)
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)

    out_path = OUTPUT_DIR / "wgi_panel.csv"
    panel.to_csv(out_path, index=False)

    print(f"\n✅ Сохранено: {out_path}")
    print(f"   Строк: {len(panel):,} | Стран: {panel['iso3'].nunique()}")

    if "institutional_quality_index" in panel.columns:
        print(f"\n📊 Топ-5 стран по институциональному качеству (последний год):")
        latest = (
            panel[panel["year"] == panel["year"].max()]
            .sort_values("institutional_quality_index", ascending=False)
            [["country", "year", "institutional_quality_index"]]
            .head(5)
        )
        print(latest.to_string(index=False))


if __name__ == "__main__":
    run()
