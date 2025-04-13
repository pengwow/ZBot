import peewee
from zbot.models.candle import Candle as CandleBase


class Candle(CandleBase):
    # 成交额
    turnover = peewee.FloatField(default=0)
    # 成交笔数
    trade_count = peewee.IntegerField(default=0)
    # 主动买入成交量
    buy_volume = peewee.FloatField(default=0)
    # 主动买入成交额
    buy_turnover = peewee.FloatField(default=0)
    # 开盘时间
    open_time = peewee.BigIntegerField(null=True)
    # 收盘时间
    close_time = peewee.BigIntegerField(null=True)
