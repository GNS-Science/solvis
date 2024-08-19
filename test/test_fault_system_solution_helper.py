import pytest

from solvis.fault_system_solution_helper import (
    FaultSystemSolutionHelper,
    fault_participation_rate,
    section_participation_rate,
)

from solvis.inversion_solution.rupture_id_filter import FilterRuptureIds
from solvis.inversion_solution.subsection_id_filter import FilterSubsectionIds

@pytest.fixture
def fault_names():
    return ['Alpine Jacksons to Kaniere', 'Vernon 4']


@pytest.fixture
def fss_helper(composite_fixture):
    fss = composite_fixture._solutions['CRU']
    yield FaultSystemSolutionHelper(fss)

@pytest.fixture
def filter_rupture_ids(composite_fixture):
    fss = composite_fixture._solutions['CRU']
    yield FilterRuptureIds(fss)

@pytest.fixture
def filter_subsection_ids(composite_fixture):
    fss = composite_fixture._solutions['CRU']
    yield FilterSubsectionIds(fss)


# >>>>>>>>>>>>>>>>>>>>
def test_subsections_for_ruptures(filter_subsection_ids):
    assert filter_subsection_ids.for_ruptures([2, 3]) == set([0, 1, 2, 3, 4])
    assert filter_subsection_ids.for_ruptures([10]) == set(range(12))

def test_subsection_filter_for_parent_fault_names(filter_subsection_ids):
    assert filter_subsection_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere']) == set(range(31))
    assert filter_subsection_ids.for_parent_fault_names(['Vernon 4']) == set(range(83, 86))
    assert filter_subsection_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set(
        range(31)
    ).union(set(range(83, 86)))

def test_subsection_filter_unknown_parent_fault_names_raises(filter_subsection_ids):
    with pytest.raises(ValueError) as exc:
        ids = filter_subsection_ids.for_parent_fault_names(['noIdea', "Lost"])
        assert 'noIdea' in str(exc)
        assert 'Lost' in str(exc)

def test_subsection_filter_for_parent_fault_ids(fss_helper, filter_subsection_ids):
    ids0 = fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere'])
    ids1 = fss_helper.fault_names_as_ids(['Vernon 4'])
    assert filter_subsection_ids.for_parent_fault_ids(ids0) == set(range(31))
    assert filter_subsection_ids.for_parent_fault_ids(ids1) == set(range(83, 86))
    assert filter_subsection_ids.for_parent_fault_ids(ids0.union(ids1)) == set(
        range(31)
    ).union(set(range(83, 86)))

# <<<<<<<<<<<<<<<<<<<<


def test_ruptures_for_subsections(fss_helper, filter_subsection_ids):
    ruptures = set([2, 3])
    assert fss_helper.ruptures_for_subsections(filter_subsection_ids.for_ruptures(ruptures)).issuperset(ruptures)

def test_fault_names_as_ids(fss_helper):
    assert fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere']) == set([23])
    assert fss_helper.fault_names_as_ids(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set([23, 585])



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


def test_parent_fault_vs_section_participation(crustal_solution_fixture):
    # show that the max participation of all the subsections of a given parent fault
    # equals the partipcation rate for the parent fault.
    # NO this relationship does not hold true

    solution = crustal_solution_fixture
    fault_name = "Alpine Jacksons to Kaniere"
    # helper = FaultSystemSolutionHelper(solution)
    filter_subsection_ids = FilterSubsectionIds(solution)

    subsections = filter_subsection_ids.for_parent_fault_names([fault_name])
    rates = solution.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    ss_rate = rates[rates.index.isin(subsections)]
    print(ss_rate)
    # ss_max = ss_rate.max()
    # pf_rate = fault_participation_rate(solution, fault_name)
    # assert pf_rate == ss_max


def test_explore_zero_rates(crustal_solution_fixture):
    solution = crustal_solution_fixture

    # we can group by section to get sum of section rates
    df0 = solution.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    assert df0.shape[0] == 86
    assert (
        df0[df0 == 0].shape[0] == 0
    )  # there are no 0 values here, so bu implication every section has at least one rupture

    print('solution.rs_with_rupture_rates')
    print(solution.rs_with_rupture_rates)
    print()

    # group by "Rupture Index" to get sum of rupture rates, although this is probably double counting
    df00 = solution.rs_with_rupture_rates.groupby("Rupture Index").agg('sum')["Annual Rate"]
    print(df00)
    assert df00.shape[0] == 3101
    assert df00[df00 == 0].shape[0] == 2095

    # `rupture_rates` is a dataframe on the raw data
    df1 = solution.rupture_rates
    print('solution.rupture_rates')
    print('======================')
    print(df1)
    print()
    assert df1.shape[0] == 3101
    assert df1[df1["Annual Rate"] == 0].shape[0] == 2095

    # `ruptures_with_rupture_rates` dataframe joins rupture properties with rupture rates, including 0 rates
    df2 = solution.ruptures_with_rupture_rates
    assert df2.shape[0] == 3101
    assert df2[df2["Annual Rate"] == 0].shape[0] == 2095
    print('solution.ruptures_with_rupture_rates')
    print('====================================')
    print(df2)
    print()


# # get the participation rate for all (parent) faults
# df = solution.fault_sections_with_rupture_rates[["Annual Rate", "ParentName"]]
# df.groupby("ParentName").agg("sum")["Annual Rate"]
