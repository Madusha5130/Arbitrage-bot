import requests
import time
from telegram import Bot

# CoinMarketCap API key
CMC_API_KEY = "7cd882b6-efa9-44ef-8715-22faca85eba3"

# Telegram bot settings
TELEGRAM_BOT_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"

# Headers for CMC API
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': CMC_API_KEY,
}

# Supported exchanges
exchanges = ['binance', 'bitget', 'bybit', 'gateio', 'coinbase', 'kucoin', 'okx', 'mexc']

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        print("Telegram response:", res.json())  # Debug msg
    except Exception as e:
        print("Telegram error:", e)

def get_top_80_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {"start": "1", "limit": "80", "convert": "USD"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return [coin["symbol"] for coin in data["data"]]
    except Exception as e:
        print("CMC Error:", e)
        return []

def get_price_from_exchange(symbol, exchange):
    try:
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": "7cd882b6-efa9-44ef-8715-22faca85eba3",
        }
        params = {
            "symbol": symbol,
            "convert": "USD"
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        price = float(data["data"][symbol]["quote"]["USD"]["price"])
        print(f"[DEBUG] {symbol} = ${price}")
        return price
    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol}: {e}")
        return None

def find_arbitrage_opportunities():
    symbols = get_top_80_symbols()
    found_opportunity = False

    for symbol in symbols:
        prices = {}
        for ex in exchanges:
            price = get_price_from_exchange(symbol, ex)
            if price:
                prices[ex] = price

        if len(prices) >= 2:
            min_ex = min(prices, key=prices.get)
            max_ex = max(prices, key=prices.get)
            min_price = prices[min_ex]
            max_price = prices[max_ex]
            diff_percent = ((max_price - min_price) / min_price) * 100

            if diff_percent >= 1.5:
                found_opportunity = True
                msg = (
                    f"*Arbitrage Alert!*\n\n"
                    f"*Token:* {symbol}\n"
                    f"Buy from *{min_ex.upper()}* at ${min_price:.4f}\n"
                    f"Sell on *{max_ex.upper()}* at ${max_price:.4f}\n"
                    f"*Difference:* {diff_percent:.2f}%"
                )
                print(msg)
                send_telegram_message(msg)

    if not found_opportunity:
        send_telegram_message("No arbitrage opportunities found in this scan.")

if __name__ == "__main__":
    while True:
        find_arbitrage_opportunities()
        time.sleep(60)  # Scan every 1 minute
