import pytest

from solvis.filter import FilterParentFaultIds, FilterRuptureIds, FilterSubsectionIds
from solvis.solution import SolutionParticipation

RATE_COLUMN = 'rate_weighted_mean'  # 'Annual Rate'

named_fault_rates = [
    ("Ohariu", 0.0002223205),
    ("Wairarapa", 0.0005474389),
]


@pytest.mark.parametrize("named_fault_name, expected_rate", named_fault_rates)
def test_named_fault_participation_rate_all(tiny_crustal_solution_fixture, named_fault_name, expected_rate):
    solution = tiny_crustal_solution_fixture
    rates = SolutionParticipation(solution).named_fault_participation_rates()
    assert pytest.approx(rates.loc[named_fault_name].participation_rate) == expected_rate


@pytest.mark.parametrize("named_fault_name, expected_rate", named_fault_rates)
def test_named_fault_participation_rate(tiny_crustal_solution_fixture, named_fault_name, expected_rate):
    solution = tiny_crustal_solution_fixture
    rates = SolutionParticipation(solution).named_fault_participation_rates([named_fault_name])
    assert pytest.approx(rates.participation_rate.tolist()[0]) == expected_rate


@pytest.mark.parametrize("named_fault_name, expected_rate", named_fault_rates)
def test_named_fault_participation_rate_conditional(tiny_crustal_solution_fixture, named_fault_name, expected_rate):
    solution = tiny_crustal_solution_fixture
    pids = list(FilterParentFaultIds(solution).for_named_fault_names([named_fault_name]))
    rids = list(FilterRuptureIds(solution).for_parent_fault_ids(pids))
    assert len(rids) > 1

    rates = SolutionParticipation(solution).named_fault_participation_rates([named_fault_name], rupture_ids=rids)
    assert pytest.approx(rates.participation_rate.tolist()[0]) == expected_rate

    rids_subset = rids[: int(len(rids) / 2)]
    rates = SolutionParticipation(solution).fault_participation_rates([named_fault_name], rupture_ids=rids_subset)
    assert rates.participation_rate.tolist()[0] < expected_rate


@pytest.mark.parametrize("named_fault_name, expected_rate", named_fault_rates)
def test_named_fault_participation_rate_vs_section_rates(
    tiny_crustal_solution_fixture, named_fault_name, expected_rate
):
    solution = tiny_crustal_solution_fixture
    named_fault_rates = SolutionParticipation(solution).named_fault_participation_rates([named_fault_name])
    assert pytest.approx(named_fault_rates.participation_rate.tolist()[0]) == expected_rate

    rids = FilterRuptureIds(solution).for_named_fault_names([named_fault_name])
    pids = FilterParentFaultIds(solution).for_named_fault_names([named_fault_name])
    sids = FilterSubsectionIds(solution).for_parent_fault_ids(pids).for_rupture_ids(rids)

    section_rates = SolutionParticipation(solution).section_participation_rates(sids)

    assert (
        sum(section_rates.participation_rate) >= expected_rate
    ), "sum(section rates) should not be less than parent rate"
    assert max(section_rates.participation_rate) <= expected_rate, "max(section rates) should not exceed parent rate"
    assert (
        sum(section_rates.participation_rate) / len(section_rates.participation_rate) <= expected_rate
    ), "mean(section rates) should not exceed parent rate"
