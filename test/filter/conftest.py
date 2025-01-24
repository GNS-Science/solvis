import pytest

from solvis.filter.parent_fault_id_filter import FilterParentFaultIds
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.filter.subsection_id_filter import FilterSubsectionIds


def pytest_configure(config):
    # register your new marker to avoid warnings
    config.addinivalue_line("markers", "review: tests for review")


# @pytest.fixture(scope='package')
# def fss_model(composite_fixture):
#     yield composite_fixture._solutions['CRU'].model


@pytest.fixture(scope='package')
def fss_crustal(composite_fixture):
    yield composite_fixture._solutions['CRU']


@pytest.fixture(scope='package')
def filter_rupture_ids(crustal_solution_fixture):
    yield FilterRuptureIds(crustal_solution_fixture)


@pytest.fixture(scope='package')
def filter_parent_fault_ids(crustal_solution_fixture):
    yield FilterParentFaultIds(crustal_solution_fixture)


@pytest.fixture(scope='package')
def filter_subsection_ids(crustal_solution_fixture):
    yield FilterSubsectionIds(crustal_solution_fixture)
