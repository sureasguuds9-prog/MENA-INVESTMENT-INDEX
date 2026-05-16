"""
Real-time CICI adjustments based on live market prices.
Oil price moves  → adjusts F4_energy score for oil exporters.
Gold price moves → minor adjustment for Gulf states (sovereign wealth).
USD Index moves  → affects F3_openness (trade competitiveness).
"""
import pandas as pd
import numpy as np
from src.dashboard.market_data import fetch_current_price
from src.dashboard.data_loader import load_cici_panel

# Countries whose CICI is sensitive to oil price
OIL_EXPORTERS  = {"SAU", "ARE", "QAT", "IRQ", "KWT", "IRN", "OMN", "DZA", "LBY"}
GOLD_SENSITIVE = {"SAU", "ARE", "QAT", "KWT"}
USD_SENSITIVE  = {"EGY", "TUN", "MAR", "JOR", "LBN"}  # importers / tourism


def get_live_adjustments() -> dict[str, float]:
    """
    Returns {iso3: delta} — CICI score adjustments based on current market moves.
    Delta is in CICI points (e.g. +2.3 means +2.3 points added to the base CICI score).
    Returns all-zero adjustments gracefully if Yahoo Finance is unreachable.
    """
    try:
        oil  = fetch_current_price("CL=F")
        gold = fetch_current_price("GC=F")
        usd  = fetch_current_price("DX-Y.NYB")

        oil_pct  = oil.get("change_pct", 0)  if not oil.get("error")  else 0.0
        gold_pct = gold.get("change_pct", 0) if not gold.get("error") else 0.0
        usd_pct  = usd.get("change_pct", 0)  if not usd.get("error")  else 0.0

    except Exception:
        oil_pct = gold_pct = usd_pct = 0.0

    try:
        panel = load_cici_panel()
        latest_year = panel["year"].max()
        base = panel[panel["year"] == latest_year].set_index("iso3")
    except Exception:
        return {}

    adjustments: dict[str, float] = {}
    for iso3 in base.index:
        delta = 0.0
        f4 = float(base.loc[iso3, "F4_energy"]) if "F4_energy" in base.columns else 50.0

        if iso3 in OIL_EXPORTERS:
            # Oil sensitivity scales with how energy-dependent the country is
            sensitivity = (f4 / 100.0) * 0.4  # max 0.4 CICI points per 1% oil move
            delta += oil_pct * sensitivity

        if iso3 in GOLD_SENSITIVE:
            delta += gold_pct * 0.05

        if iso3 in USD_SENSITIVE:
            # Strong USD hurts import-dependent economies
            delta -= usd_pct * 0.08

        adjustments[iso3] = round(delta, 2)

    return adjustments


def get_live_ranking() -> pd.DataFrame:
    """Returns ranking with live-adjusted CICI scores."""
    try:
        panel = load_cici_panel()
        latest_year = panel["year"].max()
        df = panel[panel["year"] == latest_year].copy()

        adjustments = get_live_adjustments()
        df["live_delta"]      = df["iso3"].map(adjustments).fillna(0)
        df["live_cici_score"] = (df["cici_score"] + df["live_delta"]).clip(0, 100)
        df["live_rank"]       = (
            df["live_cici_score"]
            .rank(ascending=False, method="min")
            .astype(int)
        )
        df["rank_change"] = df["cici_rank"] - df["live_rank"]  # positive = moved up

        return df.sort_values("live_rank")
    except Exception:
        return pd.DataFrame()
