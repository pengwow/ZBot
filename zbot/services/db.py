from playhouse.migrate import SqliteDatabase

# 项目根目录
import os
import sys


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Database(object):
    def __init__(self):
        from zbot.common.config import read_config
        config = read_config()
        self.trading_mode = config.get('TRADING_MODE')
        db_path = os.path.join(base_path, 'data', f'{
                               self.trading_mode}', "zbot.db")
        self.db: SqliteDatabase = SqliteDatabase(db_path)

    def closed(self):
        if self.db is None:
            return True
        if self.db.is_closed():
            self.db.close()
        return True

    def is_open(self) -> bool:
        if self.db is None:
            return False
        return not self.db.is_closed()

    def open_connection(self) -> None:
        if self.is_open():
            return
        # connect to the database
        self.db.connect()


database = Database()
