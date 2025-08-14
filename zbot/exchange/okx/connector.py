import asyncio
import aiohttp
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import urllib.parse
import json
from zbot.exchange import Exchange
from zbot.common.config import read_config
# from zbot.services.db import DBService
from zbot.models.candle import Candle
from okx.Account import AccountAPI


class OkxExchange(Exchange):
    """Okx交易所连接器实现"""
    account_api: AccountAPI  # OKX账户API客户端，用于查询账户信息

    def __init__(self, api_key: str, secret_key: str, proxy_url: str = None, testnet: bool = False, api_passphrase: str = None):
        """
        初始化做市策略基类实例，创建与OKX交易所的连接并初始化核心服务

        在加密货币量化交易中，初始化过程非常重要，它建立了与交易所的通信通道
        并准备好做市所需的所有基础组件。此构造函数完成以下关键工作：
        1. 创建交易、状态和账户API客户端
        2. 初始化市场数据服务(WSS实时行情)、订单管理服务和仓位管理服务
        3. 初始化策略订单缓存字典和参数加载器

        :param api_key: OKX API密钥
        :param secret_key: OKX API密钥密钥
        :param api_passphrase: OKX API密码
        :param testnet: 是否为模拟交易环境（True为模拟盘，False为实盘）
        """
        super().__init__(api_key, secret_key, proxy_url, testnet)
        self.base_url = 'https://www.okx.com' if not testnet else 'https://www.okx.com'
        self.ws_url = 'wss://ws.okx.com:8443/ws/v5/public' if not testnet else 'wss://wspap.okx.com:8443/ws/v5/public'
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.testnet = testnet
        self.session = aiohttp.ClientSession()
        self.ws_session = None
        self.ws_connection = None
        self.db = DBService()
        self.headers = {
            'Content-Type': 'application/json',
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': '',
            'OK-ACCESS-TIMESTAMP': '',
            'OK-ACCESS-PASSPHRASE': ''
        }
        self.passphrase = hmac.new(
            self.secret_key.encode(), b'OK_ACCESS', hashlib.sha256).hexdigest()
        self.candle_callback: Optional[Callable] = None

        # 创建OKX账户API客户端
        self.account_api = AccountAPI(api_key=api_key, api_secret_key=secret_key, passphrase=self.passphrase,
                                      flag='0' if not testnet else '1', debug=False, proxy=proxy_url or None)

    @staticmethod
    def get_account() -> Account:
        """
        获取账户信息，包括余额、可用资金和账户状态

        在加密货币做市中，实时掌握账户状态至关重要：
        1. 监控可用资金，避免超额下单
        2. 跟踪资金变动，检测异常交易
        3. 计算风险指标，如资金使用率

        :return: 账户对象，包含总资产、可用资金、冻结资金等信息
        :raises ValueError: 如果账户缓存未准备就绪
        """
        if not account_container:
            raise ValueError(
                f"account information not ready in accounts cache!")
        account: Account = account_container[0]
        return account

    async def close(self):
        """关闭所有会话连接"""
        if self.session:
            await self.session.close()
        if self.ws_connection:
            await self.ws_connection.close()
        if self.ws_session:
            await self.ws_session.close()

    async def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time()))
        self.headers['OK-ACCESS-TIMESTAMP'] = timestamp
        self.headers['OK-ACCESS-PASSPHRASE'] = self.passphrase
        self.headers['OK-ACCESS-SIGN'] = self._generate_sign(
            method, endpoint, timestamp, params, data)
        async with self.session.request(method, url, headers=self.headers, params=params, data=data) as response:
            return await response.json()

    def _generate_sign(self, method: str, endpoint: str, timestamp: str, params: Dict = None, data: Dict = None) -> str:
        """生成签名"""
        if params:
            query_string = urllib.parse.urlencode(params)
            endpoint = f"{endpoint}?{query_string}"
        if data:
            data = json.dumps(data)
        message = f"{timestamp}{method.upper()}{endpoint}{data or ''}"
        return hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

    async def connect_ws(self) -> None:
        """
        建立WebSocket连接
        Connect to OKX WebSocket server
        """
        self.ws_session = aiohttp.ClientSession()
        self.ws_connection = await self.ws_session.ws_connect(self.ws_url)
        print("WebSocket connected successfully")

    async def subscribe_candle(self, inst_id: str, bar: str = '1m') -> None:
        """
        订阅K线数据
        Subscribe to candle data
        :param inst_id: 交易对，如 BTC-USDT
        :param bar: K线周期，如 1m, 5m, 1h
        """
        if not self.ws_connection:
            await self.connect_ws()

        subscribe_msg = {
            "op": "subscribe",
            "args": [{
                "channel": "candle",
                "instId": inst_id,
                "bar": bar
            }]
        }
        await self.ws_connection.send_json(subscribe_msg)
        print(f"Subscribed to {inst_id} {bar} candles")

    async def listen_candles(self, duration: int = 30) -> None:
        """
        监听并处理K线数据
        Listen for and process candle data
        :param duration: 监听时长(秒)
        """
        if not self.ws_connection:
            await self.connect_ws()

        end_time = time.time() + duration
        while time.time() < end_time:
            msg = await self.ws_connection.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._process_candle_data(data)
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break
            await asyncio.sleep(0.1)

    async def _process_candle_data(self, data: Dict) -> None:
        """
        处理K线数据并入库
        Process candle data and store in database
        :param data: WebSocket接收的原始数据
        """
        if 'data' in data and data['arg']['channel'] == 'candle':
            candle_data = data['data'][0]
            # 解析K线数据
            candle = Candle(
                exchange='okx',
                symbol=data['arg']['instId'],
                interval=data['arg']['bar'],
                timestamp=int(candle_data[0]),
                open=float(candle_data[1]),
                high=float(candle_data[2]),
                low=float(candle_data[3]),
                close=float(candle_data[4]),
                volume=float(candle_data[5])
            )
            # 存储到数据库
            await self.db.insert_candle(candle)
            print(
                f"Stored candle: {candle.symbol} {candle.interval} {datetime.fromtimestamp(candle.timestamp/1000)}")
            if self.candle_callback:
                self.candle_callback(candle)

    def set_candle_callback(self, callback: Callable[[Candle], None]) -> None:
        """
        设置K线数据回调函数
        Set callback function for candle data
        :param callback: 处理K线数据的回调函数
        """
        self.candle_callback = callback


if __name__ == "__main__":
    """测试WebSocket订阅K线数据功能"""
    import asyncio
    from zbot.common.config import read_config

    async def test_candle_subscription():
        # 从配置文件读取API密钥
        config = read_config()
        api_key = config.get('okx', {}).get('api_key', 'your_api_key')
        secret_key = config.get('okx', {}).get('secret_key', 'your_secret_key')
        testnet = config.get('okx', {}).get('testnet', True)

        # 创建OKX交易所实例
        okx_exchange = OkxExchange(api_key, secret_key, testnet=testnet)

        try:
            # 订阅BTC-USDT的1分钟K线
            await okx_exchange.subscribe_candle('BTC-USDT', '1m')
            print("开始监听K线数据，持续30秒...")
            # 监听30秒K线数据
            await okx_exchange.listen_candles(duration=30)
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
        finally:
            # 关闭连接
            await okx_exchange.close()
            print("连接已关闭")

    # 运行测试
    asyncio.run(test_candle_subscription())
