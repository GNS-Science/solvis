import pytest

from solvis.filter import FilterRuptureIds
from solvis.solution import SolutionParticipation


def test_section_participation_rate(crustal_solution_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_solution_fixture
    rates = SolutionParticipation(solution).section_participation_rates([sec_id])
    print(f"participation rate for section {sec_id}: {rates.participation_rate.tolist()[0]} /yr")
    assert pytest.approx(rates.participation_rate.tolist()[0]) == 0.0099396


def test_section_participation_rate_default_spot_check(crustal_solution_fixture):
    # get the participation rate for a single (sub)section
    sec_id = 5
    solution = crustal_solution_fixture
    rates = SolutionParticipation(solution).section_participation_rates()
    # print(f"participation rate for section {sec_id}: {rates.participation_rate.tolist()[0]} /yr")
    # rates=r
    assert pytest.approx(rates[rates.index == sec_id].participation_rate.tolist()[0]) == 0.0099396


def test_section_participation_rate_default_all_sections(crustal_solution_fixture):
    # get the participation rate for a single (sub)section
    # sec_id = 5
    solution = crustal_solution_fixture
    rates = SolutionParticipation(solution).section_participation_rates()
    section_rates = solution.model.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
    assert section_rates.all() == rates.participation_rate.all()


def test_solution_participation_rate(crustal_solution_fixture):
    # get the participation rate of all (sub)sections
    solution = crustal_solution_fixture
    section_rates = solution.model.rs_with_rupture_rates.groupby("section").agg('sum')["Annual Rate"]
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
    # srdf = SolutionParticipation(solution).section_participation_rates(subsection_ids)
    # print(srdf)

    # section_rate = srdf[srdf.index == subsection_id].agg('sum').participation_rate
    # print(section_rate)
    # assert pytest.approx(section_rate) == expected_rate
    srdf = SolutionParticipation(solution).section_participation_rates([subsection_id])
    # print(srdf)
    assert pytest.approx(srdf.participation_rate.tolist()[0]) == expected_rate


@pytest.mark.parametrize("fault_name, subsection_id, expected_rate", section_fault_rates)
def test_section_participation_rates_conditional(crustal_solution_fixture, fault_name, subsection_id, expected_rate):
    solution = crustal_solution_fixture

    rids = list(FilterRuptureIds(crustal_solution_fixture).for_parent_fault_names([fault_name]))
    print(rids)

    rids_subset = rids[: int(len(rids) / 2)]
    print(rids_subset)

    srdf = SolutionParticipation(solution).section_participation_rates([subsection_id], rids_subset)
    print(srdf)
    assert srdf.participation_rate.tolist()[0] - 1e-10 < expected_rate
