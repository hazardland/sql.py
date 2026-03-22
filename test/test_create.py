import sql
import pytest


class SimpleObj:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class IdOnlyObj:
    def __init__(self, id=None):
        self.id = id


class SimpleTable(sql.Table):
    name = 'simple'
    type = SimpleObj
    fields = {
        'id':   {'type': 'int'},
        'name': {},
    }


class WithDecoderTable(sql.Table):
    name = 'decoded'
    type = IdOnlyObj
    fields = {
        'id':   {'type': 'int'},
        'data': {'decoder': lambda x: x.upper() if x else x},
    }


class WithJsonTable(sql.Table):
    name = 'jobj'
    type = IdOnlyObj
    fields = {
        'id':   {'type': 'int'},
        'meta': {'type': 'json'},
    }


class WithArrayTable(sql.Table):
    name = 'arrtable'
    type = IdOnlyObj
    fields = {
        'id':   {'type': 'int'},
        'tags': {'array': True},
    }


class WithHiddenTable(sql.Table):
    name = 'hidden'
    type = IdOnlyObj
    fields = {
        'id':      {'type': 'int'},
        'secret':  {'select': False},
        'visible': {},
    }


class ExtraObj:
    # name is NOT in __init__ — will be set via setattr
    def __init__(self, id=None):
        self.id = id


class ExtraTable(sql.Table):
    name = 'extra'
    type = ExtraObj
    fields = {
        'id':   {'type': 'int'},
        'name': {},
    }


def test_create_maps_tuple_to_object():
    obj = SimpleTable.create((1, 'hello'))
    assert obj.id == 1
    assert obj.name == 'hello'


def test_create_select_false_skipped_in_mapping():
    # tuple only has id and visible — secret is skipped
    obj = WithHiddenTable.create((42, 'pub'))
    assert obj.id == 42
    assert obj.visible == 'pub'


def test_create_decoder_called():
    obj = WithDecoderTable.create((1, 'hello'))
    assert obj.data == 'HELLO'


def test_create_json_string_auto_parsed():
    obj = WithJsonTable.create((1, '{"key": "val"}'))
    assert obj.meta == {'key': 'val'}


def test_create_json_already_dict_unchanged():
    obj = WithJsonTable.create((1, {'key': 'val'}))
    assert obj.meta == {'key': 'val'}


def test_create_array_list_passthrough():
    obj = WithArrayTable.create((1, ['a', 'b']))
    assert obj.tags == ['a', 'b']


def test_create_array_empty_pg_string():
    obj = WithArrayTable.create((1, '{}'))
    assert obj.tags == []


def test_create_array_pg_string_parsed():
    obj = WithArrayTable.create((1, '{a,b,c}'))
    assert obj.tags == ['a', 'b', 'c']


def test_create_extra_fields_set_via_setattr():
    # name not in ExtraObj.__init__ — goes through setattr
    obj = ExtraTable.create((1, 'world'))
    assert hasattr(obj, 'name')
    assert obj.name == 'world'
