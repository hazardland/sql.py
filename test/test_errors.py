import sql
import pytest


def test_error_code():
    e = sql.Error('my_code')
    assert e.code == 'my_code'


def test_error_message_string():
    e = sql.Error('code', 'some message')
    assert e.message == 'some message'


def test_error_message_from_list():
    e = sql.Error('code', ['part1', 'part2'])
    assert e.message == 'part1 part2'


def test_error_field():
    e = sql.Error('code', 'msg', 'myfield')
    assert e.field == 'myfield'


def test_missing_config():
    e = sql.MissingConfig()
    assert e.code == 'missing_config'


def test_missing_input():
    e = sql.MissingInput()
    assert e.code == 'missing_input'


def test_missing_field():
    e = sql.MissingField()
    assert e.code == 'missing_field'


def test_unknown_field():
    e = sql.UnknownField('badfield')
    assert e.code == 'unknown_field'
    assert e.field == 'badfield'


def test_unique_error():
    e = sql.UniqueError('email')
    assert e.code == 'unique_error'
    assert e.field == 'email'


def test_invalid_value():
    e = sql.InvalidValue('bad value', 'fieldname')
    assert e.code == 'invalid_value'
    assert e.field == 'fieldname'


def test_invalid_date_is_invalid_value():
    e = sql.InvalidDate('bad date', 'created')
    assert isinstance(e, sql.InvalidValue)


def test_invalid_float_is_invalid_value():
    e = sql.InvalidFloat('bad float', 'price')
    assert isinstance(e, sql.InvalidValue)
