import ccxt
from datetime import datetime
from zbot.exchange.exchange import Exchange
from zbot.exchange.binance.models import Candle
from zbot.exchange.binance.data import History
from zbot.utils.dateutils import str_to_timestamp
import time


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

    def download_data(self, symbol, interval, start_time=None, end_time=None, limit=500, trading_mode=None, progress_queue=None):
        """
        下载 K 线数据的方法
        :param symbol: 交易对符号
        :param interval: 时间间隔，如 '1m', '1h' 等
        :param start_time: 开始时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :param end_time: 结束时间，格式为 '2025-01-01 10:00:00' 或 '2025-01-01'，默认为 None
        :param limit: 每次获取数据的最大条数，默认为 500
        :return: 保存到数据库的 K 线数据列表
        """
        # 解析时间参数
        if start_time:
            start_time = str_to_timestamp(start_time)
        if end_time:
            end_time = str_to_timestamp(end_time)
        # 如果提供了开始时间和结束时间
        if start_time and end_time:
            # 获取当前时间戳(毫秒)
            current_time = int(time.time() * 1000)
            # 计算 30 天前的时间戳(毫秒)
            thirty_days_ago = current_time - 30 * 24 * 60 * 60 * 1000
            # 如果开始时间早于 30 天前，则从历史归档地址下载数据
            if start_time < thirty_days_ago:
                # 从历史归档地址下载历史数据
                history = History(self)
                res = history.download_from_archive(
                    symbol, interval, trading_mode or self.trading_mode, start_time, end_time, progress_queue)
                return res
            else:
                h = History(self)
                res = h.download_data(symbol, interval, start_time, end_time, limit)
        return

    