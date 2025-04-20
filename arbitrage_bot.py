import asyncio
import aiohttp
from telegram import Bot

COINMARKETCAP_API_KEY = '7cd882b6-efa9-44ef-8715-22faca85eba3'
TELEGRAM_BOT_TOKEN = '7769765331:AAEw12H4-98xYfP_2tBGQQPe10prkXF-lGM'
TELEGRAM_CHAT_ID = '5556378872'

EXCHANGES = ['binance', 'bitget', 'bybit', 'gate', 'coinbase', 'kucoin', 'okx', 'mexc']
MIN_ARBITRAGE = 1.0
COIN_LIMIT = 200

async def fetch_top_coins(session):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={COIN_LIMIT}&convert=USDT'
    headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}
    async with session.get(url, headers=headers) as response:
        data = await response.json()
        return [(coin['id'], coin['symbol'], coin['cmc_rank']) for coin in data['data']]

async def fetch_cmc_market_data(session, coin_id):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/market-pairs/latest?id={coin_id}'
    headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}
    try:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data['data']['market_pairs']
    except Exception:
        return []

async def check_arbitrage(session, bot, coin_id, symbol, rank):
    market_data = await fetch_cmc_market_data(session, coin_id)

    prices = {}
    for market in market_data:
        exchange = market['exchange_name'].lower()
        if exchange in EXCHANGES and market['quote_currency_symbol'] == 'USDT':
            price = market.get('quote', {}).get('price')
            if price:
                prices[exchange] = float(price)

    if len(prices) < 2:
        print(f"{symbol}: Not enough data")
        return

    lowest_exchange = min(prices, key=prices.get)
    highest_exchange = max(prices, key=prices.get)
    lowest = prices[lowest_exchange]
    highest = prices[highest_exchange]

    percent_diff = ((highest - lowest) / lowest) * 100
    print(f"{symbol}: {percent_diff:.2f}% arbitrage difference")

    if percent_diff >= MIN_ARBITRAGE:
        message = (
            f"Arbitrage Opportunity Detected!\n"
            f"Symbol: {symbol}\n"
            f"Market Cap Rank: {rank}\n"
            f"Lowest Price: ${lowest:.4f} @ {lowest_exchange.capitalize()}\n"
            f"Highest Price: ${highest:.4f} @ {highest_exchange.capitalize()}\n"
            f"Difference: {percent_diff:.2f}%"
        )
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            print(f"Telegram Error: {e}")

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with aiohttp.ClientSession() as session:
        while True:
            print("Fetching top coins...")
            coins = await fetch_top_coins(session)
            print("Checking arbitrage opportunities...")
            tasks = [
                check_arbitrage(session, bot, coin_id, symbol, rank)
                for coin_id, symbol, rank in coins
            ]
            await asyncio.gather(*tasks)
            print("Waiting 60 seconds...\n")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
