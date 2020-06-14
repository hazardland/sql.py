import inspect
import json
import logging as log
from functools import wraps
from dateutil.parser import parse as parse_date

class color():
    black = lambda x: '\033[30m' + str(x)+'\033[0;39m'
    red = lambda x: '\033[31m' + str(x)+'\033[0;39m'
    green = lambda x: '\033[32m' + str(x)+'\033[0;39m'
    yellow = lambda x: '\033[33m' + str(x)+'\033[0;39m'
    blue = lambda x: '\033[34m' + str(x)+'\033[0;39m'
    magenta = lambda x: '\033[35m' + str(x)+'\033[0;39m'
    cyan = lambda x: '\033[36m' + str(x)+'\033[0;39m'
    white = lambda x: '\033[37m' + str(x)+'\033[0;39m'

class Error(Exception):
    def __init__(self, code, message=None, field=None):
        super().__init__(code)
        self.code = code
        if message is not None and not isinstance(message, str):
            self.message = " ".join(map(str, message))
        else:
            self.message = message
        self.field = field

        log.exception('%s %s %s',
                      color.red(self.code+':'),
                      color.yellow(self.message),
                      color.green('['+self.field+']') if not self.field is None else '')

class MissingConfig(Error):
    def __init__(self):
        super().__init__('missing_config')

class MissingInput(Error):
    def __init__(self):
        super().__init__('missing_input')

class MissingField(Error):
    def __init__(self):
        super().__init__('missing_field')

class UnknownField(Error):
    def __init__(self, field=None):
        super().__init__('unknown_field', field=field)

class InvalidValue(Error):
    def __init__(self, message=None, field=None):
        super().__init__('invalid_value', message=message, field=field)

class InvalidDate(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__('Invalid date', message=message, field=field)

class InvalidInt(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__('Invalid int', message=message, field=field)

class InvalidFloat(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__('Invalid float', message=message, field=field)

class Clause:
    def __init__(self, fields, values, pattern='{name}', separator=', ', empty=''):
        self.__fields = fields
        self.__values = values
        self.__pattern = pattern
        self.__separator = separator
        self.__empty = empty
    def fields(self, pattern=None):
        if pattern is None and self.__pattern is not None:
            pattern = self.__pattern
        if self.__fields:
            return self.__separator.join(pattern.format(name=name) for name in self.__fields)
        return self.__empty
    def values(self, id=None):
        if id is not None:
            return self.__values+list((id,))
        return self.__values
    def exctract(self):
        return self.__fields, self.__values

'''
FIELD OPTIONS
    fields = {
        'name':{ # name is field and property name by default
            # OPTIONAL PARAMS (optional params can be not specified)
            'type': 'string'|'int'|'float'|'bool'|'date'|'json' # default is 'string'
                                   # field values ar casted in type
            'array': True # must be provided array of types
            'options': ['option1','option2']: option items must be instances of 'type'
            'field': 'table_field_name' # default is 'name'
            'select': True # default is True
            'insert': True # default is True
            'update': True # default is True
            'encoder': encoder_function # encoder function whith 1 param
                                        # output of encoder function is used directly
                                        # for value
            'decoder': decoder_function # decoder function is used to decode custom before saving
            'keys': ['en', 'ka'] is used when type==json
        }
    }
'''

class MetaTable(type):
    def __repr__(cls):
        return "<Table '"+str(cls)+"'>"
    def __str__(cls):
        return cls.str()
    # def __iadd__(cls, other):
    #     print("In __iadd_ with", other)
    #     return str(other)+str(cls)
    def __radd__(cls, other):
        #print("In __radd_ with", other)
        return str(other)+str(cls)
    def __add__(cls, other):
        #print("In __add_ with", other)
        return str(cls)+str(other)
    def __call__(cls, field):
        if field not in cls.fields:
            raise UnknownField(field)
        return '"'+cls.name+'"."'+(field if not 'field' in cls.fields[field] else cls.fields[field]['field'])+'"'

class Table(metaclass=MetaTable):
    type = lambda x: None
    schema = None
    name = None
    id = 'id'
    fields = dict()
    joins = dict()
    get_db = lambda: None
    put_db = lambda db: None
    @classmethod
    def str(cls):
        result = ''
        if cls.schema:
            result += '"'+cls.schema+'".'
        return result + '"'+cls.name+'"'
    """
        Returns an array for updating table
        update['fields'] = 'field1=%s, field2=%s'
        update['values'] = ['value1', 'value2', 'id']
    """
    @classmethod
    def update(cls, data):
        fields, values = cls.parse(data, 'update')

        if len(values) == 0:
            raise MissingInput()

        return Clause(fields, values, '{name}=%s')

    @classmethod
    def insert(cls, data):

        fields, values = cls.parse(data, 'insert')

        if len(values) == 0:
            raise MissingInput()

        return Clause(fields, values)

    @classmethod
    def where(cls, data, separator='AND'):
        if data is None:
            raise MissingInput()

        values = []
        fields = []
        for field, config in cls.fields.items():

            if field in data:

                value = data[field]
                column = config['field'] if 'field' in config else field
                repeat = None

                if not 'type' in config:
                    config['type'] = 'string'

                if 'array' in config and config['array']:
                    criteria = '%s = ANY('+cls.name+'."'+column+'")'
                elif config['type'] == 'json':
                    #repeat = '"% '+value+'%"'
                    #value = '%: "%'+value+'%"%'
                    value = '%'+value+'%'
                    #criteria = "("+cls.name+'."'+column+"\"::text LIKE %s OR "+cls.name+'."'+column+"\"::text LIKE %s)"
                    criteria = cls.name+'."'+column+"\"::text ILIKE %s"
                elif 'options' in config or config['type'] == 'bool':
                    criteria = cls.name+'."'+column+'"=%s'
                elif config['type'] == 'int' or config['type'] == 'date' or config['type'] == 'float':
                    criteria = cls.name+'."'+column+'"=%s'
                else:
                    #repeat = '% '+value+'%'
                    value = '%'+value+'%'
                    #criteria = "("+cls.name+'."'+column+"\" LIKE %s OR "+cls.name+'."'+column+"\" LIKE %s)"
                    criteria = cls.name+'."'+column+"\" ILIKE %s"


                if 'array' in config and config['array']:
                    if not isinstance(value, list) and not isinstance(value, tuple):
                        raise InvalidValue('Value of '+field+' must be instance of list '+str(type(value))+' given', field)
                    for parse in value:
                        values.append(cls.value(field, parse))
                        fields.append(criteria)
                else:
                    if (config['type'] == 'int' or
                        config['type'] == 'date' or
                        config['type'] == 'float') and \
                        (isinstance(value, list) or
                         isinstance(value, tuple) or
                         isinstance(value, dict)) and \
                        ('from' in value or
                         'to' in value or
                         'in' in value):
                        if 'from' in value:
                            values.append(cls.value(field, value['from']))
                            fields.append(cls.name+'."'+column+"\">=%s")
                        if 'to' in value:
                            values.append(cls.value(field, value['to']))
                            fields.append(cls.name+'."'+column+"\"<=%s")
                        if 'in' in value and (isinstance(value['in'], list) or isinstance(value['in'], tuple)) and len(value['in']):
                            for item in value['in']:
                                log.info(color.cyan('%s'), item)
                                values.append(cls.value(field, item))
                            fields.append(cls.name+'."'+column+"\" IN ("+','.join(['%s'] * len(value['in']))+")")

                    else:
                        if config['type'] != 'json':
                            values.append(cls.value(field, value))
                            if repeat:
                                values.append(cls.value(field, repeat))
                        else:
                            values.append(str(value))
                            if repeat:
                                values.append(str(repeat))
                        fields.append(criteria)

        return Clause(fields, values, separator=' '+separator+' ', empty='1=1')

    @classmethod
    def order(cls, field, method=None, data=None):
        if data:
            if not 'field' in data:
                return ''

            split = data['field'].split('.', 1)
            if len(split) == 2:
                data['key'] = split[1]
                data['field'] = split[0]
            elif len(split) > 2:
                return ''

            if data['field'] in cls.fields:
                field = data['field']
            else:
                return ''
        elif field:
            if field not in cls.fields:
                raise UnknownField()
        else:
            raise MissingField()

        config = cls.fields[field]
        if 'type' not in config:
            config['type'] = 'string'

        column = cls.name+'."'+(config['field'] if 'field' in config else field)+'"'

        if config['type'] == 'json':
            if 'key' not in data:
                raise MissingField()
            if 'keys' not in config:
                raise MissingConfig()
            if data['key'] not in config['keys']:
                raise UnknownField()
            column += "->'"+data['key']+"'"

        if data and 'method' in data:
            method = data['method'].upper()
            if method not in ['ASC', 'DESC']:
                method = 'ASC'
        else:
            method = 'ASC'

        return column+' '+method

    @classmethod
    def parse(cls, data, mode):
        if data is None:
            raise MissingInput()

        log.info(color.cyan('In a parse %s'), cls.fields)

        values = []
        fields = []
        for field, config in cls.fields.items():
            log.info(color.cyan('Parsing field %s'), field)
            if mode in config and not config[mode]:
                continue

            if field in data:

                value = data[field]

                if 'array' in config and config['array']:
                    if value is not None:
                        if not isinstance(value, list) and not isinstance(value, tuple):
                            raise InvalidValue('Value of '+field+' must be instance of list '+str(type(value))+' given', field)
                        value = '{'+(','.join([cls.value(field, parse) for parse in value]))+'}'
                else:
                    value = cls.value(field, value)

                values.append(value)

                if 'field' in config:
                    name = config['field']
                else:
                    name = field
                fields.append(name)

        return (fields, values)

    @classmethod
    def value(cls, field, value):
        if value is None:
            return None

        config = cls.fields[field]

        # type casting
        if value is None and 'null' in config and config['null']:
            return None
        elif 'type' not in config or config['type'] == 'string':
            value = str(value)
        elif config['type'] == 'int':
            value = int(value)
        elif config['type'] == 'bool':
            value = bool(value)
        elif config['type'] == 'json':
            value = json.dumps(value)
        elif config['type'] == 'date':
            try:
                value = parse_date(value)
            except Exception:
                raise InvalidDate('Invalid date '+value+' for field'+field, field)
        elif config['type'] == 'float':
            try:
                value = float(value)
            except Exception:
                raise InvalidFloat('Invalid float '+value+' for field'+field, field)

        # checking for options
        if 'options' in config:
            if value not in config['options']:
                raise InvalidValue('Invalid value '+value+' for field '+field, field)

        # encoding
        if 'encoder' in config:
            value = config['encoder'](value)

        return str(value)
    """
        Returns list of field names for selecting
        field1, field2, field3
    """
    @classmethod
    def select(cls):
        fields = []
        for field, config in cls.fields.items():
            if 'select' in config and not config['select']:
                continue
            if 'field' in config:
                fields.append(config['field'])
            else:
                fields.append(field)

        return (', '.join(cls.name+'.'+value for value in fields))

    @classmethod
    def offset(cls):
        count = 0
        for field, config in cls.fields.items():
            if 'select' in config and not config['select']:
                continue
            count += 1
        return count


    """
        Returns query result raw array converted into a object of cls.type
    """
    @classmethod
    def create(cls, data, offset=0):
        params = {}
        position = 0
        for field, config in cls.fields.items():
            if 'select' in config and not config['select']:
                continue
            if 'array' in config and config['array'] and data[position] is not None:
                if isinstance(data[position], list):
                    params[field] = data[position]
                elif data[position] == '{}':
                    params[field] = []
                else:
                    params[field] = data[position][1:-1].split(',')
            else:
                if 'decoder' in config:
                    params[field] = config['decoder'](data[position])
                else:
                    params[field] = data[position]
            position += 1
        #print(params)
        # if cls.name=='user_media':print(color.magenta(cls.type.__name__))
        # if cls.name=='user_media':print(color.magenta(params))

        init_args = {}
        for argument in inspect.getargspec(cls.type).args:
            if argument != 'self':
                if argument in params:
                    init_args[argument] = params[argument]
        result = cls.type(**init_args)
        for key, value in params.items():
            if key not in init_args:
                setattr(result, key, value)

        return result

        #return cls.type(**params)
    @classmethod
    def get(cls, id):
        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(f"""SELECT {cls.select()}
                             FROM {cls}
                             WHERE {cls('id')}=%s""",
                             (id,))
            return cls.create(cursor.fetchone())
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

    @classmethod
    def all(cls, filter={}, order={}, search={}):
        filter = cls.where(filter)
        search = cls.where(search, separator='OR')

        row = Row()
        row.offset(cls.name, cls.offset())
        join = Join(cls, row)
        row.offset('total')

        result = []

        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(*debug(f"""SELECT
                           {','.join((cls.select(), join.select()))}
                           FROM {cls}
                           {join}
                           WHERE ({filter.fields()}) AND ({search.fields()})
                           ORDER BY {cls.order('id', 'desc', order)}""",
                           filter.values()+search.values()))
            log.debug(color.cyan('Total fetched %s'))
            while True:
                try:
                    row.data(cursor.fetchone())
                    item = cls.create(row(cls.name))
                    join.set(item)
                    result.append(item)
                except TypeError:
                    break
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

        return result

    @classmethod
    def filter(cls, page=1, limit=100, filter={}, order={}, search={}):
        filter = cls.where(filter)
        search = cls.where(search, separator='OR')
        limit = min(limit, 100)
        offset = (page-1)*limit

        row = Row()
        row.offset(cls.name, cls.offset())
        join = Join(cls, row)
        row.offset('total')

        result = Result()

        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(*debug(f"""SELECT
                           {cls.select()},
                           {join.select()}
                           COUNT(*) OVER()
                           FROM {cls}
                           {join}
                           WHERE ({filter.fields()}) AND ({search.fields()})
                           ORDER BY {cls.order('id', 'desc', order)}
                           LIMIT %s OFFSET %s""",
                           filter.values()+search.values()+[limit, offset]))
            while True:
                try:
                    row.data(cursor.fetchone())
                    if result.total is None:
                        result.total = row('total')
                        print('Total', result.total)
                    item = cls.create(row(cls.name))
                    join.set(item)
                    result.add(item)
                except TypeError:
                    break
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

        if result.total is None:
            result.total = 0

        return result

    @classmethod
    def save(cls, id, data, filter={}):
        filter = cls.where(filter)
        update = cls.update(data)
        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(*debug(f"""UPDATE {cls}
                                    SET {update.fields()}
                                    WHERE {cls('id')}=%s AND {filter.fields()}
                                    RETURNING {cls.select()}""",
                                update.values(id)+filter.values()))
            result = cls.create(cursor.fetchone())
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

        return result

    @classmethod
    def add(cls, data):
        insert = cls.insert(data)
        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(*debug(f"""INSERT INTO {cls}
                                    ({insert.fields()})
                                    VALUES ({insert.fields('%s')})
                                    RETURNING {cls.select()}""",
                                insert.values()))
            result = cls.create(cursor.fetchone())
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

        return result

    @classmethod
    def delete(cls, id):
        try:
            db = cls.get_db()
            cursor = db.cursor()
            cursor.execute(*debug(f"""DELETE FROM {cls}
                                    WHERE {cls('id')}=%s""",
                                (id,)))
            return bool(cursor.rowcount)
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.put_db(db)

        return False

class Row:
    def __init__(self):
        self.position = 0
        self.offsets = {}
        self.__data = None
    def offset(self, name, count=1):
        if hasattr(count, 'offset') and callable(count.offset):
            count = count.offset()
        self.offsets[name] = {}
        self.offsets[name]['position'] = self.position
        self.offsets[name]['count'] = count
        self.position += count
    def data(self, data):
        #print('data', data)
        self.__data = data
    def get(self, name):
        if self.offsets[name]['count'] > 1:
            #print(name, self.offsets[name], self.__data[self.offsets[name]['position']:self.offsets[name]['position']+self.offsets[name]['count']])
            return self.__data[self.offsets[name]['position']:self.offsets[name]['position']+self.offsets[name]['count']]
        return self.__data[self.offsets[name]['position']]
    def __call__(self, name):
        return self.get(name)

class Join():
    def __init__(self, table, row):
        self.table = table
        self.row = row
        if self.table.joins:
            for join in self.table.joins.values():
                self.row.offset(join['table'].name, join['table'])
    def select(self):
        result = ''
        if self.table.joins:
            result = ','.join([join['table'].select() for join in self.table.joins.values()]) + ','
        return result

    def clause(self, name):
        return f"LEFT JOIN {self.table.joins[name]['table']} ON \
{self.table.joins[name]['table'](self.table.joins[name]['table'].id)}={self.table(self.table.joins[name]['field'])}"

    def __str__(self):
        if self.table.joins:
            return '\n'.join([self.clause(join) for join in self.table.joins.keys()])
        return ''

    def set(self, item):
        if self.table.joins:
            for name, join in self.table.joins.items():
                setattr(item, name, join['table'].create(self.row(join['table'].name)))



class Result():
    def __init__(self, total=None):
        self.total = total
        self.items = []
    def add(self, item):
        self.items.append(item)

def debug(query, params):
    params_debug = tuple([str(param) for param in params])

    query_debug = ''
    for line in query.splitlines():
        query_debug += line.strip()+" "

    query_debug = query_debug.replace('SELECT', '\n'+color.cyan('SELECT'))
    query_debug = query_debug.replace('INSERT', '\n'+color.cyan('INSERT'))
    query_debug = query_debug.replace('UPDATE', '\n'+color.cyan('UPDATE'))
    query_debug = query_debug.replace('DELETE', '\n'+color.cyan('DELETE'))
    query_debug = query_debug.replace('UNION', '\n'+color.blue('UNION'))
    query_debug = query_debug.replace('LEFT JOIN', '\n'+color.yellow('LEFT JOIN'))
    query_debug = query_debug.replace('INNER JOIN', '\n'+color.blue('INNER JOIN'))
    query_debug = query_debug.replace('WHERE', '\n'+color.green('WHERE'))
    query_debug = query_debug.replace(' AND ', '\n    '+color.yellow('AND')+' ')
    query_debug = query_debug.replace(' OR ', '\n    '+color.red('OR')+' ')
    query_debug = query_debug.replace(' ON ', ' '+color.cyan('ON')+' ')
    query_debug = query_debug.replace('FROM', '\n'+color.green('FROM'))
    query_debug = query_debug.replace('ORDER', '\n'+color.red('ORDER'))
    query_debug = query_debug.replace('LIMIT', '\n'+color.yellow('LIMIT'))
    query_debug = query_debug.replace('CASE', color.green('CASE'))
    query_debug = query_debug.replace('THEN', color.blue('THEN'))
    query_debug = query_debug.replace('ELSE', color.red('ELSE'))
    query_debug = query_debug.replace('END', color.green('END'))
    query_debug = query_debug.replace('NULL', color.blue('NULL'))
    query_debug = query_debug.replace('NOT', color.red('NOT'))
    query_debug = query_debug.replace('IS', color.red('IS'))
    query_debug = query_debug.replace('COALESCE', color.green('COALESCE'))
    query_debug = query_debug.replace('WHEN', color.green('WHEN'))
    query_debug = query_debug.replace('OVER', color.green('OVER'))
    query_debug = query_debug.replace('COUNT', color.red('COUNT'))
    query_debug += '\n'

    if query_debug.count('%s') != len(params_debug):
        log.error(color.red('Query contains %s params while %s provided'), query_debug.count('%s'), len(params_debug))
    log.debug(query_debug % params_debug)

    return (query, params)
