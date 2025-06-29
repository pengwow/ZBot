# coding=utf-8
import os
from datetime import datetime, timedelta
from tkinter import N
import zipfile
import pandas as pd
import numpy as np
import aiohttp
import asyncio
import ccxt
from io import BytesIO
import ssl
import certifi

from zbot.exchange.binance.models import Candle


class History(object):
    def __init__(self, exchange):
        self.exchange = exchange.exchange
        self.candle_names = exchange.candle_names

        self.exchange.parse_ohlcv = self.prase_ohlcv_custom

    def prase_ohlcv_custom(self, ohlcv, market):
        # 获取原始OHLCV响应
        return ohlcv

    @staticmethod
    def get_interval_minutes(interval):
        """
        静态方法，用于获取时间间隔对应的分钟数
        :param interval: 时间间隔，如 '1m', '1h' 等
        :return: 时间间隔对应的分钟数，如果未找到则返回 1
        """
        # 定义时间间隔与分钟数的映射关系
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
        # 根据时间间隔获取对应的分钟数，未找到则返回 1
        return interval_map.get(interval, 1)

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
        # TODO: 未完,根据fetch_ohlcv返回结果,进行遍历,只取所有符合要求的 start_time 和 end_time时间戳数据返回
        all_ohlcv = []
        ohlcv = self.exchange.fetch_ohlcv(
            symbol, interval, None, limit, params={})
        all_ohlcv.extend(ohlcv)
        self._process_ohlcv_data(symbol, interval, ohlcv)
        return all_ohlcv

    def _get_interval_ms(self, interval):
        """将时间间隔字符串转换为毫秒数"""
        interval_map = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
        }
        return interval_map.get(interval, 60 * 1000)  # 默认1分钟

    def _process_ohlcv_data(self, symbol, interval, ohlcv):
        """
        处理获取到的 K 线数据，插入或更新到数据库
        :param symbol: 货币对
        :param interval: 时间间隔
        :param ohlcv: K 线数据列表
        """
        for candle in ohlcv:
            candle_data = self.format_candle(candle)
            # 根据 symbol、open_time 和 interval 查询是否已存在记录
            existing_candle = Candle.select().where(
                (Candle.symbol == symbol) &
                (Candle.timeframe == interval) &
                (Candle.open_time == candle_data['open_time'])
            ).first()
            if existing_candle:
                # 如果存在则更新记录
                for key, value in candle_data.items():
                    setattr(existing_candle, key, value)
                existing_candle.save()
            else:
                # 如果不存在则创建新记录
                Candle.create(
                    symbol=symbol,
                    timeframe=interval,
                    **candle_data
                )

    def download_from_archive(self, symbol, timeframe, candle_type, date):
        res = asyncio.run(self.get_daily_klines(
            symbol, timeframe, candle_type, date))
        if not res.empty:
            bulk_data = []
            for _, row in res.iterrows():
                candle_data = row.to_dict()
                # 根据 symbol、open_time 和 timeframe 查询是否已存在记录
                existing_candle = Candle.select().where(
                    (Candle.symbol == symbol) &
                    (Candle.timeframe == timeframe) &
                    (Candle.open_time == candle_data['open_time'])
                ).first()
                if existing_candle:
                    # 如果存在则更新记录
                    for key, value in candle_data.items():
                        setattr(existing_candle, key, value)
                    existing_candle.save()
                else:
                    # 如果不存在则创建新记录
                    bulk_data.append(
                        Candle(
                            symbol=symbol,
                            timeframe=timeframe,
                            **candle_data
                        )
                    )

            if bulk_data:
                Candle.bulk_create(bulk_data)

        print(res.head())

    @staticmethod
    def get_url_by_candle_type(candle_type):
        if candle_type in ('spot', 'option'):
            return candle_type
        elif candle_type == 'futures':
            return 'futures/um'
        else:
            raise ValueError('Invalid candle_type')

    def get_zip_name(self, symbol, timeframe, date):
        return f"{symbol}-{timeframe}-{date}.zip"

    def get_zip_url(self, symbol, timeframe, candle_type, date):
        """
        获取压缩文件下载地址
        https://data.binance.vision/data/spot/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2024-10-27.zip
        https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1h/BTCUSDT-1h-2024-10-27.zip
        :param symbol: 货币对
        :param timeframe: 时间间隔
        :param candle_type: 类型
        :param date: 日期
        :return:
        """
        asset_type = self.get_url_by_candle_type(candle_type)
        zip_name = self.get_zip_name(symbol, timeframe, date)
        url = (
            f"https://data.binance.vision/data/{
                asset_type}/daily/klines/{symbol}"
            f"/{timeframe}/{zip_name}"
        )
        return url

    # 异步获取指定日期的K线数据
    async def get_daily_klines(self, symbol, timeframe, candle_type, date):
        url = self.get_zip_url(symbol, timeframe, candle_type, date)
        connector = aiohttp.TCPConnector(
            ssl=ssl.create_default_context(cafile=certifi.where()))
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    # logger.debug(f"Successfully downloaded {url}")
                    with zipfile.ZipFile(BytesIO(content)) as zipf:
                        with zipf.open(zipf.namelist()[0]) as csvf:
                            # https://github.com/binance/binance-public-data/issues/283
                            first_byte = csvf.read(1)[0]
                            if chr(first_byte).isdigit():
                                header = None
                            else:
                                header = 0
                            csvf.seek(0)

                            df = pd.read_csv(
                                csvf,
                                usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                                names=self.candle_names,
                                header=header
                            )
                            # df["open_time"] = pd.to_datetime(
                            #     np.where(df["open_time"] > 1e13, df["open_time"] // 1000, df["open_time"]),
                            #     unit="ms",
                            #     utc=True,
                            # )
                            return df
        return None


if __name__ == '__main__':
    from zbot.common.config import read_config
    config = read_config('BINANCE')
    # exchange = ccxt.binance({
    #         'apiKey': config.get('api_key'),
    #         'secret': config.get('secret_key'),
    #         'enableRateLimit': True,
    #         'options': {'defaultType': 'spot'},
    # })
    # exchange.fetch_ohlcv()
    # exchange.proxies = {
    #     'https': config.get('proxy_url'),
    #     'http': config.get('proxy_url')
    # }
    from zbot.exchange.binance.client import BinanceExchange
    exchange = BinanceExchange(**{
        'api_key': config.get('api_key'),
        'secret_key': config.get('secret_key'),
        'proxy_url': config.get('proxy_url')
    })
    h = History(exchange)
    # h.download_data('BTC/USDT', '15m')
    h.download_data('BTCUSDT', '15m', 'futures')
    # h.download_from_archive('BTCUSDT', '15m', 'futures', '2024-10-27')
    # res = h.get_zip_url('BTCUSDT', '15m', 'spot', '2024-10-27')
    # print(res)
