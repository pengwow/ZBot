from abc import ABC, abstractmethod
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from zbot.trading.events import event_bus, EventType, MarketDataEvent, OrderEvent


class AsyncExchange(ABC):
    """异步交易所连接器抽象基类，定义实盘交易所需的核心接口"""
    def __init__(self, exchange_name: str, api_key: str, secret_key: str, proxy_url: Optional[str] = None,
                 testnet: bool = False, cache_dir: str = 'data/cache/exchanges'):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.testnet = testnet
        self.cache_dir = cache_dir
        self._session = None
        self._initialized = False
        self._rate_limit_delay = 0.1  # 默认请求间隔(秒)
        self._cache_ttl = timedelta(days=1)  # 缓存默认有效期1天

    async def initialize(self):
        """异步初始化连接器"""
        if self._initialized:
            return
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        # 初始化网络会话
        self._session = await self._create_session()
        self._initialized = True

    @abstractmethod
    async def _create_session(self):
        """创建网络会话(由子类实现)"""
        pass

    async def close(self):
        """关闭连接器资源"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._initialized = False

    async def _get_cache_file_path(self, endpoint: str, params: Dict) -> str:
        """生成缓存文件路径"""
        param_str = '_'.join([f'{k}={v}' for k, v in sorted(params.items())])
        filename = f'{self.exchange_name}_{endpoint}_{param_str}.json'
        return os.path.join(self.cache_dir, filename)

    async def _load_from_cache(self, endpoint: str, params: Dict) -> Optional[Any]:
        """从缓存加载数据"""
        cache_path = await self._get_cache_file_path(endpoint, params)
        if not os.path.exists(cache_path):
            return None

        # 检查缓存是否过期
        modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - modified_time > self._cache_ttl:
            return None

        # 读取缓存文件
        try:
            async with open(cache_path, 'r') as f:
                return json.loads(await f.read())
        except Exception as e:
            print(f"读取缓存失败: {str(e)}")
            return None

    async def _save_to_cache(self, endpoint: str, params: Dict, data: Any):
        """保存数据到缓存"""
        cache_path = await self._get_cache_file_path(endpoint, params)
        try:
            async with open(cache_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            print(f"写入缓存失败: {str(e)}")

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """异步获取K线数据"""
        pass

    @abstractmethod
    async def create_order(self, symbol: str, order_type: str, side: str, quantity: float,
                          price: Optional[float] = None, params: Optional[Dict] = None) -> Dict:
        """异步创建订单"""
        pass

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """异步取消订单"""
        pass

    @abstractmethod
    async def fetch_balance(self) -> Dict:
        """异步获取账户余额"""
        pass

    async def _publish_market_event(self, symbol: str, interval: str, data: Dict):
        """发布市场数据事件"""
        event = MarketDataEvent(symbol, interval, data)
        asyncio.create_task(event_bus.publish(EventType.MARKET_DATA, event.to_dict()))

    async def _publish_order_event(self, order: Dict):
        """发布订单事件"""
        event_type = {
            'created': EventType.ORDER_CREATED,
            'updated': EventType.ORDER_UPDATED,
            'filled': EventType.ORDER_FILLED,
            'cancelled': EventType.ORDER_CANCELLED
        }.get(order.get('status'), EventType.ORDER_UPDATED)

        event = OrderEvent(
            order_id=order.get('id'),
            symbol=order.get('symbol'),
            order_type=order.get('type'),
            side=order.get('side'),
            price=order.get('price'),
            quantity=order.get('quantity'),
            status=order.get('status')
        )
        event.type = event_type
        asyncio.create_task(event_bus.publish(event_type, event.to_dict()))

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        return False