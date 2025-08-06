from abc import abstractmethod
import asyncio
from typing import Dict, List, Optional, Any
from zbot.strategies.base_strategy import BaseStrategy
from zbot.services.events import event_bus, EventType


class AsyncBaseStrategy(BaseStrategy):
    """异步策略基类，继承自BaseStrategy，添加异步支持"""
    def __init__(self, params: Dict = None):
        super().__init__(params)
        self._running = False
        self._task = None
        self._connector = None  # 交易所连接器
        self._data_provider = None  # 数据提供器
        self._event_handlers = {
            EventType.MARKET_DATA: self.on_market_data,
            EventType.ORDER_CREATED: self.on_order_created,
            EventType.ORDER_UPDATED: self.on_order_updated,
            EventType.ORDER_FILLED: self.on_order_filled,
            EventType.ORDER_CANCELLED: self.on_order_cancelled,
            EventType.ACCOUNT_UPDATE: self.on_account_update
        }

    async def initialize(self, connector: 'AsyncExchange', data_provider: Any):
        """异步初始化策略"""
        self._connector = connector
        self._data_provider = data_provider
        await self.on_strategy_init()

    async def start(self):
        """启动策略"""
        if self._running:
            return

        self._running = True
        # 订阅事件
        for event_type, handler in self._event_handlers.items():
            await event_bus.subscribe_once(event_type, handler)

        # 启动主策略任务
        self._task = asyncio.create_task(self._run_strategy())
        await self.on_strategy_start()
        return self._task

    async def stop(self):
        """停止策略"""
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # 取消所有未完成订单
        await self.cancel_all_orders()
        await self.on_strategy_stop()

    async def _run_strategy(self):
        """策略主循环"""
        while self._running:
            try:
                await self.on_strategy_tick()
                # 根据策略需求调整循环间隔
                await asyncio.sleep(self.params.get('tick_interval', 1))
            except Exception as e:
                print(f"策略运行错误: {str(e)}")
                await asyncio.sleep(1)  # 出错后延迟一秒再试

    async def on_strategy_init(self):
        """策略初始化回调(异步版)"""
        pass

    async def on_strategy_start(self):
        """策略启动回调"""
        pass

    async def on_strategy_stop(self):
        """策略停止回调"""
        pass

    async def on_strategy_tick(self):
        """策略主循环回调"""
        pass

    async def on_market_data(self, data: Dict):
        """市场数据事件处理"""
        pass

    async def on_order_created(self, order: Dict):
        """订单创建事件处理"""
        pass

    async def on_order_updated(self, order: Dict):
        """订单更新事件处理"""
        pass

    async def on_order_filled(self, order: Dict):
        """订单成交事件处理"""
        pass

    async def on_order_cancelled(self, order: Dict):
        """订单取消事件处理"""
        pass

    async def on_account_update(self, balance: Dict):
        """账户更新事件处理"""
        pass

    async def buy(self, symbol: str, quantity: float, price: Optional[float] = None, order_type: str = 'MARKET') -> Dict:
        """异步买入"""
        if not self._connector:
            return {'error': '未初始化交易所连接器'}

        return await self._connector.create_order(
            symbol=symbol,
            order_type=order_type,
            side='BUY',
            quantity=quantity,
            price=price
        )

    async def sell(self, symbol: str, quantity: float, price: Optional[float] = None, order_type: str = 'MARKET') -> Dict:
        """异步卖出"""
        if not self._connector:
            return {'error': '未初始化交易所连接器'}

        return await self._connector.create_order(
            symbol=symbol,
            order_type=order_type,
            side='SELL',
            quantity=quantity,
            price=price
        )

    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """异步取消订单"""
        if not self._connector:
            return {'error': '未初始化交易所连接器'}

        return await self._connector.cancel_order(symbol, order_id)

    async def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """异步取消所有订单"""
        if not self._connector or not hasattr(self._connector, 'cancel_all_orders'):
            return []

        return await self._connector.cancel_all_orders(symbol=symbol)

    async def fetch_balance(self) -> Dict:
        """异步获取账户余额"""
        if not self._connector:
            return {'error': '未初始化交易所连接器'}

        return await self._connector.fetch_balance()

    async def fetch_ohlcv(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """异步获取K线数据"""
        if not self._data_provider:
            return []

        return await self._data_provider.fetch_ohlcv(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()
        return False


class AsyncDataProvider:
    """异步数据提供器基类"""
    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str, start_time: Optional[float] = None,
                         end_time: Optional[float] = None, limit: int = 100) -> List[Dict]:
        """异步获取K线数据"""
        pass

    @abstractmethod
    async def subscribe_ohlcv(self, symbol: str, interval: str) -> bool:
        """订阅K线数据"""
        pass

    @abstractmethod
    async def unsubscribe_ohlcv(self, symbol: str, interval: str) -> bool:
        """取消订阅K线数据"""
        pass