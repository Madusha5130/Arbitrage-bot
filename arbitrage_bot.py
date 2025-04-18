import requests
import time
import telegram

CMC_API_KEY = "7cd882b6-efa9-44ef-8715-22faca85eba3"
TELEGRAM_BOT_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"

EXCHANGES = ["binance", "bitget", "bybit", "gate", "coinbase", "kucoin", "okx", "mexc"]

def get_top_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"start": "1", "limit": "80", "convert": "USDT"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()["data"]
    return [crypto["symbol"] for crypto in data]

def get_prices(symbol):
    exchange_prices = {}
    for ex in EXCHANGES:
        try:
            url = f"https://api.coingecko.com/api/v3/exchanges/{ex}/tickers?coin_ids={symbol.lower()}"
            response = requests.get(url)
            data = response.json()
            for item in data.get("tickers", []):
                if item["target"] == "USDT":
                    exchange_prices[ex] = item["last"]
                    break
        except:
            continue
    return exchange_prices

def check_arbitrage():
    symbols = get_top_symbols()
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    opportunities_found = False

    for symbol in symbols:
        prices = get_prices(symbol)
        if len(prices) < 2:
            continue
        min_ex, min_price = min(prices.items(), key=lambda x: x[1])
        max_ex, max_price = max(prices.items(), key=lambda x: x[1])
        diff_percent = ((max_price - min_price) / min_price) * 100

        if diff_percent >= 1.5:
            opportunities_found = True
            message = (f"Arbitrage Opportunity Found for {symbol}:\n"
                       f"Buy from {min_ex} @ {min_price} USD\n"
                       f"Sell at {max_ex} @ {max_price} USD\n"
                       f"Difference: {diff_percent:.2f}%")
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    if not opportunities_found:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="No arbitrage opportunity found in this scan.")

while True:
    check_arbitrage()
    time.sleep(60)
