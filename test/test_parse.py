import sql
import pytest


class ParseData:
    def __init__(self):
        pass


class ParseTable(sql.Table):
    name = 'item'
    type = ParseData
    fields = {
        'id':        {'type': 'int', 'insert': False, 'update': False},
        'name':      {},
        'price':     {'type': 'float', 'update': False},
        'col_alias': {'field': 'actual_col'},
        'tags':      {'array': True},
    }


def test_insert_includes_default_fields():
    fields, values = ParseTable.parse({'name': 'thing', 'price': '5.0'}, 'insert')
    assert '"name"' in fields
    assert '"price"' in fields


def test_insert_skips_insert_false():
    fields, values = ParseTable.parse({'id': 1, 'name': 'x'}, 'insert')
    assert '"id"' not in fields


def test_update_skips_update_false_fields():
    fields, values = ParseTable.parse({'id': 1, 'name': 'x', 'price': '5.0'}, 'update')
    assert '"id"' not in fields
    assert '"price"' not in fields


def test_field_alias_used_as_column_name():
    fields, values = ParseTable.parse({'col_alias': 'val'}, 'insert')
    assert '"actual_col"' in fields
    assert '"col_alias"' not in fields


def test_missing_field_in_data_is_skipped():
    fields, values = ParseTable.parse({'name': 'x'}, 'insert')
    assert len(fields) == 1
    assert fields[0] == '"name"'


def test_array_field_formatted_as_pg_array():
    fields, values = ParseTable.parse({'tags': ['a', 'b']}, 'insert')
    assert values[0] == '{a,b}'


def test_array_field_none_passes_through():
    fields, values = ParseTable.parse({'tags': None}, 'insert')
    assert values[0] is None


def test_array_field_non_list_raises():
    with pytest.raises(sql.InvalidValue):
        ParseTable.parse({'tags': 'notalist'}, 'insert')
