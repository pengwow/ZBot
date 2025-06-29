import pandas as pd
from .base_strategy import BaseStrategy


class SMAStrategy(BaseStrategy):
    """简单移动平均策略示例
    当短期均线穿过长期均线上方时买入，当短期均线穿过长期均线下方时卖出
    """
    def __init__(self, params: dict = None):
        super().__init__(params)
        # 默认参数
        self.short_window = self.params.get('short_window', 20)
        self.long_window = self.params.get('long_window', 50)

    def on_strategy_init(self):
        """初始化策略指标"""
        # 计算短期和长期移动平均线
        self.sma_short = self.I(
            lambda: pd.Series(self.data.Close).rolling(window=self.short_window).mean(),
            name=f'SMA{self.short_window}'
        )
        self.sma_long = self.I(
            lambda: pd.Series(self.data.Close).rolling(window=self.long_window).mean(),
            name=f'SMA{self.long_window}'
        )

    def on_strategy_next(self):
        """执行策略逻辑"""
        # 确保有足够数据计算均线
        if len(self.data) < self.long_window:
            return

        # 获取当前和前一根K线的均线值
        current_short = self.sma_short[-1]
        current_long = self.sma_long[-1]
        prev_short = self.sma_short[-2]
        prev_long = self.sma_long[-2]

        # 金叉: 短期均线上穿长期均线
        if prev_short < prev_long and current_short > current_long:
            if not self.position:
                self.buy()
                self.signals[-1] = 'BUY'

        # 死叉: 短期均线下穿长期均线
        elif prev_short > prev_long and current_short < current_long:
            if self.position:
                self.sell()
                self.signals[-1] = 'SELL'

        # 持有状态
        else:
            self.signals[-1] = 'HOLD'