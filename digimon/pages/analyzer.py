"""
pages/3_Analyzer.py
────────────────────
Database analyzer — visual breakdown of the card collection
(or a chosen subset of sets) using bar charts, donut charts,
and histograms.

All chart data comes from aggregation queries in query_db.py
(get_summary_stats, get_type_distribution, get_color_distribution,
get_rarity_distribution, get_level_distribution,
get_attribute_distribution, get_dp_values, get_cost_values,
get_cards_per_set) — no raw card rows are pulled into this page.
"""

import streamlit as st
import plotly.graph_objects as go

from query_db import (
    get_all_sets,
    get_summary_stats,
    get_type_distribution,
    get_color_distribution,
    get_rarity_distribution,
    get_level_distribution,
    get_attribute_distribution,
    get_dp_values,
    get_cost_values,
    get_cards_per_set,
)

st.set_page_config(
    page_title="Analyzer — Digimon Card Database",
    layout="wide",
)

# ── Theme CSS (matches app.py / other pages) ────────────────────────────────────
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
    padding: 2rem;
    color: #2a4a6a;
    font-family: 'Orbitron', monospace;
    font-size: 0.85rem;
    letter-spacing: 2px;
}
.chart-card {
    background: linear-gradient(145deg, #0d1a2e, #0a1220);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 6px;
    margin-bottom: 18px;
}
[data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    color: #00d4ff !important;
}
[data-testid="stMetricLabel"] {
    color: #4a7fa5 !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0d1a2e, #0a1220);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 10px 14px;
}
[data-baseweb="menu"] {
    background-color: #0d1a2e !important;
    border: 1px solid #1e3a5f !important;
}
[data-baseweb="menu"] li {
    background-color: #0d1a2e !important;
    color: #e0e8ff !important;
}
[data-baseweb="menu"] li:hover {
    background-color: #1e3a5f !important;
    color: #00d4ff !important;
}
[data-baseweb="popover"] { z-index: 9999 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⬡ DATABASE ANALYZER")


# ── Cached data loaders ────────────────────────────────────────────────────────

@st.cache_data
def cached_set_list():
    return get_all_sets()

@st.cache_data
def cached_stats(set_names):
    return get_summary_stats(set_names or None)

@st.cache_data
def cached_type_dist(set_names):
    return get_type_distribution(set_names or None)

@st.cache_data
def cached_color_dist(set_names):
    return get_color_distribution(set_names or None)

@st.cache_data
def cached_rarity_dist(set_names):
    return get_rarity_distribution(set_names or None)

@st.cache_data
def cached_level_dist(set_names):
    return get_level_distribution(set_names or None)

@st.cache_data
def cached_attr_dist(set_names):
    return get_attribute_distribution(set_names or None)

@st.cache_data
def cached_dp_values(set_names):
    return get_dp_values(set_names or None)

@st.cache_data
def cached_cost_values(set_names):
    return get_cost_values(set_names or None)

@st.cache_data
def cached_cards_per_set(set_names):
    return get_cards_per_set(set_names or None)


# ── Color palettes (matched to the app's badge colors) ──────────────────────────

COLOR_HEX = {
    "Red": "#ff5555", "Blue": "#55aaff", "Yellow": "#ffdd55",
    "Green": "#55cc55", "Black": "#aaaaaa", "Purple": "#bb55ff",
    "White": "#ddeeff",
}
TYPE_HEX = {
    "Digimon": "#00d4ff", "Digi-Egg": "#55ffee",
    "Tamer": "#7b2fff", "Option": "#ff6b35",
}
ATTRIBUTE_HEX = {
    "Vaccine": "#55cc55", "Virus": "#ff5555", "Data": "#55aaff",
    "Free": "#ffdd55", "Variable": "#bb55ff", "Unknown": "#aaaaaa",
}
RARITY_ORDER  = ["c", "u", "r", "sr", "ur", "sec", "p", "lm"]
RARITY_LABELS = {"c": "Common", "u": "Uncommon", "r": "Rare", "sr": "Super Rare",
                  "ur": "Ultra Rare", "sec": "Secret", "p": "Promo", "lm": "Limited"}
RARITY_HEX    = {"c": "#778899", "u": "#aa77ff", "r": "#55aaff", "sr": "#ffaa33",
                  "ur": "#b56edc", "sec": "#ff55aa", "p": "#55ff99", "lm": "#8899ff"}

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d1a2e",
    font=dict(family="Rajdhani, sans-serif", color="#e0e8ff", size=12),
    margin=dict(l=10, r=10, t=44, b=10),
    legend=dict(font=dict(color="#e0e8ff", size=11)),
    # height intentionally omitted — each chart sets its own below
)

def _title(text: str) -> dict:
    return dict(text=text, font=dict(family="Orbitron, monospace", size=13, color="#00d4ff"))


# ── Chart builders ────────────────────────────────────────────────────────────

def donut(labels, values, color_map, title, fallback="#888888"):
    colors = [color_map.get(l, fallback) for l in labels]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0a0e1a", width=2)),
        textfont=dict(color="#e0e8ff", family="Rajdhani, sans-serif", size=12),
        textinfo="label+percent",
    )])
    fig.update_layout(**DARK_LAYOUT, title=_title(title), showlegend=False, height=320)
    return fig


def bar(x, y, colors, title, xaxis_title=""):
    fig = go.Figure(data=[go.Bar(x=x, y=y, marker_color=colors)])
    fig.update_layout(
        **DARK_LAYOUT, title=_title(title),
        xaxis=dict(gridcolor="#1e3a5f", title=xaxis_title),
        yaxis=dict(gridcolor="#1e3a5f"),
        height=320,
    )
    return fig


def histogram(values, title, xaxis_title="", color="#00d4ff", nbins=None):
    fig = go.Figure(data=[go.Histogram(
        x=values, marker_color=color, opacity=0.85, nbinsx=nbins
    )])
    fig.update_layout(
        **DARK_LAYOUT, title=_title(title),
        xaxis=dict(gridcolor="#1e3a5f", title=xaxis_title),
        yaxis=dict(gridcolor="#1e3a5f", title="Cards"),
        bargap=0.05,
        height=320,
    )
    return fig


def hbar(labels, values, title, color="#00d4ff"):
    fig = go.Figure(data=[go.Bar(
        x=values, y=labels, orientation="h", marker_color=color
    )])
    fig.update_layout(
        **DARK_LAYOUT, title=_title(title),
        xaxis=dict(gridcolor="#1e3a5f"),
        yaxis=dict(gridcolor="#1e3a5f", autorange="reversed"),
        height=max(320, 26 * len(labels)),  # grows with number of bars
    )
    return fig


def empty(message="No data available for this selection."):
    st.html(f'<div class="no-results">{message}</div>')


# ── Scope selector ────────────────────────────────────────────────────────────

try:
    all_sets = cached_set_list()
except Exception:
    st.error("Database not found — run scraper.py first.")
    st.stop()

selected_sets = st.multiselect(
    "Filter to specific sets (leave empty to analyze the whole database)",
    options=all_sets,
    placeholder="All sets…",
    key="analyzer_sets",
)

scope_label = (
    f"{len(selected_sets)} SET{'S' if len(selected_sets) != 1 else ''} SELECTED"
    if selected_sets else "ALL SETS"
)
st.html(f'<div class="result-count">{scope_label}</div>')


# ── KPI row ───────────────────────────────────────────────────────────────────

stats = cached_stats(selected_sets)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Cards", f"{stats['total_cards']:,}")
with k2:
    st.metric("Sets Covered", stats["total_sets"])
with k3:
    avg_dp = stats["avg_dp"]
    st.metric("Avg DP", f"{avg_dp:,.0f}" if avg_dp else "—")
with k4:
    avg_cost = stats["avg_cost"]
    st.metric("Avg Play Cost", f"{avg_cost:.1f}" if avg_cost else "—")

st.markdown("---")


# ── Row 1: Card Type | Color Distribution ────────────────────────────────────

c1, c2 = st.columns(2)

with c1:
    data = cached_type_dist(selected_sets)
    if data:
        labels = [d["card_type"] for d in data]
        values = [d["count"] for d in data]
        st.plotly_chart(donut(labels, values, TYPE_HEX, "CARD TYPE"),
                        use_container_width=True)
    else:
        empty()

with c2:
    data = cached_color_dist(selected_sets)
    if data:
        labels = [d["color"] for d in data]
        values = [d["count"] for d in data]
        st.plotly_chart(donut(labels, values, COLOR_HEX, "COLOR DISTRIBUTION"),
                        use_container_width=True)
    else:
        empty()


# ── Row 2: Rarity | Attribute ─────────────────────────────────────────────────

c3, c4 = st.columns(2)

with c3:
    data = cached_rarity_dist(selected_sets)
    if data:
        by_rarity = {d["rarity"]: d["count"] for d in data}
        ordered   = [r for r in RARITY_ORDER if r in by_rarity]
        # Catch any rarity values not in our known order list
        ordered  += [r for r in by_rarity if r not in ordered]
        labels = [RARITY_LABELS.get(r, r.upper()) for r in ordered]
        values = [by_rarity[r] for r in ordered]
        colors = [RARITY_HEX.get(r, "#778899") for r in ordered]
        st.plotly_chart(bar(labels, values, colors, "RARITY BREAKDOWN"),
                        use_container_width=True)
    else:
        empty()

with c4:
    data = cached_attr_dist(selected_sets)
    if data:
        labels = [d["attribute"] for d in data]
        values = [d["count"] for d in data]
        st.plotly_chart(donut(labels, values, ATTRIBUTE_HEX, "ATTRIBUTE DISTRIBUTION"),
                        use_container_width=True)
    else:
        empty()


# ── Row 3: Level | DP ──────────────────────────────────────────────────────────

c5, c6 = st.columns(2)

with c5:
    data = cached_level_dist(selected_sets)
    if data:
        labels = [f"Lv.{d['level']}" for d in data]
        values = [d["count"] for d in data]
        st.plotly_chart(bar(labels, values, "#00d4ff", "LEVEL DISTRIBUTION"),
                        use_container_width=True)
    else:
        empty()

with c6:
    values = cached_dp_values(selected_sets)
    if values:
        st.plotly_chart(histogram(values, "DP DISTRIBUTION", xaxis_title="DP", color="#7b2fff"),
                        use_container_width=True)
    else:
        empty()


# ── Row 4: Play Cost | Cards per Set ──────────────────────────────────────────

c7, c8 = st.columns(2)

with c7:
    values = cached_cost_values(selected_sets)
    if values:
        st.plotly_chart(
            histogram(values, "PLAY COST DISTRIBUTION", xaxis_title="Cost",
                     color="#ff6b35", nbins=max(values) + 1 if values else None),
            use_container_width=True,
        )
    else:
        empty()

with c8:
    data = cached_cards_per_set(selected_sets)
    if data:
        # Cap to top 20 when looking at the whole database so the chart stays readable
        capped = data[:20]
        labels = [d["set_name"] for d in capped]
        values = [d["count"] for d in capped]
        note = f" (top 20 of {len(data)})" if len(data) > 20 else ""
        st.plotly_chart(hbar(labels, values, f"CARDS PER SET{note}"),
                        use_container_width=True)
    else:
        empty()