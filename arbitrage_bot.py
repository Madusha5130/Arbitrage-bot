import asyncio
import aiohttp
from aiohttp import ClientSession
from telegram import Bot
import time

# SETTINGS
CMC_API_KEY = "7cd882b6-efa9-44ef-8715-22faca85eba3"
TELEGRAM_TOKEN = "7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM"
TELEGRAM_CHAT_ID = "5556378872"
COINS_LIMIT = 150
MIN_ARBITRAGE = 1.5
MAX_ARBITRAGE = 100
SCAN_INTERVAL = 60

EXCHANGES = [
    "binance", "bitget", "bybit", "gate", "coinbase", "kucoin", "okx", "mexc"
]

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

async def get_top_coins(session: ClientSession):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={COINS_LIMIT}"
    async with session.get(url, headers=HEADERS) as response:
        data = await response.json()
        return {coin["symbol"]: coin["cmc_rank"] for coin in data["data"]}

async def fetch_price(session: ClientSession, symbol: str, exchange: str):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=false"
    try:
        async with session.get(url) as response:
            result = await response.json()
            return result.get(symbol, {}).get("usd", None)
    except:
        return None

async def fetch_prices_all_exchanges(session: ClientSession, symbol: str):
    tasks = []
    for exchange in EXCHANGES:
        tasks.append(fetch_price(session, symbol.lower(), exchange))
    prices = await asyncio.gather(*tasks)
    return [p for p in prices if p is not None]

async def check_arbitrage(session: ClientSession, bot: Bot, symbol: str, rank: int):
    prices = await fetch_prices_all_exchanges(session, symbol)
    if len(prices) < 2:
        return

    lowest = min(prices)
    highest = max(prices)
    if lowest == 0:
        return

    percent_diff = ((highest - lowest) / lowest) * 100

    if MIN_ARBITRAGE <= percent_diff <= MAX_ARBITRAGE:
        message = (
            f"Arbitrage Opportunity Detected!\n"
            f"Symbol: {symbol}\n"
            f"Market Cap Rank: {rank}\n"
            f"Lowest Price: ${lowest:.4f}\n"
            f"Highest Price: ${highest:.4f}\n"
            f"Difference: {percent_diff:.2f}%"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def main_loop():
    bot = Bot(token=TELEGRAM_TOKEN)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                print("Fetching top coins...")
                top_coins = await get_top_coins(session)

                print("Checking arbitrage opportunities...")
                tasks = []
                for symbol, rank in top_coins.items():
                    tasks.append(check_arbitrage(session, bot, symbol, rank))

                await asyncio.gather(*tasks)

            except Exception as e:
                print(f"Error in main loop: {e}")

            print(f"Waiting {SCAN_INTERVAL} seconds...\n")
            await asyncio.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
