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
    # Triggers Apify's pre-built Carousell scraper
    url = f"https://api.apify.com/v2/acts/automation-lab~carousell-listings-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
    
    # Pass exact Carousell URLs with sort_by=3 so it only scrapes recent items
    start_urls = [{"url": f"https://www.carousell.sg/search/{requests.utils.quote(kw)}?sort_by=3"} for kw in KEYWORDS]
    
    payload = {
        "startUrls": start_urls,
        "maxItems": 10, # Fetch top 10 recent items per keyword
        "proxyType": "residential"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300) 
        if response.status_code in [200, 201]:
            return response.json()
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
                    
                    title = item.get('title', 'New Item')
                    price = item.get('price', '')
                    link = item.get('listingUrl', '')
                    
                    msg = f"🚨 *New Listing Detected!*\n*Title:* {title}\n*Price:* {price}\n🔗 [View on Carousell]({link})"
                    send_message(msg)

# Start the continuous background loop
threading.Thread(target=run_bot, daemon=True).start()

# Start the Dummy Web Server to keep Render happy
@app.route('/')
def home():
    return "Carousell Bot is running on Apify!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
