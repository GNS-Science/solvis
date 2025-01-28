'''
This module defines type classes for the main interfaces shared
across the `inversion_solution` package.

Todo:
    With the refactoring done on various classes/modules, most of these protocol classes can be
    dropped and function docstrings migrated to the functional code.

Classes:
    InversionSolutionProtocol: the interface for an InversionSolution
    CompositeSolutionProtocol: interface for CompositeSolution

'''
import zipfile
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, List, Mapping, Optional, Protocol, Union

import geopandas as gpd

if TYPE_CHECKING:
    # from numpy.typing import NDArray
    from pandera.typing import DataFrame

    from .dataframe_models import FaultSectionSchema, RuptureRateSchema


class InversionSolutionFileProtocol(Protocol):

    FAULTS_PATH: Union[Path, str] = ''

    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""
        raise NotImplementedError()

    @property
    def average_slips(self) -> gpd.GeoDataFrame:
        """the average slips for each rupture."""
        raise NotImplementedError()

    @property
    def section_target_slip_rates(self) -> gpd.GeoDataFrame:
        """the inversion target slip rates for each rupture."""
        raise NotImplementedError()

    @property
    def indices(self) -> gpd.GeoDataFrame:
        """the fault sections involved in each rupture."""
        raise NotImplementedError()

    @property
    def archive_path(self) -> Optional[Path]:
        """the path to the archive file"""
        raise NotImplementedError()

    @property
    def archive(self) -> Optional[zipfile.ZipFile]:
        """the archive instance"""
        raise NotImplementedError()


class AggregateSolutionFileProtocol(Protocol):
    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        """enable fast indices"""


class InversionSolutionModelProtocol(Protocol):
    @property
    def fault_sections(self) -> 'DataFrame[FaultSectionSchema]':
        """Get the fault sections."""
        raise NotImplementedError()

    @property
    def fault_sections_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """
        Get fault sections and their rupture rates.
        """
        raise NotImplementedError()

    @property
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        """A dataframe containing ruptures and their rates

        Returns:
          dataframe: a [rupture rates][solvis.solution.dataframe_models.RuptureRateSchema] dataframe
        """
        raise NotImplementedError()

    def rate_column_name(self) -> str:
        """the name of the rate_column returned in dataframes."""
        raise NotImplementedError()

    @property
    def parent_fault_names(self) -> List[str]:
        """The parent_fault_names."""
        raise NotImplementedError()

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        """get section participation"""
        raise NotImplementedError()

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        """get fault_partipation"""
        raise NotImplementedError()

    @property
    def rs_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture section."""
        raise NotImplementedError()

    @property
    def ruptures_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture."""
        raise NotImplementedError()

    @property
    def rupture_sections(self) -> gpd.GeoDataFrame:
        """the rupture sections for each rupture."""
        raise NotImplementedError()

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        """A dataframe containing ruptures

        this is internal list only

        Returns:
          dataframe: a ruptures dataframe
        """
        raise NotImplementedError()


class InversionSolutionProtocol(Protocol):
    @property
    def model(self) -> 'InversionSolutionModelProtocol':
        """the pandas dataframes API model of the solution.

        Returns:
            model: an instance of type InversionSolutionModelProtocol
        """
        raise NotImplementedError()

    @property
    def solution_file(self) -> 'InversionSolutionFileProtocol':
        """the file protocol instance for the solution.

        Returns:
            instance: an instance of type InversionSolutionFileProtocol
        """
        raise NotImplementedError()

    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""

    @staticmethod
    def filter_solution(solution: Any, rupture_ids: Iterable[int]) -> Any:
        """return a new solution containing just the ruptures specified"""
        raise NotImplementedError()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the rupture surface projected onto the earth surface.

        Parameters:
            rupture_id: ID of the rupture

        Returns:
            a gpd.GeoDataFrame
        """
        raise NotImplementedError()

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the solution fault surfaces projected onto the earth surface.

        Returns:
            a gpd.GeoDataFrame
        """
        raise NotImplementedError()


class CompositeSolutionProtocol(Protocol):

    _solutions: Mapping[str, InversionSolutionProtocol] = {}
    _archive_path: Optional[Path]

    def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
        """builder method returning the rupture surface of a given rupture id."""
        raise NotImplementedError()

    @property
    def archive_path(self):
        """the path to the archive file"""
        raise NotImplementedError()


class ModelLogicTreeBranch(Protocol):
    """what we can expect from nzshm-model.....Branch"""

    values: List[Any]
    weight: float
    onfault_nrml_id: Union[str, None] = ""
    distributed_nrml_id: Union[str, None] = ""
    inversion_solution_id: Union[str, None] = ""
    inversion_solution_type: Union[str, None] = ""


class BranchSolutionProtocol(InversionSolutionProtocol):
    fault_system: Union[str, None] = ""
    rupture_set_id: Union[str, None] = ""
    branch: ModelLogicTreeBranch


class SetOperationEnum(Enum):
    """Enumerated type for common set operations."""

    UNION = 1
    INTERSECTION = 2
    DIFFERENCE = 3
