import pytest


@pytest.mark.skip("This is not in doing much yet")
def test_explore_zero_rates(crustal_solution_fixture):
    solution = crustal_solution_fixture

    # we can group by section to get sum of section rates
    df0 = solution.model.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    assert df0.shape[0] == 86
    assert (
        df0[df0 == 0].shape[0] == 0
    )  # there are no 0 values here, so bu implication every section has at least one rupture

    print('solution.model.rs_with_rupture_rates')
    print(solution.model.rs_with_rupture_rates)
    print()

    # group by "Rupture Index" to get sum of rupture rates, although this is probably double counting
    df00 = solution.model.rs_with_rupture_rates.groupby("Rupture Index").agg('sum')["Annual Rate"]
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
    df2 = solution.model.ruptures_with_rupture_rates
    assert df2.shape[0] == 3101
    assert df2[df2["Annual Rate"] == 0].shape[0] == 2095
    print('solution.model.ruptures_with_rupture_rates')
    print('====================================')
    print(df2)
    print()


# # get the participation rate for all (parent) faults
# df = solution.fault_sections_with_rupture_rates[["Annual Rate", "ParentName"]]
# df.groupby("ParentName").agg("sum")["Annual Rate"]
