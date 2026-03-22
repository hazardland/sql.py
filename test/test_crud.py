import pytest
from conftest import UserTable, GroupTable


# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------

def test_add_returns_object(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John Doe', 'status': 'active'})
    assert user is not None


def test_add_returns_correct_values(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John Doe', 'status': 'active'})
    assert user.username == 'john'
    assert user.fullname == 'John Doe'


def test_add_generates_id(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John Doe', 'status': 'active'})
    assert user.id is not None
    assert isinstance(user.id, int)


def test_add_with_join_sets_nested_object(truncate):
    group = GroupTable.add({'name': 'admins'})
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active', 'group_id': group.id})
    assert user.group is not None
    assert user.group.name == 'admins'


def test_add_without_join_nested_object_has_none_fields(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    assert user.group is not None    # group object exists but all fields are None
    assert user.group.id is None


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------

def test_get_returns_inserted_object(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John Doe', 'status': 'active'})
    fetched = UserTable.get(user.id)
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.username == 'john'


def test_get_returns_none_when_not_found(truncate):
    result = UserTable.get(99999)
    assert result is None


def test_get_with_matching_filter(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    fetched = UserTable.get(user.id, {'status': 'active'})
    assert fetched is not None


def test_get_with_non_matching_filter_returns_none(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    fetched = UserTable.get(user.id, {'status': 'inactive'})
    assert fetched is None


def test_get_with_join_populates_nested_object(truncate):
    group = GroupTable.add({'name': 'editors'})
    user = UserTable.add({'username': 'jane', 'fullname': 'Jane', 'status': 'active', 'group_id': group.id})
    fetched = UserTable.get(user.id)
    assert fetched.group is not None
    assert fetched.group.name == 'editors'


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------

def test_save_returns_updated_object(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    updated = UserTable.save(user.id, {'username': 'jane', 'fullname': 'Jane'})
    assert updated is not None
    assert updated.username == 'jane'
    assert updated.fullname == 'Jane'


def test_save_persists_to_db(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    UserTable.save(user.id, {'username': 'jane'})
    fetched = UserTable.get(user.id)
    assert fetched.username == 'jane'


def test_save_returns_none_when_id_not_found(truncate):
    result = UserTable.save(99999, {'username': 'ghost'})
    assert result is None


def test_save_with_matching_filter(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    result = UserTable.save(user.id, {'fullname': 'Updated'}, {'status': 'active'})
    assert result is not None
    assert result.fullname == 'Updated'


def test_save_with_non_matching_filter_returns_none(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    result = UserTable.save(user.id, {'fullname': 'Updated'}, {'status': 'inactive'})
    assert result is None


def test_save_does_not_change_unincluded_fields(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    UserTable.save(user.id, {'fullname': 'New Name'})
    fetched = UserTable.get(user.id)
    assert fetched.username == 'john'    # untouched


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

def test_delete_returns_true_on_success(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    assert UserTable.delete(user.id) is True


def test_delete_removes_record(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    UserTable.delete(user.id)
    assert UserTable.get(user.id) is None


def test_delete_returns_false_when_not_found(truncate):
    assert UserTable.delete(99999) is False


def test_delete_with_matching_filter(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    assert UserTable.delete(user.id, {'status': 'active'}) is True
    assert UserTable.get(user.id) is None


def test_delete_with_non_matching_filter_leaves_record(truncate):
    user = UserTable.add({'username': 'john', 'fullname': 'John', 'status': 'active'})
    result = UserTable.delete(user.id, {'status': 'inactive'})
    assert result is False
    assert UserTable.get(user.id) is not None
