# coding=utf-8
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, FractionalBacktest

from backtesting.test import SMA, GOOG, BTCUSD
from zbot.services.model import get_candles_from_db


class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 10)
        self.ma2 = self.I(SMA, price, 20)

    def next(self):
        print(self.data.Close[-1], self.data.index[-1])
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()


if __name__ == '__main__':
    from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
    candles = get_candles_from_db('binance', "BTC/USDT", "15m", "2025-01-01", "2025-01-03")
    del candles['id']
    # 将open_time时间戳转换为时间字符串
    candles['open_time'] = candles['open_time'].apply(lambda x: timestamp_to_datetime(x))
    # del candles['id']
    candles.rename(columns={'open': 'Open', 'close':'Close', 'high':'High', 'low':'Low', 'volume':'Volume'}, inplace=True)
    candles.set_index('open_time', drop=True, inplace=True)
    print(candles.head())
    print(candles.columns)
    # df = BTCUSD
    # print(df.columns)
    # print(df.head())

    bt = FractionalBacktest(candles, SmaCross, fractional_unit=1e-06, cash=10_000, commission=0.002,exclusive_orders=True)
    stats = bt.run()
    print(stats)
    bt.plot()
