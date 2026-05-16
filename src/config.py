from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

DATA_RAW      = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_FINAL    = BASE_DIR / "data" / "final"

# 19 MENA countries
COUNTRIES: list[str] = [
    "SAU", "ARE", "QAT", "KWT", "BHR", "OMN",  # Gulf
    "EGY", "MAR", "TUN", "LBY", "DZA", "SDN",  # North Africa
    "IRQ", "JOR", "LBN", "SYR", "YEM", "ISR",  # Levant
    "IRN",                                        # Other
]

COUNTRY_NAMES: dict[str, str] = {
    "SAU": "Saudi Arabia", "ARE": "UAE", "QAT": "Qatar",
    "KWT": "Kuwait", "BHR": "Bahrain", "OMN": "Oman",
    "EGY": "Egypt", "MAR": "Morocco", "TUN": "Tunisia",
    "LBY": "Libya", "DZA": "Algeria", "SDN": "Sudan",
    "IRQ": "Iraq", "JOR": "Jordan", "LBN": "Lebanon",
    "SYR": "Syria", "YEM": "Yemen", "ISR": "Israel",
    "IRN": "Iran",
}

START_YEAR = 2000
END_YEAR   = 2024
