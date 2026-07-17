import sqlite3
import streamlit as st
DB_PATH = "digimon.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
def search_cards(
    name=None,
    card_type=None,
    color=None,
    rarity=None,
    level=None,
    min_dp=None,
    max_dp=None,
    min_cost=None,
    max_cost=None,
    attribute=None,
    digi_type=None,
    set_name=None,
    effect_text=None,
):
    conn = get_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM cards WHERE 1=1"
    params = []

    if name:
        query += " AND card_name LIKE ?"
        params.append(f"%{name}%")
    if card_type:
        query += " AND card_type = ?"
        params.append(card_type)
    if color:
        query += " AND (color = ? OR color2 = ? OR color3 = ?)"
        params.extend([color, color, color])
    if rarity:
        query += " AND rarity = ?"
        params.append(rarity)
    if level is not None:
        query += " AND level = ?"
        params.append(level)
    if min_dp is not None:
        query += " AND dp >= ?"
        params.append(min_dp)
    if max_dp is not None:
        query += " AND dp <= ?"
        params.append(max_dp)
    if min_cost is not None:
        query += " AND play_cost >= ?"
        params.append(min_cost)
    if max_cost is not None:
        query += " AND play_cost <= ?"
        params.append(max_cost)
    if attribute:
        query += " AND attribute = ?"
        params.append(attribute)
    if digi_type:
        query += " AND (digi_type LIKE ? OR digi_type2 LIKE ?)"
        params.extend([f"%{digi_type}%", f"%{digi_type}%"])
    if set_name:
        # Instead of set_name column, search the card_number for prefixes like 'BT1'
        query += " AND card_number LIKE ?"
        params.append(f"{set_name}%") # Searching for cards STARTING with the input
    if effect_text:
        query += " AND (main_effect LIKE ? OR source_effect LIKE ? OR alt_effect LIKE ?)"
        params.extend([f"%{effect_text}%"] * 3)

    query += " ORDER BY card_number ASC"

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    return results


def print_card(card):
    print(f"\n{'='*60}")
    print(f"  {card['card_number']} — {card['card_name']}")
    print(f"{'='*60}")
    print(f"  Type      : {card['card_type']}  |  Rarity: {card['rarity']}")
    print(f"  Color     : {card['color']}{' / ' + card['color2'] if card['color2'] else ''}")
    if card['level']:
        print(f"  Level     : Lv.{card['level']}  |  DP: {card['dp']}  |  Cost: {card['play_cost']}")
    if card['attribute']:
        print(f"  Attribute : {card['attribute']}  |  Type: {card['digi_type']}{' / ' + card['digi_type2'] if card['digi_type2'] else ''}")
    if card['form']:
        print(f"  Form      : {card['form']}  |  Stage: {card['stage']}")
    if card['evolution_cost']:
        print(f"  Evo Cost  : {card['evolution_cost']}  |  Evo Color: {card['evolution_color']}  |  Evo Lv: {card['evolution_level']}")
    print(f"  Set       : {card['set_name']}")
    if card['main_effect']:
        print(f"\n  [Effect]\n  {card['main_effect']}")
    if card['source_effect']:
        print(f"\n  [Inherited Effect]\n  {card['source_effect']}")
    if card['alt_effect']:
        print(f"\n  [Security Effect]\n  {card['alt_effect']}")


def interactive_search():
    print("\n╔══════════════════════════════════╗")
    print("║   Digimon Card Database Search   ║")
    print("╚══════════════════════════════════╝")
    print("  Leave blank to skip any filter.\n")

    name       = input("  Card name (partial ok): ").strip() or None
    card_type  = input("  Type (Digimon/Tamer/Option): ").strip() or None
    color      = input("  Color (Red/Blue/Yellow/Green/Black/Purple/White): ").strip() or None
    rarity     = input("  Rarity (c/u/r/sr/sec): ").strip() or None
    level_in   = input("  Level (2-7): ").strip()
    level      = int(level_in) if level_in else None
    min_dp_in  = input("  Min DP: ").strip()
    min_dp     = int(min_dp_in) if min_dp_in else None
    max_dp_in  = input("  Max DP: ").strip()
    max_dp     = int(max_dp_in) if max_dp_in else None
    min_cost_in= input("  Min play cost: ").strip()
    min_cost   = int(min_cost_in) if min_cost_in else None
    max_cost_in= input("  Max play cost: ").strip()
    max_cost   = int(max_cost_in) if max_cost_in else None
    attribute  = input("  Attribute (Vaccine/Virus/Data/Free/Variable/Unknown): ").strip() or None
    digi_type  = input("  Digimon type (e.g. Dragon, Beast, Wizard): ").strip() or None
    set_name   = input("  Set name (partial ok, e.g. BT-04): ").strip() or None
    effect_text= input("  Effect contains text: ").strip() or None

    
    results = search_cards(
        name=name,
        card_type=card_type,
        color=color,
        rarity=rarity,
        level=level,
        min_dp=min_dp,
        max_dp=max_dp,
        min_cost=min_cost,
        max_cost=max_cost,
        attribute=attribute,
        digi_type=digi_type,
        set_name=set_name,
        effect_text=effect_text,
    )

    print(f"\n  Found {len(results)} card(s).\n")

    if not results:
        return

    # If many results, ask before printing all
    if len(results) > 10:
        show = input(f"  Show all {len(results)} cards? (y/n, or enter a number): ").strip()
        if show.lower() == 'n':
            return
        elif show.isdigit():
            results = results[:int(show)]

    for card in results:
        print_card(card)

    print(f"\n{'='*60}")
    print(f"  Total results: {len(results)}")


if __name__ == "__main__":
    while True:
        interactive_search()
        again = input("\n  Search again? (y/n): ").strip().lower()
        if again != 'y':
            print("\n  Goodbye!\n")
            break