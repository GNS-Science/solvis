import pytest

from solvis.filter import FilterRuptureIds, FilterSubsectionIds
from solvis.solution import SolutionParticipation

RATE_COLUMN = 'rate_weighted_mean'  # 'Annual Rate'


def test_section_participation_rate(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_small_fss_fixture
    rates = SolutionParticipation(solution).section_participation_rates([sec_id])
    print(rates)
    assert pytest.approx(rates.participation_rate.tolist()[0]) == 0.0026206877  # 0.0099396


def test_section_participation_rate_default_spot_check(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_small_fss_fixture
    rates = SolutionParticipation(solution).section_participation_rates()
    # print(f"participation rate for section {sec_id}: {rates['Annual Rate'].tolist()[0]} /yr")
    # rates=r
    assert pytest.approx(rates[rates.index == sec_id].participation_rate.tolist()[0]) == 0.0026206877


def test_section_participation_rate_default_all_sections(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    solution = crustal_small_fss_fixture
    rates = SolutionParticipation(solution).section_participation_rates()

    section_rates = solution.model.rs_with_rupture_rates.groupby("section").agg('sum')[RATE_COLUMN]

    assert section_rates.all() == rates.participation_rate.all()

    # print(sum(section_rates))
    # assert pytest.approx(sum(section_rates)) == 0.023329016054049134
    # df0 = model.rs_with_composite_rupture_rates

    # use this to check what 'good' expected result looks like
    # print(df0.columns)
    # print(df0[['section', 'Rupture Index', 'weight', 'Annual Rate', 'weighted_rate']] )
    # assert 0


def test_sum_vs_weighted_mean_all_sections(crustal_small_fss_fixture):

    solution = crustal_small_fss_fixture
    rates = SolutionParticipation(solution).section_participation_rates()
    print("rates")
    print(rates)

    df0 = solution.model.rs_with_rupture_rates  # property

    weighted_mean_rates = df0.pivot_table(values="rate_weighted_mean", index=['section'], aggfunc='sum')

    print("weighted_mean_rates")
    print(weighted_mean_rates)

    for section in rates.index:
        assert pytest.approx(rates.participation_rate[section]) == weighted_mean_rates['rate_weighted_mean'][section]


section_fault_rates = [
    ("Alpine Jacksons to Kaniere", 0, 0.0026206877),
    ("Alpine Jacksons to Kaniere", 10, 0.000590668118),
]


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_sum_vs_weighted_mean_conditional(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):

    solution = crustal_small_fss_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    print(rids)

    rids_subset = rids[2:]
    print(rids_subset)

    srdf = SolutionParticipation(solution).section_participation_rates([subsection_id], rids_subset)
    print("srdf")
    print(srdf)

    df0 = solution.model.rs_with_rupture_rates  # property
    df0 = df0[df0["section"] == subsection_id]
    df0 = df0[df0["Rupture Index"].isin(rids_subset)]

    weighted_mean_rates = df0.pivot_table(values="rate_weighted_mean", index=['section'], aggfunc='sum')

    print("weighted_mean_rates")
    print(weighted_mean_rates)
    assert pytest.approx(srdf.participation_rate) == weighted_mean_rates.rate_weighted_mean


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_small_fss_fixture

    subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names([fault_name])
    srdf = SolutionParticipation(solution).section_participation_rates(subsection_ids)
    print(srdf)

    section_rate = srdf[srdf.index == subsection_id].agg('sum').participation_rate
    # print(section_rate)

    assert pytest.approx(section_rate) == expected_rate

    srdf2 = SolutionParticipation(solution).section_participation_rates([subsection_id])
    print(srdf2)
    assert pytest.approx(srdf2.participation_rate.tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates_conditional(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_small_fss_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    print(rids)

    rids_subset = rids[2:]
    print(rids_subset)

    srdf = SolutionParticipation(solution).section_participation_rates([subsection_id], rids_subset)
    print(srdf)
    assert srdf.participation_rate.tolist()[0] - 1e-10 < expected_rate


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates_detail(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_small_fss_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    rids_subset = rids[2:]

    print(rids_subset)

    df0 = solution.model.rs_with_rupture_rates
    df1 = df0[df0['Rupture Index'].isin(rids_subset)]
    df2 = df1[df1['section'] == subsection_id]

    # # use this to check what 'good' expected result looks like
    # print(df2.columns)
    # print(df2[['section', 'Rupture Index', RATE_COLUMN]])

    new_expected_rate = sum(df2[RATE_COLUMN])

    srdf = SolutionParticipation(solution).section_participation_rates([subsection_id], rids_subset)
    print(srdf)
    assert pytest.approx(srdf.participation_rate.tolist()[0]) == new_expected_rate
