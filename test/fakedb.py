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
