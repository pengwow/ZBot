# coding=utf-8
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
        return dict(timestamp=candle[0], open=candle[1], high=candle[2], low=candle[3], close=candle[4],
                    volume=candle[5], close_time=candle[6], turnover=candle[7], trade_count=candle[8],
                    buy_volume=candle[9], buy_turnover=candle[10])

    def download_data(self, symbol, interval, start_time=None, end_time=None, limit=10):
        res = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
        bulk_data = []
        for i in res:
            # print(self.format_candle(i))
            bulk_data.append(Candle(symbol=symbol, timeframe=interval, **self.format_candle(i)))
            # Candle.create(**self.format_candle(i))
        print(res)
        Candle.bulk_create(bulk_data)


if __name__ == '__main__':
    config = {"apiKey": 'cYeBjS80ysmWBgsbftH2w1KWFZcZ9Zn7UsfF6JuitjZu1hwfEZA6NsxB4veoeqjk',
              'secret': 'VWuITQrZGcpVm9FdbzHUQKstSCs90f0nzVm3jGk8ac2JogWdNTHjbTOEShrPek70',
              'httpsProxy': 'http://127.0.0.1:7890/'
              }
    h = History(config)
    h.download_data('BTC/USDT', '15m')
