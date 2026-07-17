"""
scraper.py
──────────
Scrapes ALL card data from world.digimoncard.com/cards/
by looping through every set category found in the search dropdown.

Strategy:
  - GET /cards/?search=true&category=XXXXXX  for each set
  - Parse all <li class="image_lists_item"> elements
  - Store in local SQLite database

Usage:
    python scraper.py               # scrape everything
    python scraper.py --set BT-25   # scrape one set by name
    python scraper.py --list-sets   # print all known sets and exit
"""

import argparse
import sqlite3
import time
import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL  = "https://world.digimoncard.com/cards/"
DB_PATH   = "digimon_cards.db"
DELAY     = 1.5   # seconds between requests — be polite

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://world.digimoncard.com/cardlist/",
}

RARITY_MAP = {
    "C": "c", "U": "u", "R": "r",
    "SR": "sr", "UR": "ur", "SEC": "sec", "P": "p", "LM": "lm",
}

# Labels that always route to a specific field regardless of Card Text section.
# Any label NOT in these sets is treated as part of main_effect.
_SOURCE_LABELS = {"Inherited Effect"}
_ALT_LABELS    = {"Security Effect"}


# ── Set catalog ───────────────────────────────────────────────────────────────
# No hardcoded set list. "Known" sets live in the scraped_sets table —
# discover_sets() finds what's live on the site, get_known_sets() finds
# what's already in the database, and the two are diffed to find new sets.

def discover_sets() -> list[tuple[str, str]]:
    """
    Fetch the live category dropdown from the search page and parse
    every <option> into (category_id, set_name) tuples.
    """
    url = "https://world.digimoncard.com/cardlist/"
    response = requests.get(url, headers=HEADERS, params={"search": "true"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    select = soup.find("select", attrs={"name": "category"})
    if not select:
        raise RuntimeError(
            "Could not find the category dropdown — page structure may have changed."
        )

    sets = []
    for option in select.find_all("option"):
        value = option.get("value", "").strip()
        name  = option.get_text(strip=True)
        if value:   # skip the blank "Version" placeholder option
            sets.append((value, name))

    if not sets:
        raise RuntimeError("Category dropdown was found but contained no sets.")

    return sets


def get_known_sets(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Return every (category_id, set_name) already recorded in scraped_sets."""
    rows = conn.execute(
        "SELECT category_id, set_name FROM scraped_sets ORDER BY set_name"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def get_set_catalog(conn: sqlite3.Connection) -> tuple[list[tuple[str, str]], bool]:
    """
    Returns (sets, was_live). Tries live discover_sets() first;
    falls back to whatever sets are already known in the database
    on any failure (network issue, site structure change, offline use).
    """
    try:
        return discover_sets(), True
    except Exception as e:
        print(f"⚠ Live set discovery failed ({e}); falling back to sets already in the database.\n")
        return get_known_sets(conn), False


def find_category_id(query: str, sets: list[tuple[str, str]]) -> str | None:
    """Find a category ID from a partial set name e.g. 'BT-25' or 'gaia red'."""
    lookup = {name.lower(): cid for cid, name in sets}
    query  = query.lower()
    for name, cid in lookup.items():
        if query in name:
            return cid
    return None


# ── HTML parsing ──────────────────────────────────────────────────────────────

def _get_info_field(popup, label: str) -> str | None:
    for dl in popup.find_all("dl", class_="cardInfoBox"):
        dt = dl.find("dt")
        if dt and dt.get_text(strip=True) == label:
            dd = dl.find("dd")
            return dd.get_text(strip=True) if dd else None
    return None


def _parse_colors(popup) -> tuple:
    color_dd = popup.find("dd", class_="cardColor")
    if not color_dd:
        return None, None, None
    colors = [
        span.get_text(strip=True)
        for span in color_dd.find_all("span")
        if span.get_text(strip=True)
    ]
    colors += [None, None, None]
    return colors[0], colors[1], colors[2]


def _parse_effects(popup) -> dict:
    """
    Parse all Card Text sections and route each effect block to the
    correct field by its label.

    Card structure:
        <div class="cardInfoBox">
            <div class="cardInfoTitMedium">Card Text 1</div>
            <dl class="cardInfoBoxSmall">
                <dt class="cardInfoTitSmall">[Special Digivolution Condition]</dt>
                <dd>...</dd>
            </dl>
            <dl class="cardInfoBoxSmall">
                <dt class="cardInfoTitSmall">[Effect]</dt>
                <dd>...</dd>
            </dl>
        </div>
        <div class="cardInfoBox">
            <div class="cardInfoTitMedium">Card Text 2</div>
            <dl class="cardInfoBoxSmall">
                <dt class="cardInfoTitSmall">[Inherited Effect]</dt>
                <dd>...</dd>
            </dl>
        </div>

    Routing rules:
        [Inherited Effect]  → source_effect
        [Security Effect]   → alt_effect
        everything else     → appended to main_effect
    """
    result       = {"main_effect": None, "source_effect": None, "alt_effect": None}
    main_parts   = []

    # Only look inside divs that have a cardInfoTitMedium — those are Card Text sections
    for section in popup.find_all("div", class_="cardInfoBox"):
        if not section.find("div", class_="cardInfoTitMedium"):
            continue

        for dl in section.find_all("dl", class_="cardInfoBoxSmall"):
            dt = dl.find("dt", class_="cardInfoTitSmall")
            dd = dl.find("dd", class_="cardInfoData")
            if not (dt and dd):
                continue

            label = dt.get_text(strip=True).strip("[]")
            text  = dd.get_text(strip=True)

            if label in _SOURCE_LABELS:
                result["source_effect"] = text
            elif label in _ALT_LABELS:
                result["alt_effect"] = text
            else:
                # Preserve the label so app.py can display it clearly
                # e.g. "[Effect] When attacking..."
                # "[Special Digivolution Condition] Lv.2 w/[TS]..."
                main_parts.append(f"[{label}] {text}")

    if main_parts:
        result["main_effect"] = "\n".join(main_parts)

    return result


def _parse_set_name(popup) -> str | None:
    for dl in popup.find_all("dl", class_="cardInfoBox"):
        dt = dl.find("dt")
        if dt and dt.get_text(strip=True) == "Notes":
            dd = dl.find("dd")
            if dd:
                for child in dd.children:
                    text = str(child).strip()
                    if text:
                        return text
    return None


def _parse_product_url(popup) -> str | None:
    """
    Extract the PRODUCTS link from the Notes section, e.g. '/products/pack/ver25'.
    This points to the product page where the box/pack art lives.

    HTML:
        <dd class="cardInfoData">
            Booster DUAL REVOLUTION [BT-25]
            <ul class="cardInfoLink">
                <li class="cardInfoLinkItem"><a href="?search=true&category=...">CARD LIST</a></li>
                <li class="cardInfoLinkItem"><a href="/products/pack/ver25">PRODUCTS</a></li>
            </ul>
        </dd>
    """
    for dl in popup.find_all("dl", class_="cardInfoBox"):
        dt = dl.find("dt")
        if dt and dt.get_text(strip=True) == "Notes":
            dd = dl.find("dd")
            if dd:
                for link in dd.find_all("a", class_="cardInfoLinkBtn"):
                    if link.get_text(strip=True) == "PRODUCTS":
                        href = link.get("href", "")
                        if href.startswith("/"):
                            return "https://world.digimoncard.com" + href
                        return href
    return None


def _parse_digivolve_cost(popup, extract: str) -> str | int | None:
    """
    Parse the 'Digivolve Cost 1' field, which packs color(s), cost, and
    level into a single <dd>:

        <dt class="cardInfoTit">Digivolve Cost 1</dt>
        <dd class="cardInfoData cardColor cardColorCost">
            <span class='cardColor_red'>Red</span>
            <span class='cardColor_blue'>Blue</span>
            0 from Lv.2
        </dd>

    Args:
        extract: "cost"  → returns the integer cost (0 in the example)
                 "level" → returns the integer level (2 in the example)
                 "color" → returns the first color string ("Red")
    """
    for dl in popup.find_all("dl", class_="cardInfoBox"):
        dt = dl.find("dt")
        if not (dt and dt.get_text(strip=True).startswith("Digivolve Cost")):
            continue
        dd = dl.find("dd")
        if not dd:
            continue

        if extract == "color":
            span = dd.find("span")
            return span.get_text(strip=True) if span else None

        # Get the plain text after stripping color span text
        # e.g. "Red Blue 0 from Lv.2" → we want "0 from Lv.2"
        full_text = dd.get_text(strip=True)
        # Remove color names from the front of the text
        for span in dd.find_all("span"):
            full_text = full_text.replace(span.get_text(strip=True), "")
        remainder = full_text.strip()   # "0 from Lv.2"

        if extract == "cost":
            # First token is the cost integer
            parts = remainder.split()
            if parts:
                return _safe_int(parts[0])

        if extract == "level":
            # "from Lv.2" → 2
            import re
            m = re.search(r"Lv\.(\d+)", remainder)
            return int(m.group(1)) if m else None

    return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    cleaned = str(val).replace(",", "").replace("Lv.", "").strip()
    return int(cleaned) if cleaned.lstrip("-").isdigit() else None


def parse_card(li_tag) -> dict | None:
    popup = li_tag.find("div", class_="popupCol")
    if not popup:
        return None

    card_number_tag = popup.find("li", class_="cardNo")
    card_number = card_number_tag.get_text(strip=True) if card_number_tag else None
    if not card_number:
        return None

    name_tag  = popup.find("div", class_="cardTitle")
    rarity_tag = popup.find("li", class_="cardRarity")
    type_tag  = popup.find("li", class_="cardType")
    level_tag = popup.find("li", class_="cardLv")

    rarity_raw = rarity_tag.get_text(strip=True) if rarity_tag else ""

    # The official site lists every Limited Card Pack card's rarity as its
    # normal value (e.g. "P"), with no distinct "LM" rarity in that field —
    # "LM" only shows up in the card ID prefix and set name. Override here
    # so LM-xxx cards get their own rarity bucket in this app regardless of
    # what the site's rarity field says.
    rarity = RARITY_MAP.get(rarity_raw.upper(), rarity_raw.lower())
    if card_number.upper().startswith("LM-"):
        rarity = "lm"

    color, color2, color3 = _parse_colors(popup)
    effects = _parse_effects(popup)

    img_tag   = li_tag.find("img")
    image_url = img_tag.get("src", "") if img_tag else ""
    if image_url.startswith("../"):
        image_url = "https://world.digimoncard.com/" + image_url[3:]

    return {
        "card_number":     card_number,
        "card_name":       name_tag.get_text(strip=True) if name_tag else "",
        "card_type":       type_tag.get_text(strip=True) if type_tag else "",
        "rarity":          rarity,
        "level":           _safe_int(level_tag.get_text(strip=True)) if level_tag else None,
        "color":           color,
        "color2":          color2,
        "color3":          color3,
        "form":            _get_info_field(popup, "Form"),
        "digi_type":       _get_info_field(popup, "Type"),
        "attribute":       _get_info_field(popup, "Attribute"),
        "dp":              _safe_int(_get_info_field(popup, "DP")),
        "play_cost":       _safe_int(_get_info_field(popup, "Cost")),
        "evolution_cost":  _safe_int(
                               _parse_digivolve_cost(popup, "cost")
                               or _get_info_field(popup, "Digivolution Cost")
                               or _get_info_field(popup, "Evolution Cost")
                           ),
        "evolution_color": (
                               _parse_digivolve_cost(popup, "color")
                               or _get_info_field(popup, "Digivolution Color")
                           ),
        "evolution_level": _safe_int(
                               _parse_digivolve_cost(popup, "level")
                               or _get_info_field(popup, "Digivolution Lv.")
                           ),
        "main_effect":     effects["main_effect"],
        "source_effect":   effects["source_effect"],
        "alt_effect":      effects["alt_effect"],
        "set_name":        _parse_set_name(popup),
        "product_url":     _parse_product_url(popup),
        "image_url":       image_url,
    }


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_set(category_id: str, set_name: str) -> tuple[list[dict], str | None]:
    """
    Fetch and parse all cards from one set.
    Returns (cards, product_url) — product_url is pulled from the first
    card that has one, since it's the same link repeated on every card.
    """
    url    = BASE_URL
    params = {"search": "true", "category": category_id}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return [], None

    soup  = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all("li", class_="image_lists_item")

    if not items:
        print(f"  ⚠ No cards found — HTML structure may have changed")
        return [], None

    cards = []
    product_url = None
    for li in items:
        card = parse_card(li)
        if card:
            cards.append(card)
            if product_url is None and card.get("product_url"):
                product_url = card["product_url"]

    return cards, product_url


def scrape_sets(
    category_ids: list[tuple[str, str]],
    conn: sqlite3.Connection,
) -> list[dict]:
    """
    Loop through a list of (category_id, set_name) tuples,
    fetch each one, save cards immediately, and record the set as scraped.
    Saving per-set means a mid-run failure doesn't lose completed sets.
    """
    total     = len(category_ids)
    all_cards = []

    for i, (cid, name) in enumerate(category_ids, 1):
        print(f"[{i}/{total}] {name} (category {cid})")
        cards, product_url = fetch_set(cid, name)
        print(f"  → {len(cards)} cards parsed")

        if cards:
            save_cards(conn, cards)
            all_cards.extend(cards)

        # Record this set as scraped regardless of card count
        # (some sets may legitimately have 0 cards in the EN list)
        mark_set_scraped(conn, cid, name, product_url)

        if i < total:
            time.sleep(DELAY)

    return all_cards


# ── Database ──────────────────────────────────────────────────────────────────

def create_db(conn: sqlite3.Connection, reset: bool = False) -> None:
    if reset:
        conn.execute("DROP TABLE IF EXISTS cards")
        conn.execute("DROP TABLE IF EXISTS scraped_sets")
        print("Tables dropped — rebuilding schema.")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_number     TEXT PRIMARY KEY,
            card_name       TEXT,
            card_type       TEXT,
            rarity          TEXT,
            level           INTEGER,
            color           TEXT,
            color2          TEXT,
            color3          TEXT,
            form            TEXT,
            digi_type       TEXT,
            attribute       TEXT,
            dp              INTEGER,
            play_cost       INTEGER,
            evolution_cost  INTEGER,
            evolution_color TEXT,
            evolution_level INTEGER,
            main_effect     TEXT,
            source_effect   TEXT,
            alt_effect      TEXT,
            set_name        TEXT,
            image_url       TEXT
        )
    """)

    # Tracks which category IDs have already been scraped and when.
    # product_url:  the set's product page, e.g. /products/pack/ver25
    # box_art_url:  packaging image, filled in later by fetch_box_art.py
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scraped_sets (
            category_id TEXT PRIMARY KEY,
            set_name    TEXT,
            product_url TEXT,
            box_art_url TEXT,
            scraped_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def mark_set_scraped(
    conn: sqlite3.Connection, category_id: str, set_name: str,
    product_url: str | None = None,
) -> None:
    # Preserve box_art_url if it was already set by a previous fetch_box_art run
    existing = conn.execute(
        "SELECT box_art_url FROM scraped_sets WHERE category_id = ?", (category_id,)
    ).fetchone()
    box_art_url = existing[0] if existing else None

    conn.execute("""
        INSERT OR REPLACE INTO scraped_sets
            (category_id, set_name, product_url, box_art_url, scraped_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (category_id, set_name, product_url, box_art_url))
    conn.commit()


def get_scraped_ids(conn: sqlite3.Connection) -> set[str]:
    """Return all category IDs that have already been scraped."""
    rows = conn.execute("SELECT category_id FROM scraped_sets").fetchall()
    return {r[0] for r in rows}


def save_cards(conn: sqlite3.Connection, cards: list[dict]) -> None:
    conn.executemany("""
        INSERT OR REPLACE INTO cards VALUES (
            :card_number, :card_name, :card_type, :rarity, :level,
            :color, :color2, :color3,
            :form, :digi_type, :attribute, :dp, :play_cost,
            :evolution_cost, :evolution_color, :evolution_level,
            :main_effect, :source_effect, :alt_effect,
            :set_name, :image_url
        )
    """, cards)
    conn.commit()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Digimon card data")
    parser.add_argument("--set",       help="Partial set name e.g. 'BT-25' or 'gaia red'")
    parser.add_argument("--list-sets", action="store_true",
                         help="Print sets already in the database and exit")
    parser.add_argument("--discover",  action="store_true",
                         help="Fetch the live category list from the site and print it (no scraping)")
    parser.add_argument("--all",       action="store_true",
                         help="Scrape every live set, not just ones missing from the database")
    parser.add_argument("--offline",   action="store_true",
                         help="Skip live discovery — use sets already in the database instead")
    parser.add_argument("--reset",     action="store_true",
                         help="Drop and recreate all tables")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    create_db(conn, reset=args.reset)

    # ── --list-sets — show what's already in the database ─────────────────────
    if args.list_sets:
        known = get_known_sets(conn)
        print(f"{'ID':<10} {'Set Name'}")
        print("-" * 60)
        for cid, name in known:
            print(f"{cid:<10} {name}")
        print(f"\n{len(known)} set(s) currently in the database.")
        conn.close()
        raise SystemExit(0)

    # ── --discover — show what's live on the site, tag anything new ───────────
    if args.discover:
        live_sets = discover_sets()
        known_ids = {cid for cid, _ in get_known_sets(conn)}
        print(f"{'ID':<10} {'Set Name'}")
        print("-" * 60)
        for cid, name in live_sets:
            tag = "  ← NEW" if cid not in known_ids else ""
            print(f"{cid:<10} {name}{tag}")
        new_count = sum(1 for cid, _ in live_sets if cid not in known_ids)
        print(f"\n{len(live_sets)} set(s) live on site, {new_count} not yet in the database.")
        conn.close()
        raise SystemExit(0)

    # ── Resolve the working catalog — live by default, DB-known if --offline ──
    if args.offline:
        catalog, was_live = get_known_sets(conn), False
    else:
        catalog, was_live = get_set_catalog(conn)

    if not catalog:
        print("No sets available — database is empty and live discovery failed.")
        conn.close()
        raise SystemExit(1)

    if was_live:
        known_ids = {cid for cid, _ in get_known_sets(conn)}
        new_ids   = {cid for cid, _ in catalog} - known_ids
        print(f"Using live set list from the site ({len(catalog)} set(s)"
              f"{f', {len(new_ids)} new' if new_ids else ''}).\n")
    else:
        print(f"Using sets already in the database ({len(catalog)} set(s)).\n")

    # ── --set — scrape one specific set by partial name ────────────────────────
    if args.set:
        cid = find_category_id(args.set, sets=catalog)
        if not cid:
            print(f"No set found matching '{args.set}'. Run --discover to see live options.")
            conn.close()
            raise SystemExit(1)
        name    = next(n for c, n in catalog if c == cid)
        targets = [(cid, name)]

    # ── --all — scrape every set in the catalog, known or not ─────────────────
    elif args.all:
        targets = catalog

    # ── default — only sets not already in the database ───────────────────────
    else:
        already_scraped = get_scraped_ids(conn)
        targets = [(cid, name) for cid, name in catalog if cid not in already_scraped]
        if not targets:
            print("No new sets found — database is already up to date.")
            conn.close()
            raise SystemExit(0)
        print(f"{len(targets)} new set(s) to scrape.\n")

    # ── Scrape ────────────────────────────────────────────────────────────────
    print(f"Scraping {len(targets)} set(s)...\n")
    cards = scrape_sets(targets, conn)

    conn.close()
    print(f"\nDone. {len(cards)} cards saved to {DB_PATH}")