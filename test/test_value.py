import sql
import pytest
import json


class ValueData:
    def __init__(self):
        pass


class ValueTable(sql.Table):
    name = 'sample'
    type = ValueData
    fields = {
        'name':    {},
        'age':     {'type': 'int'},
        'price':   {'type': 'float'},
        'active':  {'type': 'bool'},
        'data':    {'type': 'json'},
        'created': {'type': 'date'},
        'status':  {'options': ['active', 'disabled']},
        'encoded': {'encoder': lambda x: x.upper()},
    }


def test_none_returns_none():
    assert ValueTable.value('name', None) is None


def test_string_cast():
    assert ValueTable.value('name', 123) == '123'


def test_int_cast_returns_string():
    # value() always returns str at the end — int is validated then stringified
    result = ValueTable.value('age', '42')
    assert result == '42'


def test_int_invalid_raises_value_error():
    # int type has no try/except — raw ValueError from int('abc')
    with pytest.raises(ValueError):
        ValueTable.value('age', 'abc')


def test_float_cast_returns_string():
    result = ValueTable.value('price', '3.14')
    assert result == '3.14'


def test_float_invalid_raises():
    with pytest.raises(sql.InvalidFloat):
        ValueTable.value('price', 'abc')


def test_bool_true():
    assert ValueTable.value('active', True) == 'True'


def test_bool_false():
    assert ValueTable.value('active', False) == 'False'


def test_bool_from_zero():
    assert ValueTable.value('active', 0) == 'False'


def test_json_dict_serialized():
    result = ValueTable.value('data', {'key': 'val'})
    assert result == json.dumps({'key': 'val'})


def test_date_valid_iso():
    result = ValueTable.value('created', '2025-01-15')
    assert '2025' in result


def test_date_natural_language():
    result = ValueTable.value('created', 'March 1 2025')
    assert '2025' in result


def test_date_invalid_raises():
    with pytest.raises(sql.InvalidDate):
        ValueTable.value('created', '$$$')


def test_options_valid():
    assert ValueTable.value('status', 'active') == 'active'


def test_options_invalid_raises():
    with pytest.raises(sql.InvalidValue):
        ValueTable.value('status', 'unknown')


def test_encoder_applied():
    assert ValueTable.value('encoded', 'hello') == 'HELLO'


def test_return_is_always_string():
    assert isinstance(ValueTable.value('age', 42), str)
    assert isinstance(ValueTable.value('price', 1.5), str)
    assert isinstance(ValueTable.value('active', True), str)
