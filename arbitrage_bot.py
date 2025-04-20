import asyncio
import aiohttp
from telegram import Bot

TELEGRAM_BOT_TOKEN = '7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM'
TELEGRAM_CHAT_ID = '5556378872'

COIN_LIMIT = 150    # Top 150 coins
MIN_ARBITRAGE = 1.0 # Minimum % difference

COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3'

async def fetch_top_coins(session):
    url = f'{COINGECKO_BASE_URL}/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': COIN_LIMIT,
        'page': 1,
        'sparkline': 'false'
    }
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        return [(coin['id'], coin['symbol'], coin['market_cap_rank']) for coin in data]

async def fetch_prices(session, coin_id):
    url = f'{COINGECKO_BASE_URL}/coins/{coin_id}/tickers'
    async with session.get(url) as resp:
        data = await resp.json()
        prices = []
        for ticker in data.get('tickers', []):
            price = ticker.get('last')
            if price:
                prices.append(price)
        return prices

async def check_arbitrage(session, bot, coin_id, symbol, rank):
    prices = await fetch_prices(session, coin_id)
    if len(prices) < 2:
        print(f"{symbol}: Not enough data")
        return

    lowest = min(prices)
    highest = max(prices)

    if lowest == 0:
        print(f"{symbol}: Invalid price data")
        return

    percent_diff = ((highest - lowest) / lowest) * 100
    print(f"{symbol.upper()}: {percent_diff:.2f}% price difference")

    if percent_diff >= MIN_ARBITRAGE:
        message = (
            f"Arbitrage Opportunity Detected!\n"
            f"Symbol: {symbol.upper()}\n"
            f"Market Cap Rank: {rank}\n"
            f"Lowest Price: ${lowest:.4f}\n"
            f"Highest Price: ${highest:.4f}\n"
            f"Difference: {percent_diff:.2f}%"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with aiohttp.ClientSession() as session:
        while True:
            print("Fetching top coins...")
            coins = await fetch_top_coins(session)
            print(f"Found {len(coins)} coins. Checking arbitrage opportunities...")
            tasks = [
                check_arbitrage(session, bot, coin_id, symbol, rank)
                for coin_id, symbol, rank in coins
            ]
            await asyncio.gather(*tasks)
            print("Waiting 60 seconds...\n")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())

