import os
import time
import requests
import threading
from flask import Flask

# === YOUR SETTINGS ===
TELEGRAM_BOT_TOKEN = '8958780535:AAHvyyBxIIEy1MJTX4se0aTV1v3jd8kpU6Q'
TELEGRAM_CHAT_ID = '402777873'
APIFY_API_TOKEN = 'apify_api_GbQVxB1a8AJ1rNkk2AlefBEliToLj90lzV8j'

KEYWORDS = ['ntuc', 'sheng siong', 'trip', 'klook', 'dairy farm', 'fairprice', 'voucher', 'giant', 'vouchers']

# Set to 15 hours
POLL_INTERVAL = 54000  
# ============================================

app = Flask(__name__)
seen_listings = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

def fetch_all_listings():
    url = f"https://api.apify.com/v2/acts/automation-lab~carousell-listings-scraper/runs?token={APIFY_API_TOKEN}"
    payload = {
        "keywords": KEYWORDS,
        "market": "sg",
        "maxItems": 200,  # Increased to 200 items per scan
        "proxyType": "residential"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code in [200, 201]:
            run_data = response.json()
            run_id = run_data['data']['id']
            dataset_id = run_data['data']['defaultDatasetId']
            
            while True:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
                status = requests.get(status_url).json()['data']['status']
                
                if status == 'SUCCEEDED':
                    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
                    return requests.get(dataset_url).json()
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    return []
                time.sleep(15)
    except Exception as e:
        print(f"Request Error: {e}")
    return []

def run_bot():
    send_message(f"✅ *Apify Bot is active!*\nMonitoring: {', '.join(k.title() for k in KEYWORDS)}")
    
    while True:
        items = fetch_all_listings()
        for item in items:
            if 'listingId' in item:
                listing_id = item['listingId']
                
                if listing_id not in seen_listings:
                    seen_listings.add(listing_id)
                    
                    title = item.get('title', 'New Item')
                    price = item.get('price', '')
                    link = item.get('listingUrl', '')
                    
                    msg = f"🚨 *New Listing!*\n*Title:* {title}\n*Price:* {price}\n🔗 [View on Carousell]({link})"
                    send_message(msg)
                    time.sleep(1) # Protects bot from Telegram spam filters
                    
        time.sleep(POLL_INTERVAL)

def run_manual_scan():
    send_message("🔍 *Manual scan initiated...*")
    items = fetch_all_listings()
    for
