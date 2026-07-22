"""
Human + Banking + Tech Navigator — News collector
Fetches AI in financial services news from Google News RSS
and saves results to noticias.json, preserving historical items.

Categories:
  Signal Board: banca_trad, neobancos, cripto, pagos, latam
  Pillars:      impacto, liderazgo, habilidades
"""

import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ── Queries per category and language ──────────────────────────────────────

CATEGORY_QUERIES: dict[str, dict[str, list[str]]] = {

    # ── SIGNAL BOARD ──────────────────────────────────────────────────────

    "banca_trad": {
        "en": [
            "AI traditional banking transformation 2025",
            "artificial intelligence bank credit risk automation",
            "AI banking operations technology financial",
        ],
        "es": [
            "inteligencia artificial banca tradicional 2025",
            "IA transformacion digital banco Colombia",
            "inteligencia artificial credito riesgo operaciones bancarias",
        ],
    },

    "neobancos": {
        "en": [
            "neobank AI fintech 2025",
            "digital bank artificial intelligence product innovation",
            "fintech challenger bank AI Latin America",
        ],
        "es": [
            "neobanco inteligencia artificial fintech Latinoamerica 2025",
            "banco digital IA Colombia Panama innovacion",
            "fintech IA expansion America Latina",
        ],
    },

    "cripto": {
        "en": [
            "crypto AI blockchain banking 2025",
            "artificial intelligence cryptocurrency institutional adoption",
            "blockchain AI financial services regulation",
        ],
        "es": [
            "criptoactivos inteligencia artificial regulacion 2025",
            "blockchain IA banco Colombia Panama Salvador",
            "criptomonedas inteligencia artificial America Latina",
        ],
    },

    "pagos": {
        "en": [
            "AI payment systems digital wallets 2025",
            "artificial intelligence fraud detection payments banking",
            "real-time payments AI instant banking",
        ],
        "es": [
            "inteligencia artificial medios de pago digitales 2025",
            "IA deteccion fraude pagos banco Colombia",
            "pagos instantaneos inteligencia artificial billetera digital",
        ],
    },

    "latam": {
        "en": [
            "AI banking Latin America Colombia Panama 2025",
            "fintech regulation El Salvador Guatemala Miami artificial intelligence",
            "artificial intelligence financial inclusion Latin America",
        ],
        "es": [
            "inteligencia artificial banca Colombia Panama El Salvador Guatemala 2025",
            "IA fintech regulacion America Latina inclusion financiera",
            "transformacion digital banco Miami expansion latinoamerica",
        ],
    },

    # ── PILLARS ───────────────────────────────────────────────────────────

    "impacto": {
        "en": [
            "AI impact banking jobs workforce future 2025",
            "artificial intelligence replace financial roles automation",
            "AI transformation C-suite banking executives impact",
        ],
        "es": [
            "impacto inteligencia artificial empleos banca sector financiero 2025",
            "IA reemplazar roles trabajadores banco automatizacion",
            "transformacion inteligencia artificial alta direccion banca",
        ],
    },

    "liderazgo": {
        "en": [
            "AI leadership banking executives strategy 2025",
            "CEO CFO artificial intelligence strategy financial sector",
            "AI C-suite human-centered leadership banking",
        ],
        "es": [
            "liderazgo inteligencia artificial banca directivos alta gerencia 2025",
            "CEO CFO estrategia inteligencia artificial banco",
            "liderazgo humano IA sector financiero habilidades directivos",
        ],
    },

    "habilidades": {
        "en": [
            "AI skills upskilling reskilling banking professionals 2025",
            "artificial intelligence technical skills finance workers",
            "AI literacy financial sector learning development",
        ],
        "es": [
            "habilidades inteligencia artificial profesionales banca 2025",
            "capacitacion IA upskilling reskilling sector financiero",
            "competencias digitales inteligencia artificial banco Colombia",
        ],
    },
}

# ── Direct RSS feeds ───────────────────────────────────────────────────────

DIRECT_FEEDS = [
    # Banking/fintech English
    {"url": "https://thefinancialbrand.com/feed/",      "category": "banca_trad", "lang": "en"},
    {"url": "https://www.pymnts.com/feed/",             "category": "pagos",      "lang": "en"},
    {"url": "https://fintechnews.org/feed/",            "category": "neobancos",  "lang": "en"},
    # Research / impact
    {"url": "https://arxiv.org/rss/cs.AI",              "category": "impacto",    "lang": "en"},
    {"url": "https://arxiv.org/rss/econ.GN",            "category": "liderazgo",  "lang": "en"},
    # Spanish LatAm
    {"url": "https://www.technologyreview.es/feed/",    "category": "latam",      "lang": "es"},
    {"url": "https://hipertextual.com/feed",            "category": "habilidades","lang": "es"},
]

# Keywords to filter direct feeds
BANKING_KEYWORDS_EN = [
    "bank", "banking", "fintech", "financial", "payment", "credit",
    "artificial intelligence", "AI", "machine learning", "automation",
    "digital", "crypto", "blockchain", "neobank", "leader", "executive",
]

BANKING_KEYWORDS_ES = [
    "banco", "banca", "fintech", "financiero", "pago", "credito",
    "inteligencia artificial", " ia ", "machine learning", "automatizacion",
    "digital", "cripto", "blockchain", "neobanco", "lider", "directivo",
]

# ── Constants ──────────────────────────────────────────────────────────────

MAX_ITEMS_PER_QUERY    = 12
MAX_ITEMS_PER_CATEGORY = 60
OUTPUT_FILE            = "noticias.json"

GOOGLE_NEWS_LOCALES = {
    "en": "hl=en-US&gl=US&ceid=US:en",
    "es": "hl=es-419&gl=US&ceid=US:es-419",
}


# ── Fetching ───────────────────────────────────────────────────────────────

def fetch_google_news(query: str, category: str, lang: str) -> list[dict]:
    query = query.replace("2025", str(datetime.now(timezone.utc).year))
    locale  = GOOGLE_NEWS_LOCALES.get(lang, GOOGLE_NEWS_LOCALES["en"])
    encoded = urllib.parse.quote(query)
    url     = f"https://news.google.com/rss/search?q={encoded}&{locale}"
    req     = urllib.request.Request(url, headers={"User-Agent": "HBTNavigator/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    return _parse_rss(raw, category, lang, source_query=query)


def fetch_direct(
    url: str, category: str, lang: str, keywords: list[str]
) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "HBTNavigator/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    items = _parse_rss(raw, category, lang, source_query=url)
    return [
        item for item in items
        if any(
            kw.lower() in (item["title"] + " " + item["description"]).lower()
            for kw in keywords
        )
    ]


def _parse_rss(raw: bytes, category: str, lang: str, source_query: str = "") -> list[dict]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item")[:MAX_ITEMS_PER_QUERY]:
        title       = _text(item, "title")
        link        = _text(item, "link")
        pub_date    = _text(item, "pubDate")
        description = _clean_html(_text(item, "description"))
        source_el   = item.find("source")
        source      = source_el.text.strip() if source_el is not None else ""
        source_url  = source_el.get("url", link) if source_el is not None else link

        if not title or not link:
            continue

        items.append({
            "title":       title,
            "link":        link,
            "pub_date":    _normalize_date(pub_date),
            "description": description,
            "source":      source,
            "source_url":  source_url,
            "query":       source_query,
            "category":    category,
            "lang":        lang,
        })
    return items


# ── Helpers ────────────────────────────────────────────────────────────────

def _text(element, tag: str) -> str:
    el = element.find(tag)
    return el.text.strip() if el is not None and el.text else ""


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return (
        text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .strip()
    )


def _normalize_date(date_str: str) -> str:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return date_str


# ── History ────────────────────────────────────────────────────────────────

def load_existing() -> dict[str, list[dict]]:
    path = Path(OUTPUT_FILE)
    if not path.exists():
        return {cat: [] for cat in CATEGORY_QUERIES}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        by_cat: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_QUERIES}
        for item in data.get("items", []):
            cat = item.get("category")
            if cat in by_cat:
                by_cat[cat].append(item)
        return by_cat
    except Exception:
        return {cat: [] for cat in CATEGORY_QUERIES}


def merge_category(existing: list[dict], new_items: list[dict]) -> list[dict]:
    seen   = {item["link"] for item in new_items}
    merged = list(new_items)
    for item in existing:
        if item["link"] not in seen:
            seen.add(item["link"])
            merged.append(item)
    merged.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
    return merged[:MAX_ITEMS_PER_CATEGORY]


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    existing_by_cat = load_existing()
    all_items: list[dict] = []
    successful_fetches = 0
    fetched_items = 0

    for category, lang_queries in CATEGORY_QUERIES.items():
        new_items: list[dict] = []

        # Google News per language
        for lang, queries in lang_queries.items():
            for query in queries:
                print(f"  [{category}/{lang}] {query}")
                try:
                    items = fetch_google_news(query, category, lang)
                    successful_fetches += 1
                    fetched_items += len(items)
                    print(f"    → {len(items)} items")
                    new_items.extend(items)
                except Exception as exc:
                    print(f"    → ERROR: {exc}")

        # Direct feeds for this category
        for feed in DIRECT_FEEDS:
            if feed["category"] != category:
                continue
            keywords = BANKING_KEYWORDS_EN if feed["lang"] == "en" else BANKING_KEYWORDS_ES
            print(f"  [direct/{feed['lang']}] {feed['url']}")
            try:
                items = fetch_direct(feed["url"], category, feed["lang"], keywords)
                successful_fetches += 1
                fetched_items += len(items)
                print(f"    → {len(items)} items (filtered)")
                new_items.extend(items)
            except Exception as exc:
                print(f"    → ERROR: {exc}")

        # Deduplicate within category
        seen_links: set[str] = set()
        unique_new: list[dict] = []
        for item in new_items:
            if item["link"] not in seen_links:
                seen_links.add(item["link"])
                unique_new.append(item)

        merged = merge_category(existing_by_cat[category], unique_new)
        all_items.extend(merged)
        print(f"  ✓ '{category}': {len(merged)} total items\n")

    if successful_fetches == 0 or fetched_items == 0:
        raise RuntimeError(
            "News collection produced no fresh results; preserving the existing file."
        )

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total":      len(all_items),
        "items":      all_items,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved {len(all_items)} total items to {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Human + Banking + Tech Navigator — collecting news...\n")
    main()
