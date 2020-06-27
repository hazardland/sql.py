import sql
import fakedb
import config

sql.Table.get_db = fakedb.get_db
sql.Table.put_db = fakedb.put_db

class Category:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

class CategoryTable(sql.Table):
    type = Category
    schema = 'site'
    name = 'category'
    fields = {
        'id':{
            'type': 'int'
        },
        'name':{
            'type': 'json',
            'keys': [
                'ka',
                'en'
            ]
        }
    }

class Product:
    def __init__(self, id=None, title=None, category_id=None):
        self.id = id
        self.title = title
        self.category_id = category_id
        self.category = None

class ProductTable(sql.Table):
    type = Product
    schema = 'site'
    name = 'product'
    fields = {
        'id':{
            'type': 'int'
        },
        'title':{
            'type': 'json',
            'keys': [
                'ka',
                'en'
            ]
        },
        'category_id': {'type': 'int'}
    }
    joins = {
        'category': {'table':CategoryTable, 'field':'category_id'}
    }

ProductTable.filter()

ProductTable.filter(filter={
                                'title':'xxx',
                                'category':{
                                    'name':'yyy'
                                    }
                            },
search={
                                'title':'xxx',
                                'category':{
                                    'name':'yyy'
                                    }
                            },

                            )
