import streamlit as st
import json

@st.cache_data # This keeps the 8000 cards in memory so it's instant
def load_data():
    with open("cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

cards = load_data()

# ── Faster Filtering ──────────────────────────────────────────────────────────
st.sidebar.header("Search Filters")
search_query = st.sidebar.text_input("Search Name or ID").lower()
color_filter = st.sidebar.selectbox("Color", ["All"] + ["Red", "Blue", "Yellow", "Green", "Black", "Purple", "White"])

# The "Magic" of Python list comprehension (Instant filtering)
filtered_cards = [
    c for c in cards 
    if (search_query in c['name'].lower() or search_query in c['cardnumber'].lower())
    and (color_filter == "All" or color_filter in c.get('color', []))
]

# ── Display ──────────────────────────────────────────────────────────────────
st.title(f"Digimon Explorer ({len(filtered_cards)} cards)")

cols = st.columns(4)
for i, card in enumerate(filtered_cards[:100]): # Limit to first 100 for browser speed
    with cols[i % 4]:
        # Use local image if available, else fallback to URL
        local_img = f"assets/cards/{card['cardnumber']}.jpg"
        img_source = local_img if os.path.exists(local_img) else f"https://images.digimoncard.io/images/cards/{card['cardnumber']}.jpg"
        
        st.image(img_source)
        st.caption(f"{card['cardnumber']} - {card['name']}")