import sys
import os
import sys
import inspect
import json
import logging as log
from functools import wraps
from dateutil.parser import parse as parse_date
import re

db = None

if sys.platform.lower() == "win32":
    os.system('color')

ESCAPE = '"'

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

class UniqueError(Error):
    def __init__(self, field=None):
        print(color.red(field))
        super().__init__('unique_error', field=field)

class InvalidValue(Error):
    def __init__(self, message=None, field=None):
        super().__init__('invalid_value', message=message, field=field)

class InvalidDate(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__(message=message, field=field)

class InvalidInt(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__(message=message, field=field)

class InvalidFloat(InvalidValue):
    def __init__(self, message=None, field=None):
        super().__init__(message=message, field=field)

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

class Db:
    def __init__(self, config, size=20):
        self.pool = None
        self.config = config
        self.size = size
        if Table.db is None:
            Table.db = self

    def get(self, key=None):
        if self.pool is None:
            self.init()
        conn = self.pool.getconn(key)
        log.debug(color.yellow('Using db connection at address %s'), id(conn))
        return conn

    def put(self, conn, key=None):
        log.debug(color.yellow('Releasing db connection at address %s'), id(conn))
        self.pool.putconn(conn, key=key)

    def init(self):
        import psycopg2.pool
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(1, self.size, self.config)
            log.debug(color.cyan('Initialized db connection pool'))
        except psycopg2.OperationalError as e:
            log.error(e)
            sys.exit(0)

    def version(self):
        db = None
        try:
            db = self.get()
            cursor = db.cursor()
            cursor.execute(*debug('SELECT VERSION()'))
        finally:
            self.put(db)
        return cursor.fetchone()[0]

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
        return ESCAPE+cls.name+ESCAPE+'.'+ESCAPE+(field if not 'field' in cls.fields[field] else cls.fields[field]['field'])+ESCAPE

class Table(metaclass=MetaTable):
    type = lambda x: None
    schema = None
    name = None
    id = 'id'
    fields = dict()
    joins = dict()
    #order = {'field':'id', 'method':'desc'}
    db = None

    @classmethod
    def str(cls):
        result = ''
        if cls.schema:
            result += ESCAPE+cls.schema+ESCAPE+'.'
        return result + ESCAPE+cls.name+ESCAPE
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
        #log.debug(color.cyan('Where data %s'), data)

        if data is None:
            raise MissingInput()

        values = []
        fields = []
        for field, config in cls.fields.items():

            #log.debug(color.cyan('Parsing field %s %s'), field, config)

            if field in data:

                value = data[field]
                column = config['field'] if 'field' in config else field
                repeat = None

                if not 'type' in config:
                    config['type'] = 'string'

                if 'array' in config and config['array']:
                    criteria = '%s = ANY('+cls.name+'.'+ESCAPE+column+ESCAPE+')'
                elif config['type'] == 'json':
                    value = '%'+value+'%'
                    criteria = cls.name+'.'+ESCAPE+column+ESCAPE+'::TEXT ILIKE %s'
                elif 'options' in config or config['type'] == 'bool':
                    criteria = cls.name+'.'+ESCAPE+column+ESCAPE+'=%s'
                elif config['type'] == 'int' or config['type'] == 'date' or config['type'] == 'float':
                    criteria = cls.name+'.'+ESCAPE+column+ESCAPE+'=%s'
                else:
                    value = '%'+value+'%'
                    criteria = cls.name+'."'+column+"\"::TEXT ILIKE %s"

                if 'array' in config and config['array']:
                    if not isinstance(value, list) and not isinstance(value, tuple):
                        raise InvalidValue('Value of '+field+' must be instance of list '+str(type(value))+' given', field)
                    for parse in value:
                        values.append(cls.value(field, parse))
                        fields.append(criteria)
                else:
                    if 'options' in config and (isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set)):
                        fields.append(cls.name+'."'+column+"\" IN ("+','.join(['%s'] * len(value))+")")
                        for item in value:
                            log.debug(color.cyan('%s'), item)
                            values.append(cls.value(field, item))
                    elif (config['type'] == 'int' or
                        config['type'] == 'date' or
                        config['type'] == 'float') and \
                        (isinstance(value, list) or
                         isinstance(value, tuple) or
                         isinstance(value, set) or
                         isinstance(value, dict)):
                        # ('from' in value or
                        #  'to' in value or
                        #  'in' in value):
                        if isinstance(value, dict) and 'from' in value:
                            values.append(cls.value(field, value['from']))
                            fields.append(cls.name+'."'+column+"\">=%s")
                        if isinstance(value, dict) and 'to' in value:
                            values.append(cls.value(field, value['to']))
                            fields.append(cls.name+'."'+column+"\"<=%s")
                        if (isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set)) and len(value):
                            for item in value:
                                #log.debug(color.cyan('%s'), item)
                                values.append(cls.value(field, item))
                            fields.append(cls.name+'."'+column+"\" IN ("+','.join(['%s'] * len(value))+")")
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
    def order(cls, field=None, method=None, data=None):
        if data is None:
            data = {}
        if 'field' in data:
            field = data['field']
        if 'method' in data:
            method = data['method']

        key = None

        if not field:
            raise MissingField()

        split = field.split('.', 1)
        if len(split) == 2:
            key = split[1]
            field = split[0]
        elif len(split) > 2:
            return ''

        if not field:
            raise MissingField()

        if field not in cls.fields:
            raise UnknownField(field)

        config = cls.fields[field]
        if 'type' not in config:
            config['type'] = 'string'

        column = cls.name+'.'+ESCAPE+(config['field'] if 'field' in config else field)+ESCAPE

        if config['type'] == 'json':
            if key is None:
                raise MissingField()
            if 'keys' not in config:
                raise MissingConfig()
            if key not in config['keys']:
                raise UnknownField()
            column += "->'"+key+"'"

        if method is None:
            method = ''

        method = method.upper()

        if method and method not in ['ASC', 'DESC']:
            raise InvalidValue(method)

        if method:
            method = ' '+method

        return column+method

    @classmethod
    def parse(cls, data, mode):
        if data is None:
            raise MissingInput()

        #log.debug(color.cyan('In a parse %s'), cls.fields)

        values = []
        fields = []
        for field, config in cls.fields.items():
            #log.debug(color.cyan('Parsing field %s'), field)
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
                fields.append(ESCAPE+name+ESCAPE)

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

        return (', '.join(cls.name+'.'+ESCAPE+value+ESCAPE for value in fields))

    @classmethod
    def offset(cls):
        #log.debug(color.red(cls.fields))
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
                    if 'type' in config and config['type'] == 'json' and isinstance(params[field], str):
                        params[field] = json.loads(params[field])
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
    def get(cls, id, filter=None):
        if filter is None:
            filter = {}
        filter = cls.where(filter)
        join = Join(cls)
        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""SELECT {join.select()}
                             FROM {cls}
                             {join}
                             WHERE {cls(cls.id)}=%s AND {filter.fields()}""",
                             [id,]+filter.values()))
            if cursor.rowcount > 0:
                join.row.data(cursor.fetchone())
                return join.create()
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.db.put(db)

    @classmethod
    def all(cls, filter=None, order=None, search=None, limit=None):
        if filter is None:
            filter = {}
        if order is None:
            order = {}
        if search is None:
            search = {}
        join = Join(cls, filter, search)

        result = []

        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""SELECT
                           {join.select()}
                           FROM {cls}
                           {join}
                           WHERE {join.fields()}
                           ORDER BY {cls.order(cls.id, 'desc', order)}
                           {f'LIMIT {int(limit)}' if limit else ''}""",
                           join.values()))
            log.debug(color.cyan('Total fetched %s'), cursor.rowcount)
            while True:
                try:
                    join.row.data(cursor.fetchone())
                    item = join.create()
                    result.append(item)
                except TypeError:
                    break
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.db.put(db)

        return result

    @classmethod
    def filter(cls, page=1, limit=100, filter=None, order=None, search=None):
        if filter is None:
            filter = {}
        if order is None:
            order = {}
        if search is None:
            search = {}


        join = Join(cls, filter, search)
        join.row.offset('total')

        limit = min(limit, 100)
        offset = (page-1)*limit

        result = Result()

        db = None

        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""SELECT
                           {join.select()},
                           COUNT(*) OVER()
                           FROM {cls}
                           {join}
                           WHERE {join.fields()}
                           ORDER BY {join.order(cls.id, 'desc', order)}
                           LIMIT %s OFFSET %s""",
                           join.values()+[limit, offset]))
            log.debug(color.cyan('Total fetched %s'), cursor.rowcount)
            while True:
                try:
                    join.row.data(cursor.fetchone())
                    if result.total is None:
                        result.total = join.row('total')
                    item = join.create()
                    result.add(item)
                except TypeError:
                    break
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.db.put(db)

        if result.total is None:
            result.total = 0

        return result

    @classmethod
    def save(cls, id, data, filter=None):
        if filter is None:
            filter = {}

        filter = cls.where(filter)
        join = Join(cls)
        update = cls.update(data)
        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""WITH "{cls.name}" AS (
                                        UPDATE {cls}
                                        SET {update.fields()}
                                        WHERE {cls(cls.id)}=%s AND {filter.fields()}
                                        RETURNING {cls.select()}
                                    )
                                    SELECT {join.select()}
                                    FROM "{cls.name}"
                                    {join}
                                    """,
                                update.values(id)+filter.values()))
            if cursor.rowcount > 0:
                join.row.data(cursor.fetchone())
                return join.create()
        except Exception as error:
            match = re.search(r''+cls.name+'_unique_(.*?)_index', str(error))
            print(match)
            if match is not None and match.lastindex > 0:
                index = match.group(1)
                if index in cls.fields:
                    raise UniqueError(index)
                for field, config in cls.fields:
                    if 'field' in config and config['field'] == index:
                        raise UniqueError(field)
            raise error
        finally:
            db.commit()
            cls.db.put(db)


    @classmethod
    def add(cls, data):
        join = Join(cls)
        insert = cls.insert(data)
        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""WITH "{cls.name}" AS (
                                        INSERT INTO {cls}
                                        ({insert.fields()})
                                        VALUES ({insert.fields('%s')})
                                        RETURNING {cls.select()}
                                    )
                                    SELECT {join.select()}
                                    FROM "{cls.name}"
                                    {join}
                                    """,
                                insert.values()))
            log.debug(color.cyan('Total fetched %s'), cursor.rowcount)
            if cursor.rowcount > 0:
                join.row.data(cursor.fetchone())
                return join.create()

        except Exception as error:
            match = re.search(r''+cls.name+'_unique_(.*?)_index', str(error))
            print(match)
            if match is not None and match.lastindex > 0:
                index = match.group(1)
                if index in cls.fields:
                    raise UniqueError(index)
                for field, config in cls.fields:
                    if 'field' in config and config['field'] == index:
                        raise UniqueError(field)
            raise error
        finally:
            db.commit()
            cls.db.put(db)


    @classmethod
    def delete(cls, id, filter=None):
        if filter is None:
            filter = {}

        filter = cls.where(filter)
        try:
            db = cls.db.get()
            cursor = db.cursor()
            cursor.execute(*debug(f"""DELETE FROM {cls}
                                    WHERE {filter.fields()} AND {cls(cls.id)}=%s""",
                                  filter.values(id)))
            return bool(cursor.rowcount)
        except Exception as error:
            raise error
        finally:
            db.commit()
            cls.db.put(db)

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
            #log.debug(color.cyan('Row offset %s'), name)
            #print(name, self.offsets[name], self.__data[self.offsets[name]['position']:self.offsets[name]['position']+self.offsets[name]['count']])
            return self.__data[self.offsets[name]['position']:self.offsets[name]['position']+self.offsets[name]['count']]
        return self.__data[self.offsets[name]['position']]
    def __call__(self, name):
        return self.get(name)

class Join():
    def __init__(self, table, filter=None, search=None):

        if filter is None:
            filter = {}
        if search is None:
            search = {}


        self.table = table

        self.row = Row()
        self.row.offset(self.table.name, self.table)
        if self.table.joins:
            for join in self.table.joins.values():
                self.row.offset(join['table'].name, join['table'])

        self.searchs = {}
        self.filters = {}
        if filter:
            self.filters[self.table.name] = self.table.where(filter)
            if self.table.joins:
                for key, value in self.table.joins.items():
                    if key in filter:
                        self.filters[key] = value['table'].where(filter[key])

        if search:
            self.searchs[self.table.name] = self.table.where(search, separator='OR')
            if self.table.joins:
                for key, value in self.table.joins.items():
                    if key in search:
                        self.searchs[key] = value['table'].where(search[key], separator='OR')

    def select(self):
        result = ''
        if self.table.joins:
            result = ','.join([join['table'].select() for join in self.table.joins.values()])
        return select(self.table.select(), result)

    def fields(self):
        search = ' OR '.join(where.fields() for where in self.searchs.values())
        filter = ' AND '.join(where.fields() for where in self.filters.values())
        if not search:
            search = '1=1'
        if not filter:
            filter = '1=1'
        return '('+search+ ') AND ('+filter+')'

    def values(self):
        result = []
        for where in self.searchs.values():
            result.extend(where.values())
        for where in self.filters.values():
            result.extend(where.values())
        return result

    def clause(self, name):
        return f"LEFT JOIN {self.table.joins[name]['table']} ON \
{self.table.joins[name]['table'](self.table.joins[name]['table'].id)}={self.table(self.table.joins[name]['field'])}"

    def __str__(self):
        if self.table.joins:
            return '\n'.join([self.clause(join) for join in self.table.joins.keys()])
        return ''

    def create(self):
        item = self.table.create(self.row(self.table.name))
        if self.table.joins:
            for name, join in self.table.joins.items():
                setattr(item, name, join['table'].create(self.row(join['table'].name)))
        return item

    def order(self, field, method, order=None):
        if order is None:
            order = {}

        if 'field' in order:
            field = order['field']
        if 'method' in order:
            method = order['method']

        order = None
        if self.table.joins:
            for name, join in self.table.joins.items():
                if field.startswith(name+'.'):
                    try:
                        order = join['table'].order(data={'field':field[len(name)+1:], 'method':method})
                    except Exception:
                        pass
        if not order:
            return self.table.order(field, method)
        return order

def select(*args):
    return ','.join([item for item in args if str(item).strip() != ''])

class Result():
    def __init__(self, total=None):
        self.total = total
        self.items = []
    def add(self, item):
        #log.debug('Adding %s', item)
        self.items.append(item)

def debug(query, params=None):
    if params is None:
        params = []
    params_debug = tuple(["'"+str(param)+"'" for param in params])

    query_debug = '\n'
    for line in query.splitlines():
        query_debug += line.strip()+" "

    query_debug = query_debug.replace('SELECT', '\n'+color.cyan('SELECT'))
    query_debug = query_debug.replace('INSERT', '\n'+color.cyan('INSERT'))
    query_debug = query_debug.replace('UPDATE', '\n'+color.cyan('UPDATE'))
    query_debug = query_debug.replace('DELETE', '\n'+color.cyan('DELETE'))
    query_debug = query_debug.replace('TRUNCATE', '\n'+color.red('TRUNCATE'))
    query_debug = query_debug.replace('UNION', '\n'+color.blue('UNION'))
    query_debug = query_debug.replace('LEFT JOIN', '\n'+color.yellow('LEFT JOIN'))
    query_debug = query_debug.replace('INNER JOIN', '\n'+color.blue('INNER JOIN'))
    query_debug = query_debug.replace('WHERE', '\n'+color.green('WHERE')+'\n   ')
    query_debug = query_debug.replace(' AND ', '\n    '+color.yellow('AND')+' ')
    query_debug = query_debug.replace(' OR ', '\n    '+color.red('OR')+' ')
    query_debug = query_debug.replace(' ON ', ' '+color.cyan('ON')+' ')
    query_debug = query_debug.replace('WITH ', '\n'+color.cyan('WITH')+' ')
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
    query_debug = query_debug.replace('RETURNING', '\n'+color.cyan('RETURNING'))
    query_debug = query_debug.replace('VALUES', '\n'+color.cyan('VALUES'))
    query_debug += '\n'

    if query_debug.count('%s') != len(params_debug):
        log.error(color.red('Query contains %s params while %s provided'), query_debug.count('%s'), len(params_debug))
        log.debug(query_debug)
        log.debug(params_debug)
    else:
        log.debug(query_debug % params_debug)

    return (query, params)

def query(source, params=None):
    db_ = None
    try:
        db_ = db.get()
        cursor = db_.cursor()
        cursor.execute(*debug(source, params))
        log.debug(color.cyan('Total %s'), cursor.rowcount)
        if cursor.rowcount > 0:
            result = []
            for record in cursor:
                result.append(record)
            return result
    finally:
        db_.commit()
        db.put(db_)
