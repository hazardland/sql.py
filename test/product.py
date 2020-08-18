import sql
import category
import config

class Product:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.price = None
        self.category_id = None
        self.category = None

class Table(sql.Table):
    type = Product
    schema = 'site'
    name = 'product'
    fields = {
        'id': {'type':'int', 'insert':False, 'update':False},
        'name': {},
        'price': {'type':'float'},
        'category_id': {'type':'int'}
    }
    joins = {
        'category': {'table':category.Table, 'field':'category_id'}
    }

def add(data):
    return Table.add(data)

def save(id, data):
    return Table.save(id, data)

def get(id):
    return Table.get(id)

def all(filter={}, order={}, search={}):
    return Table.all(filter=filter,
                     order=order,
                     search=search)

def filter(page=1, limit=100, filter={}, order={}, search={}):
    return Table.filter(page=page,
                        limit=limit,
                        filter=filter,
                        order=order,
                        search=search)

print(filter(filter={
        'price':{
            'from': 5,
            'to': 1
        },
        'category_id': 1
    },
    search={
        'name': 'plumbus',
        'category':{
            'name': 'plumbus'
        }
    },
    order={
        'field': 'price',
        'method': 'desc'
    },
    page=2,
    limit=50
).__dict__)
