# coding=utf-8
import warnings
import os
import re
import importlib
from backtesting import Backtest as BacktestBase
from backtesting.lib import crossover, FractionalBacktest
from zbot.services.model import get_candles_from_db
from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
from zbot.common.config import read_config


def load_strategy_class(strategy_name):
    """
    根据策略名称动态加载strategies目录中的策略类
    :param strategy_name: 策略类名
    :return: 策略类
    """
    # 策略目录路径
    strategies_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '../strategies')

    # 遍历目录下的所有Python文件
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            # 模块名称
            module_name = f'zbot.strategies.{filename[:-3]}'

            # 导入模块
            module = importlib.import_module(module_name)

            # 读取文件内容查找类定义
            with open(os.path.join(strategies_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()

                # 使用正则表达式匹配类定义
                class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

                # 查找匹配的类
                for class_name in class_matches:
                    if class_name == strategy_name:
                        return getattr(module, class_name)

    # 如果未找到策略类
    raise ValueError(f"未找到策略类: {strategy_name}")


class Backtest(object):
    def __init__(self, strategy: str, symbol: str, interval: str, start: str, end: str, cash: float,
                 commission: float, exchange: str = None):
        self.strategy = strategy
        self.symbol = symbol
        self.interval = interval
        self.start = start
        self.end = end
        self.cash = cash
        self.commission = commission
        self.exchange = exchange or read_config('exchange')['name']

    def run(self):
        candles = get_candles_from_db(
            self.exchange, self.symbol, self.interval, self.start, self.end)
        del candles['id']
        # 将open_time时间戳转换为时间字符串
        candles['open_time'] = candles['open_time'].apply(
            lambda x: timestamp_to_datetime(x))
        candles.rename(columns={'open': 'Open', 'close': 'Close',
                       'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
        candles.set_index('open_time', drop=True, inplace=True)
        # 动态加载策略类
        strategy_class = load_strategy_class(self.strategy)
        bt = BacktestBase(candles, strategy_class, cash=self.cash,
                          commission=self.commission, exclusive_orders=True)
        return bt.run()


if __name__ == '__main__':
    backtest = Backtest('SmaCross', 'ETH/USDT', '15m', '2025-01-01', '2025-06-01', 10_000, 0.002)
    stats = backtest.run()
    print(stats)
    # from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
    # candles = get_candles_from_db(
    #     'binance', "ETH/USDT", "15m", "2025-01-01", "2025-06-01")
    # if not candles.empty:
    #     del candles['id']
    #     # 将open_time时间戳转换为时间字符串
    #     candles['open_time'] = candles['open_time'].apply(
    #         lambda x: timestamp_to_datetime(x))
    #     # del candles['id']
    #     candles.rename(columns={'open': 'Open', 'close': 'Close',
    #                    'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
    #     candles.set_index('open_time', drop=True, inplace=True)
    #     print(candles.tail())
    #     print(candles.columns)
    #     # df = BTCUSD
    #     # print(df.columns)
    #     # print(df.head())
    #     bt = Backtest(candles, SmaCross, cash=10_000,
    #                   commission=0.002, exclusive_orders=True)
    #     bt = FractionalBacktest(candles, SmaCross, fractional_unit=1e-06,
    #                             cash=10_000, commission=0.002, exclusive_orders=True)
    #     stats = bt.run()
    #     print(stats)
    #     bt.plot()
