import asyncio
import aiohttp
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import urllib.parse
import json
from zbot.trading.connectors.base_connector import AsyncExchange
from zbot.common.config import read_config


class AsyncBinanceExchange(AsyncExchange):
    """Binance交易所异步连接器实现"""
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None,
                 proxy_url: Optional[str] = None, testnet: bool = False):
        # 从配置读取默认参数
        config = read_config('exchange').get('binance', {})
        api_key = api_key or config.get('api_key')
        secret_key = secret_key or config.get('secret_key')
        proxy_url = proxy_url or config.get('proxy_url')
        testnet = testnet if testnet is not None else config.get('testnet', False)

        # 初始化父类
        super().__init__(
            exchange_name='binance',
            api_key=api_key,
            secret_key=secret_key,
            proxy_url=proxy_url,
            testnet=testnet,
            cache_dir='data/cache/exchanges/binance'
        )

        # 设置API基础URL
        self.base_url = 'https://testnet.binance.vision/api' if testnet else 'https://api.binance.com/api'
        self.ws_base_url = 'wss://testnet.binance.vision/ws' if testnet else 'wss://stream.binance.com:9443/ws'
        self._ws_connections = {}  # 存储WebSocket连接
        self._session = None  # aiohttp会话
        self._order_book = {}  # 订单簿缓存
    self._ohlcv_cache = {}  # K线数据缓存

    async def _create_session(self) -> aiohttp.ClientSession:
        """创建aiohttp会话"""
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=10)

        session_kwargs = {
            'timeout': timeout,
            'connector': connector
        }

        # 添加代理
        if self.proxy_url:
            session_kwargs['trust_env'] = True
            session_kwargs['proxy'] = self.proxy_url

        return aiohttp.ClientSession(**session_kwargs)

    def _sign_request(self, params: Dict) -> Dict:
        """为请求参数添加签名"""
        if not self.secret_key:
            return params

        # 添加时间戳
        params['timestamp'] = int(time.time() * 1000)
        # 生成签名
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        params['signature'] = signature
        return params

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                      data: Optional[Dict] = None, signed: bool = False) -> Dict:
        """发送API请求"""
        if not self._initialized:
            await self.initialize()

        url = f'{self.base_url}{endpoint}'
        headers = {'X-MBX-APIKEY': self.api_key} if self.api_key else {}
        params = params or {}

        # 签名请求
        if signed:
            params = self._sign_request(params)

        # 发送请求
        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result
        except aiohttp.ClientError as e:
            print(f"API请求错误: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            print(f"请求处理错误: {str(e)}")
            return {'error': str(e)}
        finally:
            # 遵守API速率限制
            await asyncio.sleep(self._rate_limit_delay)

    async def fetch_ohlcv(self, symbol: str, interval: str, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
        """异步获取K线数据（优先WebSocket实时数据，回退到REST API）"""
        # 如果有活跃的WebSocket订阅，尝试从缓存获取
        ws_symbol = symbol.replace('/', '').lower()
        ws_key = f'{ws_symbol}_{interval}'
        
        if ws_key in self._ws_connections and ws_key in self._ohlcv_cache:
            # 返回最近的limit条数据
            return self._ohlcv_cache[ws_key][-limit:] if len(self._ohlcv_cache[ws_key]) >= limit else self._ohlcv_cache[ws_key]
        
        # 检查本地缓存
        cache_params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        cached_data = await self._load_from_cache('fetch_ohlcv', cache_params)
        if cached_data:
            return cached_data

        # 回退到REST API获取
        params = {
            'symbol': ws_symbol,
            'interval': interval,
            'limit': limit
        }

        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)

        # 发送请求
        data = await self._request('GET', '/v3/klines', params=params)

        if 'error' not in data:
            # 格式化数据
            formatted_data = []
            for item in data:
                formatted_data.append({
                    'open_time': item[0],
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': item[6],
                    'quote_volume': float(item[7]),
                    'count': item[8],
                    'taker_buy_volume': float(item[9]),
                    'taker_buy_quote_volume': float(item[10])
                })

            # 缓存数据
            await self._save_to_cache('fetch_ohlcv', cache_params, formatted_data)
            # 发布市场数据事件
            await self._publish_market_event(symbol, interval, formatted_data[-1] if formatted_data else {})
            return formatted_data

        return []

    async def create_order(self, symbol: str, order_type: str, side: str, quantity: float,
                          price: Optional[float] = None, params: Optional[Dict] = None) -> Dict:
        """异步创建订单"""
        params = params or {}
        order_params = {
            'symbol': symbol.replace('/', ''),
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity,
            **params
        }

        # 添加价格参数(限价单)
        if order_type.upper() == 'LIMIT' and price:
            order_params['price'] = price
            order_params['timeInForce'] = params.get('timeInForce', 'GTC')

        # 发送请求
        result = await self._request('POST', '/v3/order', params=order_params, signed=True)

        if 'error' not in result:
            # 格式化订单数据
            order = {
                'id': result.get('orderId'),
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'price': float(result.get('price', 0)),
                'quantity': float(result.get('origQty')),
                'executed_quantity': float(result.get('executedQty', 0)),
                'status': result.get('status').lower(),
                'timestamp': result.get('transactTime')
            }

            # 发布订单事件
            await self._publish_order_event(order)
            return order

        return {'error': result.get('error', '未知错误')}

    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """异步取消订单"""
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id
        }

        result = await self._request('DELETE', '/v3/order', params=params, signed=True)

        if 'error' not in result:
            order = {
                'id': order_id,
                'symbol': symbol,
                'status': 'cancelled',
                'timestamp': int(time.time() * 1000)
            }
            await self._publish_order_event(order)
            return order

        return {'error': result.get('error', '取消订单失败')}

    async def fetch_balance(self) -> Dict:
        """异步获取账户余额"""
        # 检查缓存
        cached_data = await self._load_from_cache('fetch_balance', {})
        if cached_data:
            return cached_data

        result = await self._request('GET', '/v3/account', signed=True)

        if 'error' not in result and 'balances' in result:
            balance = {}
            for item in result['balances']:
                asset = item['asset']
                free = float(item['free'])
                locked = float(item['locked'])
                if free > 0 or locked > 0:
                    balance[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }

            # 缓存数据
            await self._save_to_cache('fetch_balance', {}, balance)
            # 发布账户更新事件
            asyncio.create_task(event_bus.publish(EventType.ACCOUNT_UPDATE, balance))
            return balance

        return {'error': result.get('error', '获取余额失败')}

    async def subscribe_to_order_book(self, symbol: str, interval: str = '100ms'):
        """订阅订单簿WebSocket"""
        symbol = symbol.replace('/', '').lower()
        ws_url = f'{self.ws_base_url}/{symbol}@depth@{interval}'

        if symbol in self._ws_connections:
            return  # 已订阅

        async def ws_handler():
            """WebSocket消息处理"""
            try:
                async with self._session.ws_connect(ws_url) as websocket:
                    self._ws_connections[symbol] = websocket
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            # 更新本地订单簿
                            self._update_order_book(symbol, data)
                            # 发布订单簿事件
                            asyncio.create_task(event_bus.publish(
                                f'{EventType.MARKET_DATA}_order_book',
                                {'symbol': symbol, 'order_book': self._order_book.get(symbol, {})}
                            ))
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
            except Exception as e:
                print(f"WebSocket错误: {str(e)}")
            finally:
                if symbol in self._ws_connections:
                    del self._ws_connections[symbol]

        # 启动WebSocket处理任务
        asyncio.create_task(ws_handler())
        await asyncio.sleep(1)  # 等待连接建立
        return True

    async def subscribe_to_ohlcv(self, symbol: str, interval: str):
        """订阅K线数据WebSocket

        Args:
            symbol: 交易对符号
            interval: K线周期，如'1m', '5m', '1h'

        Returns:
            bool: 订阅是否成功启动
        """
        symbol = symbol.replace('/', '').lower()
        ws_url = f'{self.ws_base_url}/{symbol}@kline_{interval}'

        ws_key = f'{symbol}_{interval}'
        if ws_key in self._ws_connections:
            return True  # 已订阅

        async def ws_handler():
            """WebSocket消息处理协程"""
            try:
                async with self._session.ws_connect(ws_url) as websocket:
                    self._ws_connections[ws_key] = websocket
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            # 只处理完整K线数据
                            if 'k' in data and data['k']['x']:
                                kline = data['k']
                                formatted_data = {
                                    'open_time': kline['t'],
                                    'open': float(kline['o']),
                                    'high': float(kline['h']),
                                    'low': float(kline['l']),
                                    'close': float(kline['c']),
                                    'volume': float(kline['v']),
                                    'close_time': kline['T'],
                                    'quote_volume': float(kline['q']),
                                    'count': kline['n'],
                                    'taker_buy_volume': float(kline['V']),
                                    'taker_buy_quote_volume': float(kline['Q'])
                                }
                                # 更新缓存
                                if ws_key not in self._ohlcv_cache:
                                    self._ohlcv_cache[ws_key] = []
                                self._ohlcv_cache[ws_key].append(formatted_data)
                                # 限制缓存大小
                                max_cache_size = 1000
                                if len(self._ohlcv_cache[ws_key]) > max_cache_size:
                                    self._ohlcv_cache[ws_key] = self._ohlcv_cache[ws_key][-max_cache_size:]
                                # 发布市场数据事件
                                await self._publish_market_event(symbol, interval, formatted_data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
            except Exception as e:
                print(f"K线WebSocket错误({symbol} {interval}): {str(e)}")
            finally:
                if ws_key in self._ws_connections:
                    del self._ws_connections[ws_key]

        # 启动WebSocket处理任务
        asyncio.create_task(ws_handler())
        await asyncio.sleep(1)  # 等待连接建立
        return True

    def _update_order_book(self, symbol: str, data: Dict):
        """更新订单簿缓存"""
        if symbol not in self._order_book:
            self._order_book[symbol] = {'bids': [], 'asks': []}

        # 更新买单
        for price, quantity in data.get('b', []):
            price = float(price)
            quantity = float(quantity)
            self._order_book[symbol]['bids'] = [
                (p, q) for p, q in self._order_book[symbol]['bids'] if p != price
            ]
            if quantity > 0:
                self._order_book[symbol]['bids'].append((price, quantity))
                # 按价格排序(降序)
                self._order_book[symbol]['bids'].sort(reverse=True, key=lambda x: x[0])

        # 更新卖单
        for price, quantity in data.get('a', []):
            price = float(price)
            quantity = float(quantity)
            self._order_book[symbol]['asks'] = [
                (p, q) for p, q in self._order_book[symbol]['asks'] if p != price
            ]
            if quantity > 0:
                self._order_book[symbol]['asks'].append((price, quantity))
                # 按价格排序(升序)
                self._order_book[symbol]['asks'].sort(key=lambda x: x[0])

    async def close(self):
        """关闭连接器资源"""
        # 关闭所有WebSocket连接
        for symbol, ws in self._ws_connections.items():
            try:
                await ws.close()
            except Exception as e:
                print(f"关闭WebSocket连接 {symbol} 失败: {str(e)}")

        self._ws_connections.clear()
        self._order_book.clear()

        # 关闭aiohttp会话
        if self._session and not self._session.closed:
            await self._session.close()

        self._initialized = False