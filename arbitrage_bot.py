import asyncio
import aiohttp
from aiohttp import ClientSession
from telegram import Bot

COINMARKETCAP_API_KEY = '7cd882b6-efa9-44ef-8715-22faca85eba3'
TELEGRAM_BOT_TOKEN = '7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM'
TELEGRAM_CHAT_ID = '5556378872'

EXCHANGES = ['binance', 'bitget', 'bybit', 'gate', 'coinbase', 'kucoin', 'okx', 'mexc']
MIN_ARBITRAGE = 1.0
COIN_LIMIT = 200

# Optional symbol mapping if exchange-specific symbol names differ
EXCHANGE_SYMBOL_MAP = {
    'BTC': 'BTC',
    'ETH': 'ETH',
    'XRP': 'XRP',
    'DOGE': 'DOGE',
    'SOL': 'SOL',
    'MATIC': 'MATIC',
    'TRX': 'TRX',
    'ADA': 'ADA',
    'LTC': 'LTC',
    'LINK': 'LINK',
    # Add more if needed
}

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
                (float(m['price']), m['exchange']['name'])
                for m in data.get('data', [])
                if m['exchange']['id'] == exchange and m.get('price')
            ]
            return prices[0] if prices else None
    except Exception as e:
        return None

async def fetch_prices_all_exchanges(session: ClientSession, symbol: str):
    tasks = [fetch_price(session, exch, symbol) for exch in EXCHANGES]
    results = await asyncio.gather(*tasks)

    valid_prices = [r for r in results if r is not None]
    if not valid_prices:
        print(f"{symbol}: Not enough data")
    return valid_prices

async def check_arbitrage(session: ClientSession, bot: Bot, symbol: str, rank: int):
    actual_symbol = EXCHANGE_SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    prices_data = await fetch_prices_all_exchanges(session, actual_symbol)
    if len(prices_data) < 2:
        return

    prices = [p[0] for p in prices_data]
    lowest_price, lowest_exchange = min(prices_data, key=lambda x: x[0])
    highest_price, highest_exchange = max(prices_data, key=lambda x: x[0])

    percent_diff = ((highest_price - lowest_price) / lowest_price) * 100
    print(f"{symbol}: {percent_diff:.2f}% arbitrage difference")

    if percent_diff >= MIN_ARBITRAGE:
        message = (
            f"Arbitrage Opportunity Detected!\n"
            f"Symbol: {symbol}\n"
            f"Market Cap Rank: {rank}\n"
            f"Lowest Price: ${lowest_price:.4f} @ {lowest_exchange}\n"
            f"Highest Price: ${highest_price:.4f} @ {highest_exchange}\n"
            f"Difference: {percent_diff:.2f}%"
        )
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            print(f"Telegram send error: {e}")

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with aiohttp.ClientSession() as session:
        while True:
            print("Fetching top coins...")
            coins = await fetch_top_coins(session)
            print("Checking arbitrage opportunities...\n")
            tasks = [
                check_arbitrage(session, bot, symbol, rank)
                for symbol, rank in coins
            ]
            await asyncio.gather(*tasks)
            print("Waiting 60 seconds...\n")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
