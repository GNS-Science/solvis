#! test_dataframe_models.py
import pytest

from solvis.inversion_solution.dataframe_models import (
    FaultSectionRuptureRateSchema,
    FaultSectionSchema,
    ParentFaultParticipationSchema,
    RuptureSectionSchema,
    SectionParticipationSchema,
)


def test_section_participation_rates_model(crustal_fixture):
    rates = crustal_fixture.section_participation_rates(range(10))
    print(rates)
    SectionParticipationSchema.validate(rates)


def test_parent_fault_participation_rates_model(crustal_fixture):
    rates = crustal_fixture.fault_participation_rates()
    print(rates)
    ParentFaultParticipationSchema.validate(rates)


def test_fault_section_model(crustal_fixture):
    df = crustal_fixture.fault_sections
    print(df)
    FaultSectionSchema.validate(df)


def test_rupture_section_model(crustal_fixture):
    df = crustal_fixture.rupture_sections
    print(df)
    RuptureSectionSchema.validate(df)

def test_fault_sections_with_rupture_rates_model(crustal_fixture):
    df = crustal_fixture.fault_sections_with_rupture_rates
    print(df.index)
    print(df.info())
    print()
    index = FaultSectionRuptureRateSchema.to_schema().index
    print(index)
    print()
    FaultSectionRuptureRateSchema.validate(df)
