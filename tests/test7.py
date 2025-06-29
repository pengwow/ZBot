from backtesting import Backtest, Strategy
import pandas as pd

# 模拟生成一些示例数据
data = {
    'Open': [100, 101, 102, 103, 104, 105, 104, 103, 102, 101],
    'High': [101, 102, 103, 104, 105, 106, 105, 104, 103, 102],
    'Low': [99, 100, 101, 102, 103, 104, 103, 102, 101, 100],
    'Close': [101, 102, 103, 104, 105, 104, 103, 102, 101, 100],
    'Volume': [1000, 1200, 1300, 1400, 1500, 1400, 1300, 1200, 1100, 1000]
}
df = pd.DataFrame(data)
df.index = pd.date_range(start='2023-01-01', periods=len(df))

# 定义一个简单的策略：当收盘价连续两天上涨时买入，连续两天下跌时卖出
class SimpleStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if len(self.data.Close) < 2:
            return
        if self.data.Close[-1] > self.data.Close[-2] and self.data.Close[-2] > self.data.Close[-3]:
            self.buy()
        elif self.data.Close[-1] < self.data.Close[-2] and self.data.Close[-2] < self.data.Close[-3]:
            self.sell()

# 创建回测对象并运行回测
bt = Backtest(df, SimpleStrategy, cash=10000, commission=.002)
stats = bt.run()

# 输出回测结果
print(stats)

# 绘制回测结果
bt.plot()
