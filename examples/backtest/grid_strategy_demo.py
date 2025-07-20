import numpy as np
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GridStrategy:
    """
    网格交易策略实现类，支持现货和加密货币的订单簿生成与动态区间调整

    主流网格策略原理：
    1. 在价格区间[lower_price, upper_price]内均匀分布买单和卖单
    2. 当价格波动触发订单时，自动在反方向生成新订单（网格重置）
    3. 支持动态调整价格区间以适应市场趋势
    """
    def __init__(self,
                 symbol: str,
                 lower_price: float,
                 upper_price: float,
                 grid_count: int,
                 initial_capital: float = 10000,
                 dynamic_adjust: bool = True,
                 adjust_ratio: float = 0.1):
        """
        初始化网格策略参数

        :param symbol: 交易对，如"BTC/USDT"
        :param lower_price: 初始价格下边界
        :param upper_price: 初始价格上边界
        :param grid_count: 网格数量（买卖单总数）
        :param initial_capital: 初始资金
        :param dynamic_adjust: 是否启用动态区间调整
        :param adjust_ratio: 区间调整比例（当价格突破边界时）
        """
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_count = grid_count
        self.initial_capital = initial_capital
        self.dynamic_adjust = dynamic_adjust
        self.adjust_ratio = adjust_ratio
        self.current_capital = initial_capital
        self.orders = []
        self.grid_prices = self._calculate_grid_prices()
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """验证输入参数的有效性"""
        if self.lower_price >= self.upper_price:
            raise ValueError("下边界价格必须小于上边界价格")
        if self.grid_count <= 0:
            raise ValueError("网格数量必须为正整数")
        if self.adjust_ratio <= 0 or self.adjust_ratio > 1:
            raise ValueError("调整比例必须在(0, 1]范围内")

    def _calculate_grid_prices(self) -> List[float]:
        """计算网格价格点，采用等比间隔（更适合加密货币的对数价格分布）"""
        # 对于加密货币，使用对数间隔更符合实际价格分布
        if '/' in self.symbol and self.symbol.split('/')[1] in ['USDT', 'BTC', 'ETH']:
            return np.exp(np.linspace(np.log(self.lower_price), np.log(self.upper_price), self.grid_count)).tolist()
        # 对于传统现货，使用线性间隔
        return np.linspace(self.lower_price, self.upper_price, self.grid_count).tolist()

    def generate_order_book(self, current_price: float) -> List[Dict[str, any]]:
        """
        根据当前价格生成订单簿

        :param current_price: 当前市场价格
        :return: 订单列表，每个订单包含price, quantity, side, timestamp字段
        """
        self.orders = []
        mid_idx = self._find_mid_index(current_price)
        remaining_capital = self.current_capital
        grid_interval = self.grid_count // 2

        # 生成买单（当前价格下方）
        for i in range(max(0, mid_idx - grid_interval), mid_idx):
            if remaining_capital <= 0:
                break
            price = self.grid_prices[i]
            # 价格越低，买单数量越多（金字塔策略）
            quantity = (remaining_capital / price) * (1 - (i / mid_idx) * 0.5) if mid_idx > 0 else 0
            if quantity > 0:
                self.orders.append({
                    'price': round(price, 4),
                    'quantity': round(quantity, 6),
                    'side': 'buy',
                    'timestamp': datetime.now().timestamp()
                })
                remaining_capital -= price * quantity

        # 生成卖单（当前价格上方）
        for i in range(mid_idx + 1, min(self.grid_count, mid_idx + grid_interval + 1)):
            price = self.grid_prices[i]
            # 价格越高，卖单数量越多
            quantity = (self.initial_capital / price) * ((i / self.grid_count) * 0.5 + 0.5)
            self.orders.append({
                'price': round(price, 4),
                'quantity': round(quantity, 6),
                'side': 'sell',
                'timestamp': datetime.now().timestamp()
            })

        logger.info(f"为{self.symbol}生成订单簿，当前价格: {current_price}, 订单总数: {len(self.orders)}")
        return self.orders

    def _find_mid_index(self, current_price: float) -> int:
        """找到当前价格在网格中的位置索引"""
        # 动态调整价格区间
        if self.dynamic_adjust:
            self._adjust_price_range(current_price)

        # 找到最接近当前价格的网格索引
        return min(range(len(self.grid_prices)), key=lambda i: abs(self.grid_prices[i] - current_price))

    def _adjust_price_range(self, current_price: float) -> None:
        """当价格突破边界时，动态调整网格区间"""
        range_width = self.upper_price - self.lower_price
        # 价格突破上边界
        if current_price > self.upper_price:
            new_upper = current_price + range_width * self.adjust_ratio
            logger.info(f"价格突破上边界，调整区间: {self.upper_price} -> {new_upper}")
            self.upper_price = new_upper
            self.grid_prices = self._calculate_grid_prices()
        # 价格突破下边界
        elif current_price < self.lower_price:
            new_lower = current_price - range_width * self.adjust_ratio
            logger.info(f"价格突破下边界，调整区间: {self.lower_price} -> {new_lower}")
            self.lower_price = new_lower
            self.grid_prices = self._calculate_grid_prices()

    def simulate_price_movement(self, start_price: float, volatility: float = 0.02, steps: int = 10) -> List[Tuple[float, List[Dict[str, any]]]]:
        """
        模拟价格波动并生成对应的订单簿变化

        :param start_price: 起始价格
        :param volatility: 价格波动率
        :param steps: 模拟步数
        :return: 每步的价格和对应订单簿
        """
        simulation_results = []
        current_price = start_price

        for step in range(steps):
            # 模拟价格随机波动
            price_change = current_price * volatility * (np.random.rand() * 2 - 1)
            current_price += price_change
            current_price = max(0.01, current_price)  # 确保价格不为负

            # 生成新的订单簿
            order_book = self.generate_order_book(current_price)
            simulation_results.append((current_price, order_book))

        return simulation_results


if __name__ == '__main__':
    # 示例：创建BTC/USDT网格策略
    try:
        # 初始化参数（可根据实际情况调整）
        btc_strategy = GridStrategy(
            symbol="BTC/USDT",
            lower_price=40000.0,
            upper_price=60000.0,
            grid_count=20,
            initial_capital=10000,
            dynamic_adjust=True,
            adjust_ratio=0.1
        )

        # 生成初始订单簿（当前价格45000）
        initial_orders = btc_strategy.generate_order_book(current_price=45000)
        print("初始订单簿示例:")
        for order in initial_orders[:5] + initial_orders[-5:]:  # 打印前5个和后5个订单
            print(f"{order['side']}: 价格={order['price']}, 数量={order['quantity']}")

        # 模拟价格波动
        print("\n模拟价格波动和订单簿变化...")
        simulation_results = btc_strategy.simulate_price_movement(start_price=45000, steps=5)

        # 打印模拟结果摘要
        for i, (price, orders) in enumerate(simulation_results):
            print(f"\n第{i+1}步: 当前价格={price:.2f}, 订单数={len(orders)}")
            print(f"最新区间: [{btc_strategy.lower_price:.2f}, {btc_strategy.upper_price:.2f}]")

    except Exception as e:
        logger.error(f"策略执行失败: {str(e)}")