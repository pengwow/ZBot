from datetime import datetime
import time

import ccxt
import pandas as pd
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import SPOT_REST_API_TESTNET_URL, SPOT_REST_API_PROD_URL, DERIVATIVES_TRADING_COIN_FUTURES_REST_API_TESTNET_URL, DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
from binance_sdk_spot.spot import Spot
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import DerivativesTradingUsdsFutures as Future
from zbot.exchange import Exchange
from zbot.exchange.binance.data import History
from zbot.exchange.binance.models import Candle
from zbot.services.model import get_candles_from_db
from zbot.utils.dateutils import str_to_timestamp


class BinanceExchange(Exchange):
    """
    定义 BinanceExchange 类，继承自 Exchange 类，用于与 Binance 交易所进行交互
    """

    def __init__(self, exchange_name='binance', api_key=None, secret_key=None, trading_mode='spot', proxy_url=None, testnet=False):
        """
        初始化方法，用于创建 Binance 交易所客户端实例
        :param exchange_name: 交易所名称
        :param api_key: API 密钥
        :param secret_key: 密钥
        :param proxy_url: 代理 URL
        :param testnet: 是否使用测试网络，默认为 False
        """
        # 调用父类的初始化方法
        super().__init__(exchange_name, api_key, secret_key, trading_mode, proxy_url, testnet)
        # 创建 ccxt 的 binance 交易所实例
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })
        # 如果提供了代理 URL，则设置代理
        if proxy_url:
            self.exchange.proxies = {
                'https': proxy_url,
                'http': proxy_url
            }
        # 如果使用测试网络，则开启沙箱模式
        if testnet:
            self.exchange.set_sandbox_mode(True)
        # 设置自定义的 ohlcv 解析方法
        self.exchange.parse_ohlcv = self.prase_ohlcv_custom

        # 定义 K 线数据的字段名称
        self.candle_names = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'count', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ]
        self.trading_mode = trading_mode
        self.exchange.load_markets()
        self._symbols = None
        self.spot_api = Spot(ConfigurationRestAPI(api_key, secret_key, SPOT_REST_API_TESTNET_URL if testnet else SPOT_REST_API_PROD_URL))
        self.future_api = Future(ConfigurationRestAPI(api_key, secret_key, DERIVATIVES_TRADING_COIN_FUTURES_REST_API_TESTNET_URL if testnet else DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL))

    
    def health_check(self) -> bool:
        """
        策略健康检查，确保市场数据和账户信息正常，是做市风险控制的第一道防线
        
        健康检查在加密货币做市中至关重要，因为实时市场数据和账户状态的准确性直接影响：
        1. 订单定价合理性
        2. 风险敞口控制
        3. 策略决策有效性
        
        检查项包括：
        1. 订单簿数据新鲜度（延迟不超过设定阈值）
        2. 订单簿校验和（确保数据完整性，防止传输错误）
        3. 账户信息时效性
        
        :return: True表示健康状态良好，False表示存在异常需要处理
        """

        return super().health_check()

    def check_status(self):
        """
        检查交易所系统状态，避免在维护期间进行交易
        
        加密货币交易所会定期进行系统维护，期间可能暂停交易或数据更新
        在此期间进行做市可能导致：
        - 订单无法成交
        - 市场数据延迟或不准确
        - API响应异常
        
        实现逻辑：
        - 查询交易所状态API
        - 检查是否有正在进行或即将进行的维护
        - 返回维护状态，决定是否继续做市
        
        :return: True表示交易所正常，False表示存在维护或异常
        """
        
        if self.spot_api.rest_api.ping():
            return True
        return False

    def prase_ohlcv_custom(self, ohlcv, market):
        """
        自定义的 ohlcv 解析方法，当前直接返回原始数据
        :param ohlcv: K 线数据
        :param market: 市场信息
        :return: 解析后的 K 线数据
        """
        return ohlcv

    @staticmethod
    def format_candle(candle: list) -> dict:
        """
        静态方法，用于将 K 线数据列表格式化为字典
        :param candle: K 线数据列表
        :return: 格式化后的 K 线数据字典
        """
        return dict(
            open_time=candle[0],
            open=candle[1],
            high=candle[2],
            low=candle[3],
            close=candle[4],
            volume=candle[5],
            close_time=candle[6],
            quote_volume=candle[7],
            count=candle[8],
            taker_buy_volume=candle[9],
            taker_buy_quote_volume=candle[10],
            ignore=candle[11]
        )

    # 下载数据
    def download_data(self, symbol: str, interval: str, start_time=None, end_time=None, limit=500, candle_type=None, progress_queue=None):
        """
        下载 K 线数据的方法
        :param symbol: 交易对符号
        :param interval: 时间间隔，如 '1m', '1h' 等
        :param start_time: 开始时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :param end_time: 结束时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :param limit: 每次获取数据的最大条数，默认为 500
        :param candle_type: 交易模式，spot 或 future，默认为 None
        :return: 保存到数据库的 K 线数据列表
        """
        # 解析时间参数
        if start_time:
            start_time = str_to_timestamp(start_time)
        if end_time:
            end_time = str_to_timestamp(end_time)
        symbol = symbol.replace('/', '')
        # 如果提供了开始时间和结束时间
        if start_time and end_time:
            # 获取当前时间戳(毫秒)
            current_time = int(time.time() * 1000)
            # 计算 30 天前的时间戳(毫秒)
            thirty_days_ago = current_time - 7 * 24 * 60 * 60 * 1000
            # 接口只能获取7天内数据,超过七天的数据从归档地址获取
            if start_time < thirty_days_ago:
                # 从历史归档地址下载历史数据
                history = History(self)
                res = history.download_from_archive(
                    symbol, interval, candle_type or self.trading_mode, start_time, end_time, progress_queue)
                return res
            else:
                h = History(self)
                res = h.download_data(
                    symbol, interval, start_time, end_time, limit)
        return

    def load_data(self, symbol, interval, start_time=None, end_time=None):
        """
        从数据库加载 K 线数据的方法
        :param symbol: 交易对符号
        :param interval: 时间间隔，如 '1m', '1h' 等
        :param start_time: 开始时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :param end_time: 结束时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :return: 从数据库加载的 K 线数据列表
        """
        candles = get_candles_from_db(
            'binance', symbol, interval, start_time, end_time)
        return candles

    @property
    def symbols(self):
        if not self._symbols:
            self._symbols = [i for i in self.exchange.symbols if ':' not in i]
        return self._symbols


    def balance(self):
        response: AccountInformationV3Response = self.future_api.rest_api.account_information_v3()
        return response.data()

if __name__ == '__main__':
    from zbot.common.config import read_config
    config = read_config('exchange')['binance']
    client = BinanceExchange(
        api_key=config['api_key'], secret_key=config['secret_key'], proxy_url=config['proxy_url'])
    symbols = client.symbols
    print(symbols)
    response = client.rest_api.futures_account_balance_v3()
