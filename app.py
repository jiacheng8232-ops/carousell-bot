import os
import time
import requests
import threading
from bs4 import BeautifulSoup
from flask import Flask

# === YOUR SETTINGS (KEYS INSERTED) ===
TELEGRAM_BOT_TOKEN = '8958780535:AAHvyyBxIIEy1MJTX4se0aTV1v3jd8kpU6Q'
TELEGRAM_CHAT_ID = '402777873'
SCRAPER_API_KEY = 'c059b91623176fb7fe6318867ffde831'

KEYWORDS = ['ntuc', 'sheng siong', 'trip', 'klook', 'dairy farm']
POLL_INTERVAL = 13000  # Checks every ~3.6 hours
# ============================================

app = Flask(__name__)
seen_listings = set()

# 1. The Dummy Web Server
@app.route('/')
def home():
    return "Carousell Bot is awake and running!"

# 2. Simple Telegram Sender
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

# 3. The Scraping Logic
def fetch_listings(keyword):
    url = f"https://www.carousell.sg/search/{requests.utils.quote(keyword)}?sort_by=3"
    try:
        response = requests.get('https://api.scraperapi.com', params={'api_key': SCRAPER_API_KEY, 'url': url}, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = []
            for a in soup.find_all('a', href=True):
                if '/p/' in a['href']:
                    listing_id = a['href'].strip('/').split('-')[-1]
                    if listing_id.isdigit():
                        listings.append({'id': listing_id, 'link': "https://www.carousell.sg" + a['href']})
            return listings
    except Exception as e:
        print(f"Error: {e}")
    return []

# 4. The Continuous Background Loop
def run_bot():
    print("Bot started...")
    send_message(f"✅ *Bot is active!*\nMonitoring keywords: {', '.join(k.title() for k in KEYWORDS)}")
    
    test_sent = False
    
    for kw in KEYWORDS: 
        for item in fetch_listings(kw):
            # Send exactly ONE test link as proof it is working
            if test_sent == False:
                send_message(f"🧪 *TEST SCAN SUCCESSFUL!*\n*Found a recent item for:* {kw.title()}\n🔗 [View Here]({item['link']})")
                test_sent = True
                
            seen_listings.add(item['id'])
            
    while True:
        time.sleep(POLL_INTERVAL)
        for kw in KEYWORDS:
            for item in fetch_listings(kw):
                if item['id'] not in seen_listings:
                    seen_listings.add(item['id'])
                    send_message(f"🚨 *New Listing!*\n*Search:* {kw.title()}\n🔗 [View Here]({item['link']})")

# Start the background loop
threading.Thread(target=run_bot, daemon=True).start()

# Start the Web Server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
