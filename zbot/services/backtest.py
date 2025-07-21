# coding=utf-8
import warnings
import os
import re
import importlib
from backtesting import Backtest as BacktestBase
import pandas as pd
from backtesting.lib import crossover, FractionalBacktest
from zbot.services.model import get_candles_from_db
from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
from zbot.common.config import read_config

# 策略目录路径
strategies_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '../strategies')

# 查找策略目录下全部策略


def get_strategy_names():
    # 查找所有策略文件
    strategy_files = [f for f in os.listdir(
        strategies_dir) if f.endswith('.py')]

    return strategy_files


def get_strategy_class_names():
    # 查找策略目录下的策略文件中的策略类名
    class_names = []
    strategy_names = get_strategy_names()
    for filename in strategy_names:
        # 读取文件内容查找类定义
        with open(os.path.join(strategies_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()

            # 使用正则表达式匹配类定义
            class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

            # 查找匹配的类
            for name in class_matches:
                class_names.append(name)
    return class_names


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


# 自定义Backtest类
class CustomBacktest(BacktestBase):
    def __init__(self, *args, **kwargs):
        with warnings.catch_warnings(record=True):
            warnings.filterwarnings(action='ignore', message='frac')
            super().__init__(*args, **kwargs)


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

        # 定义英文到中文的映射关系
        self.translations = {
            'Start': '起始资金',
            'End': '结束资金',
            'Duration': '回测时长',
            'Exposure Time [%]': '持仓时间百分比',
            'Equity Final [$]': '最终权益',
            'Equity Peak [$]': '权益峰值',
            'Commissions [$]': '手续费',
            'Return [%]': '收益率',
            'Buy & Hold Return [%]': '买入持有收益率',
            'Return (Ann.) [%]': '年化收益率',
            'Volatility (Ann.) [%]': '年化波动率',
            'CAGR [%]': '复合年化增长率',
            'Max. Drawdown [%]': '最大回撤',
            'Sharpe Ratio': '夏普比率',
            'Sortino Ratio': '索提诺比率',
            'Calmar Ratio': '卡尔马比率',
            'Alpha [%]': '阿尔法系数',
            'Beta': '贝塔系数',
            'Win Rate [%]': '胜率',
            'Best Trade [%]': '最佳交易',
            'Worst Trade [%]': '最差交易',
            'Avg. Trade [%]': '平均交易',
            'Total Trades': '总交易次数',
            'Max. Trade Duration': '最大交易时长',
            'Avg. Trade Duration': '平均交易时长',
            'Max. Drawdown Duration': '最大回撤时长',
            'Avg. Drawdown Duration': '平均回撤时长',
            'Avg. Drawdown [%]': '平均回撤',
            'Profit Factor': '利润因子',
            'Expectancy [%]': '期望值',
            'SQN': '系统质量数',
            'Kelly Criterion': '凯利准则',
            # 可以根据实际输出结果添加更多映射
        }

    def to_dict(self, result):
        # 创建翻译后的结果字典
        translated_result = {}
        for key, value in result.items():
            if key in ['_strategy', '_equity_curve', '_trade_list', '_trades']:
                continue
            # 如果键在翻译字典中存在，则使用中文键，否则保留原键
            translated_key = self.translations.get(key, key)
            translated_result[translated_key] = value
        return translated_result

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
        self.bt = CustomBacktest(candles, strategy_class, cash=self.cash,
                                 commission=self.commission, exclusive_orders=True)
        self.stats = self.bt.run()
        return self.to_dict(self.stats)


if __name__ == '__main__':
    # backtest = Backtest('SmaCross', 'ETH/USDT', '15m',
    #                     '2025-01-01', '2025-06-01', 10_000, 0.002)
    # stats = backtest.run()
    # print(stats)
    # backtest.bt.plot()
    names = get_strategy_class_names()
    print(names)

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
