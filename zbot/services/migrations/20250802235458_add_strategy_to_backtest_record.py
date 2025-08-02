#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移文件: add_strategy_to_backtest_record
生成时间: 2025-08-02 23:54:58
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
    migrate(migrator.add_column('backtest_records', 'strategy', peewee.TextField(help_text="策略数据", null=True)))

def down():
    """回滚迁移"""
    db = database.db
    migrator = SqliteMigrator(db)

    # 在这里添加回滚操作
    # 示例: migrate(migrator.drop_column('table_name', 'column_name'))
