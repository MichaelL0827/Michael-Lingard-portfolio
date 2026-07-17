import requests
import json
import os

# The community source catalog listing all sets cleanly
CATALOG_URL = "https://raw.githubusercontent.com/apitcg/digimon-tcg-data/master/data/sets.json"

def fetch_latest_data():
    print("📥 Downloading card dataset metadata...")
    response = requests.get(CATALOG_URL)
    
    # Defensive check: ensure the request actually succeeded before processing JSON
    if response.status_code != 200:
        print(f"❌ Failed to reach GitHub data source. Status code: {response.status_code}")
        return []
        
    try:
        sets_list = response.json()
    except Exception as e:
        print("❌ Error: The data returned by GitHub was not valid JSON.")
        print(f"Received text preview: {response.text[:100]}")
        return []

    all_cards = []
    print(f"📂 Found {len(sets_list)} card sets. Merging into a single dataset...")
    
    # Loop through each individual set file and extract the cards
    for set_info in sets_list:
        set_id = set_info.get("id")
        if not set_id:
            continue
            
        set_url = f"https://raw.githubusercontent.com/apitcg/digimon-tcg-data/master/data/sets/{set_id}.json"
        set_res = requests.get(set_url)
        
        if set_res.status_code == 200:
            try:
                set_data = set_res.json()
                # The individual set files contain a list of cards inside the 'cards' key
                cards_in_set = set_data.get("cards", [])
                all_cards.extend(cards_in_set)
            except Exception:
                continue # Skip broken sets gracefully

    # Save the consolidated file locally
    with open("cards.json", "w", encoding="utf-8") as f:
        json.dump(all_cards, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! Consolidated {len(all_cards)} cards into cards.json")
    return all_cards