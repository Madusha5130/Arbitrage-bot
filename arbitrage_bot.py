import asyncio
import aiohttp
from telegram import Bot
from datetime import datetime

TELEGRAM_BOT_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"
ARBITRAGE_THRESHOLD = 1.5  # percent

bot = Bot(token=TELEGRAM_BOT_TOKEN)

EXCHANGES = {
    "BINANCE": lambda symbol: f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT",
    "BITGET": lambda symbol: f"https://api.bitget.com/api/spot/v1/market/ticker?symbol={symbol}USDT",
    "BYBIT": lambda symbol: f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}USDT",
    "GATEIO": lambda symbol: f"https://api.gate.io/api2/1/ticker/{symbol}_usdt",
    "COINBASE": lambda symbol: f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot",
    "KUCOIN": lambda symbol: f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT",
    "OKX": lambda symbol: f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT",
    "MEXC": lambda symbol: f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}USDT"
}

async def fetch_price(session, url, exchange, symbol):
    try:
        async with session.get(url, ssl=False) as response:
            data = await response.json()

            if exchange == "BINANCE":
                return float(data['price'])
            elif exchange == "BITGET" and data.get('data'):
                return float(data['data'].get('last', 0))
            elif exchange == "BYBIT" and data.get('result'):
                return float(data['result']['list'][0]['lastPrice'])
            elif exchange == "GATEIO" and data:
                return float(data['last'])
            elif exchange == "COINBASE" and data.get('data'):
                return float(data['data']['amount'])
            elif exchange == "KUCOIN" and data.get('data'):
                return float(data['data']['price'])
            elif exchange == "OKX" and data.get('data'):
                return float(data['data'][0]['last'])
            elif exchange == "MEXC":
                return float(data['price'])
    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol} from {exchange}: {e}")
    return None

async def get_prices(symbol):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for exchange, url_fn in EXCHANGES.items():
            url = url_fn(symbol)
            tasks.append(fetch_price(session, url, exchange, symbol))
        results = await asyncio.gather(*tasks)
        return dict(zip(EXCHANGES.keys(), results))

async def check_arbitrage():
    print(f"\n[SCAN STARTED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=80"
    headers = {"X-CMC_PRO_API_KEY": "7cd882b6-efa9-44ef-8715-22faca85eba3"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            symbols = [x['symbol'] for x in data.get('data', []) if 'symbol' in x]

    opportunities = []
    for symbol in symbols:
        prices = await get_prices(symbol)
        filtered = {k: v for k, v in prices.items() if v is not None}
        if len(filtered) < 2:
            continue

        min_ex, min_price = min(filtered.items(), key=lambda x: x[1])
        max_ex, max_price = max(filtered.items(), key=lambda x: x[1])
        diff_percent = ((max_price - min_price) / min_price) * 100

        if diff_percent >= ARBITRAGE_THRESHOLD:
            msg = f"- {symbol}: {min_price:.2f} ({min_ex}) -> {max_price:.2f} ({max_ex}) | Diff: {diff_percent:.2f}%"
            print(msg)
            opportunities.append(msg)

    if opportunities:
        message = "**Arbitrage Opportunities Found:**\n" + "\n".join(opportunities)
    else:
        message = "No arbitrage opportunities found this cycle."

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

async def main():
    while True:
        await check_arbitrage()
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
