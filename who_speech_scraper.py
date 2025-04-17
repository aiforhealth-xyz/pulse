import requests
from datetime import datetime, timedelta

# Constants
API_URL = "https://www.who.int/api/hubs/speeches?sf_site=15210d59-ad60-47ff-a542-7ed76645f0c7&sf_provider=OpenAccessProvider&sf_culture=en&$orderby=PublicationDateAndTime%20desc&$select=Title,ItemDefaultUrl,FormatedDate&$format=json&$top=50"

HEADERS = {
    'accept': 'application/json',
}

# Use the current local time as per the system: 2025-04-17
TODAY = datetime(2025, 4, 17)
DAYS_BACK = 90
cutoff_date = TODAY - timedelta(days=DAYS_BACK)

# Helper to parse the date format in 'FormatedDate', e.g., '14 April 2025'
def parse_formated_date(date_str):
    try:
        return datetime.strptime(date_str, "%d %B %Y")
    except Exception:
        return None

def fetch_recent_speeches():
    response = requests.get(API_URL, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    speeches = data.get("value", [])
    recent_speeches = []
    for speech in speeches:
        date = parse_formated_date(speech.get("FormatedDate", ""))
        if date and date >= cutoff_date:
            recent_speeches.append(speech)
    return recent_speeches

import os
import json

def main():
    speeches = fetch_recent_speeches()
    # Prepare data directory and file path
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    data_file = os.path.join(data_dir, 'who_speeches.json')

    # Load existing speeches if file exists
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                existing = json.load(f)
            except Exception:
                existing = []
    else:
        existing = []

    # Build a set of unique keys (ItemDefaultUrl) from existing data
    existing_urls = set(s.get('ItemDefaultUrl') for s in existing)

    # Add only new speeches
    # Remove unwanted fields from new_entries
    cleaned_new_entries = []
    for s in speeches:
        if s.get('ItemDefaultUrl') not in existing_urls:
            s = {k: v for k, v in s.items() if k in ('Title', 'ItemDefaultUrl', 'FormatedDate')}
            cleaned_new_entries.append(s)
    if cleaned_new_entries:
        all_entries = existing + cleaned_new_entries
        # Optionally, sort by date descending
        def get_date(s):
            d = parse_formated_date(s.get('FormatedDate',''))
            return d if d else datetime.min
        all_entries.sort(key=get_date, reverse=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, ensure_ascii=False, indent=2)
        print(f"Added {len(cleaned_new_entries)} new speeches. Total: {len(all_entries)}.")
    else:
        print("No new speeches to add.")

if __name__ == "__main__":
    main()
