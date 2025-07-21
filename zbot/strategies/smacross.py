# coding=utf-8
from backtesting import Backtest, Strategy
from backtesting.test import SMA, GOOG, BTCUSD
from backtesting.lib import crossover
class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 10)
        self.ma2 = self.I(SMA, price, 20)

    def next(self):
        print(self.data.Close[-1], self.data.index[-1])
        if crossover(self.ma1, self.ma2):
            self.buy(size=0.000001)
            # self.sell()
        elif crossover(self.ma2, self.ma1):
            self.sell()