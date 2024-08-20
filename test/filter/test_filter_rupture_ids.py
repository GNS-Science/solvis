import pytest

from solvis.inversion_solution.parent_fault_id_filter import FilterParentFaultIds
from solvis.inversion_solution.rupture_id_filter import FilterRuptureIds
from solvis.inversion_solution.subsection_id_filter import FilterSubsectionIds


@pytest.fixture
def fss(composite_fixture):
    yield composite_fixture._solutions['CRU']


@pytest.fixture
def filter_rupture_ids(fss):
    yield FilterRuptureIds(fss)


@pytest.fixture
def filter_parent_fault_ids(fss):
    yield FilterParentFaultIds(fss)


@pytest.fixture
def filter_subsection_ids(fss):
    yield FilterSubsectionIds(fss)


def test_ruptures_for_subsections(filter_rupture_ids, filter_subsection_ids):
    ruptures = set([2, 3])
    assert filter_rupture_ids.for_subsection_ids(filter_subsection_ids.for_rupture_ids(ruptures)).issuperset(ruptures)


def test_ruptures_for_parent_fault_ids(filter_rupture_ids, filter_parent_fault_ids):
    fault_ids = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4'])
    assert filter_rupture_ids.for_parent_fault_ids(fault_ids).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )


def test_ruptures_for_parent_fault_names(filter_rupture_ids):
    assert filter_rupture_ids.for_parent_fault_names(['Vernon 4']).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )
