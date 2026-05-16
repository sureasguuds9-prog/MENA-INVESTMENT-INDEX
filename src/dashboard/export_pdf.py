"""
PDF/PNG export for country scorecard report.
Uses kaleido for chart rendering, reportlab for PDF assembly.
Falls back to PNG-only if reportlab not installed.
"""
import io
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


def _fig_to_png_bytes(fig: go.Figure, width: int = 900, height: int = 400) -> bytes:
    return fig.to_image(format="png", width=width, height=height, scale=2)


def export_country_report_png(iso3: str) -> bytes:
    """
    Renders a multi-chart PNG report for a country.
    Returns raw PNG bytes of a combined image.
    """
    from src.dashboard.data_loader import load_cici_panel, load_monte_carlo, FACTOR_LABELS, FLAG_EMOJI
    from src.dashboard.layouts.scorecard import make_radar_chart, make_factor_bars, make_timeseries_chart
    from src.model.build_panel import FACTOR_COLS

    panel = load_cici_panel()
    mc = load_monte_carlo()
    latest_year = panel["year"].max()

    row = panel[(panel["iso3"] == iso3) & (panel["year"] == latest_year)]
    if row.empty:
        return b""
    row = row.iloc[0]

    radar_png  = _fig_to_png_bytes(make_radar_chart(row), 600, 400)
    bars_png   = _fig_to_png_bytes(make_factor_bars(row), 600, 300)
    trend_png  = _fig_to_png_bytes(make_timeseries_chart(panel, iso3), 900, 280)

    # Combine images vertically using PIL if available
    try:
        from PIL import Image
        imgs = [Image.open(io.BytesIO(b)) for b in [radar_png, bars_png, trend_png]]
        total_h = sum(im.height for im in imgs)
        max_w = max(im.width for im in imgs)
        combined = Image.new("RGB", (max_w, total_h), (6, 7, 13))
        y = 0
        for im in imgs:
            combined.paste(im, (0, y))
            y += im.height
        buf = io.BytesIO()
        combined.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return trend_png


def build_export_layout(iso3: str):
    """Returns a Dash layout with download button for the country report."""
    from dash import html, dcc
    return html.Div([
        dcc.Download(id="export-download"),
        html.Button(
            "⬇ EXPORT PNG",
            id="export-btn",
            style={
                "fontFamily": "var(--mono)", "fontSize": "10px",
                "background": "transparent",
                "border": "1px solid rgba(0,229,212,0.4)",
                "color": "var(--teal)", "padding": "5px 14px",
                "cursor": "pointer", "letterSpacing": "2px",
                "marginLeft": "8px",
            }
        ),
    ], style={"display": "inline-block"})
