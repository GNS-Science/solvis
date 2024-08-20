import pytest

from solvis.inversion_solution.parent_fault_id_filter import FilterParentFaultIds
from solvis.inversion_solution.subsection_id_filter import FilterSubsectionIds

# from solvis.fault_system_solution_helper import (
#     fault_participation_rate,
#     section_participation_rate,
# )


@pytest.fixture
def fss(composite_fixture):
    yield composite_fixture._solutions['CRU']


@pytest.fixture
def filter_subsection_ids(fss):
    yield FilterSubsectionIds(fss)


@pytest.fixture
def filter_parent_fault_ids(fss):
    yield FilterParentFaultIds(fss)


def test_subsections_for_ruptures(filter_subsection_ids):
    assert filter_subsection_ids.for_rupture_ids([2, 3]) == set([0, 1, 2, 3, 4])
    assert filter_subsection_ids.for_rupture_ids([10]) == set(range(12))


def test_subsection_filter_for_parent_fault_names(filter_subsection_ids):
    assert filter_subsection_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere']) == set(range(31))
    assert filter_subsection_ids.for_parent_fault_names(['Vernon 4']) == set(range(83, 86))
    assert filter_subsection_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set(
        range(31)
    ).union(set(range(83, 86)))


def test_subsection_filter_unknown_parent_fault_names_raises(filter_subsection_ids):
    with pytest.raises(ValueError) as exc:
        filter_subsection_ids.for_parent_fault_names(['noIdea', "Lost"])
        assert 'noIdea' in str(exc)
        assert 'Lost' in str(exc)


def test_subsection_filter_for_parent_fault_ids(filter_parent_fault_ids, filter_subsection_ids):
    ids0 = filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere'])
    ids1 = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4'])
    assert filter_subsection_ids.for_parent_fault_ids(ids0) == set(range(31))
    assert filter_subsection_ids.for_parent_fault_ids(ids1) == set(range(83, 86))
    assert filter_subsection_ids.for_parent_fault_ids(ids0.union(ids1)) == set(range(31)).union(set(range(83, 86)))
