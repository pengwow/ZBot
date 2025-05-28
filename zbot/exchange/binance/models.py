import peewee
from zbot.models.candle import Candle as CandleBase
from zbot.services.db import database


class Candle(CandleBase):
    # 成交额
    turnover = peewee.FloatField(default=0)
    # 成交笔数
    trade_count = peewee.IntegerField(default=0)
    # 主动买入成交量
    buy_volume = peewee.FloatField(default=0)
    # 主动买入成交额
    buy_turnover = peewee.FloatField(default=0)
    # 收盘时间
    close_time = peewee.BigIntegerField(null=True)

    class Meta:
        table_name = "binance_candle"
        database = database.db
        indexes = ((("symbol", "timeframe", "timestamp"), True),)


database.open_connection()
database.db.create_tables([Candle])
database.db.close()
