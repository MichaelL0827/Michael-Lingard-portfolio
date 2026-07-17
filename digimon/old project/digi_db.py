import sqlite3
import requests
import time

DB_PATH = "digimon.db"
BASE_URL = "https://digimoncard.io/api-public"
HEADERS = {"User-Agent": "DigimonPriceTracker/1.0 (your@email.com)"}

SETS = [
    "1-Year Anniversary Promo Pack",
    "2025 Evolution Cup Season 1",
    "2025 Evolution Cup Season 2",
    "2025 Evolution Cup Season 3",
    "2026 Dash Pack Campaign",
    "2026 Evolution Cup Season 1",
    "25th Special Memorial Pack",
    "3rd Anniversary Survey Pack",
    "3rd Anniversary Update Pack",
    "AD-01: Advanced Booster Digimon Generation",
    "BT-01: Booster New Evolution",
    "BT-02: Booster Ultimate Power",
    "BT-03: Booster Union Impact",
    "BT-04: Booster Great Legend",
    "BT-05: Booster Battle Of Omni",
    "BT-06: Booster Double Diamond",
    "BT-07: Booster Next Adventure",
    "BT-08: Booster New Awakening",
    "BT-09: Booster X Record",
    "BT-10: Booster Xros Encounter",
    "BT-11: Booster Dimensional Phase",
    "BT-12: Booster Across Time",
    "BT-12: Limited Card Pack",
    "BT-13: Booster Versus Royal Knights",
    "BT-14: Booster Blast Ace",
    "BT-15: Booster Exceed Apocalypse",
    "BT-16: Booster Beginning Observer",
    "BT-17: Booster Secret Crisis",
    "BT-18: Booster Elemental Successor",
    "BT-19: Booster Xros Evolution",
    "BT-20: Booster Over the X",
    "BT-21: Booster World Convergence",
    "BT-21: Illustration Celebration Pack",
    "BT-21: Limited Card Pack",
    "BT-22: Booster Cyber Eden",
    "BT-23: Booster Hackers' Slumber",
    "BT-24: Booster Time Stranger",
    "BT-25: Booster Dual Revolution",
    "BT01-03: Release Special Booster Ver.1.0",
    "BT01-03: Release Special Booster Ver.1.5",
    "BT18-19: Special Booster Ver.2.0",
    "BT19-20: Special Booster Ver.2.5",
    "BTC-01: Booster Ultimate Evolution",
    "Bandai Card Games Official Guide",
    "Box Promotion Pack -Next Adventure-",
    "Box Promotion Pack: Across Time",
    "Box Promotion Pack: Alternative Being",
    "Box Promotion Pack: Animal Colosseum",
    "Box Promotion Pack: Beginning Observer",
    "Box Promotion Pack: Blast Ace",
    "Box Promotion Pack: Cyber Eden",
    "Box Promotion Pack: Dawn of Liberator",
    "Box Promotion Pack: Dimensional Phase",
    "Box Promotion Pack: Elemental Successor",
    "Box Promotion Pack: Exceed Apocalypse",
    "Box Promotion Pack: Hackers' Slumber",
    "Box Promotion Pack: Infernal Ascension",
    "Box Promotion Pack: Over the X",
    "Box Promotion Pack: Resurgence Booster",
    "Box Promotion Pack: Secret Crisis",
    "Box Promotion Pack: Time Stranger",
    "Box Promotion Pack: Versus Royal Knights",
    "Box Promotion Pack: Xros Evolution",
    "Box Promotion: Special Booster Ver.2.0",
    "Box Promotion: Special Booster Ver.2.5",
    "Chain of Liberation Upgrade Pack",
    "DC-1 2021",
    "DC-1 2022",
    "Dash Pack Ver. 1.0",
    "Dash Pack Ver. 1.5",
    "Demo Deck: Imperialdramon",
    "Demo Deck: ST-15",
    "Demo Deck: ST-16",
    "Digimon Adventure 02 THE BEGINNING Viewings",
    "Digimon Adventure 02: The Beginning Promotion Pack",
    "Digimon Card Game Deck Box Set Beelzemon",
    "Digimon Card Game Fest",
    "Digimon Day Memorial Digimon Card x Plastic Model Twitter Campaign",
    "Digimon Dreamers Manga Volume Promo Cards",
    "Digimon Illustration Competition Promotion Pack 2022",
    "Digimon Liberator Promotion Pack",
    "Digimon Story: Time Stranger Promo Pack",
    "Digimon Story: Time Stranger Tutorial Deck",
    "Digimon Survive Promo Pack",
    "Digimon Survive Promotion Pack",
    "Double Diamond Dash Pack",
    "EX-01: Theme Booster Classic Collection",
    "EX-02: Theme Booster Digital Hazard",
    "EX-03: Theme Booster Draconic Roar",
    "EX-04: Theme Booster Alternative Being",
    "EX-05: Theme Booster Animal Colosseum",
    "EX-06: Theme Booster Infernal Ascension",
    "EX-07: Extra Booster Digimon Liberator",
    "EX-07: Legend Pack 2024",
    "EX-08: Extra Booster Chain of Liberation",
    "EX-08: Legend Pack 2024",
    "EX-09: Extra Booster Versus Monsters",
    "EX-09: Legend Pack 2025",
    "EX-10: Extra Booster Sinister Order",
    "EX-10: Legend Pack 2025",
    "EX-11: Extra Booster Dawn of Liberator",
    "EX-12: Extra Booster Digital World Shambala",
    "Evolution Cup 2021",
    "Final Championships 2021",
    "Final Championships 2022",
    "Ghost Game Promo Pack",
    "Great Dash Pack",
    "Great Legend Power Up Pack",
    "Illustration Competition Promotion Pack 2023",
    "LM-01: Limited Card Pack Digimon Ghost Game",
    "LM-02: Limited Card Pack DeathXmon",
    "LM-03: Limited Card Set 2024",
    "LM-04: Limited Card Pack Torrid Weiss",
    "LM-05: Limited Card Pack Final Elysion",
    "LM-06: Limited Card Pack Billion Bullet",
    "LM-07: Limited Card Pack Another Knight",
    "LM-08: Limited Card Pack Final Crest",
    "Limited Card Set ONLINE 2023",
    "Limited Card Set Ver 2",
    "Memorial Collection 01",
    "Memorial Collection 02",
    "Memorial Collection 25th Anniversary",
    "Memorial Collection Digimon Adventure 02",
    "MetalGarurumon GET Campaign",
    "Omegamon GET Campaign",
    "PB-06: Tamer's Evolution Box 2",
    "PB-08: Digimon Tamers Playmat",
    "PB-09: Memorial Collection 01 Playmat",
    "PB-12: Digimon Frontier 20th Memorial Set",
    "PB-12E: Digimon Card Game 2nd Anniversary Set",
    "PB-13: Digimon Card Game Royal Knights Binder Set",
    "PB-14: Digimon Card Game Tamer's Set EX2",
    "PB-15: Digimon Card Game 3rd Anniversary Set",
    "Playmat & Card Set Paildramon & Dinobeemon",
    "Premier TO Event June 2021",
    "Premium Bandai Apparel Promo Cards",
    "RB-01: Resurgence Booster",
    "Regionals 2021",
    "Regionals 2022",
    "Revision Pack 2023",
    "ST-10: Starter Deck Parallel World Tactician",
    "ST-11 Special Entry Pack",
    "ST-11: Starter Deck Special Entry Deck",
    "ST-12: Starter Deck Jesmon",
    "ST-13: Starter Deck RagnaLoardmon",
    "ST-14: Advanced Deck Set Beelzemon",
    "ST-15: Starter Deck Dragon of Courage",
    "ST-16: Starter Deck Wolf of Friendship",
    "ST-17: Advanced Deck Set Double Typhoon",
    "ST-18: Starter Deck Guardian Vortex",
    "ST-19: Starter Deck Fable Waltz",
    "ST-1: Starter Deck Gaia Red",
    "ST-20: Starter Deck Protector of Light",
    "ST-21: Starter Deck Hero of Hope",
    "ST-22: Advanced Deck Set Amethyst Mandala",
    "ST-23: Starter Deck Digimon Beatbreak",
    "ST-24: Starter Deck Digimon Data Squad",
    "ST-2: Starter Deck Cocytus Blue",
    "ST-3: Starter Deck Heaven's Yellow",
    "ST-4: Starter Deck Giga Green",
    "ST-5: Starter Deck Machine Black",
    "ST-6: Starter Deck Venomous Violet",
    "ST-7: Starter Deck Gallantmon",
    "ST-8: Starter Deck UlforceVeedramon",
    "ST-9: Starter Deck Ultimate Ancient Dragon",
    "Secret Crisis: Movie Memorial Pack",
    "Special Battle Area Set 2023",
    "Special Booster Ver.2.0 Lucky Pack",
    "Special Booster Ver.2.5 Lucky Pack",
    "Special Box Promotion Pack",
    "Special Limited Set",
    "Special Promotion Pack 2022 Ver.2.0",
    "Special Promotion Pack 2022 Ver.3.0",
    "Special Promotion Pack 2023 Ver.1.0",
    "Special Release Memorial Pack",
    "Start Deck Purchase Campaign Pack",
    "Starter Deck Complete Set 2021",
    "Summer 2022 Dash Pack",
    "Tamer Battle Pack 10",
    "Tamer Battle Pack 11",
    "Tamer Battle Pack 12",
    "Tamer Battle Pack 13",
    "Tamer Battle Pack 14",
    "Tamer Battle Pack 15",
    "Tamer Battle Pack 16",
    "Tamer Battle Pack 17",
    "Tamer Battle Pack 18",
    "Tamer Battle Pack 19",
    "Tamer Battle Pack 4",
    "Tamer Battle Pack 6",
    "Tamer Exchange Promotion Pack",
    "Tamer's Selection Box DC-1 Grand Prix 2022",
    "Tamer's Selection Box Evolution Cup 2022",
    "Tamer's Selection Box Evolution Cup 2022 Ver.2",
    "Tamer's Selection Box Super Tamer Battle 2022",
    "Trial Deck: ST-1",
    "Trial Deck: STC-1",
    "Ultimate Cup 2022",
    "Ultimate Cup 2023",
    "Ultimate Cup 2024",
    "Ultimate Cup 2024 Season 2",
    "Ultimate Cup 25-26 Season 1",
    "Ultimate Cup 25-26 Season 2",
    "Ultimate Cup 26-27 Season 1",
    "Update Pack",
    "Update Pack 2024",
    "Update Pack 2025",
    "V-Jump Magazine Promo Cards",
    "WarGreymon GET Campaign",
    "World Championship 2021",
]

EXPECTED_COLUMNS = {
    "card_number", "card_name", "card_type", "color", "color2", "color3",
    "rarity", "level", "dp", "play_cost", "evolution_cost",
    "evolution_color", "evolution_color2", "evolution_level", "xros_req", "attribute",
    "digi_type", "digi_type2", "form", "stage", "artist",
    "main_effect", "source_effect", "alt_effect", "set_name",
    "date_added", "tcgplayer_name", "tcgplayer_id",
}


# ── Step 1: Create tables ─────────────────────────────────────────────────────

def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number      TEXT UNIQUE,   -- API: "id"              e.g. "BT4-016"
            card_name        TEXT,          -- API: "name"
            card_type        TEXT,          -- API: "type"            e.g. "Digimon", "Tamer", "Option"
            color            TEXT,          -- API: "color"
            color2           TEXT,          -- API: "color2"          for multi-color cards
            color3           TEXT,          -- API: "color3"          for multi-color cards
            rarity           TEXT,          -- API: "rarity"          e.g. "sr", "r", "c"
            level            INTEGER,       -- API: "level"
            dp               INTEGER,       -- API: "dp"
            play_cost        INTEGER,       -- API: "play_cost"
            evolution_cost   INTEGER,       -- API: "evolution_cost"
            evolution_color  TEXT,          -- API: "evolution_color"
            evolution_color2  TEXT,          -- API: "evolution_color2"
            evolution_level  INTEGER,       -- API: "evolution_level"
            xros_req         TEXT,          -- API: "xros_req"        for Xros/jogress cards
            attribute        TEXT,          -- API: "attribute"       e.g. "Variable", "Vaccine"
            digi_type        TEXT,          -- API: "digi_type"
            digi_type2       TEXT,          -- API: "digi_type2"      for dual-type cards
            form             TEXT,          -- API: "form"            e.g. "Hybrid", "Mega"
            stage            TEXT,          -- API: "stage"
            artist           TEXT,          -- API: "artist"
            main_effect      TEXT,          -- API: "main_effect"
            source_effect    TEXT,          -- API: "source_effect"   inherited effect
            alt_effect       TEXT,          -- API: "alt_effect"      security effect
            set_name         TEXT,          -- API: "series"
            date_added       TEXT,          -- API: "date_added"
            tcgplayer_name   TEXT,          -- API: "tcgplayer_name"
            tcgplayer_id     INTEGER,       -- API: "tcgplayer_id"
            fetched_at       TEXT DEFAULT (datetime('now'))
        )
    """)
    print("  Tables created.")


# ── Step 2: Schema validation ─────────────────────────────────────────────────

def check_schema(cursor):
    """Return True if the cards table exists with the correct columns."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
    if not cursor.fetchone():
        return False
    cursor.execute("PRAGMA table_info(cards)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    missing = EXPECTED_COLUMNS - existing_columns
    if missing:
        print(f"  Schema mismatch — missing columns: {missing}")
        return False
    return True

def reset_database(cursor, conn):
    """Drop and recreate tables when schema is wrong or missing."""
    print("  Dropping existing tables and rebuilding...")
    cursor.execute("DROP TABLE IF EXISTS prices")
    cursor.execute("DROP TABLE IF EXISTS cards")
    conn.commit()
    create_tables(cursor)
    conn.commit()


# ── Step 3: Fetch from API ────────────────────────────────────────────────────

def fetch_cards_for_set(set_name, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(
                f"{BASE_URL}/search.php",
                headers=HEADERS,
                params={"pack": set_name, "sort": "name", "sortdirection": "asc"},
                timeout=30,
            )
            if response.status_code == 400:
                return []
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectTimeout:
            print(f"    Timeout on attempt {attempt + 1}/{retries}, retrying...")
            time.sleep(3)
        except Exception as e:
            print(f"    Request error: {e}")
            return []
    print(f"    Failed after {retries} attempts, skipping.")
    return []


# ── Step 4: Insert cards ──────────────────────────────────────────────────────

def seed_cards(cursor, cards):
    inserted = 0
    skipped = 0
    errors = 0

    # Print first card's raw keys so you can verify field names if inserts fail
    #if cards:
        #print(f"    Sample API keys: {list(cards[0].keys())}")

    for card in cards:
        card_number = card.get("id")       # API uses "id" not "cardnumber"
        if not card_number:
            continue

        try:
            cursor.execute("""
                INSERT INTO cards (
                    card_number, card_name, card_type, color, color2, color3,
                    rarity, level, dp, play_cost, evolution_cost,
                    evolution_color, evolution_color2, evolution_level, xros_req, attribute,
                    digi_type, digi_type2, form, stage, artist,
                    main_effect, source_effect, alt_effect,
                    set_name, date_added, tcgplayer_name, tcgplayer_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(card_number) DO UPDATE SET
                    card_name=excluded.card_name,
                    card_type=excluded.card_type,
                    color=excluded.color,
                    color2=excluded.color2,
                    color3=excluded.color3,
                    rarity=excluded.rarity,
                    level=excluded.level,
                    dp=excluded.dp,
                    play_cost=excluded.play_cost,
                    evolution_cost=excluded.evolution_cost,
                    evolution_color=excluded.evolution_color,
                    evolution_color2=excluded.evolution_color2,
                    evolution_level=excluded.evolution_level,
                    xros_req=excluded.xros_req,
                    attribute=excluded.attribute,
                    digi_type=excluded.digi_type,
                    digi_type2=excluded.digi_type2,
                    form=excluded.form,
                    stage=excluded.stage,
                    artist=excluded.artist,
                    main_effect=excluded.main_effect,
                    source_effect=excluded.source_effect,
                    alt_effect=excluded.alt_effect,
                    set_name=excluded.set_name,
                    date_added=excluded.date_added,
                    tcgplayer_name=excluded.tcgplayer_name,
                    tcgplayer_id=excluded.tcgplayer_id
            """, (
                card_number,
                card.get("name"),
                card.get("type"),
                card.get("color"),
                card.get("color2"),
                card.get("color3"),
                card.get("rarity"),
                card.get("level"),
                card.get("dp"),
                card.get("play_cost"),
                card.get("evolution_cost"),
                card.get("evolution_color"),
                card.get("evolution_color2"),
                card.get("evolution_level"),
                card.get("xros_req"),
                card.get("attribute"),
                card.get("digi_type"),
                card.get("digi_type2"),
                card.get("form"),
                card.get("stage"),
                card.get("artist"),
                card.get("main_effect"),
                card.get("source_effect"),
                card.get("alt_effect"),
                card.get("series"),
                card.get("date_added"),
                card.get("tcgplayer_name"),
                card.get("tcgplayer_id"),
            ))

            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"    Failed to insert {card_number}: {e}")
            errors += 1
            continue

    return inserted, skipped, errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1 — validate schema, reset and recreate if needed
    print("Checking database schema...")
    if check_schema(cursor):
        print("  Schema is correct, skipping recreation.")
    else:
        reset_database(cursor, conn)

    # Step 2 — seed card data
    print(f"\nSeeding card data from {len(SETS)} sets...\n")
    total_inserted = 0
    total_skipped = 0
    total_errors = 0

    for set_name in SETS:
        print(f"  Fetching {set_name}...")
        cards = fetch_cards_for_set(set_name)

        if not cards:
            print("    No cards returned.")
            time.sleep(1)
            continue

        try:
            inserted, skipped, errors = seed_cards(cursor, cards)
            conn.commit()
            total_inserted += inserted
            total_skipped += skipped
            total_errors += errors
            print(f"    {len(cards)} fetched — {inserted} inserted, {skipped} skipped, {errors} errors")
        except Exception as e:
            print(f"    Error processing {set_name}: {e}")
            conn.rollback()

        time.sleep(1)

    conn.close()
    print(f"\nSetup complete.")
    print(f"Total inserted : {total_inserted}")
    print(f"Total skipped  : {total_skipped}")
    print(f"Total errors   : {total_errors}")
    print(f"Database saved : {DB_PATH}")


if __name__ == "__main__":
    main()