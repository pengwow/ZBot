# coding=utf-8
import zipfile
import pandas as pd
import numpy as np
import aiohttp
import asyncio
import ccxt
from io import BytesIO
import ssl
import certifi
from zbot.data.history import History as HistoryBase
from zbot.exchange.binance.models import Candle


class History(HistoryBase):
    def __init__(self, config):
        # super(History, self).__init__()
        self.exchange = ccxt.binance(config)
        # self.exchange. =
        # self.exchange.httpsProxy = 'https://127.0.0.1:7890/'
        # self.prase_ohlcv_original = self.exchange.parse_ohlcv
        self.exchange.parse_ohlcv = self.prase_ohlcv_custom

        self.candle_names = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume',
                            'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']

    def prase_ohlcv_custom(self, ohlcv, market):
        # 获取原始OHLCV响应
        return ohlcv

    @staticmethod
    def format_candle(candle: list) -> dict:
        return dict(open_time=candle[0],
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
        res = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
        bulk_data = []
        for i in res:
            # print(self.format_candle(i))
            bulk_data.append(Candle(symbol=symbol, timeframe=interval, **self.format_candle(i)))
            # Candle.create(**self.format_candle(i))
        print(res)
        Candle.bulk_create(bulk_data)

    def download_archive_data(self, symbol, timeframe, candle_type, date):
        res = asyncio.run(self.get_daily_klines(symbol, timeframe, candle_type, date))
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
            f"https://data.binance.vision/data/{asset_type}/daily/klines/{symbol}"
            f"/{timeframe}/{zip_name}"
        )
        return url

    # 异步获取指定日期的K线数据
    async def get_daily_klines(self, symbol, timeframe, candle_type, date):
        url = self.get_zip_url(symbol, timeframe, candle_type, date)
        connector = aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where()))
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
                                header=header,
                            )
                            df["open_time"] = pd.to_datetime(
                                np.where(df["open_time"] > 1e13, df["open_time"] // 1000, df["open_time"]),
                                unit="ms",
                                utc=True,
                            )
                            return df
                return ''
                # print(f"状态码: {resp.status}")
                # html = await resp.text()  # 获取文本响应
                # return html[:100]  # 截取前100字符


if __name__ == '__main__':
    config = {"apiKey": 'cYeBjS80ysmWBgsbftH2w1KWFZcZ9Zn7UsfF6JuitjZu1hwfEZA6NsxB4veoeqjk',
              'secret': 'VWuITQrZGcpVm9FdbzHUQKstSCs90f0nzVm3jGk8ac2JogWdNTHjbTOEShrPek70',
              'httpsProxy': 'http://127.0.0.1:7890/'
              }
    h = History(config)
    # h.download_data('BTC/USDT', '15m')
    h.download_archive_data('BTCUSDT', '15m', 'futures', '2024-10-27')
    # res = h.get_zip_url('BTCUSDT', '15m', 'spot', '2024-10-27')
    # print(res)
