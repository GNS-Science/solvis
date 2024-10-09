#! test_dataframe_models.py
import pytest

from solvis.inversion_solution.dataframe_models import (
    FaultSectionRuptureRateSchema,
    FaultSectionSchema,
    FaultSectionWithSolutionSlipRate,
    FSS_RuptureSectionsWithRuptureRatesSchema,
    FSS_RupturesWithRuptureRatesSchema,
    ParentFaultParticipationSchema,
    RuptureSectionSchema,
    RuptureSectionsWithRuptureRatesSchema,
    RupturesWithRuptureRatesSchema,
    SectionParticipationSchema,
)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_section_participation_rates_model(request, soln_fixture):
    rates = request.getfixturevalue(soln_fixture).section_participation_rates(range(10))
    print(rates)
    SectionParticipationSchema.validate(rates)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_parent_fault_participation_rates_model(request, soln_fixture):
    rates = request.getfixturevalue(soln_fixture).fault_participation_rates()
    print(rates)
    ParentFaultParticipationSchema.validate(rates)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_fault_section_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).fault_sections
    print(df)
    FaultSectionSchema.validate(df)


@pytest.mark.parametrize(("soln_fixture",), [("crustal_fixture",), ("crustal_solution_fixture",)])
def test_rupture_section_model(request, soln_fixture):
    df = request.getfixturevalue(soln_fixture).rupture_sections
    print(df)
    RuptureSectionSchema.validate(df)


def test_FSS_ONLY_fault_sections_with_rupture_rates_model(crustal_fixture):
    df = crustal_fixture.fault_sections_with_rupture_rates
    FaultSectionRuptureRateSchema.validate(df)


def test_IS_ONLY_fault_sections_with_solution_slip_rates_model(crustal_solution_fixture):

    df = crustal_solution_fixture.fault_sections_with_solution_slip_rates
    print(df.index)
    print(df.info())
    print()

    index = FaultSectionWithSolutionSlipRate.to_schema().index
    print(index)
    print()
    FaultSectionWithSolutionSlipRate.validate(df)


def test_IS_ONLY_ruptures_with_rupture_rates(crustal_solution_fixture):
    df = crustal_solution_fixture.ruptures_with_rupture_rates
    print(df)
    RupturesWithRuptureRatesSchema.validate(df)


def test_FSS_ONLY_ruptures_with_rupture_rates(crustal_fixture):
    df = crustal_fixture.ruptures_with_rupture_rates
    print(df)
    FSS_RupturesWithRuptureRatesSchema.validate(df)


def test_IS_ONLY_rs_with_rupture_rates(crustal_solution_fixture):
    df = crustal_solution_fixture.rs_with_rupture_rates
    print(df)
    RuptureSectionsWithRuptureRatesSchema.validate(df)


def test_FSS_ONLY_rs_with_rupture_rates(crustal_fixture):
    df = crustal_fixture.rs_with_rupture_rates
    print(df)
    print()
    print(df.info())
    print()
    print(FSS_RuptureSectionsWithRuptureRatesSchema.to_schema())
    FSS_RuptureSectionsWithRuptureRatesSchema.validate(df)
