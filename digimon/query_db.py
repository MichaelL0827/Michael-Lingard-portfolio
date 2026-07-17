"""
query_db.py
───────────
Query layer connecting app.py to the SQLite database
populated by scrap_test.py.

Since scrap_test.py stores human-readable strings directly
(e.g. "Red", "Rookie", "Vaccine") there is no enum
mapping needed — queries go straight to the DB.
"""

import sqlite3
from typing import Optional

DB_PATH = "digimon_cards.db"


# ── Connection ────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict matching app.py's expected keys."""
    return dict(row)


# ── Main search ───────────────────────────────────────────────────────────────

def search_cards(
    name:        Optional[str] = None,
    card_type:   Optional[str] = None,
    color:       Optional[str] = None,
    rarity:      Optional[str] = None,
    levels:      Optional[tuple] = None,
    attribute:   Optional[str] = None,
    digi_type:   Optional[str] = None,
    set_name:    Optional[str] = None,
    effect_text: Optional[str] = None,
    min_dp:      Optional[int] = None,
    max_dp:      Optional[int] = None,
    min_cost:    Optional[int] = None,
    max_cost:    Optional[int] = None,
) -> list[dict]:
    """
    Search cards with optional filters.
    All parameters are optional — omitting one means no restriction.
    `levels` accepts a tuple of one or more levels (e.g. (3, 4)) since a
    card has exactly one level, but the UI lets the user select several
    — matching cards from any selected level (a union, not intersection).
    Returns a list of card dicts ready for app.py's render functions.
    """
    conditions: list[str] = []
    params:     list      = []

    # ── Text filters ──────────────────────────────────────────────────────────
    if name:
        conditions.append("card_name LIKE ?")
        params.append(f"%{name}%")

    if digi_type:
        conditions.append("digi_type LIKE ?")
        params.append(f"%{digi_type}%")

    if set_name:
        conditions.append("set_name LIKE ?")
        params.append(f"%{set_name}%")

    if effect_text:
        # Search across all three effect columns at once
        conditions.append(
            "(main_effect LIKE ? OR source_effect LIKE ? OR alt_effect LIKE ?)"
        )
        params.extend([f"%{effect_text}%"] * 3)

    # ── Exact / enum filters ──────────────────────────────────────────────────
    if card_type:
        # Site uses "Digi-Egg" but app.py sends "Digitama" from the old schema.
        # Map it so both work.
        type_map = {"Digitama": "Digi-Egg"}
        conditions.append("card_type = ?")
        params.append(type_map.get(card_type, card_type))

    if rarity:
        conditions.append("rarity = ?")
        params.append(rarity.lower())

    if attribute:
        conditions.append("attribute = ?")
        params.append(attribute)

    # ── Color filter ──────────────────────────────────────────────────────────
    # Multi-color cards store up to 3 colors in separate columns.
    # Check all three so e.g. searching "Red" finds Red/Black cards too.
    if color:
        conditions.append("(color = ? OR color2 = ? OR color3 = ?)")
        params.extend([color, color, color])

    # ── Numeric / range filters ───────────────────────────────────────────────
    if levels:
        placeholders = ",".join("?" * len(levels))
        conditions.append(f"level IN ({placeholders})")
        params.extend(levels)

    if min_dp is not None:
        conditions.append("dp >= ?")
        params.append(min_dp)

    if max_dp is not None:
        conditions.append("dp <= ?")
        params.append(max_dp)

    if min_cost is not None:
        conditions.append("play_cost >= ?")
        params.append(min_cost)

    if max_cost is not None:
        conditions.append("play_cost <= ?")
        params.append(max_cost)

    # ── Build & run query ─────────────────────────────────────────────────────
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql   = f"SELECT * FROM cards {where} ORDER BY card_number ASC"

    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_dict(row) for row in rows]


# ── Convenience helpers ───────────────────────────────────────────────────────

def get_card(card_number: str) -> Optional[dict]:
    """Fetch a single card by its ID e.g. 'BT25-001'."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM cards WHERE card_number = ?", (card_number,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_all_sets() -> list[str]:
    """Return a sorted list of all distinct set names for a dropdown."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT set_name FROM cards "
            "WHERE set_name IS NOT NULL ORDER BY set_name"
        ).fetchall()
    return [r[0] for r in rows]


def get_sets_with_metadata() -> list[dict]:
    """
    Return all sets with card count, a thumbnail card number (fallback image),
    and packaging box art when available from scraped_sets.box_art_url.

    box_art_url is populated by running fetch_box_art.py — until then it
    will be None and callers should fall back to the first card's image.
    """
    with _get_connection() as conn:
        rows = conn.execute("""
            SELECT
                c.set_name,
                COUNT(*)           AS card_count,
                MIN(c.card_number) AS first_card,
                ss.box_art_url
            FROM cards c
            LEFT JOIN scraped_sets ss ON ss.set_name = c.set_name
            WHERE c.set_name IS NOT NULL
            GROUP BY c.set_name
            ORDER BY MIN(c.card_number) DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_card_count() -> int:
    """Total number of cards in the local database."""
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]


# ── Deck management ───────────────────────────────────────────────────────────

def init_deck_tables() -> None:
    """Create deck tables if they don't exist. Call once on app startup."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deck_cards (
                deck_id     INTEGER NOT NULL,
                card_number TEXT    NOT NULL,
                quantity    INTEGER NOT NULL DEFAULT 1,
                is_egg      INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (deck_id, card_number),
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
        """)
        conn.commit()


def list_decks() -> list[dict]:
    """Return all saved decks ordered by most recently updated."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at, updated_at FROM decks ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def save_deck(name: str, main: dict[str, int], eggs: dict[str, int],
              deck_id: Optional[int] = None) -> int:
    """
    Save or update a deck. Returns the deck ID.

    Args:
        name:    Deck name
        main:    {card_number: quantity} for the main deck
        eggs:    {card_number: quantity} for the egg deck
        deck_id: If provided, update existing deck; otherwise create new
    """
    with _get_connection() as conn:
        if deck_id:
            conn.execute(
                "UPDATE decks SET name = ?, updated_at = datetime('now') WHERE id = ?",
                (name, deck_id)
            )
            conn.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))
        else:
            cur = conn.execute("INSERT INTO decks (name) VALUES (?)", (name,))
            deck_id = cur.lastrowid

        rows = (
            [(deck_id, cn, qty, 0) for cn, qty in main.items()] +
            [(deck_id, cn, qty, 1) for cn, qty in eggs.items()]
        )
        conn.executemany(
            "INSERT INTO deck_cards (deck_id, card_number, quantity, is_egg) VALUES (?,?,?,?)",
            rows
        )
        conn.commit()
    return deck_id


def load_deck(deck_id: int) -> Optional[dict]:
    """
    Load a deck by ID. Returns:
        {
            "id": int, "name": str,
            "main": {card_number: quantity},
            "eggs": {card_number: quantity},
            "main_cards": [full card dicts],
            "egg_cards":  [full card dicts],
        }
    """
    with _get_connection() as conn:
        deck_row = conn.execute(
            "SELECT id, name FROM decks WHERE id = ?", (deck_id,)
        ).fetchone()
        if not deck_row:
            return None

        card_rows = conn.execute(
            "SELECT card_number, quantity, is_egg FROM deck_cards WHERE deck_id = ?",
            (deck_id,)
        ).fetchall()

    main = {r["card_number"]: r["quantity"] for r in card_rows if not r["is_egg"]}
    eggs = {r["card_number"]: r["quantity"] for r in card_rows if r["is_egg"]}

    # Hydrate with full card data
    main_cards = [c for cn in main for c in [get_card(cn)] if c]
    egg_cards  = [c for cn in eggs for c in [get_card(cn)] if c]

    return {
        "id":         deck_row["id"],
        "name":       deck_row["name"],
        "main":       main,
        "eggs":       eggs,
        "main_cards": main_cards,
        "egg_cards":  egg_cards,
    }


def delete_deck(deck_id: int) -> None:
    with _get_connection() as conn:
        conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        conn.commit()


# ── Deck validation ───────────────────────────────────────────────────────────

DECK_RULES = {
    "main_exact":   50,   # main deck must be exactly this many cards
    "main_max_copy": 4,   # max copies of one card in main deck
    "egg_max":       5,   # max cards in egg deck
    "egg_max_copy":  4,   # max copies of one egg card
}


def validate_deck(main: dict[str, int], eggs: dict[str, int]) -> list[str]:
    """
    Check deck against official rules.
    Returns a list of violation strings (empty = valid).
    """
    errors = []

    main_total = sum(main.values())
    egg_total  = sum(eggs.values())

    if main_total != DECK_RULES["main_exact"]:
        errors.append(
            f"Main deck has {main_total} cards — must be exactly {DECK_RULES['main_exact']}"
        )

    for cn, qty in main.items():
        if qty > DECK_RULES["main_max_copy"]:
            errors.append(f"{cn}: {qty} copies in main deck (max {DECK_RULES['main_max_copy']})")

    if egg_total > DECK_RULES["egg_max"]:
        errors.append(
            f"Egg deck has {egg_total} cards — max is {DECK_RULES['egg_max']}"
        )

    for cn, qty in eggs.items():
        if qty > DECK_RULES["egg_max_copy"]:
            errors.append(f"{cn}: {qty} copies in egg deck (max {DECK_RULES['egg_max_copy']})")

    return errors


# ── Analyzer aggregation queries ───────────────────────────────────────────────
# All functions here accept an optional list of set names to scope the
# analysis to. None or an empty list means "across the whole database".

def _set_filter_where(set_names: Optional[list[str]]) -> tuple[str, list]:
    """WHERE clause for simple single-table queries."""
    if not set_names:
        return "", []
    placeholders = ",".join("?" * len(set_names))
    return f"WHERE set_name IN ({placeholders})", list(set_names)


def _set_filter_and(set_names: Optional[list[str]]) -> tuple[str, list]:
    """AND clause for queries that already have a WHERE ... IS NOT NULL."""
    if not set_names:
        return "", []
    placeholders = ",".join("?" * len(set_names))
    return f" AND set_name IN ({placeholders})", list(set_names)


def get_summary_stats(set_names: Optional[list[str]] = None) -> dict:
    """High-level KPI numbers for the top of the analyzer page."""
    where, params = _set_filter_where(set_names)
    with _get_connection() as conn:
        row = conn.execute(f"""
            SELECT
                COUNT(*)                         AS total_cards,
                COUNT(DISTINCT set_name)          AS total_sets,
                AVG(dp)                           AS avg_dp,
                MAX(dp)                           AS max_dp,
                AVG(play_cost)                    AS avg_cost,
                MAX(play_cost)                    AS max_cost
            FROM cards {where}
        """, params).fetchone()
    return dict(row)


def get_type_distribution(set_names: Optional[list[str]] = None) -> list[dict]:
    where, params = _set_filter_where(set_names)
    sql = f"""
        SELECT card_type, COUNT(*) AS count
        FROM cards {where}
        GROUP BY card_type
        ORDER BY count DESC
    """
    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_color_distribution(set_names: Optional[list[str]] = None) -> list[dict]:
    """
    Counts every color a card has, across color/color2/color3.
    A dual-color card counts once toward each of its colors.
    """
    and_clause, and_params = _set_filter_and(set_names)
    clauses, params = [], []
    for col in ("color", "color2", "color3"):
        clauses.append(f"SELECT {col} AS color FROM cards WHERE {col} IS NOT NULL{and_clause}")
        params.extend(and_params)
    sql = (
        "SELECT color, COUNT(*) AS count FROM (" + " UNION ALL ".join(clauses) + ") "
        "GROUP BY color ORDER BY count DESC"
    )
    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_rarity_distribution(set_names: Optional[list[str]] = None) -> list[dict]:
    where, params = _set_filter_where(set_names)
    sql = f"""
        SELECT rarity, COUNT(*) AS count
        FROM cards {where}
        GROUP BY rarity
        ORDER BY count DESC
    """
    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_level_distribution(set_names: Optional[list[str]] = None) -> list[dict]:
    and_clause, and_params = _set_filter_and(set_names)
    sql = f"""
        SELECT level, COUNT(*) AS count
        FROM cards
        WHERE level IS NOT NULL{and_clause}
        GROUP BY level
        ORDER BY level ASC
    """
    with _get_connection() as conn:
        rows = conn.execute(sql, and_params).fetchall()
    return [dict(r) for r in rows]


def get_attribute_distribution(set_names: Optional[list[str]] = None) -> list[dict]:
    and_clause, and_params = _set_filter_and(set_names)
    sql = f"""
        SELECT attribute, COUNT(*) AS count
        FROM cards
        WHERE attribute IS NOT NULL{and_clause}
        GROUP BY attribute
        ORDER BY count DESC
    """
    with _get_connection() as conn:
        rows = conn.execute(sql, and_params).fetchall()
    return [dict(r) for r in rows]


def get_dp_values(set_names: Optional[list[str]] = None) -> list[int]:
    """Raw DP values (non-null) for histogram binning."""
    and_clause, and_params = _set_filter_and(set_names)
    sql = f"SELECT dp FROM cards WHERE dp IS NOT NULL{and_clause}"
    with _get_connection() as conn:
        rows = conn.execute(sql, and_params).fetchall()
    return [r[0] for r in rows]


def get_cost_values(set_names: Optional[list[str]] = None) -> list[int]:
    """Raw play_cost values (non-null) for histogram binning."""
    and_clause, and_params = _set_filter_and(set_names)
    sql = f"SELECT play_cost FROM cards WHERE play_cost IS NOT NULL{and_clause}"
    with _get_connection() as conn:
        rows = conn.execute(sql, and_params).fetchall()
    return [r[0] for r in rows]


def get_cards_per_set(set_names: Optional[list[str]] = None) -> list[dict]:
    """
    Card count per set. If set_names is given, scoped to just those sets
    (useful for side-by-side comparison); otherwise covers every set.
    """
    if set_names:
        placeholders = ",".join("?" * len(set_names))
        sql = f"""
            SELECT set_name, COUNT(*) AS count
            FROM cards
            WHERE set_name IS NOT NULL AND set_name IN ({placeholders})
            GROUP BY set_name
            ORDER BY count DESC
        """
        params = list(set_names)
    else:
        sql = """
            SELECT set_name, COUNT(*) AS count
            FROM cards
            WHERE set_name IS NOT NULL
            GROUP BY set_name
            ORDER BY count DESC
        """
        params = []

    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]