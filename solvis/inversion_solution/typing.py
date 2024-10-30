'''
This module defines type classes for the main interfaces shared
across the `inversion_solution` package.

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

    @property
    def average_slips(self) -> gpd.GeoDataFrame:
        """the average slips for each rupture."""

    @property
    def section_target_slip_rates(self) -> gpd.GeoDataFrame:
        """the inversion target slip rates for each rupture."""

    @property
    def indices(self) -> gpd.GeoDataFrame:
        """the fault sections involved in each rupture."""

    @property
    def archive_path(self) -> Optional[Path]:
        """the path to the archive file"""

    @property
    def archive(self) -> Optional[zipfile.ZipFile]:
        """the archive instance"""


class AggregateSolutionFileProtocol(Protocol):
    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        pass


class InversionSolutionModelProtocol(Protocol):
    @property
    def fault_sections(self) -> 'DataFrame[FaultSectionSchema]':
        """something pass"""

    @property
    def fault_sections_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """solution requires fault sections with rates"""

    @property
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        """A dataframe containing ruptures and their rates

        Returns:
          dataframe: a [rupture rates][solvis.inversion_solution.dataframe_models.RuptureRateSchema] dataframe
        """

    def rate_column_name(self) -> str:
        """the name of the rate_column returned in dataframes."""

    @property
    def parent_fault_names(self) -> List[str]:
        """The parent_fault_names."""

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        pass

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        pass

    @property
    def rs_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture section."""

    @property
    def ruptures_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture."""

    @property
    def rupture_sections(self) -> gpd.GeoDataFrame:
        """the rupture sections for each rupture."""

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        """A dataframe containing ruptures

        this is internal list only

        Returns:
          dataframe: a ruptures dataframe
        """


class InversionSolutionProtocol(Protocol):
    @property
    def model(self) -> 'InversionSolutionModelProtocol':
        """the pandas dataframes API model of the solution.

        Returns:
            model: an instance of type InversionSolutionModelProtocol
        """

    @property
    def solution_file(self) -> 'InversionSolutionFileProtocol':
        """the file protocol instance for the solution.

        Returns:
            instance: an instance of type InversionSolutionFileProtocol
        """

    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""

    @staticmethod
    def filter_solution(solution: Any, rupture_ids: Iterable) -> Any:
        """return a new solution containing just the ruptures specified"""
        raise NotImplementedError()

    # def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
    #     """builder method returning the rupture surface of a given rupture id."""

    # def fault_surfaces(self) -> gpd.GeoDataFrame:
    #     pass


'''
class AggregateSolutionProtocol(Protocol):
    @property
    def model(self) -> 'AggregateSolutionModelProtocol':
        pass

    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""

    @property
    def solution_file(self) -> 'InversionSolutionFileProtocol':
        """the file protocol instance for the solution.

        Returns:
            instance: an instance of type InversionSolutionFileProtocol
        """

    # def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
    #     """builder method returning the rupture surface of a given rupture id."""

    # def fault_surfaces(self) -> gpd.GeoDataFrame:
    #     pass


    @staticmethod
    def filter_solution(solution: Any, rupture_ids: Iterable) -> Any:
        """return a new solution containing just the ruptures specified"""
        raise NotImplementedError()

    # def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
    #     """builder method returning the rupture surface of a given rupture id."""

    # def fault_surfaces(self) -> gpd.GeoDataFrame:
    #     pass


class AggregateSolutionModelProtocol(InversionSolutionModelProtocol):
    @property
    def composite_rates(self):
        pass

    @property
    def aggregate_rates(self):
        pass
'''


class CompositeSolutionProtocol(Protocol):

    _solutions: Mapping[str, InversionSolutionProtocol] = {}
    _archive_path: Optional[Path]

    def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
        """builder method returning the rupture surface of a given rupture id."""

    @property
    def archive_path(self):
        """the path to the archive file"""


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
