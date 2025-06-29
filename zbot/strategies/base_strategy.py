from abc import ABC, abstractmethod
import pandas as pd
from backtesting import Backtest, Strategy


class BaseStrategy(Strategy, ABC):
    """策略抽象基类，所有策略需继承此类并实现抽象方法"""
    def __init__(self, params: dict = None):
        self.params = params or {}
        self.data = None
        self.signals = None
        self.positions = None

    def set_data(self, data: pd.DataFrame):
        """设置回测数据
        :param data: 格式化后的K线数据，需包含'Open','High','Low','Close','Volume'列
        """
        required_columns = {'Open', 'High', 'Low', 'Close', 'Volume'}
        if not required_columns.issubset(data.columns):
            missing = required_columns - set(data.columns)
            raise ValueError(f"数据缺少必要列: {missing}")
        self.data = data
        self._initialize()

    def _initialize(self):
        """初始化策略状态"""
        # 初始化策略状态
        self.signals = self.I(lambda: pd.Series(index=self.data.index, dtype='object'), name='signals')
        self.positions = self.I(lambda: pd.Series(index=self.data.index, dtype='int').fillna(0), name='positions')

    def init(self):
        """策略初始化回调，Backtesting.py框架自动调用"""
        self._initialize()
        self.on_strategy_init()

    def next(self):
        """每根K线处理回调，Backtesting.py框架自动调用"""
        self.on_strategy_next()

    def on_strategy_init(self):
        """策略初始化扩展点，子类可重写"""
        pass

    def on_strategy_next(self):
        """K线处理扩展点，子类可重写"""
        pass

    def get_signals(self) -> pd.Series:
        """获取交易信号序列"""
        return self.signals

    def get_positions(self) -> pd.Series:
        """获取持仓序列"""
        return self.positions

    def buy(self, index: int, price: float = None, volume: float = None):
        """生成买入信号"""
        price = price or self.data.iloc[index]['Close']
        self.signals.iloc[index] = ('BUY', price, volume)
        self.positions.iloc[index] = 1

    def sell(self, index: int, price: float = None, volume: float = None):
        """生成卖出信号"""
        price = price or self.data.iloc[index]['Close']
        self.signals.iloc[index] = ('SELL', price, volume)
        self.positions.iloc[index] = 0

    def short(self, index: int, price: float = None, volume: float = None):
        """生成做空信号"""
        price = price or self.data.iloc[index]['Close']
        self.signals.iloc[index] = ('SHORT', price, volume)
        self.positions.iloc[index] = -1

    def cover(self, index: int, price: float = None, volume: float = None):
        """生成平仓信号"""
        price = price or self.data.iloc[index]['Close']
        self.signals.iloc[index] = ('COVER', price, volume)
        self.positions.iloc[index] = 0


class BacktestEngine:
    """回测引擎，集成Backtesting.py提供专业回测功能"""
    def __init__(self, strategy_class, data: pd.DataFrame, params: dict = None):
        self.strategy_class = strategy_class
        self.data = data
        self.params = params or {}
        self.backtest = Backtest(
            data, 
            strategy_class, 
            cash=100000, 
            commission=.001, 
            exclusive_orders=True
        )
        self.results = None

    def run(self, **kwargs):
        """运行回测并返回结果
        :param kwargs: 传递给Backtesting.py的run方法的参数
        :return: 回测结果字典
        """
        self.results = self.backtest.run(**kwargs)
        return self.results

    def plot(self, **kwargs):
        """绘制回测结果图表"""
        if self.results is None:
            raise RuntimeError("请先运行回测")
        return self.backtest.plot(**kwargs)

    def optimize(self, parameter_ranges: dict, **kwargs):
        """优化策略参数
        :param parameter_ranges: 参数范围字典，如{'window': range(5, 20)}
        :param kwargs: 传递给Backtesting.py的optimize方法的参数
        :return: 优化结果
        """
        return self.backtest.optimize(** parameter_ranges, **kwargs)