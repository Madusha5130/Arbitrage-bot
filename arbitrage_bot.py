import asyncio
import aiohttp
from aiohttp import ClientSession
from telegram import Bot

COINMARKETCAP_API_KEY = '7cd882b6-efa9-44ef-8715-22faca85eba3'
TELEGRAM_BOT_TOKEN = '7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM'
TELEGRAM_CHAT_ID = '5556378872'

EXCHANGES = [
    'binance', 'bitget', 'bybit', 'gate', 'coinbase',
    'kucoin', 'okx', 'mexc'
]

MIN_ARBITRAGE = 1.0  # Only notify if greater than 1%
COIN_LIMIT = 150     # Top 150 coins

async def fetch_top_coins(session: ClientSession):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={COIN_LIMIT}&convert=USDT'
    headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}
    async with session.get(url, headers=headers) as response:
        data = await response.json()
        return [(coin['symbol'], coin['cmc_rank']) for coin in data['data']]

async def fetch_price(session: ClientSession, exchange: str, symbol: str):
    url = f'https://api.cryptorank.io/v0/coins/{symbol}/markets'
    try:
        async with session.get(url) as response:
            data = await response.json()
            prices = [
                float(m['price']) for m in data.get('data', [])
                if m['exchange']['id'] == exchange and m.get('price')
            ]
            return prices[0] if prices else None
    except Exception:
        return None

async def fetch_prices_all_exchanges(session: ClientSession, symbol: str):
    tasks = [fetch_price(session, exch, symbol) for exch in EXCHANGES]
    prices = await asyncio.gather(*tasks)
    return [p for p in prices if p is not None]

async def check_arbitrage(session: ClientSession, bot: Bot, symbol: str, rank: int):
    prices = await fetch_prices_all_exchanges(session, symbol)
    if len(prices) < 2:
        print(f"{symbol}: Not enough data")
        return

    lowest = min(prices)
    highest = max(prices)
    if lowest == 0:
        print(f"{symbol}: Invalid lowest price")
        return

    percent_diff = ((highest - lowest) / lowest) * 100
    print(f"{symbol}: {percent_diff:.2f}% price difference")

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
            print("Fetching top coins...\n")
            try:
                coins = await fetch_top_coins(session)
            except Exception as e:
                print(f"Error fetching top coins: {e}")
                await asyncio.sleep(60)
                continue

            print("Checking arbitrage opportunities...\n")
            tasks = [
                check_arbitrage(session, bot, symbol.lower(), rank)
                for symbol, rank in coins
            ]
            await asyncio.gather(*tasks)
            print("\nWaiting 60 seconds...\n")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
