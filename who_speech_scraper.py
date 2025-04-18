import warnings
warnings.filterwarnings("ignore")
import requests
import os
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Constants
API_URL = "https://www.who.int/api/hubs/speeches?sf_site=15210d59-ad60-47ff-a542-7ed76645f0c7&sf_provider=OpenAccessProvider&sf_culture=en&$orderby=PublicationDateAndTime%20desc&$select=Title,ItemDefaultUrl,FormatedDate&$format=json&$top=50"
HEADERS = {
    'accept': 'application/json',
}

# Use the current local time as per the system
TODAY = datetime.now()
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

def parse_formated_date(date_str):
    """Helper to parse the date format in 'FormatedDate', e.g., '14 April 2025'"""
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

def save_speeches_to_file(speeches, data_file):
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

def enrich_speeches_with_text(data_file):
    base_url = "https://www.who.int/news-room/speeches/item"
    # Load speeches
    with open(data_file, 'r', encoding='utf-8') as f:
        speeches = json.load(f)
    updated = False
    for speech in speeches:
        if 'speech' not in speech or not speech['speech']:
            url = base_url + speech['ItemDefaultUrl']
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')
                article = soup.find('article', class_='sf-detail-body-wrapper')
                if article:
                    div = article.find('div')
                    if div:
                        # Join all paragraphs as text, separated by double newlines
                        paragraphs = [p.get_text(separator=' ', strip=True) for p in div.find_all('p')]
                        speech_text = '\n\n'.join(paragraphs)
                        speech['speech'] = speech_text
                        updated = True
                        print(f"Fetched speech for: {speech['Title']}")
                    else:
                        print(f"No <div> found in article for: {speech['Title']}")
                else:
                    print(f"No article found for: {speech['Title']}")
            except Exception as e:
                print(f"Error fetching/parsing {url}: {e}")
    if updated:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(speeches, f, ensure_ascii=False, indent=2)
        print("Updated speeches with extracted text.")
    else:
        print("No new speeches updated with text.")

def main():
    speeches = fetch_recent_speeches()
    # Prepare data directory and file path
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    data_file = os.path.join(data_dir, 'who_speeches.json')
    save_speeches_to_file(speeches, data_file)
    enrich_speeches_with_text(data_file)

if __name__ == "__main__":
    main()
