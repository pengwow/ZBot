import ccxt
from datetime import datetime
from zbot.exchange.exchange import Exchange
from zbot.exchange.binance.models import Candle
from zbot.exchange.binance.data import History
from zbot.utils.dateutils import format_datetime
import time


class BinanceExchange(Exchange):
    def __init__(self, exchange_name, api_key, secret_key, proxy_url, testnet=False):
        super().__init__(exchange_name, api_key, secret_key, testnet)
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })
        if proxy_url:
            self.exchange.proxies = {
                'https': proxy_url,
                'http': proxy_url
            }
        if testnet:
            self.exchange.set_sandbox_mode(True)
        self.exchange.parse_ohlcv = self.prase_ohlcv_custom

        self.candle_names = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'count', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ]

    def prase_ohlcv_custom(self, ohlcv, market):
        return ohlcv

    @staticmethod
    def format_candle(candle: list) -> dict:
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

    def download_data(self, symbol, interval, start_time=None, end_time=None, limit=500):
        if start_time and end_time:
            current_time = int(time.time() * 1000)  # 获取当前时间戳(毫秒)
            thirty_days_ago = current_time - 30 * \
                24 * 60 * 60 * 1000  # 30天前的时间戳(毫秒)
            if start_time < thirty_days_ago:
                # 从历史归档地址下载历史数据
                history = History(self)
                res = history.download_from_archive(
                    symbol, interval, start_time, end_time)
            else:
                # 将时间戳转换为 datetime 对象
                start_datetime = datetime.fromtimestamp(start_time / 1000)
                end_datetime = datetime.fromtimestamp(end_time / 1000)
                # 计算时间差
                delta = end_datetime - start_datetime
                # 计算需要的总条数
                total_minutes = delta.total_seconds() / 60
                interval_minutes = self.get_interval_minutes(interval)
                total_bars = int(total_minutes / interval_minutes) + 1
                # 如果总条数超过限制，则分多次获取
                if total_bars > limit:
                    all_ohlcv = []
                    current_time = start_time
                    while current_time < end_time:
                        next_time = current_time + limit * interval_minutes * 60 * 1000
                        if next_time > end_time:
                            next_time = end_time
                        ohlcv = self.exchange.fetch_ohlcv(
                            symbol, interval, current_time, min(limit, total_bars), params={})
                        if not ohlcv:
                            break
                        all_ohlcv.extend(ohlcv)
                        current_time = ohlcv[-1][0] + 1
                        total_bars -= len(ohlcv)
                        if total_bars <= 0:
                            break
                    res = all_ohlcv
                else:
                    res = self.exchange.fetch_ohlcv(
                        symbol, interval, start_time, limit, params={})
        else:
            res = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)

        bulk_data = []
        for i in res:
            bulk_data.append(
                Candle(symbol=symbol, timeframe=interval, **self.format_candle(i)))

        if bulk_data:
            Candle.bulk_create(bulk_data)
        return bulk_data
        # if start_time and end_time:
        #     # 将时间戳转换为 datetime 对象
        #     start_datetime = datetime.fromtimestamp(start_time / 1000)
        #     end_datetime = datetime.fromtimestamp(end_time / 1000)
        #     # 计算时间差
        #     delta = end_datetime - start_datetime
        #     # 计算需要的总条数
        #     total_minutes = delta.total_seconds() / 60
        #     interval_minutes = self.get_interval_minutes(interval)
        #     total_bars = int(total_minutes / interval_minutes) + 1
        #     # 如果总条数超过限制，则分多次获取
        #     if total_bars > limit:
        #         all_ohlcv = []
        #         current_time = start_time
        #         while current_time < end_time:
        #             next_time = current_time + limit * interval_minutes * 60 * 1000
        #             if next_time > end_time:
        #                 next_time = end_time
        #             ohlcv = self.exchange.fetch_ohlcv(symbol, interval, current_time, min(limit, total_bars), params={})
        #             if not ohlcv:
        #                 break
        #             all_ohlcv.extend(ohlcv)
        #             current_time = ohlcv[-1][0] + 1
        #             total_bars -= len(ohlcv)
        #             if total_bars <= 0:
        #                 break
        #         res = all_ohlcv
        #     else:
        #         res = self.exchange.fetch_ohlcv(symbol, interval, start_time, limit, params={})
        # else:
        #     res = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)

        # bulk_data = []
        # for i in res:
        #     bulk_data.append(Candle(symbol=symbol, timeframe=interval, **self.format_candle(i)))

        # if bulk_data:
        #     Candle.bulk_create(bulk_data)
        # return bulk_data

    @staticmethod
    def get_interval_minutes(interval):
        interval_map = {
            '1m': 1,
            '3m': 3,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '8h': 480,
            '12h': 720,
            '1d': 1440,
            '3d': 4320,
            '1w': 10080,
            '1M': 43200
        }
        return interval_map.get(interval, 1)
