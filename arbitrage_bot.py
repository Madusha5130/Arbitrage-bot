import asyncio
import aiohttp
from telegram import Bot

TELEGRAM_BOT_TOKEN = '7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM'
TELEGRAM_CHAT_ID = '5556378872'

COIN_LIMIT = 150
MIN_ARBITRAGE = 1.5  # % difference threshold
COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3'

semaphore = asyncio.Semaphore(1)  # Telegram message lock

async def fetch_top_coins(session):
    url = f'{COINGECKO_BASE_URL}/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': COIN_LIMIT,
        'page': 1
    }
    async with session.get(url, params=params) as resp:
        return await resp.json()

async def fetch_tickers(session, coin_id):
    url = f'{COINGECKO_BASE_URL}/coins/{coin_id}/tickers'
    async with session.get(url) as resp:
        return await resp.json()

async def send_telegram(bot, msg):
    async with semaphore:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        await asyncio.sleep(1)  # Prevent spamming Telegram

async def check_arbitrage(session, bot, coin):
    symbol = coin['symbol']
    coin_id = coin['id']
    rank = coin['market_cap_rank']

    try:
        data = await fetch_tickers(session, coin_id)
        tickers = data.get('tickers', [])
        prices = []

        for t in tickers:
            price = t.get('converted_last', {}).get('usd')
            exchange = t.get('market', {}).get('name')
            if price and exchange:
                prices.append((price, exchange))

        if len(prices) < 2:
            print(f"{symbol}: Not enough data")
            return

        prices.sort()
        lowest_price, low_exchange = prices[0]
        highest_price, high_exchange = prices[-1]

        if lowest_price == 0:
            print(f"{symbol}: Invalid lowest price")
            return

        diff = ((highest_price - lowest_price) / lowest_price) * 100
        print(f"{symbol.upper()}: {diff:.2f}% difference")

        if diff >= MIN_ARBITRAGE:
            msg = (
                f"Arbitrage Opportunity Detected!\n"
                f"Symbol: {symbol.upper()}\n"
                f"Market Cap Rank: {rank}\n"
                f"Lowest Price: ${lowest_price:.4f} @ {low_exchange}\n"
                f"Highest Price: ${highest_price:.4f} @ {high_exchange}\n"
                f"Difference: {diff:.2f}%"
            )
            await send_telegram(bot, msg)

    except Exception as e:
        print(f"Error checking {symbol}: {e}")

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with aiohttp.ClientSession() as session:
        while True:
            print("\nFetching top coins...")
            coins = await fetch_top_coins(session)
            print(f"Checking arbitrage for {len(coins)} coins...")

            tasks = [
                check_arbitrage(session, bot, coin)
                for coin in coins
            ]
            await asyncio.gather(*tasks)

            print("Sleeping for 60 seconds...\n")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
