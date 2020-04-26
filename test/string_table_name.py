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
        'user_id':{
            'field': 'id'
        }
    }

print(Table)
print(Table+' Only Right')
print('Only Left '+Table)
print('Both Left '+Table+' Both Right')
a = 'ss '
a += Table
print(a)
print("SELECT * FROM "+Table+" WHERE "+Table("user_id")+"=%s")

print(Table('user_id'))

a = f"""SELECT {Table.select()}
        FROM {Table}
        WHERE {Table('user_id')}='%s'"""
print(a)
