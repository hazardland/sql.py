import sql
import pytest


class WhereData:
    def __init__(self):
        pass


class WhereTable(sql.Table):
    name = 'item'
    type = WhereData
    fields = {
        'name':    {},
        'age':     {'type': 'int'},
        'price':   {'type': 'float'},
        'active':  {'type': 'bool'},
        'data':    {'type': 'json', 'keys': ['en', 'ka']},
        'status':  {'options': ['active', 'disabled']},
        'tags':    {'array': True},
        'created': {'type': 'date'},
    }


def test_none_data_raises():
    with pytest.raises(sql.MissingInput):
        WhereTable.where(None)


def test_empty_data_returns_1_equals_1():
    clause = WhereTable.where({})
    assert clause.fields() == '1=1'


def test_string_field_uses_ilike():
    clause = WhereTable.where({'name': 'john'})
    assert 'ILIKE' in clause.fields()
    assert clause.values()[0] == '%john%'


def test_int_field_exact_match():
    clause = WhereTable.where({'age': 5})
    assert '=%s' in clause.fields()
    assert 'ILIKE' not in clause.fields()
    assert clause.values()[0] == '5'


def test_float_field_exact_match():
    clause = WhereTable.where({'price': 3.14})
    assert '=%s' in clause.fields()
    assert 'ILIKE' not in clause.fields()


def test_bool_true_exact_match():
    clause = WhereTable.where({'active': True})
    assert '=%s' in clause.fields()
    assert 'ILIKE' not in clause.fields()


def test_bool_false_passes_as_value():
    clause = WhereTable.where({'active': False})
    assert clause.values()[0] == 'False'


def test_json_field_uses_text_ilike():
    clause = WhereTable.where({'data': 'search'})
    assert '::TEXT ILIKE' in clause.fields()
    assert clause.values()[0] == '%search%'


def test_options_single_value_exact_match():
    clause = WhereTable.where({'status': 'active'})
    assert '=%s' in clause.fields()
    assert 'IN' not in clause.fields()


def test_options_list_generates_in():
    clause = WhereTable.where({'status': ['active', 'disabled']})
    assert 'IN' in clause.fields()
    assert len(clause.values()) == 2


def test_int_range_from():
    clause = WhereTable.where({'age': {'from': 10}})
    assert '>=' in clause.fields()
    assert clause.values()[0] == '10'


def test_int_range_to():
    clause = WhereTable.where({'age': {'to': 20}})
    assert '<=' in clause.fields()
    assert clause.values()[0] == '20'


def test_int_range_from_and_to_both_clauses():
    clause = WhereTable.where({'age': {'from': 10, 'to': 20}})
    fields = clause.fields()
    assert '>=' in fields
    assert '<=' in fields
    assert len(clause.values()) == 2


def test_float_range_from_and_to():
    clause = WhereTable.where({'price': {'from': 1.0, 'to': 9.99}})
    fields = clause.fields()
    assert '>=' in fields
    assert '<=' in fields


def test_int_list_generates_in():
    clause = WhereTable.where({'age': [1, 2, 3]})
    assert 'IN' in clause.fields()
    assert len(clause.values()) == 3


def test_array_field_generates_any():
    clause = WhereTable.where({'tags': ['python']})
    assert 'ANY' in clause.fields()


def test_array_field_non_list_raises():
    with pytest.raises(sql.InvalidValue):
        WhereTable.where({'tags': 'notalist'})


def test_unknown_key_in_data_ignored():
    clause = WhereTable.where({'nonexistent': 'value'})
    assert clause.fields() == '1=1'


def test_or_separator():
    clause = WhereTable.where({'name': 'a', 'age': 1}, separator='OR')
    assert 'OR' in clause.fields()


def test_values_count_matches_placeholders():
    clause = WhereTable.where({'name': 'x', 'age': 5})
    assert clause.fields().count('%s') == len(clause.values())
