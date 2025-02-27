from solvis.solution import named_fault


def test_named_fault_table():
    df0 = named_fault.named_fault_table()
    assert df0.loc["Ostler"].parent_fault_ids == [334, 335]
    assert df0.loc["Wairarapa"].parent_fault_ids == [506, 507, 508]
    assert df0.loc["Alpine: Jacksons to Kaniere"].parent_fault_ids == [13]


def test_get_named_fault_for_parent():
    assert named_fault.get_named_fault_for_parent(334) == 'Ostler'
    assert named_fault.get_named_fault_for_parent(507) == 'Wairarapa'


def test_named_fault_for_parent_ids_table_unknown():
    assert named_fault.get_named_fault_for_parent(10507) is None


def test_named_fault_for_parent_ids_table():
    df0 = named_fault.named_fault_for_parent_ids_table()
    assert df0.loc[334].named_fault_name == 'Ostler'
    assert df0.loc[335].named_fault_name == 'Ostler'
    assert df0.loc[507].named_fault_name == 'Wairarapa'
