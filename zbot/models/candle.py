import peewee


class Candle(peewee.Model):
    id = peewee.AutoField()
    open_time = peewee.BigIntegerField()
    open = peewee.FloatField()
    close = peewee.FloatField()
    high = peewee.FloatField()
    low = peewee.FloatField()
    volume = peewee.FloatField()
    symbol = peewee.CharField()
    timeframe = peewee.CharField()

    def get_by_symbol(symbol: str):
        """按symbol查询单条记录（自动处理斜杠）"""
        formatted_symbol = symbol.replace('/', '')
        return formatted_symbol

    class Meta:
        indexes = (
            (('symbol', 'timeframe', 'open_time'), True),
        )
