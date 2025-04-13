from playhouse.sqlite_ext import SqliteExtDatabase


class Database(object):
    def __init__(self):
        self.db: SqliteExtDatabase = SqliteExtDatabase('zbot.db')



database = Database()