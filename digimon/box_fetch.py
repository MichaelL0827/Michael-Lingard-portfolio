"""
fetch_box_art.py
────────────────
Fetches packaging artwork for every set from the official products
listing page and stores it in the scraped_sets.box_art_url column.

Source: https://world.digimoncard.com/products/

Each product block looks like:
    <article class="genrecol-pack ..." data-url="pack/ver25/">
      <div class="itembox">
        <div class="prodinfo">
          <div class="image"><img src="/images/products/pack/ver25/img_pkg.png"></div>
          ...
          <a class="btn_smallest" href="/cards/?search=true&category=522036">...</a>
        </div>
      </div>
    </article>

Box art is matched to sets by extracting the `category=` query param
from the CARD LIST link inside each block — not by product_url —
since the category id is the stable join key already used throughout
the database.

Usage:
    python fetch_box_art.py
"""

import re
import sqlite3
import requests
from bs4 import BeautifulSoup

PRODUCTS_URL = "https://world.digimoncard.com/products/"
DB_PATH      = "digimon_cards.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://world.digimoncard.com/",
}

CATEGORY_RE = re.compile(r"category=(\d+)")


def fetch_box_art_map() -> dict[str, str]:
    """
    Returns {category_id: absolute_image_url} for every product block
    on the products page that links through to a card list category.
    """
    response = requests.get(PRODUCTS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    mapping: dict[str, str] = {}

    for article in soup.find_all("article"):
        # The CARD LIST link inside this block carries the category id
        link = article.find("a", href=CATEGORY_RE)
        if not link:
            continue
        match = CATEGORY_RE.search(link["href"])
        if not match:
            continue
        category_id = match.group(1)

        img = article.select_one(".image img")
        if not img or not img.get("src"):
            continue

        src = img["src"]
        if src.startswith("/"):
            src = "https://world.digimoncard.com" + src

        mapping[category_id] = src

    return mapping


def update_box_art(conn: sqlite3.Connection, mapping: dict[str, str]) -> int:
    updated = 0
    for category_id, image_url in mapping.items():
        cur = conn.execute(
            "UPDATE scraped_sets SET box_art_url = ? WHERE category_id = ?",
            (image_url, category_id)
        )
        if cur.rowcount:
            updated += 1
    conn.commit()
    return updated


if __name__ == "__main__":
    print(f"Fetching {PRODUCTS_URL} ...")
    mapping = fetch_box_art_map()
    print(f"Found {len(mapping)} product blocks with a category + image match.\n")

    conn = sqlite3.connect(DB_PATH)
    updated = update_box_art(conn, mapping)

    # Report which known sets did NOT get matched, so gaps are visible
    known   = {r[0] for r in conn.execute("SELECT category_id FROM scraped_sets").fetchall()}
    matched = set(mapping.keys())
    missing = known - matched

    conn.close()

    print(f"Updated box art for {updated} set(s).")
    if missing:
        print(f"\n{len(missing)} known set(s) had no match on the products page:")
        for cid in sorted(missing):
            print(f"  {cid}")
        print("\nThese may live on a different products page (e.g. promos/accessories)")
        print("or use a different link pattern — share their HTML to add support for them.")