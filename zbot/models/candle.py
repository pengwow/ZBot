import peewee


class Candle(peewee.Model):
    id = peewee.AutoField()
    timestamp = peewee.BigIntegerField()
    open = peewee.FloatField()
    close = peewee.FloatField()
    high = peewee.FloatField()
    low = peewee.FloatField()
    volume = peewee.FloatField()
    symbol = peewee.CharField()
    timeframe = peewee.CharField()

    class Meta:
        indexes = (
            (('symbol', 'timeframe', 'timestamp'), True),
        )


