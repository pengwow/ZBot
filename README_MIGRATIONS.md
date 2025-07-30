# Peewee 数据库迁移使用指南

本项目使用Peewee ORM进行数据库操作，为了方便管理数据库结构变更，我们提供了迁移工具。

## 迁移工具介绍

迁移工具位于`zbot/services/migrations.py`，提供以下功能：
1. 生成迁移文件
2. 应用迁移
3. 创建数据表

## 准备工作

确保已安装必要的依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 生成迁移文件

当你修改了数据模型（例如添加字段、修改字段类型等），需要生成迁移文件：

```bash
python zbot/services/migrations.py generate <migration_name>
```

例如，添加一个新字段到`BacktestRecord`表：
```bash
python zbot/services/migrations.py generate add_risk_metric_to_backtest_record
```

这将在`zbot/services/migrations`目录下生成一个带有时间戳的迁移文件，如`20241106123456_add_risk_metric_to_backtest_record.py`。

### 2. 编辑迁移文件

生成迁移文件后，需要编辑它以添加具体的迁移操作。打开生成的迁移文件，在`up()`函数中添加迁移操作，在`down()`函数中添加回滚操作。

例如，添加一个新字段：
```python
from peewee import FloatField

def up():
    db = database.db
    migrator = SqliteMigrator(db)

    # 添加风险指标字段
    risk_metric = FloatField(default=0.0, help_text="风险指标")
    migrate(migrator.add_column('backtestrecord', 'risk_metric', risk_metric))

def down():
    db = database.db
    migrator = SqliteMigrator(db)

    # 删除风险指标字段
    migrate(migrator.drop_column('backtestrecord', 'risk_metric'))
```

### 3. 应用迁移

编辑完迁移文件后，应用迁移：

```bash
python zbot/services/migrations.py migrate
```

这将应用所有未应用的迁移文件，并更新`applied_migrations.json`记录。

### 4. 创建数据表

如果是首次运行项目，需要创建所有数据表：

```bash
python zbot/services/migrations.py create_tables
```

## 迁移文件格式说明

每个迁移文件包含两个主要函数：
- `up()`: 应用迁移的操作
- `down()`: 回滚迁移的操作

迁移文件使用Peewee的`playhouse.migrate`模块提供的功能，支持以下操作：
- 添加列: `migrator.add_column(table_name, column_name, field)`
- 删除列: `migrator.drop_column(table_name, column_name)`
- 修改列: `migrator.alter_column_type(table_name, column_name, new_field)`
- 添加索引: `migrator.add_index(table_name, columns, unique=False)`
- 删除索引: `migrator.drop_index(table_name, index_name)`

## 注意事项

1. 迁移操作会直接修改数据库结构，请确保在应用迁移前备份数据库。
2. 迁移文件一旦应用，应避免修改，如需修改，应创建新的迁移文件。
3. 当你添加新的数据模型时，需要将其添加到`migrations.py`中的`models`列表中，以便`create_tables`命令能够创建该表。

## 示例工作流

1. 修改数据模型（例如在`zbot/models/backtest.py`中添加新字段）
2. 生成迁移文件: `python zbot/services/migrations.py generate add_new_field`
3. 编辑迁移文件，添加具体的迁移操作
4. 应用迁移: `python zbot/services/migrations.py migrate`
5. 验证数据库结构是否更新成功

通过以上步骤，你可以方便地管理数据库结构变更，确保数据模型的变动能够正确同步到数据库表中。