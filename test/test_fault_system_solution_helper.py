import pytest

from solvis.fault_system_solution_helper import (
    FaultSystemSolutionHelper,
    fault_participation_rate,
    section_participation_rate,
)


@pytest.fixture
def fault_names():
    return ['Alpine Jacksons to Kaniere', 'Vernon 4']


@pytest.fixture
def fss_helper(composite_fixture):
    fss = composite_fixture._solutions['CRU']
    yield FaultSystemSolutionHelper(fss)


def test_subsections_for_ruptures(fss_helper):
    assert fss_helper.subsections_for_ruptures([2, 3]) == set([0, 1, 2, 3, 4])
    assert fss_helper.subsections_for_ruptures([10]) == set(range(12))


def test_ruptures_for_subsections(fss_helper):
    ruptures = set([2, 3])
    assert fss_helper.ruptures_for_subsections(fss_helper.subsections_for_ruptures(ruptures)).issuperset(ruptures)


def test_fault_names_as_ids(fss_helper):
    assert fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere']) == set([23])
    assert fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set([23, 585])


def test_subsections_for_faults(fss_helper):
    fault_ids = fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere'])
    assert fss_helper.subsections_for_faults(fault_ids) == set(range(31))


def test_subsections_for_parent_fault_names(fss_helper):
    assert fss_helper.subsections_for_parent_fault_names(['Alpine Jacksons to Kaniere']) == set(range(31))
    assert fss_helper.subsections_for_parent_fault_names(['Vernon 4']) == set(range(83, 86))
    assert fss_helper.subsections_for_parent_fault_names(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set(
        range(31)
    ).union(set(range(83, 86)))


def test_ruptures_for_faults(fss_helper):
    fault_ids = fss_helper.fault_names_as_ids(['Vernon 4'])
    assert fss_helper.ruptures_for_faults(fault_ids).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )


def test_ruptures_for_parent_fault_names(fss_helper):
    assert fss_helper.ruptures_for_parent_fault_names(['Vernon 4']).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )


def test_parent_fault_ids(fss_helper):
    assert fss_helper.fault_names_as_ids(['Vernon 4']) == set([585])


def test_parent_fault_name_id_mapping(fss_helper):
    parent_ids = list(fss_helper.fault_names_as_ids(['Vernon 4']))
    mapping = list(fss_helper.parent_fault_name_id_mapping(parent_ids))

    print(parent_ids)
    print(mapping)
    assert len(mapping) == 1
    assert mapping[0].id == 585
    assert mapping[0].parent_fault_name == 'Vernon 4'


def test_section_participation_rate(crustal_solution_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_solution_fixture
    rate = section_participation_rate(solution, sec_id)
    print(f"participation rate for section {sec_id}: {rate} /yr")
    assert pytest.approx(rate) == 0.0099396


def test_solution_participation_rate(crustal_solution_fixture):
    # get the participation rate of all (sub)sections
    solution = crustal_solution_fixture
    section_rates = solution.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    print("section participation rates")
    print(section_rates)
    assert pytest.approx(section_rates[5]) == 0.0099396


def test_parent_fault_participation_rate(crustal_solution_fixture):
    # get the participation rate for a (parent) fault
    fault_name = "Alpine Jacksons to Kaniere"
    solution = crustal_solution_fixture
    rate = fault_participation_rate(solution, fault_name)
    print(f"participation rate for fault {fault_name}: {rate} /yr")
    assert pytest.approx(rate) == 0.0158445


# # get the participation rate for all (parent) faults
# df = solution.fault_sections_with_rupture_rates[["Annual Rate", "ParentName"]]
# df.groupby("ParentName").agg("sum")["Annual Rate"]
