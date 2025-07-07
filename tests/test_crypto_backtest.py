import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

class CryptoSMAStrategy(Strategy):
    """
    基于移动平均线交叉的加密货币交易策略
    
    该策略使用两个简单移动平均线（SMA）的交叉来产生交易信号，
    特别针对加密货币的小交易单位进行了优化，支持小数头寸大小。
    """
    n1 = 50  # 短期移动平均线周期
    n2 = 200  # 长期移动平均线周期
    lot_size = 0.00001  # 加密货币最小交易单位（例如0.00001 BTC）
    price_precision = 2  # 价格小数位数
    size_precision = 5  # 数量小数位数

    def init(self):
        """初始化策略，计算移动平均线指标"""
        self.ma1 = self.I(SMA, self.data.Close, self.n1)
        self.ma2 = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        """每个时间步执行的策略逻辑"""
        # 当短期均线上穿长期均线时买入
        if crossover(self.ma1, self.ma2):
            # 使用指定的小数头寸大小买入
            # 使用指定的小数头寸大小买入，确保价格和数量精度
            price = round(self.data.Close[-1], self.price_precision)
            size = round(self.lot_size, self.size_precision)
            self.buy(price=price, size=size)
        
        # 当短期均线下穿长期均线时卖出
        elif crossover(self.ma2, self.ma1):
            # 平仓所有头寸
            # 平仓所有头寸，确保数量精度
            size = round(self.position.size, self.size_precision)
            self.sell(size=size)


def test_crypto_backtest():
    """
    测试加密货币回测策略
    
    生成模拟的加密货币OHLCV数据，运行回测并输出结果。
    展示如何处理小数交易单位和设置加密货币相关参数。
    """
    # 生成模拟的加密货币数据（例如BTC/USDT 1小时K线）
    # 实际应用中应替换为真实的历史数据
    # 生成模拟的加密货币数据（例如BTC/USDT 1小时K线）
    # 实际应用中建议替换为真实历史数据，可通过以下方式获取：
    # 1. 交易所API（如Binance、Coinbase）
    # 2. 数据提供商（如CryptoCompare、CoinGecko）
    # 3. 本地CSV文件：pd.read_csv('crypto_data.csv', index_col='datetime', parse_dates=True)
    # 先生成Open价格序列
    opens = [30000 + i*10 + (i%10)*50 for i in range(1000)]
    
    # 基于Open价格计算High、Low和Close
    highs = []
    lows = []
    closes = []
    for i, open_price in enumerate(opens):
        high = open_price + 100 + (i%5)*30
        low = open_price - 100 - (i%7)*20
        close = open_price + (i%3)*40 - 60
        highs.append(high)
        lows.append(low)
        closes.append(close)
    
    # 创建DataFrame
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': [100 + i*2 + (i%10)*50 for i in range(1000)]
    }, index=pd.date_range(start='2023-01-01', periods=1000, freq='H'))

    # 创建回测实例，设置初始资金、佣金和滑点
    bt = Backtest(
        data,
        CryptoSMAStrategy,
        cash=10000,  # 初始资金10000 USDT
        commission=0.001,  # 0.1%的佣金（加密货币交易所常见费率）
        slippage=0.0005,  # 0.05%的滑点
        exclusive_orders=True
    )

    # 运行回测
    results = bt.run()
    print(results)

    # 验证回测结果
    assert 'Equity Final [$]' in results, '回测结果不包含最终权益'
    assert results['Trades'] > 0, '策略未产生任何交易'
    assert results['Exposure Time [%]'] > 0, '策略未持有任何头寸'
    print(f"回测验证通过: 交易次数={results['Trades']}, 最终权益={results['Equity Final [$]']:.2f}")

    # 验证回测结果有效性
    if results['Trades'] == 0:
        print("警告: 策略未产生任何交易")
    elif results['Exposure Time [%]'] == 0:
        print("警告: 策略未持有任何头寸")
    else:
        pass  # 满足语法要求的else子句

    # 可选：绘制回测结果图表
    # bt.plot()

if __name__ == "__main__":
    test_crypto_backtest()