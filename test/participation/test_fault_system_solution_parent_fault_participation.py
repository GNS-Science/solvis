import pytest

from solvis.filter import FilterParentFaultIds, FilterRuptureIds, FilterSubsectionIds

RATE_COLUMN = 'rate_weighted_mean'  # 'Annual Rate'

# TODO: PROBLEM: our test fixture only has ruptures for 1 parent fault
parent_fault_rates = [
    # ("Vernon 4", 0.0013733797),
    ("Alpine Jacksons to Kaniere", 0.00262068771),
    # ("Fowlers", 0.0035734656),
    # ("Barefell", 0.0018325159),
]


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate(crustal_small_fss_fixture, fault_name, expected_rate):

    # get the participation rate for a (parent) fault
    solution = crustal_small_fss_fixture
    model = solution.model

    # # calc rate by hand ...
    df0 = model.rs_with_rupture_rates
    df1 = df0.join(model.fault_sections[['ParentID', 'ParentName']], on='section')

    print(df1['ParentName'].unique())
    df1 = df1[df1['ParentName'] == fault_name]
    pfid = df1['ParentID'].unique()[0]

    print(f'parent_fault id: {pfid}')

    df2 = df1[["ParentID", "section", RATE_COLUMN]]

    parent_rate = df2.groupby(["ParentID", "Rupture Index"]).agg('first').groupby("ParentID").agg('sum')[RATE_COLUMN]
    print(parent_rate)
    assert pytest.approx(parent_rate) == expected_rate  # the original test value

    rates = model.fault_participation_rates([fault_name])
    assert pytest.approx(rates.participation_rate.tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate_conditional(crustal_small_fss_fixture, fault_name, expected_rate):

    # get the participation rate for a (parent) fault
    solution = crustal_small_fss_fixture
    model = solution.model

    rids = list(
        FilterRuptureIds(model).for_parent_fault_ids(
            FilterParentFaultIds(model).for_parent_fault_names([fault_name])
        )
    )
    assert len(rids) > 1

    print(rids)
    rates = model.fault_participation_rates([fault_name], rupture_ids=rids)
    assert pytest.approx(rates.participation_rate.tolist()[0]) == expected_rate

    rids_subset = rids[: int(len(rids) / 2)]
    print(rids_subset)
    rates = model.fault_participation_rates([fault_name], rupture_ids=rids_subset)
    assert rates.participation_rate.tolist()[0] < expected_rate


@pytest.mark.parametrize("fault_name, expected_rate", parent_fault_rates)
def test_parent_fault_participation_rate_vs_section_rates(crustal_small_fss_fixture, fault_name, expected_rate):
    solution = crustal_small_fss_fixture
    model = solution.model
    fault_rates = model.fault_participation_rates([fault_name])
    assert pytest.approx(fault_rates.participation_rate.tolist()[0]) == expected_rate
    print(fault_rates)
    rids = list(FilterRuptureIds(model).for_parent_fault_names([fault_name]))

    subsection_ids = FilterSubsectionIds(model).for_parent_fault_names([fault_name]).for_rupture_ids(rids)
    print(f'subsection_ids {list(subsection_ids)}')

    section_rates = model.section_participation_rates(subsection_ids)
    print(section_rates)

    assert (
        sum(section_rates.participation_rate) >= expected_rate
    ), "sum(section rates) should not be less than parent rate"
    assert max(section_rates.participation_rate) <= expected_rate, "max(section rates) should not exceed parent rate"
    assert (
        sum(section_rates.participation_rate) / len(section_rates.participation_rate) <= expected_rate
    ), "mean(section rates) should not exceed parent rate"
