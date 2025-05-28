# coding=utf-8
import aiohttp
import asyncio
import ccxt
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

    def prase_ohlcv_custom(self, ohlcv, market):
        # 获取原始OHLCV响应
        return ohlcv

    @staticmethod
    def format_candle(candle: list) -> dict:
        return dict(timestamp=candle[0],
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5],
                    close_time=candle[6],
                    turnover=candle[7],
                    trade_count=candle[8],
                    buy_volume=candle[9],
                    buy_turnover=candle[10]
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

    def download_archive_data(self):
        asyncio.run(self.get_daily_klines('BTC/USDT', '15m', 'futures', '2024-10-27'))

    def get_url_by_candle_type(self, candle_type):
        if candle_type == 'spot':
            return 'spot'
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

    async def get_daily_klines(self, symbol, timeframe, candle_type, date):
        url = self.get_zip_url(symbol, timeframe, candle_type, date)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"状态码: {response.status}")
                html = await response.text()  # 获取文本响应
                return html[:100]  # 截取前100字符


if __name__ == '__main__':
    config = {"apiKey": 'cYeBjS80ysmWBgsbftH2w1KWFZcZ9Zn7UsfF6JuitjZu1hwfEZA6NsxB4veoeqjk',
              'secret': 'VWuITQrZGcpVm9FdbzHUQKstSCs90f0nzVm3jGk8ac2JogWdNTHjbTOEShrPek70',
              'httpsProxy': 'http://127.0.0.1:7890/'
              }
    h = History(config)
    # h.download_data('BTC/USDT', '15m')
    res = h.get_zip_url('BTCUSDT', '15m', 'futures', '2024-10-27')
    print(res)
