import re
import streamlit as st
import html
from difflib import SequenceMatcher
from urllib.parse import quote
from query_db import search_cards, get_card_count, get_sets_with_metadata

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Digimon Card Database",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    background-color: #0a0e1a;
    color: #e0e8ff;
    font-family: 'Rajdhani', sans-serif;
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

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1px;
    margin: 2px 2px 0 0;
    text-transform: uppercase;
}
.badge-red    { background: #3d0a0a; color: #ff5555; border: 1px solid #7a1515; }
.badge-blue   { background: #0a1a3d; color: #55aaff; border: 1px solid #155a7a; }
.badge-yellow { background: #2d2500; color: #ffdd55; border: 1px solid #665500; }
.badge-green  { background: #0a2d0a; color: #55cc55; border: 1px solid #156615; }
.badge-black  { background: #1a1a1a; color: #aaaaaa; border: 1px solid #444; }
.badge-purple { background: #1e0a3d; color: #bb55ff; border: 1px solid #55157a; }
.badge-white  { background: #1e2535; color: #ddeeff; border: 1px solid #3a4a65; }
.badge-multi  { background: #1a1000; color: #ffaa00; border: 1px solid #664400; }
.badge-sr     { background: #2d1a00; color: #ffaa33; border: 1px solid #664400; }
.badge-ur     { background: #3f1258; color: #b56edc; border: 1px solid #b56edc; }
.badge-r      { background: #0a1e3d; color: #55aaff; border: 1px solid #15447a; }
.badge-u      { background: #1a0a2d; color: #aa77ff; border: 1px solid #44157a; }
.badge-c      { background: #0d1526; color: #778899; border: 1px solid #2a3a4a; }
.badge-sec    { background: #2d0a1a; color: #ff55aa; border: 1px solid #7a1544; }
.badge-p      { background: #1a2d1a; color: #55ff99; border: 1px solid #156635; }
.badge-lm     { background: #1a1a2d; color: #8899ff; border: 1px solid #3535a0; }
.badge-egg    { background: #0a2020; color: #55ffee; border: 1px solid #156655; }
.result-count {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    color: #4a7fa5;
    letter-spacing: 2px;
    text-align: center;
    padding: 0.5rem 0 1rem;
}
.no-results {
    text-align: center;
    padding: 4rem;
    color: #2a4a6a;
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    letter-spacing: 2px;
}
.db-status {
    font-family: 'Orbitron', monospace;
    font-size: 0.65rem;
    color: #2a5a3a;
    letter-spacing: 1px;
    text-align: center;
    padding: 4px 8px;
    border: 1px solid #1a3a2a;
    border-radius: 4px;
    background: #0a1a0e;
    margin-bottom: 1rem;
}
.set-name {
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    color: #e0e8ff;
    font-weight: 600;
    margin-top: 6px;
    line-height: 1.3;
}
.set-count {
    font-size: 0.65rem;
    color: #4a7fa5;
    letter-spacing: 1px;
}
.stButton button {
    background: linear-gradient(135deg, #0d1a2e, #1e3a5f) !important;
    border: 1px solid #00d4ff !important;
    color: #00d4ff !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 2px !important;
    width: 100%;
}
.stButton button:hover {
    background: linear-gradient(135deg, #1e3a5f, #0d4a6a) !important;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.3) !important;
}
div[data-testid="stExpander"] {
    border: 1px solid #1e3a5f !important;
    background: #0a0e1a !important;
    border-radius: 4px !important;
}
div[data-testid="stExpander"] summary {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.65rem !important;
    color: #4a7fa5 !important;
    letter-spacing: 1px !important;
}
[data-baseweb="menu"] li:first-child {
    display: none !important;
}
div[data-testid="stExpander"] > div[role="button"] {
    padding: 6px 12px !important;
}
</style>
""", unsafe_allow_html=True)

# --- Title ----------------------------------------------------
st.title("Digimon Delver")

# ── Cached data loaders ────────────────────────────────────────────────────────

@st.cache_data
def cached_search(**kwargs):
    """Cache search results so filters don't re-query on every widget interaction."""
    return search_cards(**kwargs)

@st.cache_data
def cached_card_count():
    return get_card_count()

@st.cache_data
def cached_sets_with_metadata():
    return get_sets_with_metadata()


# ── Render helpers ─────────────────────────────────────────────────────────────

def color_badge(color):
    if not color:
        return ""
    key = color.lower()
    cls = {
        "red":    "badge-red",
        "blue":   "badge-blue",
        "yellow": "badge-yellow",
        "green":  "badge-green",
        "black":  "badge-black",
        "purple": "badge-purple",
        "white":  "badge-white",
    }.get(key, "badge-multi")
    return f'<span class="badge {cls}">{color}</span>'


def rarity_badge(rarity):
    if not rarity:
        return ""
    key = rarity.lower()
    cls    = {"sr": "badge-sr", "r": "badge-r", "u": "badge-u",
              "c": "badge-c", "ur": "badge-ur", "sec": "badge-sec", "p": "badge-p",
              "lm": "badge-lm"}.get(key, "badge-c")
    labels = {"sr": "Super Rare", "r": "Rare", "u": "Uncommon",
              "c": "Common", "ur": "Ultra Rare", "sec": "Secret", "p": "Promo",
              "lm": "Limited"}
    return f'<span class="badge {cls}">{labels.get(key, rarity.upper())}</span>'


def render_card_tile(card):
    """Image-only grid tile with a hover overlay showing card number + name,
    linking through to the card detail page."""
    cn    = card["card_number"]
    cname = card["card_name"]
    img_url    = f"https://images.digimoncard.io/images/cards/{cn}.jpg"
    detail_url = f"/card_detail?card={quote(cn)}"

    st.markdown(f'''
        <a href="{detail_url}" target="_self" style="text-decoration:none">
        <div style="position:relative;cursor:pointer">
            <img src="{img_url}" style="width:100%;border-radius:6px;display:block">
            <div style="
                position:absolute;bottom:0;left:0;right:0;
                background:linear-gradient(transparent,rgba(0,0,0,0.85));
                border-radius:0 0 6px 6px;
                padding:24px 8px 8px;
                opacity:0;transition:opacity 0.2s;
            " onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0">
                <div style="font-family:Orbitron,monospace;font-size:0.6rem;
                        color:#4a7fa5;letter-spacing:1px">{html.escape(cn)}</div>
                <div style="font-size:0.8rem;color:#e0e8ff;font-weight:600">{html.escape(cname)}</div>
            </div>
        </div>
        </a>
    ''', unsafe_allow_html=True)


# ── Set search scoring ─────────────────────────────────────────────────────────

def _score_set(query: str, set_name: str) -> float:
    """
    Score a set name against a search query, returning 0.0–1.0.
    Higher = better match. Uses several strategies in priority order:

      1. Exact substring            — "dual" in "DUAL REVOLUTION"
      2. Normalised substring       — "bt25" matches "BT-25" after stripping
                                      hyphens/brackets/spaces from both sides
      3. All query tokens present   — "red starter" matches
                                      "Starter Deck GAIA RED [ST-1]"
      4. Any query token present    — partial word hit
      5. Fuzzy similarity fallback  — catches typos like "duel" → "dual"
    """
    q = query.lower().strip()
    s = set_name.lower()

    # 1. Exact substring
    if q in s:
        return 1.0

    # 2. Normalised (strip non-alphanumeric) substring
    q_norm = re.sub(r"[^a-z0-9]", "", q)
    s_norm = re.sub(r"[^a-z0-9]", "", s)
    if q_norm and q_norm in s_norm:
        return 0.9

    # 3. All query tokens appear somewhere in the set name
    tokens = q.split()
    if tokens and all(t in s for t in tokens):
        return 0.8

    # 4. Any query token appears in the set name
    if tokens and any(t in s for t in tokens):
        return 0.6

    # 5. Fuzzy similarity (catches typos — SequenceMatcher is built-in)
    return SequenceMatcher(None, q, s).ratio()


def _search_sets(query: str, sets: list[dict]) -> list[dict]:
    """
    Return sets sorted by match score, filtering out poor matches
    (score below 0.3 — avoids returning completely unrelated sets).
    """
    if not query.strip():
        return sets

    scored = [
        (s, _score_set(query, s["set_name"]))
        for s in sets
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, score in scored if score >= 0.3]


# ── Set browser (landing page) ─────────────────────────────────────────────────

def render_set_browser():
    try:
        count = cached_card_count()
        st.html(f'<div class="db-status">⬡ {count:,} CARDS IN DATABASE</div>')
    except Exception:
        st.warning("Database not found — run scraper.py first.")
        return

    try:
        sets = cached_sets_with_metadata()
    except Exception:
        st.error("get_sets_with_metadata() not found — add it to query_db.py first.")
        return

    set_search = st.text_input(
        "Filter sets", placeholder="e.g. BT25, dual revolution, starter red…",
        label_visibility="collapsed", key="set_search"
    )
    sets = _search_sets(set_search, sets)

    st.html(f'<div class="result-count">{len(sets)} SET{"S" if len(sets) != 1 else ""}</div>')

    if not sets:
        st.html('<div class="no-results">NO SETS FOUND — ADJUST FILTER</div>')
        return

    SETS_PER_ROW = 4
    cols = st.columns(SETS_PER_ROW)
    for i, s in enumerate(sets):
        with cols[i % SETS_PER_ROW]:
            img_url   = s.get("box_art_url") or f"https://images.digimoncard.io/images/cards/{s['first_card']}.jpg"
            set_param = quote(s["set_name"])

            st.markdown(f'''
                <a href="?set={set_param}" target="_self" style="text-decoration:none">
                <div style="position:relative;cursor:pointer">
                    <img src="{img_url}" style="width:100%;border-radius:6px;display:block">
                    <div style="
                        position:absolute;bottom:0;left:0;right:0;
                        background:linear-gradient(transparent,rgba(0,0,0,0.85));
                        border-radius:0 0 6px 6px;
                        padding:24px 8px 8px;
                        opacity:0;transition:opacity 0.2s;
                    " onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0">
                        <div style="font-size:0.8rem;color:#e0e8ff;font-weight:600">{html.escape(s["set_name"])}</div>
                    </div>
                </div>
                </a>
            ''', unsafe_allow_html=True)

            st.html(
                f'<div class="set-name">{html.escape(s["set_name"])}</div>'
                f'<div class="set-count">{s["card_count"]} cards</div>'
            )


# ── Card view (drill-down into one set) ────────────────────────────────────────

def render_card_view(set_name):
    if st.button("← BACK TO SETS"):
        st.query_params.clear()
        st.rerun()

    st.html(f'<div class="result-count">{html.escape(set_name)}</div>')

    # ── Filter bar ───────────────────────────────────────────────────────────────
    r1c1, r1c2, r1c3, r1c4 = st.columns([3, 1.5, 2, 2])

    with r1c1:
        name = st.text_input(
            "Search", placeholder="Card name or effect text…",
            label_visibility="collapsed", key="f_name"
        )
    with r1c2:
        card_type = st.selectbox(
            "Type", ["All", "Digimon", "Digi-Egg", "Tamer", "Option"],
            label_visibility="collapsed", key="f_type"
        )
    with r1c3:
        selected_colors = st.multiselect(
            "Color",
            ["Red", "Blue", "Yellow", "Green", "Purple", "Black", "White"],
            placeholder="Color…",
            label_visibility="collapsed", key="f_colors"
        )
    with r1c4:
        selected_levels = st.multiselect(
            "Level", [2, 3, 4, 5, 6, 7],
            format_func=lambda x: f"Lv.{x}",
            placeholder="Level…",
            label_visibility="collapsed", key="f_levels"
        )

    # Row 2 — advanced filters in expander (no Set dropdown — already locked to set_name)
    with st.expander("More filters"):
        a1, a2, a3 = st.columns(3)
        with a1:
            selected_attribute = st.multiselect(
                "Attribute",
                ["Vaccine", "Virus", "Data", "Free", "Variable", "Unknown"],
                max_selections=1, key="f_attr"
            )
        with a2:
            rarity = st.selectbox(
                "Rarity", ["All", "c", "u", "r", "sr", "ur", "sec", "p", "lm"],
                key="f_rarity"
            )
        with a3:
            digi_type = st.text_input(
                "Digimon Type", placeholder="e.g. Dragon, Beast", key="f_dtype"
            )

        b1, b2, b3, b4, b5 = st.columns(5)
        with b1: min_dp   = st.number_input("Min DP",   min_value=0, value=0, step=1000, key="f_mindp")
        with b2: max_dp   = st.number_input("Max DP",   min_value=0, value=0, step=1000, key="f_maxdp")
        with b3: min_cost = st.number_input("Min Cost", min_value=0, value=0, key="f_minc")
        with b4: max_cost = st.number_input("Max Cost", min_value=0, value=0, key="f_maxc")
        with b5: cards_per_row = st.slider("Per row", 3, 8, 6, key="f_cpr")

        if st.button("CLEAR CACHE"):
            st.cache_data.clear()
            st.success("Cache cleared.")

    # ── Search — always scoped to this set ───────────────────────────────────────

    def run_search(color_filter):
        return cached_search(
            name        = name.strip() or None,
            card_type   = None if card_type == "All" else card_type,
            color       = color_filter,
            rarity      = None if rarity == "All" else rarity,
            levels      = tuple(selected_levels) if selected_levels else None,
            attribute   = selected_attribute[0] if selected_attribute else None,
            digi_type   = digi_type.strip() or None,
            set_name    = set_name,               # locked to the selected set
            effect_text = name.strip() or None,
            min_dp      = min_dp   if min_dp   > 0 else None,
            max_dp      = max_dp   if max_dp   > 0 else None,
            min_cost    = min_cost if min_cost > 0 else None,
            max_cost    = max_cost if max_cost > 0 else None,
        )

    if selected_colors:
        result_sets  = [set(r["card_number"] for r in run_search(c)) for c in selected_colors]
        matching_ids = result_sets[0].intersection(*result_sets[1:])
        all_results  = run_search(selected_colors[0])
        results      = [r for r in all_results if r["card_number"] in matching_ids]
    else:
        results = run_search(None)

    # ── Results grid ───────────────────────────────────────────────────────────────

    if results:
        PAGE_SIZE = 80
        total     = len(results)
        max_pages = max(1, -(-total // PAGE_SIZE))

        st.html(f'<div class="result-count">{total} CARD{"S" if total != 1 else ""} FOUND</div>')

        # Key includes set_name so pagination resets when switching sets
        page  = st.number_input(
            "Page", min_value=1, max_value=max_pages, value=1, step=1,
            key=f"page_{set_name}"
        )
        start = (page - 1) * PAGE_SIZE
        end   = min(start + PAGE_SIZE, total)

        st.html(f'<div class="result-count">SHOWING {start + 1}–{end} OF {total}</div>')

        cols = st.columns(cards_per_row)
        for i, card in enumerate(results[start:end]):
            with cols[i % cards_per_row]:
                render_card_tile(card)
    else:
        st.html('<div class="no-results">NO CARDS FOUND — ADJUST FILTERS</div>')


# ── Routing ────────────────────────────────────────────────────────────────────
# No "set" query param → show the set browser.
# "?set=<name>" present → drill into that set's card list.

selected_set = st.query_params.get("set")

if selected_set:
    render_card_view(selected_set)
else:
    render_set_browser()