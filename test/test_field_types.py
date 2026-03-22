import pytest
import sql
from conftest import (
    UserTable, GroupTable, CategoryTable, ProductTable,
    ItemTable, ThingTable, EncodedItemTable,
)


# ---------------------------------------------------------------------------
# string
# ---------------------------------------------------------------------------

def test_string_field_roundtrip(truncate):
    item = ItemTable.add({'title': 'hello world', 'active': True})
    fetched = ItemTable.get(item.id)
    assert fetched.title == 'hello world'


def test_string_unicode_roundtrip(truncate):
    item = ItemTable.add({'title': 'გამარჯობა', 'active': True})
    fetched = ItemTable.get(item.id)
    assert fetched.title == 'გამარჯობა'


# ---------------------------------------------------------------------------
# bool
# ---------------------------------------------------------------------------

def test_bool_true_roundtrip(truncate):
    item = ItemTable.add({'title': 'test', 'active': True})
    fetched = ItemTable.get(item.id)
    assert fetched.active is True


def test_bool_false_roundtrip(truncate):
    item = ItemTable.add({'title': 'test', 'active': False})
    fetched = ItemTable.get(item.id)
    assert fetched.active is False


# ---------------------------------------------------------------------------
# date
# ---------------------------------------------------------------------------

def test_date_field_stored_and_retrieved(truncate):
    item = ItemTable.add({'title': 'test', 'active': True, 'created_at': '2025-06-15'})
    fetched = ItemTable.get(item.id)
    assert fetched.created_at is not None
    assert fetched.created_at.year == 2025
    assert fetched.created_at.month == 6
    assert fetched.created_at.day == 15


def test_date_natural_language_parsed(truncate):
    item = ItemTable.add({'title': 'test', 'active': True, 'created_at': 'January 1 2024'})
    fetched = ItemTable.get(item.id)
    assert fetched.created_at.year == 2024
    assert fetched.created_at.month == 1


# ---------------------------------------------------------------------------
# float
# ---------------------------------------------------------------------------

def test_float_field_roundtrip(truncate):
    cat = CategoryTable.add({'name': {'en': 'Books'}, 'tags': []})
    prod = ProductTable.add({'title': 'item', 'price': 9.99, 'category_id': cat.id})
    fetched = ProductTable.get(prod.id)
    assert abs(fetched.price - 9.99) < 0.001


def test_float_integer_value(truncate):
    cat = CategoryTable.add({'name': {'en': 'Misc'}, 'tags': []})
    prod = ProductTable.add({'title': 'item', 'price': 5.0, 'category_id': cat.id})
    fetched = ProductTable.get(prod.id)
    assert abs(fetched.price - 5.0) < 0.001


# ---------------------------------------------------------------------------
# int
# ---------------------------------------------------------------------------

def test_int_field_roundtrip(truncate):
    cat = CategoryTable.add({'name': {'en': 'Tech'}, 'tags': []})
    prod = ProductTable.add({'title': 'gadget', 'price': 1.0, 'category_id': cat.id})
    fetched = ProductTable.get(prod.id)
    assert fetched.category_id == cat.id


# ---------------------------------------------------------------------------
# json
# ---------------------------------------------------------------------------

def test_json_dict_roundtrip(truncate):
    cat = CategoryTable.add({'name': {'en': 'Electronics', 'ka': 'ელექტრონიკა'}, 'tags': []})
    fetched = CategoryTable.get(cat.id)
    assert fetched.name == {'en': 'Electronics', 'ka': 'ელექტრონიკა'}


def test_json_partial_keys(truncate):
    cat = CategoryTable.add({'name': {'en': 'Books'}, 'tags': []})
    fetched = CategoryTable.get(cat.id)
    assert fetched.name['en'] == 'Books'


# ---------------------------------------------------------------------------
# array
# ---------------------------------------------------------------------------

def test_array_field_roundtrip(truncate):
    cat = CategoryTable.add({'name': {'en': 'Lit'}, 'tags': ['fiction', 'classic']})
    fetched = CategoryTable.get(cat.id)
    assert fetched.tags == ['fiction', 'classic']


def test_array_empty_roundtrip(truncate):
    cat = CategoryTable.add({'name': {'en': 'Empty'}, 'tags': []})
    fetched = CategoryTable.get(cat.id)
    assert fetched.tags == []


def test_array_single_element(truncate):
    cat = CategoryTable.add({'name': {'en': 'Solo'}, 'tags': ['only']})
    fetched = CategoryTable.get(cat.id)
    assert fetched.tags == ['only']


# ---------------------------------------------------------------------------
# encoder / decoder
# ---------------------------------------------------------------------------

def test_encoder_transforms_value_in_db(truncate):
    item = EncodedItemTable.add({'title': 'test', 'secret': 'hello'})
    # verify the stored value is uppercase (encoder ran)
    rows = sql.query('SELECT secret FROM test.encoded_items WHERE id=%s', [item.id])
    assert rows[0][0] == 'HELLO'


def test_decoder_transforms_value_on_read(truncate):
    EncodedItemTable.add({'title': 'test', 'secret': 'hello'})
    # add() returns create() which runs decoder → 'hello'
    item = EncodedItemTable.add({'title': 'test2', 'secret': 'world'})
    fetched = EncodedItemTable.get(item.id)
    assert fetched.secret == 'world'   # decoder lowercased 'WORLD' back


# ---------------------------------------------------------------------------
# field alias  ('field' key maps Python name → DB column name)
# ---------------------------------------------------------------------------

def test_field_alias_insert_and_fetch(truncate):
    item = ThingTable.add({'alias_name': 'hello'})
    fetched = ThingTable.get(item.id)
    assert fetched.alias_name == 'hello'


def test_field_alias_update(truncate):
    item = ThingTable.add({'alias_name': 'hello'})
    ThingTable.save(item.id, {'alias_name': 'world'})
    fetched = ThingTable.get(item.id)
    assert fetched.alias_name == 'world'


# ---------------------------------------------------------------------------
# select: False  (stored but never returned in SELECT)
# ---------------------------------------------------------------------------

def test_select_false_field_not_on_object(truncate):
    # insert via raw query to populate the hidden column
    sql.query(
        'INSERT INTO test.things (internal_col, hidden) VALUES (%s, %s)',
        ['visible_val', 'secret_val'],
    )
    rows = sql.query('SELECT id FROM test.things LIMIT 1')
    item = ThingTable.get(rows[0][0])
    assert not hasattr(item, 'hidden')


# ---------------------------------------------------------------------------
# insert: False  (field skipped in INSERT even if passed)
# ---------------------------------------------------------------------------

def test_insert_false_field_ignored_in_add(truncate):
    # id has insert:False — passing it has no effect, DB generates its own
    user = UserTable.add({'id': 9999, 'username': 'john', 'fullname': 'John', 'status': 'active'})
    assert user.id != 9999
    assert user.id is not None


# ---------------------------------------------------------------------------
# update: False  (field skipped in UPDATE even if passed)
# ---------------------------------------------------------------------------

def test_update_false_field_ignored_in_save(truncate):
    # id has update:False — passing a new id has no effect on the stored row
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    original_id = user.id
    UserTable.save(user.id, {'id': 9999, 'username': 'jane'})
    fetched = UserTable.get(original_id)
    assert fetched is not None        # record still at original id
    assert fetched.username == 'jane'


# ---------------------------------------------------------------------------
# schema qualification
# ---------------------------------------------------------------------------

def test_schema_in_table_str():
    assert str(UserTable) == '"test"."users"'


def test_schema_in_select():
    assert 'users.' in UserTable.select()


# ---------------------------------------------------------------------------
# join roundtrip through add / get
# ---------------------------------------------------------------------------

def test_join_nested_object_on_add(truncate):
    cat = CategoryTable.add({'name': {'en': 'Tech'}, 'tags': []})
    prod = ProductTable.add({'title': 'phone', 'price': 299.0, 'category_id': cat.id})
    assert prod.category is not None
    assert prod.category.name['en'] == 'Tech'


def test_join_nested_object_on_get(truncate):
    cat = CategoryTable.add({'name': {'en': 'Music'}, 'tags': ['audio']})
    prod = ProductTable.add({'title': 'speaker', 'price': 49.0, 'category_id': cat.id})
    fetched = ProductTable.get(prod.id)
    assert fetched.category.name['en'] == 'Music'
    assert fetched.category.tags == ['audio']
