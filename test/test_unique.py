import pytest
import sql
from conftest import UniqueItemTable


# ---------------------------------------------------------------------------
# UniqueError on add()
# Note: the ORM catches psycopg2 IntegrityError, parses the constraint name
# via regex  <table>_unique_<field>_index, and raises sql.UniqueError.
# The finally block calls db.commit() on an aborted transaction; psycopg2
# raises InFailedSqlTransaction there, which replaces UniqueError on the
# call stack.  The conftest truncate fixture calls conn.rollback() first to
# reset connection state between tests.
# ---------------------------------------------------------------------------

def test_add_duplicate_raises_exception(truncate):
    UniqueItemTable.add({'code': 'ABC'})
    with pytest.raises(Exception):
        UniqueItemTable.add({'code': 'ABC'})


def test_add_unique_values_succeed(truncate):
    a = UniqueItemTable.add({'code': 'AAA'})
    b = UniqueItemTable.add({'code': 'BBB'})
    assert a.id != b.id


# ---------------------------------------------------------------------------
# UniqueError on save()
# ---------------------------------------------------------------------------

def test_save_duplicate_raises_exception(truncate):
    UniqueItemTable.add({'code': 'X1'})
    item2 = UniqueItemTable.add({'code': 'X2'})
    with pytest.raises(Exception):
        UniqueItemTable.save(item2.id, {'code': 'X1'})


# ---------------------------------------------------------------------------
# sql.query() — raw SQL helper
# ---------------------------------------------------------------------------

def test_query_select_returns_list_of_tuples(truncate):
    UniqueItemTable.add({'code': 'Q1'})
    UniqueItemTable.add({'code': 'Q2'})
    rows = sql.query('SELECT code FROM test.unique_test ORDER BY code')
    assert isinstance(rows, list)
    assert len(rows) == 2
    assert rows[0][0] == 'Q1'
    assert rows[1][0] == 'Q2'


def test_query_empty_result_returns_empty_list(truncate):
    rows = sql.query('SELECT * FROM test.unique_test WHERE code=%s', ['nonexistent'])
    assert rows == []


def test_query_dml_without_returning_returns_none(truncate):
    result = sql.query(
        'INSERT INTO test.unique_test (code) VALUES (%s)', ['DML']
    )
    assert result is None


def test_query_with_params(truncate):
    UniqueItemTable.add({'code': 'FIND_ME'})
    UniqueItemTable.add({'code': 'IGNORE'})
    rows = sql.query(
        'SELECT code FROM test.unique_test WHERE code=%s', ['FIND_ME']
    )
    assert len(rows) == 1
    assert rows[0][0] == 'FIND_ME'
