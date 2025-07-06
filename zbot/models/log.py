import peewee
from enum import Enum
from zbot.services.db import database

class LogType(str, Enum):
    """日志类型枚举
    
    数据类型: 与数据下载、处理相关的日志
    回测类型: 策略回测过程中的日志
    操作类型: 用户操作相关的日志
    系统类型: 系统运行状态相关的日志
    """
    DATA = "data"
    BACKTEST = "backtest"
    OPERATION = "operation"
    SYSTEM = "system"


class Log(peewee.Model):
    id = peewee.AutoField()
    task_id = peewee.UUIDField(index=True)
    timestamp = peewee.BigIntegerField()
    message = peewee.TextField()
    type = peewee.CharField(max_length=10, choices=[(t.value, t.value) for t in LogType])

    class Meta:
        database = database.db
        indexes = (
            (('task_id', 'type', 'timestamp'), False),
        )

database.open_connection()
database.db.create_tables([Log])
database.db.close()