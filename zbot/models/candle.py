import peewee
from zbot.services.db import database

class Candle(peewee.Model):
    id = peewee.UUIDField(primary_key=True)
    timestamp = peewee.BigIntegerField()
    open = peewee.FloatField()
    close = peewee.FloatField()
    high = peewee.FloatField()
    low = peewee.FloatField()
    volume = peewee.FloatField()
    symbol = peewee.CharField()
    timeframe = peewee.CharField()

    class Meta:
        database = database.db
        indexes = (
            (('symbol', 'timeframe', 'timestamp'), True),
        )