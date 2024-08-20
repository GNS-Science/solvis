import pytest

from solvis.fault_system_solution_helper import fault_participation_rate, section_participation_rate


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
