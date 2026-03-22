import pytest
import sql
from conftest import UserTable, GroupTable


def _add_user(username, status='active', fullname=None, group_id=None):
    return UserTable.add({
        'username': username,
        'fullname': fullname or username.title(),
        'status': status,
        'group_id': group_id,
    })


# ---------------------------------------------------------------------------
# all()
# ---------------------------------------------------------------------------

def test_all_returns_list(truncate):
    _add_user('john')
    _add_user('jane')
    result = UserTable.all()
    assert isinstance(result, list)
    assert len(result) == 2


def test_all_empty_returns_empty_list(truncate):
    assert UserTable.all() == []


def test_all_with_filter(truncate):
    _add_user('john', status='active')
    _add_user('jane', status='inactive')
    result = UserTable.all(filter={'status': 'inactive'})
    assert len(result) == 1
    assert result[0].username == 'jane'


def test_all_with_search(truncate):
    _add_user('john', fullname='John Smith')
    _add_user('jane', fullname='Jane Doe')
    result = UserTable.all(search={'fullname': 'Smith'})
    assert len(result) == 1
    assert result[0].username == 'john'


def test_all_with_limit(truncate):
    for i in range(5):
        _add_user(f'user{i}')
    result = UserTable.all(limit=3)
    assert len(result) == 3


def test_all_with_order_asc(truncate):
    _add_user('b_user')
    _add_user('a_user')
    result = UserTable.all(order={'field': 'username', 'method': 'asc'})
    assert result[0].username == 'a_user'


def test_all_with_order_desc(truncate):
    _add_user('a_user')
    _add_user('b_user')
    result = UserTable.all(order={'field': 'username', 'method': 'desc'})
    assert result[0].username == 'b_user'


def test_all_with_join(truncate):
    group = GroupTable.add({'name': 'admins'})
    _add_user('john', group_id=group.id)
    result = UserTable.all()
    assert result[0].group is not None
    assert result[0].group.name == 'admins'


def test_all_combined_filter_and_search(truncate):
    _add_user('john', fullname='John Smith', status='active')
    _add_user('jane', fullname='Jane Smith', status='inactive')
    _add_user('bob',  fullname='Bob Jones',  status='active')
    # search OR across fullname, filter AND on status
    result = UserTable.all(filter={'status': 'active'}, search={'fullname': 'Smith'})
    assert len(result) == 1
    assert result[0].username == 'john'


# ---------------------------------------------------------------------------
# filter()
# ---------------------------------------------------------------------------

def test_filter_returns_result_object(truncate):
    _add_user('john')
    result = UserTable.filter()
    assert hasattr(result, 'total')
    assert hasattr(result, 'items')


def test_filter_total_and_items(truncate):
    for i in range(5):
        _add_user(f'user{i}')
    result = UserTable.filter(limit=2)
    assert result.total == 5
    assert len(result.items) == 2


def test_filter_empty_total_is_zero(truncate):
    result = UserTable.filter()
    assert result.total == 0
    assert result.items == []


def test_filter_pagination_no_overlap(truncate):
    for i in range(10):
        _add_user(f'user{i:02d}')
    page1 = UserTable.filter(page=1, limit=4)
    page2 = UserTable.filter(page=2, limit=4)
    ids1 = {u.id for u in page1.items}
    ids2 = {u.id for u in page2.items}
    assert ids1.isdisjoint(ids2)


def test_filter_page2_offset(truncate):
    for i in range(6):
        _add_user(f'user{i:02d}')
    page1 = UserTable.filter(page=1, limit=3)
    page2 = UserTable.filter(page=2, limit=3)
    assert len(page1.items) == 3
    assert len(page2.items) == 3


def test_filter_limit_capped_at_100(truncate):
    for i in range(5):
        _add_user(f'user{i}')
    result = UserTable.filter(limit=200)
    assert len(result.items) == 5   # capped: min(200,100)=100, only 5 exist


def test_filter_with_filter_param(truncate):
    _add_user('john', status='active')
    _add_user('jane', status='inactive')
    result = UserTable.filter(filter={'status': 'active'})
    assert result.total == 1
    assert result.items[0].username == 'john'


def test_filter_with_search_param(truncate):
    _add_user('john', fullname='John Smith')
    _add_user('jane', fullname='Jane Doe')
    result = UserTable.filter(search={'fullname': 'Smith'})
    assert result.total == 1


def test_filter_with_order(truncate):
    _add_user('b_user')
    _add_user('a_user')
    result = UserTable.filter(order={'field': 'username', 'method': 'asc'})
    assert result.items[0].username == 'a_user'


def test_filter_with_join(truncate):
    group = GroupTable.add({'name': 'mods'})
    _add_user('john', group_id=group.id)
    result = UserTable.filter()
    assert result.total == 1
    assert result.items[0].group.name == 'mods'


def test_filter_total_reflects_full_count_not_page_size(truncate):
    for i in range(7):
        _add_user(f'user{i}')
    result = UserTable.filter(page=1, limit=3)
    assert result.total == 7        # window COUNT, not just this page
    assert len(result.items) == 3
