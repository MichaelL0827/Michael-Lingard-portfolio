"""
pages/2_Deck_Builder.py
────────────────────────
Deck building page. Allows searching cards, adding them to a
main deck or egg deck, validating against official rules,
and saving/loading decks from the database.

Deck rules enforced:
  - Main deck: exactly 50 cards, max 4 copies of any card
  - Egg deck:  0–5 cards,        max 4 copies of any egg card
  - Digi-Eggs go to egg deck only; all other types to main deck
"""

import html
import streamlit as st
from query_db import (
    search_cards, get_card,
    init_deck_tables, list_decks, save_deck, load_deck, delete_deck,
    validate_deck, DECK_RULES,
)

st.set_page_config(
    page_title="Deck Builder — Digimon Card Database",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
html, body, [class*="css"] { background-color: #0a0e1a; color: #e0e8ff; font-family: 'Rajdhani', sans-serif; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1526 0%, #0a0e1a 100%); border-right: 1px solid #1e3a5f; }
h1 { font-family: 'Orbitron', monospace !important; font-weight: 900 !important; background: linear-gradient(90deg, #00d4ff, #7b2fff, #ff6b35); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 2px; text-align: center; padding: 1rem 0 0.25rem; }
[data-testid="stSidebar"] h2 { font-family: 'Orbitron', monospace !important; font-size: 0.9rem !important; color: #00d4ff !important; letter-spacing: 2px; border-bottom: 1px solid #1e3a5f; padding-bottom: 0.5rem; }
.card-row { display: flex; align-items: center; gap: 10px; background: #0d1a2e; border: 1px solid #1e3a5f; border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; }
.card-row:hover { border-color: #00d4ff; }
.card-row-name { font-family: 'Orbitron', monospace; font-size: 0.75rem; color: #e0e8ff; flex: 1; }
.card-row-id { font-size: 0.65rem; color: #4a7fa5; letter-spacing: 1px; }
.card-row-qty { font-family: 'Orbitron', monospace; font-size: 0.9rem; color: #00d4ff; font-weight: 700; min-width: 24px; text-align: center; }
.deck-section { font-family: 'Orbitron', monospace; font-size: 0.8rem; color: #00d4ff; letter-spacing: 2px; border-bottom: 1px solid #1e3a5f; padding-bottom: 6px; margin: 12px 0 8px; }
.deck-count { font-family: 'Orbitron', monospace; font-size: 0.7rem; letter-spacing: 1px; }
.count-ok   { color: #55cc55; }
.count-warn { color: #ffaa33; }
.count-bad  { color: #ff5555; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 0.6rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.badge-red    { background: #3d0a0a; color: #ff5555; border: 1px solid #7a1515; }
.badge-blue   { background: #0a1a3d; color: #55aaff; border: 1px solid #155a7a; }
.badge-yellow { background: #2d2500; color: #ffdd55; border: 1px solid #665500; }
.badge-green  { background: #0a2d0a; color: #55cc55; border: 1px solid #156615; }
.badge-black  { background: #1a1a1a; color: #aaaaaa; border: 1px solid #444;    }
.badge-purple { background: #1e0a3d; color: #bb55ff; border: 1px solid #55157a; }
.badge-white  { background: #1e2535; color: #ddeeff; border: 1px solid #3a4a65; }
.badge-multi  { background: #1a1000; color: #ffaa00; border: 1px solid #664400; }
.stButton button { background: linear-gradient(135deg, #0d1a2e, #1e3a5f) !important; border: 1px solid #00d4ff !important; color: #00d4ff !important; font-family: 'Orbitron', monospace !important; font-size: 0.65rem !important; letter-spacing: 1px !important; }
.stButton button:hover { background: linear-gradient(135deg, #1e3a5f, #0d4a6a) !important; box-shadow: 0 0 12px rgba(0,212,255,0.3) !important; }
[data-baseweb="menu"] { background-color: #0d1a2e !important; border: 1px solid #1e3a5f !important; }
[data-baseweb="menu"] li { background-color: #0d1a2e !important; color: #e0e8ff !important; }
[data-baseweb="menu"] li:hover { background-color: #1e3a5f !important; color: #00d4ff !important; }
[data-baseweb="popover"] { z-index: 9999 !important; }
[data-baseweb="menu"] li:first-child { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────

init_deck_tables()

# ── Session state ─────────────────────────────────────────────────────────────
# deck_main: {card_number: quantity}  — main deck cards
# deck_eggs: {card_number: quantity}  — egg deck cards
# deck_name: str                      — current deck name
# deck_id:   int | None               — None if unsaved

for key, default in [("deck_main", {}), ("deck_eggs", {}),
                     ("deck_name", "New Deck"), ("deck_id", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ───────────────────────────────────────────────────────────────────

def color_badge(color: str) -> str:
    if not color:
        return ""
    cls = {"red": "badge-red", "blue": "badge-blue", "yellow": "badge-yellow",
           "green": "badge-green", "black": "badge-black", "purple": "badge-purple",
           "white": "badge-white"}.get(color.lower(), "badge-multi")
    return f'<span class="badge {cls}">{color}</span>'


def add_card(card: dict) -> None:
    """Add one copy of a card to the appropriate deck section."""
    target  = "deck_eggs" if card["card_type"] == "Digi-Egg" else "deck_main"
    max_qty = DECK_RULES["egg_max_copy"] if target == "deck_eggs" else DECK_RULES["main_max_copy"]
    current = st.session_state[target].get(card["card_number"], 0)
    if current < max_qty:
        st.session_state[target][card["card_number"]] = current + 1


def remove_card(card_number: str, target: str) -> None:
    """Remove one copy; delete entry if quantity reaches 0."""
    if card_number in st.session_state[target]:
        st.session_state[target][card_number] -= 1
        if st.session_state[target][card_number] <= 0:
            del st.session_state[target][card_number]


def deck_totals() -> tuple[int, int]:
    main_total = sum(st.session_state.deck_main.values())
    egg_total  = sum(st.session_state.deck_eggs.values())
    return main_total, egg_total


def count_class(current: int, target: int) -> str:
    if current == target:
        return "count-ok"
    if current > target:
        return "count-bad"
    return "count-warn"


# ── Sidebar: card search ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ADD CARDS")

    name      = st.text_input("Card Name", placeholder="e.g. Agumon", key="db_name")
    card_type = st.selectbox("Type", ["All", "Digimon", "Digi-Egg", "Tamer", "Option"],
                             key="db_type")
    color     = st.selectbox("Color",
                             ["All", "Red", "Blue", "Yellow", "Green", "Black", "Purple", "White"],
                             key="db_color")
    levels     = st.selectbox("Level", ["Any", "2", "3", "4", "5", "6", "7"], key="db_level")

    search_results = search_cards(
        name      = name.strip() or None,
        card_type = None if card_type == "All"  else card_type,
        color     = None if color    == "All"  else color,
        levels     = None if levels    == "Any"  else int(levels),
    )

    st.markdown(f"*{len(search_results)} cards found*")
    st.markdown("---")

    # Show search results as compact add buttons
    for card in search_results[:30]:
        cols = st.columns([3, 1])
        colors_html = "".join(color_badge(c) for c in
                              [card.get("color"), card.get("color2")] if c)
        with cols[0]:
            st.html(
                f'<div style="padding:4px 0">'
                f'<div style="font-size:0.65rem;color:#4a7fa5;font-family:Orbitron,monospace">'
                f'{html.escape(card["card_number"])}</div>'
                f'<div style="font-size:0.8rem;color:#e0e8ff;font-weight:600">'
                f'{html.escape(card["card_name"])}</div>'
                f'<div>{colors_html}</div>'
                f'</div>'
            )
        with cols[1]:
            if st.button("＋", key=f"add_{card['card_number']}"):
                add_card(card)
                st.rerun()

    if len(search_results) > 30:
        st.caption(f"Showing 30 of {len(search_results)} — refine your search")


# ── Main: deck view ────────────────────────────────────────────────────────────

st.markdown("# ⬡ DECK BUILDER")

# ── Deck name + save/load controls ────────────────────────────────────────────

ctrl_cols = st.columns([3, 1, 1, 1])

with ctrl_cols[0]:
    st.session_state.deck_name = st.text_input(
        "Deck Name", value=st.session_state.deck_name, key="deck_name_input",
        label_visibility="collapsed"
    )

with ctrl_cols[1]:
    if st.button("💾 SAVE", use_container_width=True):
        deck_id = save_deck(
            name    = st.session_state.deck_name,
            main    = st.session_state.deck_main,
            eggs    = st.session_state.deck_eggs,
            deck_id = st.session_state.deck_id,
        )
        st.session_state.deck_id = deck_id
        st.success(f"Saved as '{st.session_state.deck_name}'")

with ctrl_cols[2]:
    decks = list_decks()
    if decks:
        deck_options = {f"{d['name']} ({d['updated_at'][:10]})": d["id"] for d in decks}
        load_choice  = st.selectbox("Load", ["— select —"] + list(deck_options.keys()),
                                    key="load_select", label_visibility="collapsed")
        if load_choice != "— select —":
            loaded = load_deck(deck_options[load_choice])
            if loaded:
                st.session_state.deck_main = loaded["main"]
                st.session_state.deck_eggs = loaded["eggs"]
                st.session_state.deck_name = loaded["name"]
                st.session_state.deck_id   = loaded["id"]
                st.rerun()

with ctrl_cols[3]:
    if st.button("🗑 CLEAR", use_container_width=True):
        st.session_state.deck_main = {}
        st.session_state.deck_eggs = {}
        st.session_state.deck_name = "New Deck"
        st.session_state.deck_id   = None
        st.rerun()

st.markdown("---")

# ── Two-column: egg deck | main deck ──────────────────────────────────────────

egg_col, main_col = st.columns([1, 2])

main_total, egg_total = deck_totals()

# ── Egg deck ──────────────────────────────────────────────────────────────────
with egg_col:
    egg_cls = count_class(egg_total, DECK_RULES["egg_max"])
    st.html(
        f'<div class="deck-section">EGG DECK '
        f'<span class="deck-count {egg_cls}">({egg_total}/{DECK_RULES["egg_max"]})</span>'
        f'</div>'
    )

    if st.session_state.deck_eggs:
        for cn, qty in sorted(st.session_state.deck_eggs.items()):
            card = get_card(cn)
            name_str = card["card_name"] if card else cn
            c1 = card.get("color") if card else None

            row_cols = st.columns([1, 5, 1])
            with row_cols[0]:
                st.html(f'<div class="card-row-qty">{qty}x</div>')
            with row_cols[1]:
                colors_html = color_badge(c1) if c1 else ""
                st.html(
                    f'<div>'
                    f'<div class="card-row-id">{html.escape(cn)}</div>'
                    f'<div class="card-row-name">{html.escape(name_str)}</div>'
                    f'<div>{colors_html}</div>'
                    f'</div>'
                )
            with row_cols[2]:
                if st.button("−", key=f"rem_egg_{cn}"):
                    remove_card(cn, "deck_eggs")
                    st.rerun()
    else:
        st.caption("No eggs added yet.")

# ── Main deck ─────────────────────────────────────────────────────────────────
with main_col:
    main_cls = count_class(main_total, DECK_RULES["main_exact"])
    st.html(
        f'<div class="deck-section">MAIN DECK '
        f'<span class="deck-count {main_cls}">({main_total}/{DECK_RULES["main_exact"]})</span>'
        f'</div>'
    )

    if st.session_state.deck_main:
        # Group by card type for readability
        type_order = ["Digimon", "Tamer", "Option"]
        grouped: dict[str, list] = {t: [] for t in type_order}
        grouped["Other"] = []

        for cn, qty in st.session_state.deck_main.items():
            card = get_card(cn)
            ctype = card.get("card_type", "Other") if card else "Other"
            bucket = ctype if ctype in grouped else "Other"
            grouped[bucket].append((cn, qty, card))

        for ctype, entries in grouped.items():
            if not entries:
                continue
            type_total = sum(q for _, q, _ in entries)
            st.html(f'<div style="font-size:0.65rem;color:#4a7fa5;letter-spacing:1px;'
                    f'text-transform:uppercase;margin:10px 0 4px">'
                    f'{html.escape(ctype)} ({type_total})</div>')

            for cn, qty, card in sorted(entries, key=lambda x: x[0]):
                name_str = card["card_name"] if card else cn
                c1 = card.get("color") if card else None
                lv = f'Lv.{card["level"]}' if card and card.get("level") else ""

                row_cols = st.columns([1, 6, 1])
                with row_cols[0]:
                    st.html(f'<div class="card-row-qty">{qty}x</div>')
                with row_cols[1]:
                    colors_html = color_badge(c1) if c1 else ""
                    st.html(
                        f'<div>'
                        f'<div class="card-row-id">{html.escape(cn)} {html.escape(lv)}</div>'
                        f'<div class="card-row-name">{html.escape(name_str)}</div>'
                        f'<div>{colors_html}</div>'
                        f'</div>'
                    )
                with row_cols[2]:
                    if st.button("−", key=f"rem_main_{cn}"):
                        remove_card(cn, "deck_main")
                        st.rerun()
    else:
        st.caption("No cards added yet. Search and add cards from the sidebar.")

# ── Validation ────────────────────────────────────────────────────────────────

st.markdown("---")
errors = validate_deck(st.session_state.deck_main, st.session_state.deck_eggs)

if not errors and main_total == DECK_RULES["main_exact"]:
    st.success("✓ Deck is valid and ready to play.")
elif errors:
    for e in errors:
        st.error(e)
else:
    remaining = DECK_RULES["main_exact"] - main_total
    st.info(f"Add {remaining} more card{'s' if remaining != 1 else ''} to complete the main deck.")

# ── Color distribution chart ──────────────────────────────────────────────────

if st.session_state.deck_main:
    st.markdown("---")
    st.markdown("**COLOR DISTRIBUTION**")

    color_counts: dict[str, int] = {}
    for cn, qty in st.session_state.deck_main.items():
        card = get_card(cn)
        if card:
            for color_field in ["color", "color2", "color3"]:
                c = card.get(color_field)
                if c:
                    color_counts[c] = color_counts.get(c, 0) + qty

    if color_counts:
        color_hex = {
            "Red": "#ff5555", "Blue": "#55aaff", "Yellow": "#ffdd55",
            "Green": "#55cc55", "Black": "#aaaaaa", "Purple": "#bb55ff",
            "White": "#ddeeff",
        }
        bar_cols = st.columns(len(color_counts))
        for i, (color, count) in enumerate(sorted(color_counts.items(),
                                                   key=lambda x: -x[1])):
            hex_col = color_hex.get(color, "#ffaa00")
            with bar_cols[i]:
                st.html(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.2rem;font-weight:700;color:{hex_col};'
                    f'font-family:Orbitron,monospace">{count}</div>'
                    f'<div style="font-size:0.65rem;color:#4a7fa5;letter-spacing:1px">'
                    f'{html.escape(color).upper()}</div>'
                    f'</div>'
                )