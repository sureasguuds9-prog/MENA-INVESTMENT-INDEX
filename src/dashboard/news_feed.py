"""
Live news feed для MENA дашборда.
Источники: BBC Middle East, Al Jazeera — RSS без ключей.
Логика подсветки: новость считается «market-moving» если содержит
ключевые слова по теме + имеет негативный/позитивный тон.
"""
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MENA-Index/1.0)"}

RSS_FEEDS = [
    {
        "name": "BBC Middle East",
        "url":  "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "color": "#bb1919",
        "logo": "BBC",
    },
    {
        "name": "Al Jazeera",
        "url":  "https://www.aljazeera.com/xml/rss/all.xml",
        "color": "#e8a000",
        "logo": "AJ",
    },
]

# Слова по категориям — для тегов и подсветки
KEYWORD_CATEGORIES = {
    "oil":       {"oil", "opec", "petroleum", "crude", "energy", "brent", "wti", "gas", "barrel"},
    "conflict":  {"war", "strike", "attack", "military", "troops", "bomb", "missile", "ceasefire",
                  "killed", "forces", "battle", "fighting", "clash"},
    "economy":   {"gdp", "inflation", "economy", "economic", "investment", "trade", "export",
                  "import", "growth", "recession", "imf", "bank", "currency", "dollar", "sanctions"},
    "politics":  {"president", "minister", "government", "election", "coup", "agreement",
                  "treaty", "deal", "summit", "un", "biden", "trump", "diplomacy"},
    "nuclear":   {"nuclear", "uranium", "enrichment", "iaea", "weapon", "iran nuclear"},
}

# Теги стран для фильтрации по стране
COUNTRY_TAGS = {
    "SAU": ["saudi", "riyadh", "bin salman", "aramco"],
    "ARE": ["uae", "dubai", "abu dhabi", "emirates"],
    "QAT": ["qatar", "doha", "qatari"],
    "KWT": ["kuwait", "kuwaiti"],
    "BHR": ["bahrain", "manama"],
    "OMN": ["oman", "muscat"],
    "EGY": ["egypt", "cairo", "egyptian", "sisi"],
    "MAR": ["morocco", "rabat", "moroccan"],
    "TUN": ["tunisia", "tunis", "tunisian"],
    "LBY": ["libya", "tripoli", "libyan"],
    "DZA": ["algeria", "algiers", "algerian"],
    "SDN": ["sudan", "khartoum", "sudanese"],
    "IRQ": ["iraq", "baghdad", "iraqi"],
    "JOR": ["jordan", "amman", "jordanian"],
    "LBN": ["lebanon", "beirut", "lebanese", "hezbollah"],
    "SYR": ["syria", "damascus", "syrian", "assad"],
    "YEM": ["yemen", "sanaa", "yemeni", "houthi"],
    "ISR": ["israel", "jerusalem", "tel aviv", "israeli", "netanyahu", "gaza", "hamas", "idf"],
    "IRN": ["iran", "tehran", "iranian", "khamenei", "rouhani"],
}

# Ключевые слова → большое влияние на инвестиционный индекс
HIGH_IMPACT_PATTERNS = [
    (r"sanction|embargo",          "Санкции",        "danger"),
    (r"nuclear deal|nuclear agree", "Ядерная сделка", "warning"),
    (r"ceasefire|peace deal|accord","Мирное соглашение","success"),
    (r"opec.{0,20}cut|oil.{0,20}cut","Сокращение добычи","warning"),
    (r"oil.{0,20}price|crude.{0,20}price","Цены на нефть","info"),
    (r"coup|overthrow|civil war",  "Госпереворот",   "danger"),
    (r"imf.{0,20}deal|imf.{0,20}loan","МВФ кредит",  "success"),
    (r"free trade|trade agreement","Торговое соглашение","success"),
    (r"invest.{0,10}billion|billion.{0,10}invest","Крупные инвестиции","success"),
    (r"terrorist|explosion|bomb",  "Теракт",         "danger"),
    (r"protest|uprising|unrest",   "Протесты",        "warning"),
    (r"election|vote|referendum",  "Выборы",          "info"),
    (r"default|debt crisis|bankruptcy","Долговой кризис","danger"),
    (r"normalization|diplomatic",  "Дипломатия",      "info"),
]

IMPACT_COLORS = {
    "danger":  {"bg": "#3b0d0d", "border": "#e74c3c", "badge": "danger",   "label": "🔴 Высокий риск"},
    "warning": {"bg": "#2d200a", "border": "#f39c12", "badge": "warning",  "label": "🟡 Умеренный эффект"},
    "success": {"bg": "#0d2b1a", "border": "#2ecc71", "badge": "success",  "label": "🟢 Позитивный сигнал"},
    "info":    {"bg": "#0d1b2b", "border": "#3498db", "badge": "info",     "label": "🔵 Аналитика"},
}


def _get_text(el, tag: str, ns: str = "") -> str:
    child = el.find(f"{ns}{tag}")
    return (child.text or "").strip() if child is not None else ""


def _parse_date(date_str: str) -> datetime:
    try:
        return parsedate_to_datetime(date_str).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def classify_article(title: str, description: str) -> dict:
    """
    Классифицирует новость:
    - categories: список категорий (oil, conflict, economy...)
    - impact_type: danger/warning/success/info/None
    - impact_label: текстовое описание эффекта
    - countries: список ISO3 стран
    - is_market_moving: bool — подсветить ли новость
    """
    text = (title + " " + description).lower()

    # Категории
    categories = [cat for cat, words in KEYWORD_CATEGORIES.items()
                  if any(w in text for w in words)]

    # Страны
    countries = [iso3 for iso3, tags in COUNTRY_TAGS.items()
                 if any(t in text for t in tags)]

    # Ищем высокоимпактный паттерн
    impact_type  = None
    impact_label = None
    for pattern, label, itype in HIGH_IMPACT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            impact_type  = itype
            impact_label = label
            break

    is_market_moving = impact_type in ("danger", "warning", "success")

    return {
        "categories":      categories,
        "countries":       countries,
        "impact_type":     impact_type,
        "impact_label":    impact_label,
        "is_market_moving": is_market_moving,
    }


def fetch_feed(feed: dict, max_items: int = 20) -> list[dict]:
    """Загружает один RSS фид и возвращает список статей."""
    try:
        resp = requests.get(feed["url"], headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_items]

        articles = []
        for item in items:
            title   = _get_text(item, "title")
            desc    = _get_text(item, "description")
            url     = _get_text(item, "link")
            pub_raw = _get_text(item, "pubDate")
            pub_dt  = _parse_date(pub_raw)

            # Картинка из media:thumbnail если есть
            thumb = None
            for child in item:
                if "thumbnail" in child.tag.lower():
                    thumb = child.get("url")
                    break

            meta = classify_article(title, desc)

            articles.append({
                "title":           title,
                "description":     desc[:200] + "..." if len(desc) > 200 else desc,
                "url":             url,
                "pub_date":        pub_dt,
                "pub_str":         pub_dt.strftime("%d %b, %H:%M"),
                "thumbnail":       thumb,
                "source_name":     feed["name"],
                "source_color":    feed["color"],
                "source_logo":     feed["logo"],
                **meta,
            })

        return articles

    except Exception as e:
        return []


def fetch_all_news(max_per_feed: int = 20, country_filter: str | None = None) -> list[dict]:
    """
    Загружает новости из всех источников, сортирует по дате.
    Если country_filter задан (ISO3) — оставляет только релевантные.
    """
    all_articles = []
    for feed in RSS_FEEDS:
        all_articles.extend(fetch_feed(feed, max_per_feed))

    # Сортируем по дате (свежие первые)
    all_articles.sort(key=lambda a: a["pub_date"], reverse=True)

    # Фильтр по стране
    if country_filter and country_filter != "ALL":
        filtered = [a for a in all_articles if country_filter in a["countries"]]
        # Если фильтрованных < 5 — добавляем общий MENA контекст
        if len(filtered) < 5:
            mena_general = [a for a in all_articles
                            if a["countries"] and a not in filtered]
            filtered = filtered + mena_general[:10 - len(filtered)]
        all_articles = filtered

    return all_articles[:40]
