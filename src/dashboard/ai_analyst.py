"""
AI Analyst — generates GPT-4o-mini commentary for a country scorecard.
"""
import os
import pandas as pd
from src.dashboard.data_loader import FACTOR_LABELS
from src.model.build_panel import FACTOR_COLS

_ai_cache: dict[str, str] = {}

_SYSTEM_PROMPT = (
    "You are a MENA investment analyst. Write a 3-sentence terminal-style analysis of the "
    "country's investment climate. Focus on: 1) main strength, 2) main weakness, "
    "3) trajectory. Be specific, data-driven. Use numbers. No fluff."
)


def generate_country_analysis(
    iso3: str,
    row: pd.Series,
    panel: pd.DataFrame,
    factor_labels: dict,
) -> str:
    year = int(row.get("year", panel["year"].max()))
    cache_key = f"{iso3}_{year}"

    if cache_key in _ai_cache:
        return _ai_cache[cache_key]

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[AI ANALYST OFFLINE — set OPENAI_API_KEY to enable this feature.]"

    # Build year-over-year delta
    prev_year = year - 1
    prev_rows = panel[(panel["iso3"] == iso3) & (panel["year"] == prev_year)]
    if not prev_rows.empty:
        prev_score = float(prev_rows.iloc[0]["cici_score"])
        delta = float(row["cici_score"]) - prev_score
        delta_str = f"{delta:+.2f} vs {prev_year}"
    else:
        delta_str = "n/a (no prior year data)"

    # Build factor lines
    factor_lines = []
    for f in FACTOR_COLS:
        label = factor_labels.get(f, f)
        val = row.get(f, None)
        if val is not None:
            factor_lines.append(f"  {label}: {float(val):.1f}/100")

    user_message = (
        f"Country: {row.get('country', iso3)} ({iso3})\n"
        f"Year: {year}\n"
        f"CICI Score: {float(row['cici_score']):.2f}/100\n"
        f"Rank: #{int(row['cici_rank'])} of 19\n"
        f"Year-over-year delta: {delta_str}\n"
        f"\nFactor scores:\n" + "\n".join(factor_lines)
    )

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        result = response.choices[0].message.content.strip()
    except Exception as exc:
        result = f"[AI ANALYST ERROR: {exc}]"

    _ai_cache[cache_key] = result
    return result
