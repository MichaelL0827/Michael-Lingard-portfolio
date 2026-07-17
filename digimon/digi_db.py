import sqlite3
import json

def create_db():
    conn = sqlite3.connect("digimon_cards.db")
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            gid         INTEGER,
            cardid      TEXT PRIMARY KEY,
            name        TEXT,
            cardtype    INTEGER,
            cost        INTEGER,
            ecost       INTEGER,
            ecost2      INTEGER,
            ec3         INTEGER,
            ec4         INTEGER,
            ecostcolor  INTEGER,
            ecostcolor2 INTEGER,
            ecc3        INTEGER,
            ecc4        INTEGER,
            elvfrom     INTEGER,
            elvfrom2    INTEGER,
            dp          INTEGER,
            dtype       TEXT,
            attr        INTEGER,
            stage       INTEGER,
            rare        INTEGER,
            color       INTEGER,
            level       INTEGER,
            maineffect  TEXT,
            sourceeffect TEXT,
            securityeffect TEXT,
            notes       TEXT,
            image_url   TEXT,
            language    INTEGER,
            artist      TEXT,
            sourceid    INTEGER,
            price       REAL,
            shop        TEXT,
            pid         TEXT,
            block       TEXT,
            src         TEXT,
            intl        INTEGER
        )
    """)
    
    conn.commit()
    return conn

def insert_cards(conn, cards):
    c = conn.cursor()
    
    for card in cards:
        c.execute("""
            INSERT OR REPLACE INTO cards VALUES (
                :gid, :cardid, :name, :cardtype, :cost,
                :ecost, :ecost2, :ec3, :ec4,
                :ecostcolor, :ecostcolor2, :ecc3, :ecc4,
                :elvfrom, :elvfrom2, :dp, :dtype,
                :attr, :stage, :rare, :color, :level,
                :maineffect, :sourceeffect, :securityeffect,
                :notes, :imageUrl, :language, :artist,
                :sourceid, :price, :shop, :p,
                :block, :src, :intl
            )
        """, card)
    
    conn.commit()
    print(f"Inserted {len(cards)} cards into database")

conn = create_db()
with open("cards_20260516.json") as f:
    cards = json.load(f)
insert_cards(conn, cards)