import pytest

from solvis.fault_system_solution_helper import fault_participation_rates, section_participation_rates

# from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.filter import FilterRuptureIds, FilterSubsectionIds


def test_section_participation_rate(crustal_solution_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_solution_fixture
    rates = section_participation_rates(solution, [sec_id])
    print(f"participation rate for section {sec_id}: {rates['Annual Rate'].tolist()[0]} /yr")
    assert pytest.approx(rates['Annual Rate'].tolist()[0]) == 0.0099396


def test_solution_participation_rate(crustal_solution_fixture):
    # get the participation rate of all (sub)sections
    solution = crustal_solution_fixture
    section_rates = solution.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    print("section participation rates")
    print(section_rates)
    assert pytest.approx(section_rates[5]) == 0.0099396


section_fault_rates = [
    ("Alpine Jacksons to Kaniere", 0, 0.009868714),
    ("Alpine Jacksons to Kaniere", 13, 0.008527031),
    ("Barefell", 64, 0.001748257),
    ("Barefell", 62, 0.0018325159),
]


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates(crustal_solution_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_solution_fixture

    # subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names([fault_name])
    # srdf = section_participation_rates(solution, subsection_ids)
    # print(srdf)

    # section_rate = srdf[srdf.index == subsection_id].agg('sum')['Annual Rate']
    # print(section_rate)
    # assert pytest.approx(section_rate) == expected_rate
    srdf = section_participation_rates(solution, [subsection_id])
    # print(srdf)
    assert pytest.approx(srdf['Annual Rate'].tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates_conditional(crustal_solution_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_solution_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    print(rids)

    rids_subset = rids[: int(len(rids) / 2)]
    print(rids_subset)

    srdf = section_participation_rates(solution, [subsection_id], rids_subset)
    print(srdf)
    assert srdf['Annual Rate'].tolist()[0] - 1e-10 < expected_rate


parent_fault_rates = [
    ("Alpine Jacksons to Kaniere", 0.0158445),
    ("Vernon 4", 0.0013733797),
    ("Fowlers", 0.0035734656),
    ("Barefell", 0.0018325159),
]


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate_vs_section_rates(crustal_solution_fixture, fault_name, expected_rate):
    solution = crustal_solution_fixture
    fault_rates = fault_participation_rates(solution, [fault_name])
    assert pytest.approx(fault_rates['Annual Rate'].tolist()[0]) == expected_rate

    subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names([fault_name])
    section_rates = section_participation_rates(solution, subsection_ids)
    print(section_rates)
    assert sum(section_rates['Annual Rate']) >= expected_rate, "sum(section rates) should not be less than parent rate"
    assert max(section_rates['Annual Rate']) <= expected_rate, "max(section rates) should not exceed parent rate"
    assert (
        sum(section_rates['Annual Rate']) / len(section_rates['Annual Rate']) <= expected_rate
    ), "mean(section rates) should not exceed parent rate"


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate(crustal_solution_fixture, fault_name, expected_rate):

    """
    Notes:
     - this fixture is InversionSolution - so no weights and rate col is
       ['Annual Rate']
    """
    # get the participation rate for a (parent) fault
    solution = crustal_solution_fixture

    # # calc rate by hand ...
    # df0 = solution.rs_with_rupture_rates
    # df1 = df0.join(solution.fault_sections[['ParentID','ParentName']], on='section')
    # df1 = df1[df1['ParentName']== fault_name]
    # pfid = df1['ParentID'].unique()[0]

    # print(f'parent_fault id: {pfid}')

    # df2 = df1[["Rupture Index", "ParentID", "section", "Annual Rate"]]
    # print(df2[df2["Annual Rate"]>0])

    # parent_rate = df1.groupby(["ParentID", "Rupture Index"]).agg('first')\
    #     .groupby("ParentID").agg('sum')['Annual Rate']
    # print(parent_rate)
    # assert pytest.approx(parent_rate) == expected_rate  # the original test value

    rates = fault_participation_rates(solution, [fault_name])
    assert pytest.approx(rates['Annual Rate'].tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate_conditional(crustal_solution_fixture, fault_name, expected_rate):

    """
    Notes:
     - this fixture is InversionSolution - so no weights and rate col is
       ['Annual Rate']
    """
    # get the participation rate for a (parent) fault
    solution = crustal_solution_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    assert len(rids) > 1

    print(rids)
    rates = fault_participation_rates(solution, [fault_name], rupture_ids=rids)
    assert pytest.approx(rates['Annual Rate'].tolist()[0]) == expected_rate

    rids_subset = rids[: int(len(rids) / 2)]
    print(rids_subset)
    rates = fault_participation_rates(solution, [fault_name], rupture_ids=rids_subset)
    assert rates['Annual Rate'].tolist()[0] < expected_rate


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
