#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移文件: initial_migration
生成时间: 2025-07-30 13:35:08
"""
import peewee
from playhouse.migrate import migrate
from zbot.services.db import database
from playhouse.migrate import SqliteMigrator

def up():
    """应用迁移"""
    db = database.db
    migrator = SqliteMigrator(db)

    # 在这里添加迁移操作
    # 示例: migrate(migrator.add_column('table_name', 'column_name', field))
    # 添加风险指标字段
    trades = peewee.TextField(help_text="回测交易记录，JSON格式字符串", null=True)
    migrate(migrator.add_column('backtest_records', 'trades', trades))

def down():
    """回滚迁移"""
    db = database.db
    migrator = SqliteMigrator(db)

    # 在这里添加回滚操作
    # 示例: migrate(migrator.drop_column('table_name', 'column_name'))
