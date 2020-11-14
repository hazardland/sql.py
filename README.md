<!-- MarkdownTOC autolink=true levels="1" autoanchor="true"-->

- [Installation](#installation)
- [Configuration](#configuration)
- [Prepare](#prepare)
- [Class](#class)
- [Model](#model)
- [Add](#add)
- [Get](#get)
- [Save](#save)
- [All](#all)
- [Delete](#delete)
- [Filter](#filter)

<!-- /MarkdownTOC -->


![](https://raw.githubusercontent.com/hazardland/sql.py/master/images/query.png)


# Installation
```
pip install psycopg2-binary
pip install pgsql-table
```

# Configuration

```python
import sql
```
Set log level to debug to see generated queries

```python
import logging as log
log.basicConfig(level=log.DEBUG)
```

Configure default database connetion:
```python
sql.db = sql.Db('dbname=postgres user=postgres password=1234 host=127.0.0.1 port=5432')
```
(Connetion pool is made when only before first query)
Alternatively every model can have its own database connection:
```python
sql.Table.db = sql.Db('some other database connection string')
```
Set default schema
```python
sql.Table.schema = 'demo'
```
(Models have their own different schemas)

# Prepare
Let us create demo schema:
```python
sql.query('DROP SCHEMA IF EXISTS demo CASCADE')
sql.query('CREATE SCHEMA IF NOT EXISTS demo')
```

We will create users table and groups table, users table will reference to groups table to showcase some joins
```python
sql.query("""
    CREATE TABLE IF NOT EXISTS demo.groups (
        id SMALLSERIAL PRIMARY KEY NOT NULL,
        name VARCHAR(32)
    )""")

sql.query("""
CREATE TABLE IF NOT EXISTS demo.users (
    id BIGSERIAL PRIMARY KEY NOT NULL,
    username VARCHAR(64) NOT NULL,
    fullname VARCHAR(64) NOT NULL,
    password CHAR(32) NOT NULL,
    status VARCHAR(8) NOT NULL,
    group_id SMALLINT REFERENCES demo.groups(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
)""")
```

# Class
Now we need classes to represent users and groups table rows as objects:
```python
class Group:
    def __init__(self):
        self.id = None
        self.name = None

class User:
    def __init__(self):
        self.id = None
        self.username = None
        self.fullname = None
        self.status = None
        self.created_at = None
```

# Model

Let us pause a bit and create friendly md5 hash function that we might need later for hashing passwords:
```python
import hashlib
def md5(plain):
    return hashlib.md5(plain.encode()).hexdigest()
```

Default model is sql.Table, we extend default model for Group. The naming goes like this: Class name in singular (Group) and model name which will produce objects of this class in plural (Groups):
```python
class Groups(sql.Table):
    name = 'groups'
    type = Group
    fields = {
        'id': {'type': 'int'},
        'name': {}
    }
```

And user model also:
```python
class Users(sql.Table):
    name = 'users' # Actual table name
    type = User
    fields = {
        'id': {'type': 'int'},
        'username': {}, # Default is string
        'fullname': {},
        'password': {'encoder': md5}, # md5 function will encode values for this field
        'status': {'options': ['active', 'disabled']}, # Only this values are allowed for this field
        'group_id': {'type':'int'},
        'created_at': {'type': 'date'}
    }
    joins = {
        'group': {'table':Groups, 'field':'group_id'}
    }
```

# Add
Create some groups by simply calling .add and passing dictionary:
```python
manager = Groups.add({'name':'Manager'})
customer = Groups.add({'name':'Customer'})
```
Add method will generate and run following query:
```sql
WITH "groups" AS (
INSERT INTO "demo"."groups" (name)
VALUES ('Manager')
RETURNING groups.id, groups.name )
SELECT groups.id, groups.name
FROM "groups"
```

Create users
```python
user = Users.add({
        'username': 'john',
        'fullname': 'John Doe',
        'password': '123',
        'status': 'active',
        'group_id': manager.id
    })
```
Following query will be generated:
```sql
WITH "users" AS (
INSERT INTO "demo"."users" (username, fullname, password, status, group_id)
VALUES ('john', 'John Doe', '202cb962ac59075b964b07152d234b70', 'active', '1')
RETURNING users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at )
SELECT users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at,groups.id, groups.name
FROM "users"
LEFT JOIN "demo"."groups" ON "groups"."id"="users"."group_id"
```

Let us make pretty print function
```python
import json
def pprint(object):
    print(json.dumps(object, indent=4, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x)))
```

Actually user is an object of class User, but pprint will visualise it like a dictionary:
```python
pprint(user)
```
Outputs:
```python
{
    "id": 1,
    "username": "john",
    "fullname": "John Doe",
    "status": "active",
    "created_at": "2020-11-14 03:34:46.913425",
    "password": "202cb962ac59075b964b07152d234b70",
    "group_id": 1,
    "group": {
        "id": 1,
        "name": "Manager"
    }
}
```
Notice that password we input was 123 and in query it is md5 hash thanks to encoder defined to that field.

Here we add some more users for scientific purposes:
```python
import random
random_string = lambda: ''.join(random.choice('abcdefghijklmnopqrstwxyz') for j in range(random.randrange(3, 9)))

log.getLogger().setLevel(log.INFO)
for i in range(300):
    Users.add({
        'username': random_string(),
        'fullname': random_string().capitalize() + ' ' + random_string().capitalize(),
        'group_id': random.choice((manager.id, customer.id)),
        'password': '123',
        'status': 'active'
        })
log.getLogger().setLevel(log.DEBUG)
```

# Get
```python
user = Users.get(1)
```
Wich will get user by following query and becaus we defined join on groups table join also will be present in query:
```sql
SELECT users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at,groups.id, groups.name
FROM "demo"."users"
LEFT JOIN "demo"."groups" ON "groups"."id"="users"."group_id"
WHERE
    "users"."id"='1'
    AND 1=1
```
Let us look inside User object
```python
pprint(user)
```
Which outputs:
```python
{
    "id": 1,
    "username": "john",
    "fullname": "John Doe",
    "status": "active",
    "created_at": "2020-11-14 03:34:46.913425",
    "password": "202cb962ac59075b964b07152d234b70",
    "group_id": 1,
    "group": {
        "id": 1,
        "name": "Manager"
    }
}
```
If you look closer you see that even user.group is an object, actually it is object of class Group

# Save
Saving happens via id and dict corresponding fields and values, save returns updated object of User:
```python
user = Users.save(1, {'status':'disabled', 'password':'qwerty'})
```
Generated query:
```sql
WITH "users" AS (
UPDATE "demo"."users" SET password='d8578edf8458ce06fbc5bb76a58c5ca4', status='disabled'
WHERE
    "users"."id"='1'
    AND 1=1
RETURNING users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at )
SELECT users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at,groups.id, groups.name
FROM "users"
LEFT JOIN "demo"."groups" ON "groups"."id"="users"."group_id"
```
Everything happens in same query: update, select and also join on groups table

user in case of success now contains actually updated object:
```python
pprint(user)
```

```python
{
    "id": 1,
    "username": "john",
    "fullname": "John Doe",
    "status": "disabled",
    "created_at": "2020-11-14 03:34:46.913425",
    "password": "d8578edf8458ce06fbc5bb76a58c5ca4",
    "group_id": 1,
    "group": {
        "id": 1,
        "name": "Manager"
    }
}
```

# All
```python
users = Users.all(filter={
                            'id': {
                                'from':1,
                                #'to': 300
                            },
                            'status':'active',
                            'group':{
                                'id': manager.id
                                }
                         },
                   search={
                        'username': 'j',
                        'fullname': 'j'
                   },
                   limit=2,
                   order={'field':'username', 'method':'asc'}
                   )
```
Query:
```sql
SELECT users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at,groups.id, groups.name
FROM "demo"."users"
LEFT JOIN "demo"."groups" ON "groups"."id"="users"."group_id"
WHERE
    (users."username" ILIKE '%j%'
    OR users."fullname" ILIKE '%j%')
    AND (users."id">='5'
    AND users."status"='disabled'
    AND groups."id"='2')
ORDER BY users."id" DESC
```
Difference between filter and search is that search consists with only ```OR``` criterias and filter with ```AND```.

```python
pprint(users)
```

```python
[
    {
        "id": 122,
        "username": "ahdcjq",
        "fullname": "Hbf Ngggzmce",
        "status": "active",
        "created_at": "2020-11-14 04:48:00.857954",
        "password": "202cb962ac59075b964b07152d234b70",
        "group_id": 1,
        "group": {
            "id": 1,
            "name": "Manager"
        }
    },
    {
        "id": 51,
        "username": "alabm",
        "fullname": "Ipb Ttjkxc",
        "status": "active",
        "created_at": "2020-11-14 04:48:00.612368",
        "password": "202cb962ac59075b964b07152d234b70",
        "group_id": 1,
        "group": {
            "id": 1,
            "name": "Manager"
        }
    }
]
```

# Delete
```python
Users.delete(3)
```

```sql
DELETE
FROM "demo"."users"
WHERE
    1=1
    AND "users"."id"='3'
```

# Filter
In addition with Table.all, Table.filter has paging and result is object of sql.Result:
```python
result = Users.filter(page=4,
                      limit=3,
                      order={'method':'asc'},
                      filter={'status':'active', 'group':{'id': customer.id}},
                      search={'username':'j', 'fullname':'j'})
```

```sql
SELECT users.id, users.username, users.fullname, users.password, users.status, users.group_id, users.created_at,groups.id, groups.name, COUNT(*) OVER()
FROM "demo"."users"
LEFT JOIN "demo"."groups" ON "groups"."id"="users"."group_id"
WHERE
    (users."username" ILIKE '%j%'
    OR users."fullname" ILIKE '%j%')
    AND (users."status"='active'
    AND groups."id"='2')
ORDER BY users."id" ASC
LIMIT '3' OFFSET '9'
```

Selecting 3 rows starting from 9th row as we have per page limit=3 from 9-12 will be items for 4th page

```python
pprint(result)
```

```python
{
    "total": 80,
    "items": [
        {
            "id": 42,
            "username": "xkeosa",
            "fullname": "Hxkqrfz Wxjhbalf",
            "status": "active",
            "created_at": "2020-11-14 04:50:37.132306",
            "password": "202cb962ac59075b964b07152d234b70",
            "group_id": 2,
            "group": {
                "id": 2,
                "name": "Customer"
            }
        },
        {
            "id": 50,
            "username": "lejfe",
            "fullname": "Npowa Sllgq",
            "status": "active",
            "created_at": "2020-11-14 04:50:37.156698",
            "password": "202cb962ac59075b964b07152d234b70",
            "group_id": 2,
            "group": {
                "id": 2,
                "name": "Customer"
            }
        },
        {
            "id": 52,
            "username": "pofmeyp",
            "fullname": "Xpm Zxfthj",
            "status": "active",
            "created_at": "2020-11-14 04:50:37.161491",
            "password": "202cb962ac59075b964b07152d234b70",
            "group_id": 2,
            "group": {
                "id": 2,
                "name": "Customer"
            }
        }
    ]
}
```

# Custom
But if you want to create some custom query Model class helps a lot with query templating and converting select result into objects of User:
```python
db = None
try:
    db = Users.db.get()
    cursor = db.cursor()
    cursor.execute(*sql.debug(f"""
        SELECT {Users.select()}
        FROM {Users}
        WHERE
        {Users('username')}=%s
        AND {Users('password')}=%s
        """,
        ('John', md5('123'))))
    if cursor.rowcount > 0:
        # Create User object
        user = Users.create(cursor.fetchone())
        pprint(user)
finally:
    Users.db.put(db)
```
