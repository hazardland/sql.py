import sql


class CatData:
    def __init__(self):
        pass


class ProdData:
    def __init__(self):
        pass


class CatTable(sql.Table):
    schema = 'shop'
    name = 'category'
    type = CatData
    fields = {
        'id':   {'type': 'int'},
        'name': {},
    }


class ProdTable(sql.Table):
    schema = 'shop'
    name = 'product'
    type = ProdData
    fields = {
        'id':          {'type': 'int'},
        'title':       {},
        'category_id': {'type': 'int'},
    }
    joins = {
        'category': {'table': CatTable, 'field': 'category_id'}
    }


class PlainTable(sql.Table):
    name = 'plain'
    type = CatData
    fields = {
        'id':   {'type': 'int'},
        'name': {},
    }


# --- __str__ (LEFT JOIN clause) ---

def test_no_joins_str_is_empty():
    join = sql.Join(PlainTable)
    assert str(join) == ''


def test_with_join_str_contains_left_join():
    join = sql.Join(ProdTable)
    assert 'LEFT JOIN' in str(join)


def test_join_clause_references_joined_table():
    join = sql.Join(ProdTable)
    assert 'category' in str(join)


def test_join_clause_contains_on():
    join = sql.Join(ProdTable)
    assert ' ON ' in str(join)


# --- select() ---

def test_select_no_joins_only_main_table():
    join = sql.Join(PlainTable)
    result = join.select()
    assert 'plain."id"' in result
    assert 'plain."name"' in result


def test_select_with_join_includes_joined_fields():
    join = sql.Join(ProdTable)
    result = join.select()
    assert 'product."id"' in result
    assert 'category."id"' in result


# --- fields() ---

def test_fields_no_filter_no_search():
    join = sql.Join(PlainTable)
    assert join.fields() == '(1=1) AND (1=1)'


def test_fields_with_filter_contains_criteria():
    join = sql.Join(PlainTable, filter={'name': 'x'})
    result = join.fields()
    assert 'ILIKE' in result


def test_fields_with_joined_table_filter():
    join = sql.Join(ProdTable, filter={'category': {'name': 'x'}})
    result = join.fields()
    assert 'ILIKE' in result


# --- values() ---

def test_values_search_comes_before_filter():
    join = sql.Join(PlainTable, filter={'name': 'a'}, search={'name': 'b'})
    values = join.values()
    assert values[0] == '%b%'
    assert values[1] == '%a%'


# --- order() ---

def test_join_order_delegates_to_joined_table():
    join = sql.Join(ProdTable)
    result = join.order('category.name', 'asc')
    assert 'category' in result


def test_join_order_falls_back_to_main_table():
    join = sql.Join(ProdTable)
    result = join.order('title', 'asc')
    assert 'product' in result
