import sql
import pytest


class StrData:
    def __init__(self):
        pass


class NoSchemaTable(sql.Table):
    name = 'mytable'
    type = StrData
    fields = {
        'id':        {'type': 'int'},
        'name':      {},
        'col_alias': {'field': 'actual_col'},
    }


class WithSchemaTable(sql.Table):
    schema = 'myschema'
    name = 'mytable'
    type = StrData
    fields = {
        'id': {'type': 'int'},
    }


def test_str_no_schema():
    assert str(NoSchemaTable) == '"mytable"'


def test_str_with_schema():
    assert str(WithSchemaTable) == '"myschema"."mytable"'


def test_add_right():
    result = NoSchemaTable + ' suffix'
    assert result == '"mytable" suffix'


def test_add_left():
    result = 'prefix ' + NoSchemaTable
    assert result == 'prefix "mytable"'


def test_add_both_sides():
    result = 'prefix ' + NoSchemaTable + ' suffix'
    assert result == 'prefix "mytable" suffix'


def test_iadd():
    a = 'SELECT * FROM '
    a += NoSchemaTable
    assert a == 'SELECT * FROM "mytable"'


def test_call_returns_field_reference():
    assert NoSchemaTable('id') == '"mytable"."id"'


def test_call_with_field_alias():
    # col_alias maps to actual_col column
    assert NoSchemaTable('col_alias') == '"mytable"."actual_col"'


def test_call_unknown_field_raises():
    with pytest.raises(sql.UnknownField):
        NoSchemaTable('nonexistent')


def test_repr():
    assert repr(NoSchemaTable) == "<Table '\"mytable\"'>"
