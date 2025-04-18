import asyncio
import aiohttp
import telegram
from datetime import datetime
import time

COINMARKETCAP_API_KEY = "7cd882b6-efa9-44ef-8715-22faca85eba3"
TELEGRAM_BOT_TOKEN = "<7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM>"
TELEGRAM_CHAT_ID = "<5556378872>"
EXCHANGES = ["BINANCE", "BITGET", "BYBIT", "GATEIO", "COINBASE", "KUCOIN", "OKX", "MEXC"]

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

async def fetch_top_coins():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"start": "1", "limit": "80", "convert": "USDT"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            return [coin["symbol"] for coin in data["data"] if "symbol" in coin]

async def fetch_price(session, exchange, symbol):
    try:
        if exchange == "BINANCE":
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
            async with session.get(url) as response:
                data = await response.json()
                return float(data.get("price", 0)), exchange

        elif exchange == "BITGET":
            url = f"https://api.bitget.com/api/spot/v1/market/ticker?symbol={symbol}USDT"
            async with session.get(url) as response:
                data = await response.json()
                return float(data["data"]["close"] if data.get("data") else 0), exchange

        elif exchange == "BYBIT":
            url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}USDT"
            async with session.get(url) as response:
                data = await response.json()
                return float(data["result"][0]["last_price"] if data.get("result") else 0), exchange

        elif exchange == "GATEIO":
            url = f"https://api.gate.io/api2/1/ticker/{symbol.lower()}_usdt"
            async with session.get(url, ssl=False) as response:
                data = await response.json()
                return float(data.get("last", 0)), exchange

        elif exchange == "COINBASE":
            url = f"https://api.coinbase.com/v2/prices/{symbol}-USDT/spot"
            async with session.get(url) as response:
                data = await response.json()
                return float(data["data"]["amount"] if "data" in data else 0), exchange

        elif exchange == "KUCOIN":
            url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
            async with session.get(url) as response:
                data = await response.json()
                return float(data["data"]["price"] if data.get("data") else 0), exchange

        elif exchange == "OKX":
            url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
            async with session.get(url) as response:
                data = await response.json()
                tick = data["data"][0] if data.get("data") else {}
                return float(tick.get("last", 0)), exchange

        elif exchange == "MEXC":
            url = f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}USDT"
            async with session.get(url) as response:
                data = await response.json()
                return float(data.get("price", 0)), exchange

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol} from {exchange}: {e}")
    return 0.0, exchange

async def check_arbitrage():
    async with aiohttp.ClientSession() as session:
        coins = await fetch_top_coins()
        found_opportunity = False

        for symbol in coins:
            tasks = [fetch_price(session, ex, symbol) for ex in EXCHANGES]
            results = await asyncio.gather(*tasks)

            valid_prices = [(price, ex) for price, ex in results if price > 0]
            if len(valid_prices) < 2:
                continue

            min_price, min_ex = min(valid_prices, key=lambda x: x[0])
            max_price, max_ex = max(valid_prices, key=lambda x: x[0])

            if min_price == 0:
                continue

            diff_percent = ((max_price - min_price) / min_price) * 100
            if diff_percent >= 1.5:
                message = (f"**Arbitrage Opportunity Found:**\n"
                           f"- {symbol}: {min_price:.2f} ({min_ex}) -> {max_price:.2f} ({max_ex}) | Diff: {diff_percent:.2f}%")
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
                print(message)
                found_opportunity = True

        if not found_opportunity:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="No arbitrage opportunities found this round.")
            print("[INFO] No arbitrage found in this round.")

async def main():
    while True:
        print(f"\n[SCAN STARTED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
        try:
            await check_arbitrage()
        except Exception as e:
            print(f"[FATAL ERROR] {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
