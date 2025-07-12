import pandas as pd
from zbot.services.model import get_candles_from_db


if __name__ == '__main__':
    candles = get_candles_from_db('binance','BTC/USDT', '15m', "2025-01-01", "2025-01-03")
    # print([candle.__data__ for candle in candles])
    pd_candles = pd.DataFrame([candle.__data__ for candle in candles])
    print(pd_candles.head())