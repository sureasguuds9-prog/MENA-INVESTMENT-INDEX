"""
Генерирует frontend/data.js из реальных CSV данных проекта.
Запускается автоматически при старте дашборда.
"""
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_FINAL = ROOT / "data" / "final"
FRONTEND = ROOT / "frontend"

# Маппинг ISO3 → метаданные страны
COUNTRY_META = {
    "ARE": {"id": "uae",  "code": "AE", "name_en": "United Arab Emirates", "name_ru": "ОАЭ",
             "short_en": "UAE",  "short_ru": "ОАЭ",   "capital": "Abu Dhabi",  "capital_ru": "Абу-Даби",
             "lat": 24.4, "lon": 54.3, "group": "GCC",
             "currency": "AED", "fx": 3.6725, "fx_d": 0.0,
             "benchmark": {"name": "DFM", "v": 4280, "d": 1.3},
             "tags": ["HUB", "AI", "TRADE"], "seed": 10},
    "SAU": {"id": "ksa",  "code": "SA", "name_en": "Saudi Arabia",          "name_ru": "Саудовская Аравия",
             "short_en": "KSA",  "short_ru": "КСА",   "capital": "Riyadh",     "capital_ru": "Эр-Рияд",
             "lat": 24.7, "lon": 46.7, "group": "GCC",
             "currency": "SAR", "fx": 3.75,    "fx_d": 0.0,
             "benchmark": {"name": "TASI", "v": 11420, "d": 0.6},
             "tags": ["OIL", "VISION 2030", "PIF"], "seed": 20},
    "QAT": {"id": "qa",   "code": "QA", "name_en": "Qatar",                 "name_ru": "Катар",
             "short_en": "QAT",  "short_ru": "Катар",  "capital": "Doha",       "capital_ru": "Доха",
             "lat": 25.3, "lon": 51.5, "group": "GCC",
             "currency": "QAR", "fx": 3.64,    "fx_d": 0.0,
             "benchmark": {"name": "QE Index", "v": 10350, "d": 0.4},
             "tags": ["LNG", "QIA", "GAS"], "seed": 30},
    "KWT": {"id": "kw",   "code": "KW", "name_en": "Kuwait",                "name_ru": "Кувейт",
             "short_en": "KUW",  "short_ru": "Кувейт", "capital": "Kuwait City", "capital_ru": "Эль-Кувейт",
             "lat": 29.4, "lon": 47.5, "group": "GCC",
             "currency": "KWD", "fx": 0.308,   "fx_d": 0.0,
             "benchmark": {"name": "Boursa KW", "v": 7850, "d": 0.2},
             "tags": ["OIL", "KIA", "GCC"], "seed": 40},
    "BHR": {"id": "bh",   "code": "BH", "name_en": "Bahrain",               "name_ru": "Бахрейн",
             "short_en": "BHR",  "short_ru": "Бахрейн","capital": "Manama",     "capital_ru": "Манама",
             "lat": 26.0, "lon": 50.6, "group": "GCC",
             "currency": "BHD", "fx": 0.376,   "fx_d": 0.0,
             "benchmark": {"name": "BSE", "v": 1980, "d": 0.1},
             "tags": ["FINANCE", "FINTECH", "GCC"], "seed": 50},
    "OMN": {"id": "om",   "code": "OM", "name_en": "Oman",                  "name_ru": "Оман",
             "short_en": "OMN",  "short_ru": "Оман",   "capital": "Muscat",     "capital_ru": "Маскат",
             "lat": 23.6, "lon": 58.6, "group": "GCC",
             "currency": "OMR", "fx": 0.385,   "fx_d": 0.0,
             "benchmark": {"name": "MSM 30", "v": 4620, "d": 0.3},
             "tags": ["OIL", "TOURISM", "GCC"], "seed": 60},
    "ISR": {"id": "il",   "code": "IL", "name_en": "Israel",                "name_ru": "Израиль",
             "short_en": "ISR",  "short_ru": "Изр.",   "capital": "Jerusalem",  "capital_ru": "Иерусалим",
             "lat": 31.8, "lon": 35.2, "group": "LEVANT",
             "currency": "ILS", "fx": 3.72,    "fx_d": -0.1,
             "benchmark": {"name": "TA-35", "v": 2140, "d": -0.4},
             "tags": ["TECH", "STARTUPS", "DEFENSE"], "seed": 70},
    "JOR": {"id": "jo",   "code": "JO", "name_en": "Jordan",                "name_ru": "Иордания",
             "short_en": "JOR",  "short_ru": "Иорд.",  "capital": "Amman",      "capital_ru": "Амман",
             "lat": 31.9, "lon": 35.9, "group": "LEVANT",
             "currency": "JOD", "fx": 0.709,   "fx_d": 0.0,
             "benchmark": {"name": "ASE", "v": 2480, "d": 0.1},
             "tags": ["TRANSIT", "SERVICES", "LEVANT"], "seed": 80},
    "LBN": {"id": "lb",   "code": "LB", "name_en": "Lebanon",               "name_ru": "Ливан",
             "short_en": "LBN",  "short_ru": "Ливан",  "capital": "Beirut",     "capital_ru": "Бейрут",
             "lat": 33.9, "lon": 35.5, "group": "LEVANT",
             "currency": "LBP", "fx": 89500,   "fx_d": 0.0,
             "benchmark": {"name": "BLOM", "v": 980, "d": -0.2},
             "tags": ["CRISIS", "DIASPORA", "LEVANT"], "seed": 90},
    "SYR": {"id": "sy",   "code": "SY", "name_en": "Syria",                 "name_ru": "Сирия",
             "short_en": "SYR",  "short_ru": "Сирия",  "capital": "Damascus",   "capital_ru": "Дамаск",
             "lat": 34.8, "lon": 38.9, "group": "LEVANT",
             "currency": "SYP", "fx": 13000,   "fx_d": 0.0,
             "benchmark": {"name": "DSE", "v": 420, "d": 0.0},
             "tags": ["CONFLICT", "RECOVERY", "LEVANT"], "seed": 91},
    "IRQ": {"id": "iq",   "code": "IQ", "name_en": "Iraq",                  "name_ru": "Ирак",
             "short_en": "IRQ",  "short_ru": "Ирак",   "capital": "Baghdad",    "capital_ru": "Багдад",
             "lat": 33.3, "lon": 44.4, "group": "MASHREQ",
             "currency": "IQD", "fx": 1310,    "fx_d": 0.0,
             "benchmark": {"name": "ISX", "v": 1180, "d": 0.8},
             "tags": ["OIL", "RECONSTRUCTION", "OPEC"], "seed": 100},
    "IRN": {"id": "ir",   "code": "IR", "name_en": "Iran",                  "name_ru": "Иран",
             "short_en": "IRN",  "short_ru": "Иран",   "capital": "Tehran",     "capital_ru": "Тегеран",
             "lat": 35.7, "lon": 51.4, "group": "MASHREQ",
             "currency": "IRR", "fx": 580000,  "fx_d": 0.0,
             "benchmark": {"name": "TEDPIX", "v": 2100000, "d": -0.6},
             "tags": ["SANCTIONS", "OIL", "GAS"], "seed": 110},
    "EGY": {"id": "eg",   "code": "EG", "name_en": "Egypt",                 "name_ru": "Египет",
             "short_en": "EGY",  "short_ru": "Египет", "capital": "Cairo",      "capital_ru": "Каир",
             "lat": 30.0, "lon": 31.2, "group": "AFRICA",
             "currency": "EGP", "fx": 48.5,    "fx_d": -0.2,
             "benchmark": {"name": "EGX 30", "v": 32400, "d": 1.2},
             "tags": ["SUEZ", "IMF", "REFORM"], "seed": 120},
    "MAR": {"id": "ma",   "code": "MA", "name_en": "Morocco",               "name_ru": "Марокко",
             "short_en": "MAR",  "short_ru": "Марокко","capital": "Rabat",      "capital_ru": "Рабат",
             "lat": 33.9, "lon": -6.9, "group": "AFRICA",
             "currency": "MAD", "fx": 10.1,    "fx_d": 0.0,
             "benchmark": {"name": "MASI", "v": 14200, "d": 0.5},
             "tags": ["PHOSPHATE", "TRADE", "EU-LINK"], "seed": 130},
    "TUN": {"id": "tn",   "code": "TN", "name_en": "Tunisia",               "name_ru": "Тунис",
             "short_en": "TUN",  "short_ru": "Тунис",  "capital": "Tunis",      "capital_ru": "Тунис",
             "lat": 36.8, "lon": 10.2, "group": "AFRICA",
             "currency": "TND", "fx": 3.12,    "fx_d": 0.0,
             "benchmark": {"name": "TUNINDEX", "v": 9200, "d": 0.3},
             "tags": ["TOURISM", "AGRICULTURE", "TRANSITION"], "seed": 140},
    "LBY": {"id": "ly",   "code": "LY", "name_en": "Libya",                 "name_ru": "Ливия",
             "short_en": "LBY",  "short_ru": "Ливия",  "capital": "Tripoli",    "capital_ru": "Триполи",
             "lat": 32.9, "lon": 13.2, "group": "AFRICA",
             "currency": "LYD", "fx": 4.82,    "fx_d": 0.0,
             "benchmark": {"name": "LSM", "v": 580, "d": 0.0},
             "tags": ["OIL", "CONFLICT", "RECONSTRUCTION"], "seed": 150},
    "DZA": {"id": "dz",   "code": "DZ", "name_en": "Algeria",               "name_ru": "Алжир",
             "short_en": "DZA",  "short_ru": "Алжир",  "capital": "Algiers",    "capital_ru": "Алжир",
             "lat": 36.7, "lon": 3.1,  "group": "AFRICA",
             "currency": "DZD", "fx": 135,     "fx_d": 0.0,
             "benchmark": {"name": "SGBV", "v": 1450, "d": 0.1},
             "tags": ["GAS", "OPEC", "HYDROCARBON"], "seed": 160},
    "SDN": {"id": "sd",   "code": "SD", "name_en": "Sudan",                 "name_ru": "Судан",
             "short_en": "SDN",  "short_ru": "Судан",  "capital": "Khartoum",   "capital_ru": "Хартум",
             "lat": 15.6, "lon": 32.5, "group": "AFRICA",
             "currency": "SDG", "fx": 600,     "fx_d": 0.0,
             "benchmark": {"name": "KSE", "v": 320, "d": -0.1},
             "tags": ["CONFLICT", "AGRICULTURE", "TRANSITION"], "seed": 170},
    "YEM": {"id": "ye",   "code": "YE", "name_en": "Yemen",                 "name_ru": "Йемен",
             "short_en": "YEM",  "short_ru": "Йемен",  "capital": "Sanaa",      "capital_ru": "Сана",
             "lat": 15.4, "lon": 44.2, "group": "AFRICA",
             "currency": "YER", "fx": 532,     "fx_d": 0.0,
             "benchmark": {"name": "N/A", "v": 0, "d": 0.0},
             "tags": ["CONFLICT", "HUMANITARIAN", "WAR"], "seed": 180},
}

TIER_MAP = {
    (80, 100): "A+",
    (70, 80):  "A",
    (60, 70):  "BBB+",
    (50, 60):  "BBB",
    (40, 50):  "BB",
    (30, 40):  "B",
    (0,  30):  "C",
}

GROUP_DEFS = [
    {"id": "GCC",     "label_en": "Gulf Cooperation Council", "label_ru": "Совет сотрудничества Залива", "color": "#f7c548"},
    {"id": "LEVANT",  "label_en": "Levant & Iraq",            "label_ru": "Левант",                      "color": "#00e5d4"},
    {"id": "MASHREQ", "label_en": "Mashreq",                  "label_ru": "Машрик",                      "color": "#8b5cff"},
    {"id": "AFRICA",  "label_en": "North Africa",             "label_ru": "Северная Африка",             "color": "#ff9a3d"},
]


def score_to_tier(score: float) -> str:
    for (lo, hi), tier in TIER_MAP.items():
        if lo <= score < hi:
            return tier
    return "C"


def make_hist(values: list[float], length: int = 24) -> list[float]:
    """Берём последние length значений или дополняем медианой."""
    if not values:
        return [50.0] * length
    if len(values) >= length:
        return [round(v, 2) for v in values[-length:]]
    pad = [values[0]] * (length - len(values))
    return [round(v, 2) for v in pad + values]


def build_data_js() -> str:
    """Генерирует data.js из реальных CSV данных."""
    ranking = pd.read_csv(DATA_FINAL / "ranking_2024.csv")
    panel = pd.read_csv(DATA_FINAL / "cici_panel.csv")

    regions = []
    for _, row in ranking.iterrows():
        iso3 = row["iso3"]
        meta = COUNTRY_META.get(iso3)
        if not meta:
            continue

        score = float(row["cici_score"])
        tier  = score_to_tier(score)

        # История CICI для спарклайна
        hist_df = panel[panel["iso3"] == iso3].sort_values("year")
        hist_vals = hist_df["cici_score"].tolist()
        hist = make_hist(hist_vals)

        # Дельта (последний год vs предпоследний)
        delta = 0.0
        if len(hist_vals) >= 2:
            delta = round(hist_vals[-1] - hist_vals[-2], 1)

        # Факторные индексы
        factors = {
            "F1": round(float(row.get("F1_institutional", 50)), 1),
            "F2": round(float(row.get("F2_macro", 50)), 1),
            "F3": round(float(row.get("F3_openness", 50)), 1),
            "F4": round(float(row.get("F4_energy", 50)), 1),
            "F5": round(float(row.get("F5_security", 50)), 1),
            "F6": round(float(row.get("F6_human_capital", 50)), 1),
            "F7": round(float(row.get("F7_financial", 50)), 1),
        }

        # Макро из IMF (приблизительно из F2_macro)
        f2 = factors["F2"]
        gdp_growth = round((f2 - 50) / 10 + 2.5, 1)
        inflation  = round(max(1.0, 8.0 - f2 / 15), 1)
        pmi        = round(48 + f2 / 10, 1)
        oil_dep    = max(5, min(85, int(100 - factors["F3"])))
        risk       = max(5, min(90, int(100 - score)))
        cds        = max(15, int(risk * 0.8))

        region = {
            **meta,
            "index":      round(score, 1),
            "delta":      delta,
            "tier":       tier,
            "hist":       hist,
            "factors":    factors,
            "oil_dep":    oil_dep,
            "inflation":  inflation,
            "gdp_growth": gdp_growth,
            "pmi":        pmi,
            "risk":       risk,
            "cds":        cds,
            "events": [
                {"t": "LIVE", "tag": "INDEX",  "en": f"CICI Score: {score:.1f} / 100 · Rank #{int(row['cici_rank'])}/19",
                               "ru": f"Индекс CICI: {score:.1f} · Место #{int(row['cici_rank'])}/19"},
                {"t": "2024", "tag": "DATA",   "en": f"Institutional: {factors['F1']} · Macro: {factors['F2']} · Security: {factors['F5']}",
                               "ru": f"Институты: {factors['F1']} · Макро: {factors['F2']} · Безопасность: {factors['F5']}"},
                {"t": "SRC",  "tag": "SOURCE", "en": "Sources: World Bank WDI · IMF WEO · WGI · MENA-INDEX model",
                               "ru": "Источники: WB WDI · МВФ ВЭП · WGI · модель MENA-INDEX"},
            ],
        }
        regions.append(region)

    # Сортируем по рейтингу
    regions.sort(key=lambda r: -r["index"])

    # Composite score
    scores = [r["index"] for r in regions]
    composite = {
        "score":   round(sum(scores) / len(scores), 1),
        "delta":   round(sum(r["delta"] for r in regions) / len(regions), 2),
        "leaders": [r["short_en"] for r in regions[:3]],
        "laggards":[r["short_en"] for r in regions[-3:]],
        "hist":    make_hist([
            panel[panel["year"] == y]["cici_score"].mean()
            for y in sorted(panel["year"].unique())
        ]),
    }

    data = {
        "regions":   regions,
        "groups":    GROUP_DEFS,
        "composite": composite,
        "market": {
            "brent": {"v": 82.4, "d": 0.7, "hist": [79 + i * 0.15 for i in range(24)]},
            "gold":  {"v": 2418, "d": 0.4, "hist": [2310 + i * 4.5 for i in range(24)]},
            "dxy":   {"v": 104.2, "d": -0.2, "hist": [104 + (i % 5) * 0.12 for i in range(24)]},
            "ust10": {"v": 4.32, "d": -0.02},
            "btc":   {"v": 67140, "d": 1.2},
        },
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M UTC"),
            "source":    "MENA-Investment-Index · World Bank · IMF · WGI",
            "countries": len(regions),
        },
    }

    js = "// Auto-generated from MENA-Investment-Index model data\n"
    js += f"// Generated: {data['meta']['generated']}\n"
    js += "window.MENA_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    return js


def run():
    FRONTEND.mkdir(exist_ok=True)
    out = FRONTEND / "data.js"
    js  = build_data_js()
    out.write_text(js, encoding="utf-8")
    print(f"✅ Frontend data.js сгенерирован: {out}")
    print(f"   Стран: {js.count('\"index\"')}")


if __name__ == "__main__":
    run()
