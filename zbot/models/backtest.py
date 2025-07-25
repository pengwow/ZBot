import peewee
from datetime import datetime
from zbot.services.db import database

class BacktestRecord(peewee.Model):
    """回测记录模型，用于存储策略回测的历史记录"""
    id = peewee.AutoField(primary_key=True)
    strategy_name = peewee.CharField(max_length=100, help_text="策略名称")
    start_time = peewee.DateTimeField(help_text="回测开始时间")
    end_time = peewee.DateTimeField(help_text="回测结束时间")
    file_name = peewee.CharField(max_length=255, help_text="策略文件名")
    parameters = peewee.TextField(help_text="策略参数，JSON格式字符串")
    results = peewee.TextField(help_text="回测结果数据，JSON格式字符串")
    result_file_path = peewee.CharField(max_length=255, help_text="回测结果文件路径")
    status = peewee.CharField(max_length=20, default="completed", help_text="回测状态: running/completed/failed")
    total_return = peewee.FloatField(help_text="总收益率")
    max_drawdown = peewee.FloatField(help_text="最大回撤")
    created_at = peewee.DateTimeField(default=datetime.now, help_text="记录创建时间")

    @classmethod
    def get_by_strategy(cls, strategy_name: str):
        """按策略名称查询回测记录
        Args:
            strategy_name: 策略名称
        Returns:
            匹配的回测记录列表
        """
        return cls.select().where(cls.strategy_name == strategy_name)

    @classmethod
    def get_latest_records(cls, limit: int = 10):
        """获取最新的回测记录
        Args:
            limit: 记录数量限制
        Returns:
            最新的回测记录列表
        """
        return cls.select().order_by(cls.created_at.desc()).limit(limit)

    class Meta:
        """模型元数据"""
        indexes = (
            (('strategy_name', 'start_time'), False),  # 非唯一索引
            (('created_at',), False),
        )
        table_name = 'backtest_records'
        database = database.db

database.open_connection()
database.db.create_tables([BacktestRecord])
database.db.close()

