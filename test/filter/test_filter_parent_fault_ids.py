import pytest

from solvis.inversion_solution.parent_fault_id_filter import FilterParentFaultIds, parent_fault_name_id_mapping


@pytest.fixture
def fss(composite_fixture):
    yield composite_fixture._solutions['CRU']


@pytest.fixture
def filter_parent_fault_ids(fss):
    yield FilterParentFaultIds(fss)


def test_fault_names_as_ids(filter_parent_fault_ids):
    assert filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere']) == set([23])
    assert filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set([23, 585])


def test_parent_fault_ids(filter_parent_fault_ids):
    assert filter_parent_fault_ids.for_parent_fault_names(['Vernon 4']) == set([585])


def test_parent_fault_name_id_mapping(filter_parent_fault_ids, fss):
    parent_ids = list(filter_parent_fault_ids.for_parent_fault_names(['Vernon 4']))
    mapping = list(parent_fault_name_id_mapping(fss, parent_ids))

    print(parent_ids)
    print(mapping)
    assert len(mapping) == 1
    assert mapping[0].id == 585
    assert mapping[0].parent_fault_name == 'Vernon 4'
