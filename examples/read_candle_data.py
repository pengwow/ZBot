import pandas as pd
# from zbot.services.model import get_candles_from_db
from zbot.exchange.exchange import ExchangeFactory

if __name__ == '__main__':
    exchange = ExchangeFactory.create_exchange('binance')
    candles = exchange.load_data('BTC/USDT', '15m', "2025-01-01", "2025-01-03")
    print(candles.head())
    
