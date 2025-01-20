"""This module defines the dataframes returned by solvis.

 - We use the `panderas` library to define the dataframe schemas and solvis testing validates that
   dataframes have the expected columns names and types.
 - currenty schema attributes are NOT the actual dataframe column names, For these see the
    code and the `Field(alias={column_name}) value. See below...
 - refactoring of column names is expected in a future release, but legacy column names will be supported.

"""

from typing import TYPE_CHECKING

import pandas as pd
import pandera as pda
from pandera.typing import Index, Series

if TYPE_CHECKING:
    from shapely import geometry  # noqa


class SectionParticipationSchema(pda.DataFrameModel):
    """A Dataframe schema for `section_participation_rate`.

    Attributes:
        section: unique index on section_id.
        participation_rate: sum of the ruptures involving each section.
    """

    class Config:
        strict = True

    section: Index[pd.Int32Dtype]
    participation_rate: Series[pd.Float32Dtype]


class ParentFaultParticipationSchema(pda.DataFrameModel):
    """A Dataframe schema for `fault_participation_rate`.

    Attributes:
        parent_fault_id: unique index on parent fault id.
        participation_rate: sum of the ruptures involving each section.
    """

    class Config:
        strict = True

    parent_fault_id: Index[pd.Int32Dtype] = pda.Field(alias='ParentID')
    participation_rate: Series[pd.Float32Dtype]


class FaultSectionSchemaBase(pda.DataFrameModel):
    """A base schema for common dataframe columns.

    This is not used directly, but it's fields are reused in other schema.

    Attributes:
     index: unique index on section_id.
     section_id: the section id (OpenSHA:FaultID).
     section_name: section name (OpenSHA:FaultName).
     dip_angle: dip angle in degrees (OpenSHA:DipDeg).
     rake: rake angle in degrees (OpenSHA:Rake).
     lower_depth: fault lower depth in meters (OpenSHA:LowDepth).
     upper_depth: fault upper depth in metres (OpenSHA:UpDepth).
     aseismic_slip_factor: ratio of aseismic slip  (OpenSHA:AseismicSlipFactor).
     coupling_coefficient: coupling coefficient (OpenSHA:CouplingCoeff).
     parent_fault_id: the parent fault id (OpenSHA:ParentID).
     parent_fault_name: the parent fault name (OpenSHA:ParentName).
     dir_direction: dip direction in degrees  = (OpenSHA:DipDir).
     geometry: a `shapely.geometry` object representing the section surface.
     target_slip_rate: a target slip rate (OpenSHA:'Target Slip Rate').
     target_slip_rate_stddev: standard deviation for the target slip rate (OpenSHA:'Target Slip Rate StdDev').
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
    """A Dataframe schema for `fault_section`

    Attributes:
     index: unique index on section_id.

    Note:
     remaining attributes are inherited from FaultSectionSchemaBase
    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype] = pda.Field(alias='section_id')


class FaultSectionWithSolutionSlipRate(FaultSectionSchemaBase):
    """A Dataframe schema for `fault_sections_with_solution_slip_rates`

    Notes:
     - this just adds one column to FaultSectionSchemaBase/FaultSectionSchema

    Attributes:
     index: unique index.
     solution_slip_rate: # TODO: what is this ??
    """

    index: Index[pd.Int64Dtype] = pda.Field(alias='section_id')
    solution_slip_rate: Series[pd.Float64Dtype] = pda.Field(alias='Solution Slip Rate')


class FaultSectionRuptureRateSchema(FaultSectionSchemaBase):
    """A Dataframe schema for `fault_sections_with_rupture_rates`

    This table joins all permutations of rupture_id and section_id
     with the aggregate rupture columns.

    Todo:
     - why is this schema used in inversion_solution_file, shouldn't it exclusivly on fault_system_solution ??

    Attributes:
     index: unique index.
     rupture: the id of each rupture
     section: the id of each fault_section
     key_0: Todo: drop this please!!
     fault_system: fault system short code eg 'CRU'
     rupture_id: the id of each rupture
     rate_count: count of aggregate ruptures with rate
     rate_max: Series[pd.Float32Dtype]
     rate_min: Series[pd.Float32Dtype]
     rate_weighted_mean: Series[pd.Float32Dtype]
     magnitude: Series[pd.Float32Dtype] = pda.Field(alias='Magnitude')
     mean_rake: Series[pd.Float32Dtype] = pda.Field(alias='Average Rake (degrees)')
     area: Series[pd.Float32Dtype] = pda.Field(alias='Area (m^2)')
     length: Series[pd.Float32Dtype] = pda.Field(alias='Length (m)')
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
    """A Dataframe schema for `rupture_section`

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
    magnitude: Series[pd.Float32Dtype] = pda.Field(alias='Magnitude')
    mean_rake: Series[pd.Float32Dtype] = pda.Field(alias='Average Rake (degrees)')
    area: Series[pd.Float32Dtype] = pda.Field(alias='Area (m^2)')
    length: Series[pd.Float32Dtype] = pda.Field(alias='Length (m)')


class RupturesWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `InversionSolution.ruptures_with_rupture_rates`

    Attributes:

    """

    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    annual_rate: Series[pd.Float32Dtype] = pda.Field(alias='Annual Rate')


class FSS_RupturesWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `FaultSystemSolution.ruptures_with_rupture_rates`

    Attributes:

    """

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
    """A Dataframe schema for `InversionSolution.rs_with_rupture_rates`"""

    class Config:
        strict = True

    # index: Index[pd.Int64Dtype]

    key_0: Series[pd.UInt32Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
    section_id: Series[pd.Int32Dtype] = pda.Field(alias='section')
    annual_rate: Series[pd.Float32Dtype] = pda.Field(alias='Annual Rate')


class FSS_RuptureSectionsWithRuptureRatesSchema(RuptureBaseSchema):
    """A Dataframe schema for `FaultSystemSolution.rs_with_rupture_rates`"""

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
    """A Dataframe schema for `InversionSolutionFile.rupture_rates`

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
    class Config:
        strict = True

    index: Index[pd.Int64Dtype]
    rupture_id: Series[pd.UInt32Dtype] = pda.Field(alias='Rupture Index')
