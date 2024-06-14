import io
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any, List, Mapping, Optional, Protocol, Union

import geopandas as gpd
import numpy.typing as npt
import pandas as pd


class InversionSolutionProtocol(Protocol):

    _rates: pd.DataFrame = ...
    _ruptures: pd.DataFrame = ...
    _indices: pd.DataFrame = ...
    _average_slips: pd.DataFrame = ...
    _sect_slip_rates: pd.DataFrame = ...
    _rupture_sections: pd.DataFrame = ...
    _fs_with_rates: pd.DataFrame = ...
    _fs_with_soln_rates: pd.DataFrame = ...
    _rs_with_rupture_rates: pd.DataFrame = ...
    _fault_sections: pd.DataFrame = ...
    _ruptures_with_rupture_rates: pd.DataFrame = ...
    _archive_path: Optional[Path]
    _archive: Optional[io.BytesIO]

    FAULTS_PATH: Union[Path, str] = ''

    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        """solution requires fault sections"""

    @property
    def fault_sections_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """solution requires fault sections with rates"""

    @property
    def rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture."""

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        """the properties of each rupture."""

    @property
    def average_slips(self) -> gpd.GeoDataFrame:
        """the average slips for each rupture."""

    @property
    def section_target_slip_rates(self) -> gpd.GeoDataFrame:
        """the inversion target slip rates for each rupture."""

    @property
    def indices(self) -> gpd.GeoDataFrame:
        """the fault sections involved in each rupture."""

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """builder method returning the fault surfaces."""

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """builder method returning the rupture surface of a given rupture id."""

    @staticmethod
    def filter_solution(solution: Any, rupture_ids: npt.ArrayLike) -> Any:
        """return a new solution containing just the ruptures specified"""
        raise NotImplementedError()

    @property
    def rs_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture section."""

    @property
    def archive_path(self) -> Optional[Path]:
        """the path to the archive file"""

    @property
    def archive(self) -> Optional[zipfile.ZipFile]:
        """the archive instance"""


class CompositeSolutionProtocol(Protocol):

    _solutions: Mapping[str, InversionSolutionProtocol] = {}
    _archive_path: Union[Path, str] = ''

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
