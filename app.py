import os
import time
import requests
import threading
from flask import Flask

# === YOUR SETTINGS ===
TELEGRAM_BOT_TOKEN = '8958780535:AAHvyyBxIIEy1MJTX4se0aTV1v3jd8kpU6Q'
TELEGRAM_CHAT_ID = '402777873'
APIFY_API_TOKEN = 'apify_api_GbQVxB1a8AJ1rNkk2AlefBEliToLj90lzV8j'

KEYWORDS = ['ntuc', 'sheng siong', 'trip', 'klook', 'dairy farm', 'fairprice']
POLL_INTERVAL = 13000  # Timer in seconds (13000 = ~3.6 hours)
# ============================================

app = Flask(__name__)
seen_listings = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

def fetch_all_listings():
    # Use the exact Apify endpoint for automation-lab
    url = f"https://api.apify.com/v2/acts/automation-lab~carousell-listings-scraper/runs?token={APIFY_API_TOKEN}"
    
    # We pass your keywords exactly as Apify expects them
    payload = {
        "keywords": KEYWORDS,
        "market": "sg",
        "maxItems": 10,
        "proxyType": "residential"
    }
    
    try:
        # Start the run
        print("Sending request to Apify...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code in [200, 201]:
            run_data = response.json()
            run_id = run_data['data']['id']
            dataset_id = run_data['data']['defaultDatasetId']
            
            print(f"Apify run started! Run ID: {run_id}. Waiting for completion...")
            
            # Wait for Apify to finish scraping (check every 15 seconds)
            while True:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
                status_resp = requests.get(status_url).json()
                status = status_resp['data']['status']
                
                if status == 'SUCCEEDED':
                    print("Apify scrape complete! Fetching data...")
                    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
                    return requests.get(dataset_url).json()
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"Apify run failed with status: {status}")
                    return []
                    
                time.sleep(15)
        else:
            print(f"Apify Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Request Error: {e}")
        
    return []

def run_bot():
    print("Bot started...")
    send_message(f"✅ *Apify Bot is active!*\nMonitoring: {', '.join(k.title() for k in KEYWORDS)}")
    
    print("Running initial silent scan...")
    items = fetch_all_listings()
    for item in items:
        # The Apify Carousell scraper returns 'listingId'
        if 'listingId' in item:
            seen_listings.add(item['listingId'])
            
    while True:
        time.sleep(POLL_INTERVAL)
        print("Checking for new items...")
        items = fetch_all_listings()
        
        for item in items:
            if 'listingId' in item:
                listing_id = item['listingId']
                
                if listing_id not in seen_listings:
                    seen_listings.add(listing_id)
                    
                    # Extract the clean data provided by Ap
