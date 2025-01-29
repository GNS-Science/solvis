#! test_dataframe_models.py
import pytest

from solvis.solution import SolutionParticipation
from solvis.solution.dataframe_models import (
    AggregateRuptureSectionsWithRuptureRatesSchema,
    AggregateRupturesWithRuptureRatesSchema,
    FaultSectionRuptureRateSchema,
    FaultSectionSchema,
    FaultSectionWithSolutionSlipRate,
    ParentFaultParticipationSchema,
    RuptureRateSchema,
    RuptureSchema,
    RuptureSectionSchema,
    RuptureSectionsWithRuptureRatesSchema,
    RupturesWithRuptureRatesSchema,
    SectionParticipationSchema,
)

# from solvis.solution.typing import InversionSolutionProtocol


# @pytest.mark.skip(
#     "this test is not that useful, "
#     "... see https://mypy.readthedocs.io/en/latest/protocols.html#using-isinstance-with-protocols"
# )
# @pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
# def test_model(request, soln_fixture):
#     soln = request.getfixturevalue(soln_fixture)
#     assert isinstance(soln, InversionSolutionProtocol)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_section_participation_rates_model(request, soln_fixture):
    solution = request.getfixturevalue(soln_fixture)
    rates = SolutionParticipation(solution).section_participation_rates(range(10))
    print(rates)
    SectionParticipationSchema.validate(rates)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_parent_fault_participation_rates_model(request, soln_fixture):
    solution = request.getfixturevalue(soln_fixture)
    rates = SolutionParticipation(solution).fault_participation_rates()
    print(rates)
    ParentFaultParticipationSchema.validate(rates)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_fault_section_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).solution_file.fault_sections
    print(df)
    FaultSectionSchema.validate(df)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_rupture_section_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).model.rupture_sections
    print(df)
    RuptureSectionSchema.validate(df)


def test_FSS_ONLY_fault_sections_with_rupture_rates_model(crustal_fixture):
    df = crustal_fixture.model.fault_sections_with_rupture_rates
    FaultSectionRuptureRateSchema.validate(df)


def test_IS_ONLY_fault_sections_with_solution_slip_rates_model(crustal_solution_fixture):

    df = crustal_solution_fixture.model.fault_sections_with_solution_slip_rates
    print(df.index)
    print(df.info())
    print()

    index = FaultSectionWithSolutionSlipRate.to_schema().index
    print(index)
    print()
    FaultSectionWithSolutionSlipRate.validate(df)


def test_IS_ONLY_ruptures_with_rupture_rates(crustal_solution_fixture):
    df = crustal_solution_fixture.model.ruptures_with_rupture_rates
    print(df)
    RupturesWithRuptureRatesSchema.validate(df)


def test_FSS_ONLY_ruptures_with_rupture_rates(crustal_fixture):
    df = crustal_fixture.model.ruptures_with_rupture_rates
    print(df)
    AggregateRupturesWithRuptureRatesSchema.validate(df)


def test_IS_ONLY_rs_with_rupture_rates(crustal_solution_fixture):
    df = crustal_solution_fixture.model.rs_with_rupture_rates
    print(df)
    RuptureSectionsWithRuptureRatesSchema.validate(df)


def test_FSS_ONLY_rs_with_rupture_rates(crustal_fixture):
    df = crustal_fixture.model.rs_with_rupture_rates
    print(df)
    print()
    print(df.info())
    print()
    print(AggregateRuptureSectionsWithRuptureRatesSchema.to_schema())
    AggregateRuptureSectionsWithRuptureRatesSchema.validate(df)


### Below are from InversionSolutionFile
def test_IS_ONLY_rupture_rates(crustal_solution_fixture):
    df = crustal_solution_fixture.solution_file.rupture_rates
    print(df)
    RuptureRateSchema.validate(df)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_ruptures_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).solution_file.ruptures
    print(df)
    RuptureSchema.validate(df)


@pytest.mark.skip('who would ever need this in this form? Plus it`s awkward to model.')
@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_indices_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).solution_file.indices
    print(df)
    assert 0
    # RuptureSchema.validate(df)


@pytest.mark.skip('review if we should expose this.')
@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_average_slips_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).solution_file.average_slips
    print(df)
    assert 0
    # RuptureSchema.validate(df)


@pytest.mark.skip('review if we should expose this.')
@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_section_target_slip_rates_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).model.section_target_slip_rates
    print(df)
    assert 0
    # RuptureSchema.validate(df)
