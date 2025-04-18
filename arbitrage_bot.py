import asyncio
import aiohttp
import telegram
import time
from datetime import datetime

# CoinMarketCap API Key
CMC_API_KEY = "7cd882b6-efa9-44ef-8715-22faca85eba3"

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Target exchanges
EXCHANGES = ["BINANCE", "BITGET", "BYBIT", "GATEIO", "COINBASE", "KUCOIN", "OKX", "MEXC"]

# Function to fetch top 80 coins by market cap from CoinMarketCap
async def fetch_top_coins():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"start": "1", "limit": "80", "convert": "USD"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            return [coin["symbol"] for coin in data["data"]]

# Function to fetch price from specific exchange
async def fetch_price(exchange, symbol):
    symbol_pair = symbol.upper() + "USDT"
    endpoints = {
        "BINANCE": f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}",
        "BITGET": f"https://api.bitget.com/api/spot/v1/market/ticker?symbol={symbol_pair}_SPBL",
        "BYBIT": f"https://api.bybit.com/v2/public/tickers?symbol={symbol_pair}",
        "GATEIO": f"https://api.gate.io/api/v4/spot/tickers?currency_pair={symbol_pair}",
        "COINBASE": f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot",
        "KUCOIN": f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol_pair}",
        "OKX": f"https://www.okx.com/api/v5/market/ticker?instId={symbol_pair}",
        "MEXC": f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol_pair}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoints[exchange]) as response:
                data = await response.json()

                if exchange == "BINANCE":
                    return float(data["price"])
                elif exchange == "BITGET":
                    return float(data["data"]["close"])
                elif exchange == "BYBIT":
                    return float(data["result"][0]["last_price"])
                elif exchange == "GATEIO":
                    return float(data[0]["last"])
                elif exchange == "COINBASE":
                    return float(data["data"]["amount"])
                elif exchange == "KUCOIN":
                    return float(data["data"]["price"])
                elif exchange == "OKX":
                    return float(data["data"][0]["last"])
                elif exchange == "MEXC":
                    return float(data["price"])
    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol} from {exchange}: {e}")
        return None

# Function to check arbitrage
async def check_arbitrage():
    print(f"\n[SCAN STARTED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    coins = await fetch_top_coins()
    results = []

    for symbol in coins:
        prices = {}
        for exchange in EXCHANGES:
            price = await fetch_price(exchange, symbol)
            if price:
                prices[exchange] = price
            await asyncio.sleep(0.1)  # avoid rate limits

        if len(prices) >= 2:
            min_exchange = min(prices, key=prices.get)
            max_exchange = max(prices, key=prices.get)
            min_price = prices[min_exchange]
            max_price = prices[max_exchange]

            if min_price == 0:
                continue

            diff_percent = ((max_price - min_price) / min_price) * 100

            if diff_percent >= 1.5:
                msg = f"- {symbol}: {min_price:.2f} ({min_exchange}) -> {max_price:.2f} ({max_exchange}) | Diff: {diff_percent:.2f}%"
                results.append(msg)

    if results:
        message = "**Arbitrage Opportunities Found:**\n" + "\n".join(results)
    else:
        message = "**No arbitrage opportunities found this round.**"

    print(message)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

# Main function to loop scan every 1 minute
async def main():
    while True:
        try:
            await check_arbitrage()
        except Exception as e:
            print(f"[FATAL ERROR] {e}")
        await asyncio.sleep(60)

# Entry point
if __name__ == "__main__":
    asyncio.run(main())
