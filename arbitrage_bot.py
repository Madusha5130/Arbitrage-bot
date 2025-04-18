import requests
import time

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

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
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
        url = f"https://api.coinmarketcap.com/data-api/v3/tools/price-conversion?amount=1&convert=USD&symbol={symbol}&e={exchange}"
        res = requests.get(url)
        data = res.json()
        return float(data["data"]["quote"]["price"])
    except:
        return None

def find_arbitrage_opportunities():
    symbols = get_top_80_symbols()
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
                msg = f"*Arbitrage Alert!*\n\n*Token:* {symbol}\nBuy from *{min_ex.upper()}* at ${min_price:.4f}\nSell on *{max_ex.upper()}* at ${max_price:.4f}\n*Difference:* {diff_percent:.2f}%"
                print(msg)
                send_telegram_message(msg)

if __name__ == "__main__":
    while True:
        find_arbitrage_opportunities()
        time.sleep(60)  # scan every 1 minute
