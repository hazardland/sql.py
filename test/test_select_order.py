import sql
import pytest


class SoData:
    def __init__(self):
        pass


class SoTable(sql.Table):
    name = 'item'
    type = SoData
    fields = {
        'id':       {'type': 'int'},
        'name':     {},
        'secret':   {'select': False},
        'aliased':  {'field': 'actual_col'},
        'title':    {'type': 'json', 'keys': ['en', 'ka']},
    }


# --- select() ---

def test_select_includes_selectable_fields():
    result = SoTable.select()
    assert 'item."id"' in result
    assert 'item."name"' in result


def test_select_excludes_select_false():
    result = SoTable.select()
    assert 'secret' not in result


def test_select_uses_field_alias_as_column():
    result = SoTable.select()
    assert 'item."actual_col"' in result
    assert 'aliased' not in result


# --- offset() ---

def test_offset_counts_selectable_fields():
    # id, name, aliased, title = 4  (secret is select:False)
    assert SoTable.offset() == 4


# --- order() ---

def test_order_asc():
    assert SoTable.order('id', 'asc') == 'item."id" ASC'


def test_order_desc():
    assert SoTable.order('id', 'desc') == 'item."id" DESC'


def test_order_method_is_uppercased():
    result = SoTable.order('id', 'asc')
    assert 'ASC' in result


def test_order_none_method_returns_column_only():
    assert SoTable.order('id', None) == 'item."id"'


def test_order_invalid_method_raises():
    with pytest.raises(sql.InvalidValue):
        SoTable.order('id', 'SIDEWAYS')


def test_order_unknown_field_raises():
    with pytest.raises(sql.UnknownField):
        SoTable.order('nonexistent', 'asc')


def test_order_none_field_raises():
    with pytest.raises(sql.MissingField):
        SoTable.order(None, 'asc')


def test_order_from_data_dict_overrides_params():
    result = SoTable.order(data={'field': 'name', 'method': 'desc'})
    assert 'name' in result
    assert 'DESC' in result


def test_order_json_field_with_key_notation():
    result = SoTable.order('title.en', 'asc')
    assert "->'en'" in result


def test_order_json_field_without_key_raises():
    with pytest.raises(sql.MissingField):
        SoTable.order('title', 'asc')


def test_order_json_field_unknown_key_raises():
    with pytest.raises(sql.UnknownField):
        SoTable.order('title.fr', 'asc')
