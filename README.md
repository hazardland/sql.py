**pgsql-table** is an PostgreSQL ORM which aims to simplify JSON based API implementation process. It allows direct usage of request JSON data securely for inserting updating and selecting.

<!-- MarkdownTOC autolink=true levels="1" autoanchor="true"-->

- [Introduction](#introduction)
- [Setup](#setup)
- [Filter](#filter)
- [All](#all)

<!-- /MarkdownTOC -->



# Introduction
Following example shows how to setup simple Product model module:

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

# Setup
#### Zeroconfig
**pgsql-table** comes with sql.Db class which is used by sql.Table class to get a database connection. To prepare sql.Table you need to attach configured sql.Db object somewhere in your config file:
```python
import sql
sql.Table.db = sql.Db('dbname=postgres user=postgres password=1234 host=127.0.0.1 port=5432')
```
sql.Db class uses psycopg2.pool.ThreadedConnectionPool to create database connection pool which can be used in multi threaded enviornment safely, connection pool size is defined by second parameter sql.Db('...', 20) and by default 20 connections are created. So for example if you run Flask app worker with 4 threads, each thread can get a free connection, use it and then return it back in the pool.

sql.Db class is based on ```psycopg2``` modole but does not comes with dependency in case you will want to write your own sql.Db class or just use ORM to connect to MySQL.

#### Some advanced setup
Thats it, below is some advanced usage practices, like working with multiple different databases.

Before every query Table will get db connection from connection pool using self.db.get() and after using it the connection will be returned back to the pool using self.db.put(connection). Note that by default the connection pool is initialized during the very first call of self.db.get(), but if you want to initialize it somewhere during loading your app do it by calling sql.Table.db.init().

The fact that sql.Table has its own db property for accessing database connection can be used to have different tables with different database connections:
```python
import sql

# Define new class for db1
class TableOnDb1(sql.Table):
    pass
# Define new class for db2
class TableOnDb2(sql.Table):
    pass

# Define connection for db1
TableOnDb1.db = sql.Db('db1 connection string')
# Define connection for db2
TableOnDb2.db = sql.Db('db2 connection string')


# Define tables for db1
class Table1(TableOnDb1)
    pass

class Table2(TableOnDb1)
    pass

# Define tables for db2
class Table3(TableOnDb1)
    pass

class Table4(TableOnDb2)
    pass
```

Note that I once used this ORM for MySQL. All SELECT based methods will work if you set:
```python
sql.ESCAPE = '`'
```
But for the moment RETURN statements does not work in MySQL so UPDATE and INSERT based methods are problem.


# Filter

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
    page=3,
    limit=50
)
```

The following query will be generated and executed:
```sql
SELECT product.id, product.name, product.price, product.category_id,category.id, category.name, COUNT(*) OVER()
FROM "site"."product"
LEFT JOIN "site"."category" ON "category"."id"="product"."category_id"
WHERE (product."name" ILIKE '%plumbus%'
    OR category."name" ILIKE '%plumbus%')
    AND (product."price">=5.0
    AND product."price"<=1.0
    AND product."category_id"=1)
ORDER BY product."price" DESC
LIMIT 50 OFFSET 100
```
Notice difference between ```filter``` and ```search```: While all criterias in ```filter``` must be matched in order to get record, From ```search``` at least one criteria must be matched. In shorts query looks like this: ```(search1 OR search2 OR search3) AND (filter1 AND filter2 AND filter3)```
.

The result off filter will be an object. ```result.total``` containts count of total items matching criterias. ```result.items``` contains list of item objects which represent ```Product``` class.

The result is also paged by ```limit``` parameter and is fetched for ```page```. ```page=3, limit=50``` results ```LIMIT 50 OFFSET 100 in query```.

# All
product.all() acts like product.filter() but result is simple list and result is not paged.

# Get

# Add

# Save
