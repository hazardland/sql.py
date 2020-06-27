**pgsql-table** is an PostgreSQL ORM which aims to simplify JSON based API implementation process. It allows direct usage of request JSON data securely for inserting updating and selecting. Following example shows how to setup simple Product model module:

**product.py**
```python
import sql
import category

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
```

Let us create our first product. In data we have JSON which came througth the API:
```python
data = {
    'name': 'Plumbus',
    'price': 9.99,
    'category_id': 1
}
```

Function product.add will insert product into products table and also return instance of Product object representing newly created record:
```python
import product
print(product.add(data))
```

This will result following query execution:
```sql
WITH "product" AS (
    INSERT INTO "site"."product" (name, price, category_id)
    VALUES (Plumbus, 9.99, 1) RETURNING product.id, product.name, product.price, product.category_id
)
SELECT product.id, product.name, product.price, product.category_id,category.id, category.name
FROM "product"
LEFT JOIN "site"."category" ON "category"."id"="product"."category_id"
```

**pgsql-table** works with PostgreSQL using **psycopg2** connector module. It gets database connection using user defined Table.get_db function and returns using Table.put_db function. By this two function you can implement connection pool where get_db will accuire free connection from pool and put_db will return it back. Here is quick setup of config.py for **pgsql-table**:

```python
import sys
import os

import psycopg2
from psycopg2 import pool

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import logging as log
log.basicConfig(level=log.DEBUG)

# Ignore this part
if sys.platform.lower() == "win32":
    os.system('color')
class color():
    black = lambda x: '\033[30m' + str(x)+'\033[0;39m'
    red = lambda x: '\033[31m' + str(x)+'\033[0;39m'
    green = lambda x: '\033[32m' + str(x)+'\033[0;39m'
    yellow = lambda x: '\033[33m' + str(x)+'\033[0;39m'
    blue = lambda x: '\033[34m' + str(x)+'\033[0;39m'
    magenta = lambda x: '\033[35m' + str(x)+'\033[0;39m'
    cyan = lambda x: '\033[36m' + str(x)+'\033[0;39m'
    white = lambda x: '\033[37m' + str(x)+'\033[0;39m'

def get_db(key=None):
    if not hasattr(get_db, 'pool'):
        init_db()
    conn = getattr(get_db, 'pool').getconn(key)
    log.info(color.yellow('Using db connection at address %s'), id(conn))
    return conn

def put_db(conn, key=None):
    log.info(color.yellow('Releasing db connection at address %s'), id(conn))
    getattr(get_db, 'pool').putconn(conn, key=key)


def init_db():
    if hasattr(get_db, 'pool'):
        log.info(color.cyan('Db pool already initialized at address %s'), id(getattr(get_db, 'pool')))
        return
    try:
        setattr(get_db, 'pool', psycopg2.pool.ThreadedConnectionPool(1, 20, os.getenv("DB")))
        log.info(color.cyan('Initialized db'))
    except psycopg2.OperationalError as e:
        log.error(e)
        sys.exit(0)

# Attach db functions to orm
import sql
sql.Table.get_db = get_db
sql.Table.put_db = put_db
```

Last 3 lines renders ORM ready to use. **init_db** creates 20 connection pool to PosgreSQL. It uses .env file to get database connection string from environment variable **DB**. .env file contains ```DB="dbname=gs1 user=postgres password=1234 host=127.0.0.1 port=5432"```

```python
product.all(filter={
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
    }
)
```

The following query will be generated and executed:
```sql
SELECT
    product.id, product.name, product.price, product.category_id,
    category.id, category.name
FROM "site"."product"
LEFT JOIN "site"."category" ON "category"."id"="product"."category_id"
WHERE (product."name" ILIKE %plumbus%
    OR category."name" ILIKE %plumbus%)
    AND (product."price">=5.0
    AND product."price"<=1.0
    AND product."category_id"=1)
ORDER BY product."price" DESC
```
