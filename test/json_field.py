import sql

class Test:
    def __init__(self, id=None, title=None):
        self.id = id
        self.title = title

class Table(sql.Table):
    type = Test
    schema = 'site'
    name = 'test_table'
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
        }
    }

print(sql.color.red('SELECT'))
where = Table.where({'id':1, 'title':'xx'})
print(f"""SELECT {Table.select()}
FROM {Table}
WHERE {where.fields()}""" % tuple(where.values()))

print(sql.color.red('INSERT'))
insert = Table.insert({'id':1, 'title':{'ka':'Georgian'}})
print(f"""INSERT INTO {Table} ({insert.fields()})
VALUES ({insert.fields('%s')})""" % tuple(insert.values()))

print(sql.color.red('UPDATE'))
update = Table.update({'title':{'ka':'Georgian', 'en':'English', 'dddd':'dddd'}})
print(f"""UPDATE {Table}
SET {update.fields()}
WHERE {Table('id')}=%s""" % tuple(update.values(1)))
