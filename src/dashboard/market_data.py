"""
Рыночные данные в реальном времени через Yahoo Finance (без API ключей).
BTC, нефть (WTI), золото, курсы валют.
"""
import requests
import pandas as pd
from datetime import datetime, timezone

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MENA-Index/1.0)"}

TICKERS = {
    "BTC-USD":  {"label": "Bitcoin",       "unit": "USD",  "color": "#f7931a", "emoji": "₿"},
    "CL=F":     {"label": "Нефть WTI",     "unit": "USD",  "color": "#2ecc71", "emoji": "🛢️"},
    "GC=F":     {"label": "Золото",        "unit": "USD",  "color": "#ffd700", "emoji": "🥇"},
    "EURUSD=X": {"label": "EUR/USD",       "unit": "",     "color": "#3498db", "emoji": "€"},
    "DX-Y.NYB": {"label": "USD Index",     "unit": "",     "color": "#e74c3c", "emoji": "💵"},
}

COMPARE_TICKERS = {
    "BTC-USD":  {"label": "Bitcoin",    "color": "#f7931a"},
    "CL=F":     {"label": "Нефть WTI", "color": "#2ecc71"},
    "GC=F":     {"label": "Золото",    "color": "#ffd700"},
    "ETH-USD":  {"label": "Ethereum",  "color": "#627eea"},
    "^GSPC":    {"label": "S&P 500",   "color": "#e74c3c"},
    "EURUSD=X": {"label": "EUR/USD",   "color": "#3498db"},
}

INTERVAL_OPTIONS = [
    {"label": "1 день",   "value": "1d",  "range": "1mo"},
    {"label": "1 неделя", "value": "1wk", "range": "6mo"},
    {"label": "1 месяц",  "value": "1mo", "range": "2y"},
    {"label": "1 год",    "value": "3mo", "range": "10y"},
]


def fetch_ticker(ticker: str, interval: str = "1d", range_: str = "1mo") -> pd.DataFrame:
    """Загружает исторические данные одного тикера."""
    try:
        url = YAHOO_URL.format(ticker=ticker)
        params = {"interval": interval, "range": range_}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(timestamps, unit="s", utc=True),
            "close": closes,
        }).dropna()

        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
        return df

    except Exception as e:
        return pd.DataFrame(columns=["timestamp", "close"])


def fetch_current_price(ticker: str) -> dict:
    """Загружает текущую цену + дневное изменение."""
    try:
        url = YAHOO_URL.format(ticker=ticker)
        params = {"interval": "1d", "range": "2d"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()

        result = data["chart"]["result"][0]
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]

        if len(closes) < 2:
            return {"price": closes[-1] if closes else 0, "change_pct": 0, "error": False}

        price = closes[-1]
        prev  = closes[-2]
        change_pct = (price - prev) / prev * 100

        return {"price": price, "change_pct": change_pct, "error": False}
    except Exception:
        return {"price": 0, "change_pct": 0, "error": True}


def fetch_all_prices() -> dict:
    """Загружает текущие цены всех тикеров."""
    return {ticker: fetch_current_price(ticker) for ticker in TICKERS}


def fetch_compare_data(tickers: list[str], interval: str = "1d", range_: str = "1mo") -> dict[str, pd.DataFrame]:
    """Загружает данные для сравнительного графика (нормировано к 100)."""
    result = {}
    for ticker in tickers:
        df = fetch_ticker(ticker, interval, range_)
        if not df.empty:
            base = df["close"].iloc[0]
            if base and base != 0:
                df["normalized"] = df["close"] / base * 100
            else:
                df["normalized"] = 100
            result[ticker] = df
    return result
