#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peewee 数据库迁移工具

此脚本提供了Peewee数据库迁移功能，包括生成迁移文件和应用迁移。
使用方法:
1. 生成迁移文件: python migrations.py generate <migration_name>
2. 应用迁移: python migrations.py migrate
"""
import os
import sys
import argparse
import datetime
import json
from playhouse.migrate import SqliteMigrator, migrate
from zbot.services.db import database
from zbot.models.backtest import BacktestRecord
from zbot.models.candle import Candle
from zbot.models.log import Log


class MigrationManager:
    """迁移管理器，负责创建和应用数据库迁移"""
    def __init__(self):
        self.db = database.db
        self.migrator = SqliteMigrator(self.db)
        self.migrations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'migrations')
        self.init_migrations_dir()
        self.models = [BacktestRecord, Candle, Log]

    def init_migrations_dir(self):
        """初始化迁移目录"""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            print(f"创建迁移目录: {self.migrations_dir}")

    def generate_migration(self, migration_name):
        """生成新的迁移文件

        Args:
            migration_name: 迁移名称
        """
        # 获取当前时间戳
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        migration_filename = f"{timestamp}_{migration_name}.py"
        migration_path = os.path.join(self.migrations_dir, migration_filename)

        # 生成迁移文件内容
        with open(migration_path, 'w', encoding='utf-8') as f:
            f.write(f"#!/usr/bin/env python3\n")
            f.write(f"# -*- coding: utf-8 -*-")
            f.write(f"\n")
            f.write(f"\"\"\"\n")
            f.write(f"迁移文件: {migration_name}\n")
            f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\"\"\"\n")
            f.write(f"import peewee\n")
            f.write(f"from playhouse.migrate import migrate\n")
            f.write(f"from zbot.services.db import database\n")
            f.write(f"from playhouse.migrate import SqliteMigrator\n\n")
            f.write(f"def up():\n")
            f.write(f"    \"\"\"应用迁移\"\"\"\n")
            f.write(f"    db = database.db\n")
            f.write(f"    migrator = SqliteMigrator(db)\n\n")
            f.write(f"    # 在这里添加迁移操作\n")
            f.write(f"    # 示例: migrate(migrator.add_column('table_name', 'column_name', field))\n\n")
            f.write(f"def down():\n")
            f.write(f"    \"\"\"回滚迁移\"\"\"\n")
            f.write(f"    db = database.db\n")
            f.write(f"    migrator = SqliteMigrator(db)\n\n")
            f.write(f"    # 在这里添加回滚操作\n")
            f.write(f"    # 示例: migrate(migrator.drop_column('table_name', 'column_name'))\n")

        print(f"生成迁移文件成功: {migration_path}")
        print(f"请编辑此文件添加迁移操作，然后运行 'python migrations.py migrate' 应用迁移")

    def apply_migrations(self):
        """应用所有未应用的迁移"""
        # 读取已应用的迁移记录
        applied_migrations_file = os.path.join(self.migrations_dir, 'applied_migrations.json')
        applied_migrations = []

        if os.path.exists(applied_migrations_file):
            with open(applied_migrations_file, 'r', encoding='utf-8') as f:
                applied_migrations = json.load(f)

        # 获取所有迁移文件
        migration_files = sorted([f for f in os.listdir(self.migrations_dir)
                                 if f.endswith('.py') and not f.startswith('__')])

        # 应用未应用的迁移
        for migration_file in migration_files:
            if migration_file not in applied_migrations:
                print(f"应用迁移: {migration_file}")
                migration_module = __import__(
                    f"zbot.services.migrations.{migration_file[:-3]}",
                    fromlist=['up']
                )
                try:
                    database.open_connection()
                    migration_module.up()
                    applied_migrations.append(migration_file)
                    print(f"迁移 {migration_file} 应用成功")
                except Exception as e:
                    print(f"迁移 {migration_file} 应用失败: {str(e)}")
                finally:
                    database.db.close()

        # 保存已应用的迁移记录
        with open(applied_migrations_file, 'w', encoding='utf-8') as f:
            json.dump(applied_migrations, f, ensure_ascii=False, indent=2)

        print("所有迁移已应用完成")

    def create_tables(self):
        """创建所有模型表"""
        try:
            database.open_connection()
            self.db.create_tables(self.models)
            print("所有表创建成功")
        except Exception as e:
            print(f"创建表失败: {str(e)}")
        finally:
            database.db.close()


def main():
    parser = argparse.ArgumentParser(description='Peewee数据库迁移工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 生成迁移文件命令
    generate_parser = subparsers.add_parser('generate', help='生成迁移文件')
    generate_parser.add_argument('name', help='迁移名称')

    # 应用迁移命令
    migrate_parser = subparsers.add_parser('migrate', help='应用迁移')

    # 创建表命令
    create_parser = subparsers.add_parser('create_tables', help='创建所有表')

    args = parser.parse_args()

    migration_manager = MigrationManager()

    if args.command == 'generate':
        migration_manager.generate_migration(args.name)
    elif args.command == 'migrate':
        migration_manager.apply_migrations()
    elif args.command == 'create_tables':
        migration_manager.create_tables()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()