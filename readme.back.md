<!-- MarkdownTOC levels="1,2,3" autolink="true" -->

- [Installing](#installing)
- [Introduction](#introduction)
    - [Define class](#define-class)
    - [Define table](#define-table)
    - [Create table](#create-table)
- [Usage](#usage)
    - [Insert](#insert)
        - [Using](#using)
        - [Invalid value handling](#invalid-value-handling)
    - [Select](#select)
        - [Getting by id](#getting-by-id)
        - [Getting by filter criterias](#getting-by-filter-criterias)
        - [Filtering options](#filtering-options)

<!-- /MarkdownTOC -->

# Installing
```
pip install pgsql-table
```
Importing
```python
import sql

class Foo:
    def __init__(id=None, name=None):
        self.id = id
        self.name = name

class Table(sql.Table)
    type = Foo
    fields = {
        "name": {}
    }
```

# Introduction

Imagine you have to store in database user profile object. You get following JSON as input from API endpoint:
```python
{
    "nickname": "XXX_()_XXX",
    "gender": "female", #Allowed value one from "male", "female", "other"
    "interested_in": ["friendship", "dating"], #Allowed values many from "friendship", "dating", "relationship"
    "height": 170, #Allowed values min 100 max 200 integer
    "birthday": "2001-07-17", #Only valid dates
    "weight": 69.9, #Allowed floats,
    "has_cats": False
}
```

## Define class
First of all let us describe our profile object. Every time we select data from user profile we want to return objects of this class:
```python
class Profile:
    def __init__(
            self,
            id=None,
            nickname=None,
            gender=None,
            interested_in=None,
            birthday=None,
            height=None,
            weight=None,
            has_cats=None
        ):
        self.id = id, #Just avoiding "id" as it is builtin function
        self.nickname = nickname
        self.gender = gender
        self.interested_in = interested_in
        self.birthday = birthday
        self.height = height
        self.weight = weight
        self.has_cats = has_cats
```

## Define table
Now let us describe the table in JSON:
```python
import sql

class Table(sql.Table):
    schema = 'test'
    name = 'user_profile' #Actual table name
    type = Profile #The class we described above
    fields = {
        "id":{
            "field": "id", #Object property is "id" but in table column is "id"
            "type": "int",
            "insert": False,
            "update": False
        },
        "nickname": {
        },
        "gender": {
            "options":{
                "male",
                "female",
                "other"
            }
        },
        "interested_in": {
            "options": {
                "dating",
                "friendship",
                "relationship"
            },
            "array": True #This allows to accept multiple values for this field
        },
        "height": {
            "type": "int", #Default was string, only int between range accepted
            "min": 100,
            "max": 200
        },
        "birthday": {
            "type": "date" #Only valid date is accepted
        },
        "weight": {
            "type": "float" #Only castable to float accepted
        },
        "has_cats": {
            "type": "bool"
        }
    }
```

## Create table
That is not all. Now we need to create actual table:
```sql
SET search_path TO test;

-- THIS IS LIST OF AVAILABE VALUES FOR THE gender FIELD
CREATE TYPE USER_PROFILE_GENDER AS ENUM
(
    'female',
    'other',
    'male'
);

-- AND THIS IS FOR interedted_in FIELD
CREATE TYPE USER_PROFILE_INTERESTED_IN AS ENUM
(
    'dating',
    'relationship',
    'friendship'
);

CREATE TABLE user_profile
(
    /**
        IN REAL WORLD I WOULD HAVE ONLY FOLLOWING FIELD IN user_profile:
            user_id BIGINT NOT NULL REFERENCES users(id) PRIMARY KEY,
        BUT LET US PRETEND IT IS NOT user_profile TABLE AND HAS ITS OWN id
    **/
    id BIGSERIAL PRIMARY KEY,
    nickname TEXT,
    gender USER_PROFILE_GENDER, -- ONLY AVAILABLE VALUE
    interested_in USER_PROFILE_INTERESTED_IN[], -- SPOT THE [] THIS MEANS MULTIPLE AVAILABE VALUES
    height INT,
    birthday TIMESTAMP WITHOUT TIME ZONE,
    weight TEXT,
    has_cats BOOL
);
```

# Usage
## Insert
And finally we can advance to usage, let us create a function which creates a user profile:
```python
from sql import Error #I am not sure about this yet
#get_db and put_db are just hipotethical functions releasing free db connection from connection pool
from config import get_db, put_db

def create(data):
    try:
        insert = Table.insert(data)
    except Exception as error:
        raise error

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO "+Table+" ("+insert.fields()+") " #List all insert fields
                       "VALUES("+insert.fields('%s')+") " #Instead of insert fields generate '%s' for fields
                       "RETURNING "+Table.select(), #Table.select() lists all fields having select=True (default)
                       insert.values())
        profile = Table.create(cursor.fetchone()) #Create Profile object with what we have inserted
    except Exception as error:
        raise Error('general_error')
    finally:
        db.commit()
        put_db(db)

    return profile
```

```insert.fields()``` generates ```nickname, gender, interested_in, height, birthday, weight, has_cats``` string

```insert.fields('%')``` generates ```%s, %s, %s, %s, %s, %s, %s``` (One %s for each insert field)

```Table.select()``` generates ```user_profile.nickname, user_profile.gender, user_profile.interested_in, user_profile.height, user_profile.birthday, user_profile.weight, user_profile.has_cats``` string

```Table.create(cursor.fetchone())``` creates object of class Profile and fills in values from table row. As you will see in the usage example insert is returning actual Profile object and all this is done with a single query! (Without writing a single field name)

### Using
We should call this function now, pretend the data came from API call:
```python
profile = create({
    "nickname": "XXX_()_XXX",
    #"gender": "female", #We skipped gender
    "interested_in": ["friendship", "dating"],
    "birthday": "2001-07-17",
    "height": 169.99,
    "weight": 69.99,
    "has_cats": False,
    "something": "that_we_dont_have"
    })
print(profile.__dict__)
```
This will print ```{'id': 20, 'nickname': 'XXX_()_XXX', 'gender': None, 'interested_in': ['friendship', 'dating'], 'birthday': datetime.datetime(2001, 7, 17, 0, 0), 'height': 169, 'weight': '69.99', 'has_cats': False}```

### Invalid value handling
Allowed value checks:
```python
try:
    profile = create({
        "gender": "zebra"
        })
except Error as error:
    print(error.code, error.message)
```
Prints ```invalid_value Invalid value zebra for field gender```
```python
try:
    profile = create({
        "interested_in": ["being_sober"]
        })
except Error as error:
    print(error.code, error.message)
```
Prints ```invalid_value Invalid value being_sober for field gender```

## Select
### Getting by id

```python
def get(id):
    if not id:
        raise Error('missing_input')

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT "+Table.select()+" FROM "+Table+" WHERE "+Table('id')+"=%s", (id,))
        profile = Table.create(cursor.fetchone())
    except Exception as error:
        raise Error('general_error')
    finally:
        db.commit()
        put_db(db)

    return profile
```
The module used for executing queries is ```psycopg2``` which is well known library for working with PostgreSQL in Python. We use parametrized query with a single parameter. One thing I want to note is **never forget comma in ```(id,)``` after single parameter or you will kill database!**

A little usage of ```get``` function:
```python
try:
    profile = get(20)
    print(profile.interested_in)
    #prints ['friendship', 'dating']
except Exception as error:
    # In case nothing found
    print(error)
```

### Getting by filter criterias
JSON definition allows to filter table data with any field within allowed values:
```python
def get_all(criterias={}, order={}):

    where = Table.where(criterias)
    print(where.fields())
    print(where.values())

    total = None
    result = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT "+Table.select()+", COUNT(*) OVER() "
                       "FROM "+Table+" "
                       "WHERE " + where.fields() + ' ' + # AND something=something
                       "ORDER BY " + Table.order('id', 'desc', order), #New order, default order field, default order method
                       where.values())

        while True:
            try:
                data = cursor.fetchone()
                if total is None:
                    total = data[Table.offset()]
                profile = Table.create(data)
                result.append(profile)
            except TypeError:
                return result
    except Exception as error:
        raise Error('general_error')
    finally:
        db.commit()
        put_db(db)

    #return total, result
    return result
```

This is the usage of get_all with filter criterias
```python
# This section is for only JSON dumping our result
import json
import datetime
def json_dump(value):
    if isinstance(value, datetime.date):
        return str(value)
    elif hasattr(value, 'json') and callable(value.json):
        return value.json()
    return value.__dict__

#This is usage of get_all method
result = get_all({
        "weight":{
            "from": 45,
            "to": 71
        },
        "birthday":{
            "to": "2002-01-01"
        },
        "gender": "female",
        "interested_in": ["friendship", "dating"]
    })

#This is dumping in JSON
print(json.dumps(result, default=json_dump))

#It will print
#[{"id": [48], "nickname": "XXX_()_XXX", "gender": null, "interested_in": ["friendship", "dating"], "birthday": "2001-07-17 00:00:00", "height": 169, "weight": "69.99", "has_cats": false}, {"id": [50], "nickname": "XXX_()_XXX", "gender": null, "interested_in": ["friendship", "dating"], "birthday": "2001-07-17 00:00:00", "height": 169, "weight": "69.99", "has_cats": false}]
```

What does where.fields() do:
```python
where = Table.where(data)
print(where.fields()
```

If data is empty it will output ```1=1```. This is useful for not breaking query in case if generated where clause is followed by your custom ```AND my_custom=criteria```

If data is not empty, in case of our previous example it will output:
```
user_profile."gender"=%s AND %s = ANY(user_profile."interested_in") AND %s = ANY(user_profile."interested_in") AND user_profile."birthday"<=%s AND user_profile."weight">=%s AND user_profile."weight"<=%s
```

For the same filter criteria data ```where.values()``` will output:
```
['female', 'friendship', 'dating', '2002-01-01 00:00:00', '45.0', '71.0']
```
As a result every ```%s``` in generated where clause has its own value.

### Filtering options
```int```, ```float``` and ```date``` require ```"field_name":{"from":from_value, "to":to_value}```, or at least ```from``` or ```to```

Fields with single option value require that value matched one of defined options: "field_name": "allowed_option_value"

Fields with option arrays require that value was array and array items where allowed option values: ```"field_name":["allowed_value1", "allowed_value2"]```, even single value requires array to be passed

In case of optionless strings LIKE 'my_value%' expression is used and if we have "field_name":"abc", every value is selected which starts with 'abc'

Every value is casted in field type before using, cast errors also protect while processing unknown input.

### Ordering
For order we dedicated second parameter in our ```get_all``` function:
```python
result = get_all(order={'birthday','desc'})
```
In case you do not pass order we have default order criteria specified in our select query as
```python
Table.order('id', 'desc', order)
```
Where id is our field name. One of those keys defined in ```Table.fields``` (Not actual table field name, in case of id, id is table column name and id is property name of Profile object)

## Update
### Creating update function
Function will update only provided available fields with update permission and will return updated row on success. It will also execute only single query.
```python
def save(id, data):
    try:
        print(data)
        update = Table.update(data)
    except Exception as error:
        raise error

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE "+Table+" "
                       "SET "+update.fields()+" "
                       "WHERE "+Table('id')+"=%s "
                       "RETURNING "+Table.select(),
                       update.values(id))
        profile = Table.create(cursor.fetchone())
    except Exception as error:
        raise Error('general_error')
    finally:
        db.commit()
        put_db(db)

    return profile
```

### Using update
Take a note that only two fields are specified for update:
```python
try:
    profile = save(20, {"gender":"female", "weight":45})
    print(profile.__dict__)
    #{'id': (20,), 'nickname': 'XXX_()_XXX', 'gender': 'female', 'interested_in': ['friendship', 'dating'], 'birthday': datetime.datetime(2001, 7, 17, 0, 0), 'height': 169, 'weight': '45.0', 'has_cats': False}
except Exception as error:
    # In case nothing updated
    print(error)
```




```python
import sql
import logging as log
from hashlib

log.basicConfig(level=log.DEBUG)

sql.Table.db = sql.Db('dbname=youtube user=postgres password=1234 host=127.0.0.1 port=5432')

class User:
    def __init__(self):
        self.id = None
        self.login = None
        self.status = None
        self.created_at = None

def md5(plain):
    return hashlib.md5(plain.encode()).hexdigest()

class Table(sql.Table):
    name = 'users'
    type = User
    fields = {
        'id': {'type': 'int'},
        'login': {},
        'password': {
            'encoder': lambda plain:
        },
        'status': {
            'options': ['active', 'disabled']
        },
        'created_at': {'type': 'date'}
    }

user = Table.add({
        'login': 'Merab',
        'password': '123',
        'status': 'active'
    })
print(user.__dict__)

user = Table.get(14)
print(user.__dict__)

user = Table.save(14, {'status':'disabled', 'password':'qwerty'})
print(user.__dict__)

users = Table.all(filter={'login':'mer', 'status':'disabled'})
for user in users:
    print(user.__dict__)

Table.delete(5)

result = Table.filter(page=2, limit=3, order={'method':'asc'})
for user in result.items:
    print(user.__dict__)

db = None
try:
    db = Table.db.get()
    cursor = db.cursor()
    cursor.execute(f"""
        SELECT {Table.select()}
        FROM {Table}
        WHERE
        {Table('username')}=%s
        AND {Table('password')}""",
        ('merab', md5('123')))
    user = Table.create(cursor.fetchone())
    prin(user.__dict__)
finally:
    Table.db.put(db)

```
