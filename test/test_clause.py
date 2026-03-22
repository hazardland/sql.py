import sql


def test_fields_default_pattern():
    clause = sql.Clause(['"col1"', '"col2"'], ['v1', 'v2'])
    assert clause.fields() == '"col1", "col2"'


def test_fields_custom_pattern():
    # Used for INSERT VALUES (%s, %s)
    clause = sql.Clause(['"col1"', '"col2"'], ['v1', 'v2'])
    assert clause.fields('%s') == '%s, %s'


def test_fields_update_pattern():
    # Used for UPDATE SET col=%s
    clause = sql.Clause(['"col1"', '"col2"'], ['v1', 'v2'], pattern='{name}=%s')
    assert clause.fields() == '"col1"=%s, "col2"=%s'


def test_fields_custom_separator():
    clause = sql.Clause(['crit1', 'crit2'], ['v1', 'v2'], separator=' AND ', empty='1=1')
    assert clause.fields() == 'crit1 AND crit2'


def test_fields_empty_returns_empty_string():
    clause = sql.Clause([], [], empty='')
    assert clause.fields() == ''


def test_fields_empty_returns_custom_empty():
    # WHERE clauses use '1=1' as fallback
    clause = sql.Clause([], [], empty='1=1')
    assert clause.fields() == '1=1'


def test_values_returns_list():
    clause = sql.Clause(['"col1"'], ['v1'])
    assert clause.values() == ['v1']


def test_values_with_id_appends():
    clause = sql.Clause(['"col1"'], ['v1'])
    assert clause.values(id=5) == ['v1', 5]


def test_values_with_id_does_not_mutate_original():
    clause = sql.Clause(['"col1"'], ['v1'])
    clause.values(id=5)
    assert clause.values() == ['v1']


def test_extract():
    clause = sql.Clause(['"col1"'], ['v1'])
    fields, values = clause.exctract()
    assert fields == ['"col1"']
    assert values == ['v1']
