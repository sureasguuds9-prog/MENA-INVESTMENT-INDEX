"""
Нормализация факторов в диапазон [0, 100].
- Позитивные индикаторы: выше = лучше → прямая нормализация
- Негативные индикаторы: выше = хуже → инвертирование
"""
import pandas as pd
import numpy as np


# Индикаторы где ВЫШЕ = ХУЖЕ → нужно инвертировать
INVERT_INDICATORS: set[str] = {
    "inflation_cpi",
    "inflation_imf",
    "govt_debt_pct_gdp",
    "gross_debt_pct_gdp",
    "conflict_events_total",
    "fatalities_total",
    "conflict_log",
    "fatalities_log",
    "battles_count",
    "violence_civilians_count",
}


def minmax_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-Max нормализация в [0, 100]. Пропуски сохраняются как NaN."""
    s_min = series.min()
    s_max = series.max()

    if s_max == s_min:
        return pd.Series(50.0, index=series.index)

    normalized = (series - s_min) / (s_max - s_min) * 100

    if invert:
        normalized = 100 - normalized

    return normalized


def normalize_all(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Нормализует список колонок.
    Нормализация происходит ПОПЕРЁК ВСЕХ СТРАН И ЛЕТ (cross-sectional + temporal).
    Это даёт сопоставимость как между странами, так и во времени.
    """
    df_out = df.copy()

    for col in cols:
        if col not in df.columns:
            continue

        invert = col in INVERT_INDICATORS
        df_out[f"{col}_norm"] = minmax_normalize(df[col], invert=invert)

    return df_out


def clip_outliers(series: pd.Series, lower_pct: float = 1.0, upper_pct: float = 99.0) -> pd.Series:
    """
    Обрезает выбросы по перцентилям перед нормализацией.
    Важно для инфляции (Иран, Сирия) и конфликтных данных (Йемен, Сирия).
    """
    lower = np.percentile(series.dropna(), lower_pct)
    upper = np.percentile(series.dropna(), upper_pct)
    return series.clip(lower=lower, upper=upper)
