"""
Загрузка и кэширование данных для дашборда.
Все модули берут данные отсюда — единая точка входа.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from src.config import DATA_FINAL
from src.model.build_panel import FACTOR_COLS, BASELINE_WEIGHTS

_cache: dict = {}


def load_cici_panel() -> pd.DataFrame:
    if "panel" not in _cache:
        path = DATA_FINAL / "cici_panel.csv"
        _cache["panel"] = pd.read_csv(path)
    return _cache["panel"]


def load_ranking(year: int | None = None) -> pd.DataFrame:
    panel = load_cici_panel()
    if year is None:
        year = panel["year"].max()
    df = panel[panel["year"] == year].copy()
    df = df.sort_values("cici_rank").reset_index(drop=True)
    return df


def load_monte_carlo() -> pd.DataFrame:
    if "mc" not in _cache:
        path = DATA_FINAL / "monte_carlo_results.csv"
        _cache["mc"] = pd.read_csv(path) if path.exists() else pd.DataFrame()
    return _cache["mc"]


def load_weights() -> dict[str, float]:
    if "weights" not in _cache:
        path = DATA_FINAL / "factor_weights.csv"
        if path.exists():
            df = pd.read_csv(path)
            _cache["weights"] = dict(zip(df["factor"], df["weight_regression"]))
        else:
            _cache["weights"] = dict(BASELINE_WEIGHTS)
    return _cache["weights"]


def get_available_years() -> list[int]:
    panel = load_cici_panel()
    return sorted(panel["year"].unique().tolist())


FACTOR_LABELS: dict[str, str] = {
    "F1_institutional": "Институты",
    "F2_macro":         "Макроэкономика",
    "F3_openness":      "Открытость",
    "F4_energy":        "Энергоресурсы",
    "F5_security":      "Безопасность",
    "F6_human_capital": "Чел. капитал",
    "F7_financial":     "Финансы",
}

SCORE_COLOR_SCALE = [
    [0.0,  "#d73027"],
    [0.25, "#f46d43"],
    [0.5,  "#fee090"],
    [0.75, "#74add1"],
    [1.0,  "#313695"],
]

FLAG_EMOJI: dict[str, str] = {
    "SAU": "🇸🇦", "ARE": "🇦🇪", "QAT": "🇶🇦", "KWT": "🇰🇼",
    "BHR": "🇧🇭", "OMN": "🇴🇲", "EGY": "🇪🇬", "MAR": "🇲🇦",
    "TUN": "🇹🇳", "LBY": "🇱🇾", "DZA": "🇩🇿", "SDN": "🇸🇩",
    "IRQ": "🇮🇶", "JOR": "🇯🇴", "LBN": "🇱🇧", "SYR": "🇸🇾",
    "YEM": "🇾🇪", "ISR": "🇮🇱", "IRN": "🇮🇷",
}
