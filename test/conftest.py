import os
import pytest
import sql


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class Group:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class User:
    def __init__(self, id=None, username=None, fullname=None, status=None, group_id=None):
        self.id = id
        self.username = username
        self.fullname = fullname
        self.status = status
        self.group_id = group_id


class Category:
    def __init__(self, id=None, name=None, tags=None):
        self.id = id
        self.name = name
        self.tags = tags


class Product:
    def __init__(self, id=None, title=None, price=None, category_id=None):
        self.id = id
        self.title = title
        self.price = price
        self.category_id = category_id


class Item:
    def __init__(self, id=None, title=None, active=None, created_at=None):
        self.id = id
        self.title = title
        self.active = active
        self.created_at = created_at


class Thing:
    def __init__(self, id=None, alias_name=None):
        self.id = id
        self.alias_name = alias_name


class UniqueItem:
    def __init__(self, id=None, code=None):
        self.id = id
        self.code = code


class EncodedItem:
    def __init__(self, id=None, title=None, secret=None):
        self.id = id
        self.title = title
        self.secret = secret


# ---------------------------------------------------------------------------
# Table definitions  (all in the 'test' schema)
# ---------------------------------------------------------------------------

class GroupTable(sql.Table):
    schema = 'test'
    name = 'groups'
    type = Group
    fields = {
        'id':   {'type': 'int', 'insert': False, 'update': False},
        'name': {},
    }


class UserTable(sql.Table):
    schema = 'test'
    name = 'users'
    type = User
    fields = {
        'id':       {'type': 'int', 'insert': False, 'update': False},
        'username': {},
        'fullname': {},
        'status':   {'options': ['active', 'inactive']},
        'group_id': {'type': 'int'},
    }
    joins = {
        'group': {'table': GroupTable, 'field': 'group_id'},
    }


class CategoryTable(sql.Table):
    schema = 'test'
    name = 'categories'
    type = Category
    fields = {
        'id':   {'type': 'int', 'insert': False, 'update': False},
        'name': {'type': 'json', 'keys': ['en', 'ka']},
        'tags': {'array': True},
    }


class ProductTable(sql.Table):
    schema = 'test'
    name = 'products'
    type = Product
    fields = {
        'id':          {'type': 'int', 'insert': False, 'update': False},
        'title':       {},
        'price':       {'type': 'float'},
        'category_id': {'type': 'int'},
    }
    joins = {
        'category': {'table': CategoryTable, 'field': 'category_id'},
    }


class ItemTable(sql.Table):
    schema = 'test'
    name = 'items'
    type = Item
    fields = {
        'id':         {'type': 'int', 'insert': False, 'update': False},
        'title':      {},
        'active':     {'type': 'bool'},
        'created_at': {'type': 'date'},
    }


class ThingTable(sql.Table):
    schema = 'test'
    name = 'things'
    type = Thing
    fields = {
        'id':         {'type': 'int', 'insert': False, 'update': False},
        'alias_name': {'field': 'internal_col'},   # Python name → different DB column
        'hidden':     {'select': False},            # stored but never SELECTed
    }


class UniqueItemTable(sql.Table):
    schema = 'test'
    name = 'unique_test'
    type = UniqueItem
    fields = {
        'id':   {'type': 'int', 'insert': False, 'update': False},
        'code': {},
    }


class EncodedItemTable(sql.Table):
    schema = 'test'
    name = 'encoded_items'
    type = EncodedItem
    fields = {
        'id':    {'type': 'int', 'insert': False, 'update': False},
        'title': {},
        'secret': {
            'encoder': lambda x: x.upper(),
            'decoder': lambda x: x.lower() if x else x,
        },
    }


# ---------------------------------------------------------------------------
# Tables to truncate between tests
# ---------------------------------------------------------------------------

_TABLES = [
    'test.groups',
    'test.users',
    'test.categories',
    'test.products',
    'test.items',
    'test.things',
    'test.unique_test',
    'test.encoded_items',
]


# ---------------------------------------------------------------------------
# Session fixture: create schema + tables once, drop on teardown
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def db():
    dsn = os.environ['TEST_DSN']
    database = sql.Db(dsn, size=20)
    sql.db = database   # used by sql.query()

    conn = database.get()
    cur = conn.cursor()

    cur.execute('CREATE SCHEMA IF NOT EXISTS test')

    cur.execute('''
        CREATE TABLE test.groups (
            id   SERIAL PRIMARY KEY,
            name VARCHAR
        )
    ''')

    cur.execute('''
        CREATE TABLE test.users (
            id       BIGSERIAL PRIMARY KEY,
            username VARCHAR,
            fullname VARCHAR,
            status   VARCHAR,
            group_id INT REFERENCES test.groups(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE test.categories (
            id   SERIAL PRIMARY KEY,
            name JSONB,
            tags TEXT[]
        )
    ''')

    cur.execute('''
        CREATE TABLE test.products (
            id          SERIAL PRIMARY KEY,
            title       VARCHAR,
            price       FLOAT,
            category_id INT REFERENCES test.categories(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE test.items (
            id         SERIAL PRIMARY KEY,
            title      VARCHAR,
            active     BOOLEAN,
            created_at TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE test.things (
            id           SERIAL PRIMARY KEY,
            internal_col VARCHAR,
            hidden       VARCHAR
        )
    ''')

    cur.execute('''
        CREATE TABLE test.unique_test (
            id   SERIAL PRIMARY KEY,
            code VARCHAR
        )
    ''')
    # named exactly so the ORM regex  <tablename>_unique_<field>_index  matches
    cur.execute(
        'CREATE UNIQUE INDEX unique_test_unique_code_index '
        'ON test.unique_test(code)'
    )

    cur.execute('''
        CREATE TABLE test.encoded_items (
            id     SERIAL PRIMARY KEY,
            title  VARCHAR,
            secret VARCHAR
        )
    ''')

    conn.commit()
    database.put(conn)

    yield database

    # teardown: drop everything
    conn = database.get()
    cur = conn.cursor()
    cur.execute('DROP SCHEMA test CASCADE')
    conn.commit()
    database.put(conn)


# ---------------------------------------------------------------------------
# Function fixture: truncate all tables before each integration test
# The rollback() ensures a clean transaction even if the previous test left
# the connection in an error state.
# ---------------------------------------------------------------------------

@pytest.fixture
def truncate(db):
    conn = db.get()
    conn.rollback()                         # reset any failed-transaction state
    cur = conn.cursor()
    cur.execute(
        'TRUNCATE ' + ', '.join(_TABLES) + ' RESTART IDENTITY CASCADE'
    )
    conn.commit()
    db.put(conn)
