import os
import sys
import sql

if sys.platform.lower() == "win32":
    os.system('color')

import logging as log
log.basicConfig(level=log.DEBUG)

class Cursor:
    def __init__(self):
        self.rowcount = None
    def execute(self, query, params):
        pass
    def fetchone(self):
        pass

class Db:
    def __init__(self):
        pass
    def cursor(self):
        return Cursor()
    def commit(self):
        pass

def get_db():
    return Db()

def put_db(db):
    pass


sql.Table.get_db = get_db
sql.Table.put_db = put_db
