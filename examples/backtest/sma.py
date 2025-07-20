from turtle import st
from backtesting import Backtest, Strategy
from backtesting._stats import _Stats
from backtesting.lib import crossover
import pandas as pd
from backtesting.test import SMA, GOOG, BTCUSD
from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
# save to csv
# from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
# from zbot.services.model import get_candles_from_db
# candles = get_candles_from_db('binance', "ETH/USDT", "15m", "2025-01-01", "2025-06-01")
# candles.to_csv('ethusdt_15m.csv')
class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 10)
        self.ma2 = self.I(SMA, price, 20)

    def next(self):
        print(self.ma1[-1])
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()


candles = pd.read_csv('temp/ethusdt_15m.csv')
del candles['id']
# 将open_time时间戳转换为时间字符串
candles['open_time'] = candles['open_time'].apply(lambda x: timestamp_to_datetime(x))
# del candles['id']
candles.rename(columns={'open': 'Open', 'close':'Close', 'high':'High', 'low':'Low', 'volume':'Volume'}, inplace=True)
candles.set_index('open_time', drop=True, inplace=True)
print(candles.tail())
print(candles.columns)
# df = BTCUSD
# print(df.columns)
# print(df.head())
from backtesting import Backtest

class ChineseBacktest(Backtest):
    def run(self, *args, **kwargs):
        # 调用父类的run方法获取原始结果
        result = super().run(*args, **kwargs)
        
        # 定义英文到中文的映射关系
        translations = {
            'Start': '起始资金',
            'End': '结束资金',
            'Duration': '回测时长',
            'Exposure Time [%]': '持仓时间百分比',
            'Equity Final [$]': '最终权益',
            'Equity Peak [$]': '权益峰值',
            'Commissions [$]':'手续费',
            'Return [%]': '收益率',
            'Buy & Hold Return [%]': '买入持有收益率',
            'Return (Ann.) [%]':'年化收益率',
            'Volatility (Ann.) [%]':'年化波动率',
            'CAGR [%]':'复合年化增长率',
            'Max. Drawdown [%]': '最大回撤',
            'Sharpe Ratio': '夏普比率',
            'Sortino Ratio': '索提诺比率',
            'Calmar Ratio': '卡尔马比率',
            'Alpha [%]':'阿尔法系数',
            'Beta':'贝塔系数',
            'Win Rate [%]': '胜率',
            'Best Trade [%]': '最佳交易',
            'Worst Trade [%]': '最差交易',
            'Avg. Trade [%]': '平均交易',
            'Total Trades': '总交易次数',
            'Max. Trade Duration':'最大交易时长',
            'Avg. Trade Duration':'平均交易时长',
            'Max. Drawdown Duration':'最大回撤时长',
            'Avg. Drawdown Duration':'平均回撤时长',
            'Avg. Drawdown [%]':'平均回撤',
            'Profit Factor':'利润因子',
            'Expectancy [%]':'期望值',
            'SQN': '系统质量数',
            'Kelly Criterion':'凯利准则',


            # 可以根据实际输出结果添加更多映射
        }
        
        # 创建翻译后的结果字典
        translated_result = {}
        for key, value in result.items():
            if key in ['_strategy', '_equity_curve', '_trade_list','_trades']:
                continue
            # 如果键在翻译字典中存在，则使用中文键，否则保留原键
            translated_key = translations.get(key, key)
            translated_result[translated_key] = value
        pd_result = pd.Series(translated_result)
        return _Stats(pd_result)
         


# 使用方法

bt = ChineseBacktest(candles, SmaCross, cash=10_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
bt.plot()

# bt = Backtest(BTCUSD, SmaCross, commission=.002,    def
#               exclusive_orders=True)
# stats = bt.run()
# print(stats)
# bt.plot()

