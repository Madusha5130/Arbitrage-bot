import time
import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot

TELEGRAM_BOT_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"

# Exchanges and their API endpoints
EXCHANGES = {
    "BINANCE": "https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT",
    "BITGET": "https://api.bitget.com/api/spot/v1/market/ticker?symbol={symbol}USDT",
    "BYBIT": "https://api.bybit.com/v2/public/tickers?symbol={symbol}USDT",
    "GATEIO": "https://api.gate.io/api2/1/ticker/{symbol}_usdt",
    "COINBASE": "https://api.exchange.coinbase.com/products/{symbol}-USDT/ticker",
    "KUCOIN": "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT",
    "OKX": "https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT",
    "MEXC": "https://api.mexc.com/api/v3/ticker/price?symbol={symbol}USDT",
}

SYMBOLS = ["BTC", "ETH", "XRP", "ADA", "SOL", "MATIC", "DOGE", "DOT"]

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def fetch_price(session, exchange, url, symbol):
    try:
        api_url = url.format(symbol=symbol)
        async with session.get(api_url, timeout=10) as response:
            data = await response.json()

            if exchange == "BINANCE" or exchange == "MEXC":
                return float(data["price"])
            elif exchange == "BITGET":
                return float(data["data"]["last"])
            elif exchange == "BYBIT":
                return float(data["result"][0]["last_price"])
            elif exchange == "GATEIO":
                return float(data["last"])
            elif exchange == "COINBASE":
                return float(data["price"])
            elif exchange == "KUCOIN":
                return float(data["data"]["price"])
            elif exchange == "OKX":
                return float(data["data"][0]["last"])

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol} from {exchange}: {e}")
    return None

async def scan_arbitrage():
    async with aiohttp.ClientSession() as session:
        results = {}
        for symbol in SYMBOLS:
            prices = {}
            for exchange, url in EXCHANGES.items():
                price = await fetch_price(session, exchange, url, symbol)
                if price:
                    prices[exchange] = price
            if len(prices) >= 2:
                max_ex = max(prices, key=prices.get)
                min_ex = min(prices, key=prices.get)
                max_price = prices[max_ex]
                min_price = prices[min_ex]
                diff = ((max_price - min_price) / min_price) * 100
                if diff >= 1.5:
                    result = f"{symbol}: {min_price:.2f} ({min_ex}) -> {max_price:.2f} ({max_ex}) | Diff: {diff:.2f}%"
                    results[symbol] = result
        return results

async def send_report():
    while True:
        print(f"\n[SCAN STARTED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        results = await scan_arbitrage()
        if results:
            msg = "*Arbitrage Opportunities Found:*\n\n"
            for res in results.values():
                print(res)
                msg += f"- {res}\n"
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
        else:
            print("No arbitrage opportunities found.")
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="No arbitrage opportunities found.")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(send_report())
