import sql


# --- select() function ---

def test_select_joins_strings():
    assert sql.select('a', 'b', 'c') == 'a,b,c'


def test_select_skips_empty_string():
    assert sql.select('a', '', 'c') == 'a,c'


def test_select_skips_whitespace_only():
    assert sql.select('  ', 'b') == 'b'


def test_select_single_item():
    assert sql.select('a') == 'a'


def test_select_all_empty_returns_empty():
    assert sql.select('', '  ') == ''


# --- Result class ---

def test_result_initial_state():
    r = sql.Result()
    assert r.total is None
    assert r.items == []


def test_result_add_appends_item():
    r = sql.Result()
    r.add('item1')
    assert r.items == ['item1']


def test_result_add_multiple():
    r = sql.Result()
    r.add('a')
    r.add('b')
    assert r.items == ['a', 'b']


def test_result_with_initial_total():
    r = sql.Result(total=5)
    assert r.total == 5


# --- debug() function ---

def test_debug_returns_query_unchanged():
    query, params = sql.debug('SELECT 1', [42])
    assert query == 'SELECT 1'


def test_debug_returns_params_unchanged():
    query, params = sql.debug('SELECT 1', [42])
    assert params == [42]


def test_debug_default_params_is_empty_list():
    query, params = sql.debug('SELECT 1')
    assert params == []
