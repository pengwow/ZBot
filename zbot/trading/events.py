import asyncio
from typing import Dict, List, Callable, Coroutine, Any


class PubSub:
    """异步事件发布订阅系统，支持事件的异步发布和订阅"""
    def __init__(self):
        # 事件主题到订阅者队列的映射
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        # 事件主题到处理函数的映射（用于一次性处理）
        self.event_handlers: Dict[str, List[Callable[[Any], Coroutine]]] = {}
        self.lock = asyncio.Lock()

    async def subscribe(self, topic: str) -> asyncio.Queue:
        """订阅指定主题，返回用于接收事件的队列"""  
        async with self.lock:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
                self.event_handlers[topic] = []
            queue = asyncio.Queue()
            self.subscribers[topic].append(queue)
            return queue

    async def subscribe_once(self, topic: str, handler: Callable[[Any], Coroutine]):
        """订阅指定主题一次，使用处理函数处理事件"""
        async with self.lock:
            if topic not in self.event_handlers:
                self.event_handlers[topic] = []
            self.event_handlers[topic].append(handler)

    async def unsubscribe(self, topic: str, queue: asyncio.Queue):
        """取消订阅指定主题的队列"""        
        async with self.lock:
            if topic in self.subscribers and queue in self.subscribers[topic]:
                self.subscribers[topic].remove(queue)
                if not self.subscribers[topic]:
                    del self.subscribers[topic]
                    del self.event_handlers[topic]

    async def publish(self, topic: str, message: Any):
        """异步发布事件到指定主题"""
        async with self.lock:
            # 复制当前订阅者列表以避免发布时修改
            queues = self.subscribers.get(topic, []).copy()
            handlers = self.event_handlers.get(topic, []).copy()

        # 向所有队列发布消息
        for queue in queues:
            try:
                # 使用非阻塞put避免队列满时阻塞发布者
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # 队列满时记录警告
                print(f"警告: 事件队列 {topic} 已满，丢弃消息")

        # 执行所有一次性处理函数
        for handler in handlers:
            try:
                # 使用create_task确保处理函数不会阻塞发布者
                asyncio.create_task(handler(message))
            except Exception as e:
                print(f"处理事件 {topic} 时出错: {str(e)}")

    async def get_event(self, topic: str, timeout: float = None) -> Any:
        """获取指定主题的事件（用于订阅者主动获取）"""
        queue = await self.subscribe(topic)
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self):
        """关闭PubSub系统，清理资源"""
        async with self.lock:
            self.subscribers.clear()
            self.event_handlers.clear()


# 全局事件总线实例
event_bus = PubSub()


# 事件类型定义
class EventType:
    """事件类型常量定义"""
    MARKET_DATA = "market_data"
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ACCOUNT_UPDATE = "account_update"
    ERROR = "error"


class MarketDataEvent:
    """市场数据事件"""
    def __init__(self, symbol: str, interval: str, data: dict):
        self.type = EventType.MARKET_DATA
        self.symbol = symbol
        self.interval = interval
        self.data = data
        self.timestamp = asyncio.get_event_loop().time()

    def to_dict(self):
        return {
            "type": self.type,
            "symbol": self.symbol,
            "interval": self.interval,
            "data": self.data,
            "timestamp": self.timestamp
        }


class OrderEvent:
    """订单事件"""
    def __init__(self, order_id: str, symbol: str, order_type: str, side: str, price: float, quantity: float, status: str):
        self.type = EventType.ORDER_CREATED
        self.order_id = order_id
        self.symbol = symbol
        self.order_type = order_type
        self.side = side
        self.price = price
        self.quantity = quantity
        self.status = status
        self.timestamp = asyncio.get_event_loop().time()

    def to_dict(self):
        return {
            "type": self.type,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "order_type": self.order_type,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "timestamp": self.timestamp
        }