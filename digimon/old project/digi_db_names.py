# find_sets.py — run this once to discover exact set names
import requests

HEADERS = {"User-Agent": "DigimonPriceTracker/1.0 (your@email.com)"}

r = requests.get(
    "https://digimoncard.io/api-public/search.php",
    headers=HEADERS,
    params={"sort": "name", "series": "Digimon Card Game", "sortdirection": "asc"},
    timeout=30
)

print(f"Status: {r.status_code}")
cards = r.json()

# Extract every unique set_name value from all cards
set_names = set()
for card in cards:
    for s in card.get("set_name", []):
        set_names.add(s)

for name in sorted(set_names):
    print(f'    "{name}",')