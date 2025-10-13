"""This module defines the dataframes returned by solvis.

- We use the `panderas` library to define the dataframe schemas and solvis testing validates that
   dataframes have the expected columns names and types.
- currenty schema attributes are NOT the actual dataframe column names, For these see the
    code and the `Field(alias={column_name}) value. See below...
- refactoring of column names is expected in a future release, but legacy column names will be supported.
"""

from typing import TYPE_CHECKING

import pandas as pd
import pandera.pandas as pda
from pandera.typing import Index, Series

if TYPE_CHECKING:
    from shapely import geometry  # noqa


class SectionParticipationSchema(pda.DataFrameModel):
    """A Dataframe schema for `section_participation_rate`.

    Attributes:
        section: unique index on section_id.
        participation_rate: sum of the ruptures involving each fault section.
    """

    class Config:
        strict = True

    section: Index[pd.Int32Dtype]
    participation_rate: Series[pd.Float32Dtype]


class ParentFaultParticipationSchema(pda.DataFrameModel):
    """A Dataframe schema for `fault_participation_rate`.

    Attributes:
        parent_fault_id: unique index on parent fault id.
        participation_rate: sum of the ruptures involving each parent fault.
    """

    class Config:
        strict = True

    parent_fault_id: Index[pd.Int32Dtype] = pda.Field(alias='ParentID')
    participation_rate: Series[pd.Float32Dtype]


class NamedFaultParticipationSchema(pda.DataFrameModel):
    """A Dataframe schema for `named_fault_participation_rate`.

    Attributes:
        named_fault_name: unique index on named fault name.
        participation_rate: sum of the ruptures involving each named fault.
    """

    class Config:
        strict = True

    named_fault_name: Index[str]
    participation_rate: Series[pd.Float32Dtype]


class FaultSectionSchemaBase(pda.DataFrameModel):
    """A base schema for common dataframe columns.

    This is not used directly, but is reused in other schema.

    Attributes:
        section_id: unique section id.
        section_name: the fault section name.
        dip_angle: dip angle of the section (degrees).
        rake: rake angle of the section (degrees).
        lower_depth: lower section depth (meters).
        upper_depth: upper section depth (meters).
        aseismic_slip_factor: ratio of slip that is considered aseismic.
        coupling_coefficient: coupling coefficient.
        parent_fault_id: unique id of th parent fault.
        parent_fault_name: unique name of ther parent fault.
        dip_direction: dip direciton (degrees).
        geometry: A set of coordinates defining the section surface trace.
        target_slip_rate: the target slip reate used in the grand inversion.
        target_slip_rate_stddev: the target slip rate stddev used in the grand inversion.
    """

    section_id: Series[pd.Int32Dtype] = pda.Field(alias='FaultID')
    section_name: Series[str] = pda.Field(alias='FaultName')
    dip_angle: Series[pd.Float64Dtype] = pda.Field(alias='DipDeg')
    rake: Series[pd.Float64Dtype] = pda.Field(alias='Rake')
    lower_depth: Series[pd.Float64Dtype] = pda.Field(alias='LowDepth')
    upper_depth: Series[pd.Float64Dtype] = pda.Field(alias='UpDepth')
    aseismic_slip_factor: Series[pd.Float64Dtype] = pda.Field(alias='AseismicSlipFactor')
    coupling_coefficient: Series[pd.Float64Dtype] = pda.Field(alias='CouplingCoeff')
    parent_fault_id: Series[pd.Int32Dtype] = pda.Field(alias='ParentID')
    parent_fault_name: Series[str] = pda.Field(alias='ParentName')
    dip_direction: Series[pd.Float64Dtype] = pda.Field(alias='DipDir')
    geometry: Series['geometry']
    target_slip_rate: Series[pd.Float64Dtype] = pda.Field(alias='Target Slip Rate')
    target_slip_rate_stddev: Series[pd.Float64Dtype] = pda.Field(alias='Target Slip Rate StdDev')


class FaultSectionSchema(FaultSectionSchemaBase):
    """A Dataframe schema for `fault_section`.

    Notes:
     - this just adds an index to the base class FaultSectionSchema.

    Attributes:
        index: on section id.
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype] = pda.Field(alias='section_id')


class FaultSectionWithSolutionSlipRate(FaultSectionSchemaBase):
    """A Dataframe schema for `fault_sections_with_solution_slip_rates`.

    Notes:
     - this just adds an index and one column to the base class FaultSectionSchema.

    Attributes:
        index: on section id.
        solution_slip_rate: the slip rate calculated in the Opensha grand inversion.
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype] = pda.Field(alias='section_id')
    solution_slip_rate: Series[pd.Float64Dtype] = pda.Field(alias='Solution Slip Rate')


class FaultSectionRuptureRateSchema(FaultSectionSchemaBase):
    """A Dataframe schema for `fault_sections_with_rupture_rates`.

    This table joins each permutation of rupture_id and section_id
    with their aggregated rates across all the inversion solution branches.

    Todo:
     - why is this schema used in inversion_solution_file, shouldn't it exclusivly on fault_system_solution ??

    Attributes:
     fault_system_idx: index on fault system
     section_idx: index on section id.

     rupture: the rupture id.
     section: the fault_section id.
     key_0: Todo: drop this please!!

     fault_system: fault system short code eg 'CRU'
     rupture_id: the id of each rupture
     rate_count: count of aggregate ruptures with rate.
     rate_max: max rate of aggregate ruptures with rate.
     rate_min: min rate of aggregate ruptures with rate.
     rate_weighted_mean: rate weighted mean of aggregate ruptures with rate.
     magnitude: the rupture magnitude.
     mean_rake: the mean rake angle of the ruptures fault sections (degrees).
     area: rupture area (meters^2).
     length: rupture length (meters).
     section: Series[pd.Int32Dtype]

    Note:
     remaining attributes are inherited from FaultSectionSchemaBase
    """

    class Config:
        strict = True
        # provide multi index options in the config
        multiindex_name = "fault_system_fault_section_index"
        multiindex_strict = True
        multiindex_coerce = True

    fault_system_idx: Index[pd.CategoricalDtype] = pda.Field(alias='fault_system', coerce=True)
    section_idx: Index[pd.Int64Dtype] = pda.Field(alias='Rupture Index', coerce=True)

    key_0: Series[pd.UInt32Dtype]
    fault_system: Series['str']
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    rate_count: Series[pd.Int64Dtype]
    rate_max: Series[pd.Float32Dtype]
    rate_min: Series[pd.Float32Dtype]
    rate_weighted_mean: Series[pd.Float32Dtype]
    magnitude: Series[pd.Float32Dtype] = pda.Field(alias='Magnitude')
    mean_rake: Series[pd.Float32Dtype] = pda.Field(alias='Average Rake (degrees)')
    area: Series[pd.Float32Dtype] = pda.Field(alias='Area (m^2)')
    length: Series[pd.Float32Dtype] = pda.Field(alias='Length (m)')
    section: Series[pd.Int32Dtype]


class RuptureSectionSchema(pda.DataFrameModel):
    """A Dataframe schema for `rupture_section`.

    This is a `join` table iterating all permutations of rupture_id and section_id.

    Attributes:
     index: unique index.
     rupture_id: the id of each rupture
     section_id: the id of each fault_section
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.Int64Dtype] = pda.Field(alias='rupture')
    section_id: Series[pd.Int32Dtype] = pda.Field(alias='section')


class RuptureBaseSchema(pda.DataFrameModel):
    """A Dataframe schema base.

    Attributes:
     magnitude: the rupture magnitude.
     mean_rake: the mean rake angle of the ruptures' fault sections (degrees).
     area: rupture area (meters^2).
     length: rupture length (meters).
    """

    magnitude: Series[pd.Float32Dtype] = pda.Field(alias='Magnitude')
    mean_rake: Series[pd.Float32Dtype] = pda.Field(alias='Average Rake (degrees)')
    area: Series[pd.Float32Dtype] = pda.Field(alias='Area (m^2)')
    length: Series[pd.Float32Dtype] = pda.Field(alias='Length (m)')


class RupturesWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `InversionSolution.ruptures_with_rupture_rates`.

    Attributes:
     index: integer id.
     rupture_id: same as index.
     annual_rate: annual rupture rate.
     magnitude: the rupture magnitude.
     mean_rake: the mean rake angle of the ruptures' fault sections (degrees).
     area: rupture area (meters^2).
     length: rupture length (meters).
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    annual_rate: Series[pd.Float32Dtype] = pda.Field(alias='Annual Rate')


class AggregateRupturesWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `FaultSystemSolution.ruptures_with_rupture_rates`."""

    class Config:
        strict = True
        # provide multi index options in the config
        multiindex_strict = True
        multiindex_coerce = True

    fault_system_idx: Index[pd.CategoricalDtype] = pda.Field(alias='fault_system', coerce=True)
    section_idx: Index[pd.Int64Dtype] = pda.Field(alias='Rupture Index', coerce=True)

    fault_system: Series['str']
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    rate_count: Series[pd.Int64Dtype]
    rate_max: Series[pd.Float32Dtype]
    rate_min: Series[pd.Float32Dtype]
    rate_weighted_mean: Series[pd.Float32Dtype]


class RuptureSectionsWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `InversionSolution.rs_with_rupture_rates`."""

    class Config:
        strict = True

    # index: Index[pd.Int64Dtype]

    key_0: Series[pd.UInt32Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    section_id: Series[pd.Int32Dtype] = pda.Field(alias='section')
    annual_rate: Series[pd.Float32Dtype] = pda.Field(alias='Annual Rate')


class AggregateRuptureSectionsWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `FaultSystemSolution.rs_with_rupture_rates`."""

    class Config:
        strict = True
        # provide multi index options in the config
        multiindex_strict = True
        multiindex_coerce = True

    fault_system_idx: Index[pd.CategoricalDtype] = pda.Field(alias='fault_system', coerce=True)
    section_idx: Index[pd.Int64Dtype] = pda.Field(alias='Rupture Index', coerce=True)

    key_0: Series[pd.UInt32Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    fault_system: Series['str']
    rate_count: Series[pd.Int64Dtype]
    rate_max: Series[pd.Float32Dtype]
    rate_min: Series[pd.Float32Dtype]
    rate_weighted_mean: Series[pd.Float32Dtype]

    # from RuptureSectionSchema
    section: Series[pd.Int32Dtype]


### Below are from InversionSolutionFile
class RuptureRateSchema(pda.DataFrameModel):
    """A Dataframe schema for `InversionSolutionFile.rupture_rates`.

    Attributes:
     index: unique index on rupture_id.
     rupture_id: the id of each rupture
     annual_rate: the rupture rate
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    annual_rate: Series[pd.Float32Dtype] = pda.Field(alias='Annual Rate')


class RuptureSchema(RuptureBaseSchema):
    """A dataframe schema for Ruptures."""

    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
