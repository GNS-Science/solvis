import pytest

from solvis.filter.parent_fault_id_filter import FilterParentFaultIds
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.filter.subsection_id_filter import FilterSubsectionIds


def pytest_configure(config):
    # register your new marker to avoid warnings
    config.addinivalue_line("markers", "review: tests for review")


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
