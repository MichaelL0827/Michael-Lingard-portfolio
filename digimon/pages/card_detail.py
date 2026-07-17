"""
pages/1_Card_Details.py
───────────────────────
Full card detail view.

Navigation:
  - Arrived here from the main card browser with ?card=BT25-001
  - Or search directly from this page
"""

import html
import streamlit as st
from query_db import get_card, search_cards

st.set_page_config(
    page_title="Card Details — Digimon Card Database",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    background-color: #0a0e1a;
    color: #e0e8ff;
    font-family: 'Rajdhani', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1526 0%, #0a0e1a 100%);
    border-right: 1px solid #1e3a5f;
}
h1 {
    font-family: 'Orbitron', monospace !important;
    font-weight: 900 !important;
    background: linear-gradient(90deg, #00d4ff, #7b2fff, #ff6b35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
    text-align: center;
    padding: 1rem 0 0.25rem;
}
.detail-box {
    background: linear-gradient(145deg, #0d1a2e, #0a1220);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 20px;
}
.detail-label {
    font-size: 0.65rem;
    color: #4a7fa5;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 12px;
}
.detail-value {
    font-size: 0.95rem;
    color: #e0e8ff;
    font-weight: 600;
    margin-bottom: 4px;
}
.effect-box {
    background: #080c18;
    border-left: 3px solid #00d4ff;
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin-top: 8px;
}
.effect-label {
    font-size: 0.65rem;
    color: #4a7fa5;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
    font-family: 'Orbitron', monospace;
}
.effect-text {
    font-size: 0.85rem;
    color: #8aa8c8;
    line-height: 1.7;
}
.card-title-large {
    font-family: 'Orbitron', monospace;
    font-size: 1.4rem;
    font-weight: 900;
    color: #e0e8ff;
    margin-bottom: 4px;
}
.card-number-large {
    font-family: 'Orbitron', monospace;
    font-size: 0.8rem;
    color: #4a7fa5;
    letter-spacing: 2px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    margin: 2px 3px 0 0;
    text-transform: uppercase;
}
.badge-red    { background: #3d0a0a; color: #ff5555; border: 1px solid #7a1515; }
.badge-blue   { background: #0a1a3d; color: #55aaff; border: 1px solid #155a7a; }
.badge-yellow { background: #2d2500; color: #ffdd55; border: 1px solid #665500; }
.badge-green  { background: #0a2d0a; color: #55cc55; border: 1px solid #156615; }
.badge-black  { background: #1a1a1a; color: #aaaaaa; border: 1px solid #444;    }
.badge-purple { background: #1e0a3d; color: #bb55ff; border: 1px solid #55157a; }
.badge-white  { background: #1e2535; color: #ddeeff; border: 1px solid #3a4a65; }
.badge-multi  { background: #1a1000; color: #ffaa00; border: 1px solid #664400; }
.badge-sr  { background: #2d1a00; color: #ffaa33; border: 1px solid #664400; }
.badge-ur  { background: #C2B067; color: #EFBF04; border: 1px solid #FCD748; }
.badge-r   { background: #0a1e3d; color: #55aaff; border: 1px solid #15447a; }
.badge-u   { background: #1a0a2d; color: #aa77ff; border: 1px solid #44157a; }
.badge-c   { background: #0d1526; color: #778899; border: 1px solid #2a3a4a; }
.badge-sec { background: #2d0a1a; color: #ff55aa; border: 1px solid #7a1544; }
.badge-p   { background: #1a2d1a; color: #55ff99; border: 1px solid #156635; }
.badge-lm  { background: #3dbbba; color: #f0e4e0; border: 1px solid #942e15; }
[data-baseweb="menu"] { background-color: #0d1a2e !important; border: 1px solid #1e3a5f !important; }
[data-baseweb="menu"] li { background-color: #0d1a2e !important; color: #e0e8ff !important; }
[data-baseweb="menu"] li:hover { background-color: #1e3a5f !important; color: #00d4ff !important; }
[data-baseweb="popover"] { z-index: 9999 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def color_badge(color: str) -> str:
    if not color:
        return ""
    cls = {
        "red": "badge-red", "blue": "badge-blue", "yellow": "badge-yellow",
        "green": "badge-green", "black": "badge-black", "purple": "badge-purple",
        "white": "badge-white",
    }.get(color.lower(), "badge-multi")
    return f'<span class="badge {cls}">{color}</span>'


def rarity_badge(rarity: str) -> str:
    if not rarity:
        return ""
    key    = rarity.lower()
    cls    = {"sr": "badge-sr", "r": "badge-r", "u": "badge-u", "c": "badge-c",
              "ur": "badge-ur", "sec": "badge-sec", "p": "badge-p"}.get(key, "badge-c")
    labels = {"sr": "Super Rare", "r": "Rare", "u": "Uncommon", "c": "Common",
              "ur": "Ultra Rare", "sec": "Secret", "p": "Promo"}
    return f'<span class="badge {cls}">{labels.get(key, rarity.upper())}</span>'


def stat_row(label: str, value) -> str:
    if value is None:
        return ""
    return (
        f'<div class="detail-label">{html.escape(label)}</div>'
        f'<div class="detail-value">{html.escape(str(value))}</div>'
    )


def render_effects(card: dict) -> None:
    if card.get("main_effect"):
        for line in card["main_effect"].split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("["):
                bracket_end = line.find("]")
                if bracket_end != -1:
                    label = line[1:bracket_end]
                    text  = line[bracket_end + 1:].strip()
                    st.html(
                        f'<div class="effect-box">'
                        f'<div class="effect-label">{html.escape(label)}</div>'
                        f'<div class="effect-text">{html.escape(text)}</div>'
                        f'</div>'
                    )
                    continue
            st.html(f'<div class="effect-box"><div class="effect-text">{html.escape(line)}</div></div>')

    if card.get("source_effect"):
        st.html(
            f'<div class="effect-box" style="border-left-color:#7b2fff">'
            f'<div class="effect-label">Inherited Effect</div>'
            f'<div class="effect-text">{html.escape(card["source_effect"])}</div>'
            f'</div>'
        )

    if card.get("alt_effect"):
        st.html(
            f'<div class="effect-box" style="border-left-color:#ff6b35">'
            f'<div class="effect-label">Security Effect</div>'
            f'<div class="effect-text">{html.escape(card["alt_effect"])}</div>'
            f'</div>'
        )

    if not any([card.get("main_effect"), card.get("source_effect"), card.get("alt_effect")]):
        st.caption("No effects on this card.")


# ── Sidebar search ────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## FIND A CARD")
    search_name = st.text_input("Card Name or Number", placeholder="e.g. Agumon or BT1-010")

    if search_name:
        # Try direct ID lookup first
        direct = get_card(search_name.strip().upper())
        if direct:
            results = [direct]
        else:
            results = search_cards(name=search_name.strip())

        if results:
            options = {f"{c['card_number']} — {c['card_name']}": c["card_number"]
                       for c in results[:50]}
            choice = st.selectbox("Results", list(options.keys()), key="card_choice")
            selected_id = options[choice]
            # Store in query params so the URL is shareable
            st.query_params["card"] = selected_id
        else:
            st.caption("No cards found.")


# ── Main content ──────────────────────────────────────────────────────────────

st.markdown("# ⬡ CARD DETAILS")

# Read card from query params (set by sidebar or linked from main page)
card_id = st.query_params.get("card")

if not card_id:
    st.markdown(
        '<div style="text-align:center;padding:4rem;color:#2a4a6a;'
        'font-family:Orbitron,monospace;letter-spacing:2px">'
        'SEARCH FOR A CARD TO VIEW DETAILS</div>',
        unsafe_allow_html=True,
    )
    st.stop()

card = get_card(card_id)

if not card:
    st.error(f"Card '{card_id}' not found in database.")
    st.stop()

# ── Two-column layout: image | details ────────────────────────────────────────

img_col, info_col = st.columns([1, 2])

with img_col:
    img_url = f"https://images.digimoncard.io/images/cards/{card['card_number']}.jpg"
    st.image(img_url, use_container_width=True)

    # Quick-add to deck builder via session state
    if st.button("＋ ADD TO DECK BUILDER", use_container_width=True):
        if "deck_main" not in st.session_state:
            st.session_state.deck_main = {}
        target = "deck_eggs" if card["card_type"] == "Digi-Egg" else "deck_main"
        if target not in st.session_state:
            st.session_state[target] = {}
        current = st.session_state[target].get(card["card_number"], 0)
        st.session_state[target][card["card_number"]] = current + 1
        st.success(f"Added to deck builder — switch to Deck Builder page to view.")

with info_col:
    # Header
    colors_html = "".join(color_badge(c) for c in
                          [card.get("color"), card.get("color2"), card.get("color3")] if c)
    st.html(
        f'<div class="detail-box">'
        f'<div class="card-number-large">{html.escape(card["card_number"])}</div>'
        f'<div class="card-title-large">{html.escape(card["card_name"])}</div>'
        f'<div style="margin:8px 0">{colors_html} {rarity_badge(card.get("rarity", ""))}</div>'
        f'</div>'
    )

    # Stats grid
    st.markdown("---")
    stat_cols = st.columns(4)

    stats = [
        ("Card Type",  card.get("card_type")),
        ("Level",      f'Lv.{card["level"]}' if card.get("level") else None),
        ("Form",       card.get("form")),
        ("Attribute",  card.get("attribute")),
        ("Type",       card.get("digi_type")),
        ("DP",         f'{card["dp"]:,}' if card.get("dp") else None),
        ("Play Cost",  card.get("play_cost")),
        ("Evo. Cost",  card.get("evolution_cost")),
        ("Evo. Color", card.get("evolution_color")),
        ("Evo. Level", f'Lv.{card["evolution_level"]}' if card.get("evolution_level") else None),
        ("Set",        card.get("set_name")),
        ("Rarity",     card.get("rarity", "").upper()),
    ]

    visible = [(l, v) for l, v in stats if v is not None]
    for idx, (label, value) in enumerate(visible):
        with stat_cols[idx % 4]:
            st.html(stat_row(label, value))

# ── Effects ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### EFFECTS")
render_effects(card)