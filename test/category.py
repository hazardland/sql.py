import sql

class Category:
    def __init__(self):
        pass

class Table(sql.Table):
    type = Category
    schema = 'site'
    name = 'category'
    fields = {
        'id': {'type':'int'},
        'name': {}
    }
