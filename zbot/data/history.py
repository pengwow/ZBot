# coding=utf-8

class History(object):
    def __init__(self, exchange_name, symbol, timeframe):
        self.exchange_name = exchange_name
        self.symbol = symbol
        self.timeframe = timeframe

    # @abs
    # def download_data(self, pair, start_time, end_time):
    #     pass
