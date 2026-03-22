import sql


class MockTable(sql.Table):
    name = 'mock'
    type = object
    fields = {
        'id':   {'type': 'int'},
        'name': {},
        'desc': {},
    }


def test_offset_single_registers_position():
    row = sql.Row()
    row.offset('key', 1)
    row.data((10, 20, 30))
    assert row.get('key') == 10


def test_offset_advances_position_sequentially():
    row = sql.Row()
    row.offset('first', 1)
    row.offset('second', 1)
    row.data(('a', 'b'))
    assert row.get('first') == 'a'
    assert row.get('second') == 'b'


def test_offset_multi_count_returns_slice():
    row = sql.Row()
    row.offset('block', 3)
    row.data(('x', 'y', 'z'))
    assert row.get('block') == ('x', 'y', 'z')


def test_offset_using_table_calls_table_offset():
    row = sql.Row()
    row.offset('tbl', MockTable)
    row.data(('a', 'b', 'c'))
    # MockTable has 3 selectable fields: id, name, desc
    assert row.get('tbl') == ('a', 'b', 'c')


def test_call_is_same_as_get():
    row = sql.Row()
    row.offset('k', 1)
    row.data((42,))
    assert row('k') == row.get('k') == 42


def test_mixed_offsets():
    row = sql.Row()
    row.offset('single', 1)
    row.offset('multi', 2)
    row.data((1, 2, 3))
    assert row.get('single') == 1
    assert row.get('multi') == (2, 3)
