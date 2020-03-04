import json
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
        import sys
        import os
        import inspect
        import traceback
        self.file = inspect.stack()[1][1].rpartition(os.path.sep)[2]
        self.line = inspect.stack()[1][2]
        super(Error, self).__init__(code)
        self.code = code
        if message is not None and not isinstance(message, str):
            self.message = " ".join(map(str, message))
        else:
            self.message = message
        self.field = field
        print(color.red(self.code+':'), color.yellow(self.message), color.cyan(str(self.file)+':'+str(self.line)), color.green('['+self.field+']') if not self.field is None else '')
        traceback.print_exc(file=sys.stdout)

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
    def values(self, ID=None):
        if ID is not None:
            return self.__values+list((ID,))
        return self.__values
    def exctract(self):
        return self.__fields, self.__values

'''
FIELD OPTIONS
    fields = {
        'name':{ # name is field and property name by default
            # OPTIONAL PARAMS (optional params can be not specified)
            'type': 'string'|'int' # default is 'string'
                                   # field values ar casted in type
            'field': 'table_field_name' # default is 'name'
            'select': True # default is True
            'update': True # default is True
            'encoder': encoder_function # encoder function whith 1 param
                                        # output of encoder function is used directly
                                        # for value
        }
    }
'''
class Table:
    schema = None
    name = None
    fields = dict()
    type = lambda x: None
    @classmethod
    def table(cls):
        result = ''
        if cls.schema:
            result += cls.schema+'.'
        return result + cls.name
    """
        Returns an array for updating table
        update['fields'] = 'field1=%s, field2=%s'
        update['values'] = ['value1', 'value2', 'id']
    """
    @classmethod
    def update(cls, data):
        fields, values = cls.parse(data, 'update')

        if len(values) == 0:
            raise Error('missing_input', 'Nothing to update')

        return Clause(fields, values, '{name}=%s')

    @classmethod
    def insert(cls, data):

        fields, values = cls.parse(data, 'insert')

        if len(values) == 0:
            raise Error('missing_input', 'Nothing to insert')

        return Clause(fields, values)

    @classmethod
    def where(cls, data, prefix=None):
        if data is None:
            raise Error('missing_input', 'Where data is missing')

        values = []
        fields = []
        for field, config in cls.fields.items():

            if (field if prefix is None else prefix+field) in data:

                value = data[(field if prefix is None else prefix+field)]
                column = config['field'] if 'field' in config else field

                if not 'type' in config:
                    config['type'] = 'string'

                if 'array' in config and config['array']:
                    criteria = '%s = ANY('+cls.name+'."'+column+'")'
                elif 'options' in config or config['type']=='bool':
                    criteria = cls.name+'."'+column+'"=%s'
                elif config['type']=='int' or config['type']=='date' or config['type']=='float':
                    criteria = cls.name+'."'+column+'"=%s'
                else:
                    value = value+'%'
                    criteria = cls.name+'."'+column+"\" LIKE %s"


                if 'array' in config and config['array']:
                    if not isinstance(value, list) and not isinstance(value, tuple):
                        raise Error('invalid_value', 'Value of '+field+' must be instance of list '+str(type(value))+' given', field)
                    for parse in value:
                        values.append(cls.value(field, parse))
                        fields.append(criteria)
                else:
                    if (config['type']=='int' or config['type']=='date' or config['type']=='float') and (isinstance(value, list) or isinstance(value, tuple) or isinstance(value, dict)) and ('from' in value or 'to' in value):
                        if 'from' in value:
                            values.append(cls.value(field, value['from']))
                            fields.append(cls.name+'."'+column+"\">=%s")
                        if 'to' in value:
                            values.append(cls.value(field, value['to']))
                            fields.append(cls.name+'."'+column+"\"<=%s")
                    else:
                        values.append(cls.value(field, value))
                        fields.append(criteria)

        return Clause(fields, values, separator=' AND ', empty='1=1')

    @classmethod
    def order(cls, field, method=None, data=None, prefix=None):
        if data:
            if not 'field' in data:
                return ''
            if prefix:
                split = data['field'].split(prefix, 1)
                if len(split) > 0:
                    if split[1] in cls.fields:
                        column = split[1]
                    else:
                        return ''
                else:
                    return ''

            elif data['field'] in cls.fields:
                column = data['field']
            else:
                return ''
        elif field:
            if field not in cls.fields:
                raise Error('unknown_field', 'Order field unknown')
            column = field
        else:
            raise Error('missing_field', 'Order field not provided')

        column = cls.name+'."'+(cls.fields[column]['field'] if 'field' in cls.fields[column] else column)+'"'

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
            raise Error('missing_input', mode.capitalize()+' data is missing')

        values = []
        fields = []
        for field, config in cls.fields.items():
            if mode in config and not config[mode]:
                continue

            if field in data:

                value = data[field]

                if 'array' in config and config['array']:
                    if not isinstance(value, list) and not isinstance(value, tuple):
                        raise Error('invalid_value', 'Value of '+field+' must be instance of list '+str(type(value))+' given', field)
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
                raise Error('invalid_date', 'Invalid date '+value+' for field'+field, field)
        elif config['type'] == 'float':
            try:
                value = float(value)
            except Exception:
                raise Error('invalid_float', 'Invalid float '+value+' for field'+field, field)

        # checking for options
        if 'options' in config:
            if value not in config['options']:
                raise Error('invalid_value', 'Invalid value '+value+' for field '+field, field)

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
        return cls.type(**params)

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
    def __init__(self, *tables):
        self.tables = []
        self.prefixes = {}
        for table in tables:
            if isinstance(table, tuple):
                self.tables.append(table[0])
                self.prefixes[table[0].name] = table[1]
            else:
                self.tables.append(table)
                self.prefixes[table.name] = ''

    def where(self, data):
        fields = []
        values = []
        for table in self.tables:
            where = table.where(data, self.prefixes[table.name])
            __fields, __values = where.exctract()
            fields.extend(__fields)
            values.extend(__values)

        return Clause(fields, values, separator=' AND ', empty='1=1')

    def order(self, field, method=None, data=None):
        for table in self.tables:
            order = table.order(field, method, data, prefix=self.prefixes[table.name])
            if order:
                return order
        return ''
