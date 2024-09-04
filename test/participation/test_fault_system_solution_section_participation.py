import pytest

from solvis.filter import FilterRuptureIds

RATE_COLUMN = 'weighted_rate'  # 'Annual Rate'


def test_section_participation_rate(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_small_fss_fixture
    rates = solution.section_participation_rates([sec_id])
    print(rates)
    assert pytest.approx(rates[RATE_COLUMN].tolist()[0]) == 0.0026206877  # 0.0099396


def test_section_participation_rate_default_spot_check(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_small_fss_fixture
    rates = solution.section_participation_rates()
    # print(f"participation rate for section {sec_id}: {rates['Annual Rate'].tolist()[0]} /yr")
    # rates=r
    assert pytest.approx(rates[rates.index == sec_id][RATE_COLUMN].tolist()[0]) == 0.0026206877


def test_section_participation_rate_default_all_sections(crustal_small_fss_fixture):
    # get the participation rate for a single (sub)section
    # sec_id = 5
    solution = crustal_small_fss_fixture
    rates = solution.section_participation_rates()
    section_rates = solution.rs_with_composite_rupture_rates.groupby("section").agg('sum')[RATE_COLUMN]
    assert section_rates.all() == rates[RATE_COLUMN].all()


section_fault_rates = [
    ("Alpine Jacksons to Kaniere", 0, 0.0026206877),
    ("Alpine Jacksons to Kaniere", 10, 0.000590668118),
]


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_small_fss_fixture

    # print(solution.fault_sections[["FaultName"]])
    # subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names([fault_name])
    # print(subsection_ids)
    # print()
    # print(solution.composite_rates)
    # print(solution.rupture_sections)

    # srdf = solution.section_participation_rates(subsection_ids)
    # print(srdf)

    # section_rate = srdf[srdf.index == subsection_id].agg('sum')[RATE_COLUMN]
    # print(section_rate)
    # assert pytest.approx(section_rate) == expected_rate
    srdf = solution.section_participation_rates([subsection_id])
    # print(srdf)
    assert pytest.approx(srdf[RATE_COLUMN].tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates_conditional(crustal_small_fss_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_small_fss_fixture

    rids = list(FilterRuptureIds(solution).for_parent_fault_names([fault_name]))
    print(rids)

    rids_subset = rids[2:]
    print(rids_subset)

    srdf = solution.section_participation_rates([subsection_id], rids_subset)
    print(srdf)
    assert srdf[RATE_COLUMN].tolist()[0] - 1e-10 < expected_rate
