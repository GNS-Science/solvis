"""This module defines type classes for the main interfaces in the `inversion_solution` package.

Todo:
    With the refactoring done on various classes/modules, most of these protocol classes can be
    dropped and function docstrings migrated to the functional code.

Classes:
    InversionSolutionProtocol: the interface for an InversionSolution
    CompositeSolutionProtocol: interface for CompositeSolution

"""

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Protocol, Union

import geopandas as gpd

if TYPE_CHECKING:
    from inversion_solution import InversionSolution


class AggregateSolutionFileProtocol(Protocol):
    """Type for AggregateSolutionFile."""

    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        """Enable fast indices."""
        raise NotImplementedError()


class CompositeSolutionProtocol(Protocol):
    """Type for CompositeSolution."""

    _solutions: Mapping[str, 'InversionSolution'] = {}
    _archive_path: Optional[Path]

    def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
        """Builder method returning the rupture surface of a given rupture id."""
        raise NotImplementedError()

    @property
    def archive_path(self):
        """The path to the archive file."""
        raise NotImplementedError()


class ModelLogicTreeBranch(Protocol):
    """what we can expect from nzshm-model.....Branch."""

    values: List[Any]
    weight: float
    onfault_nrml_id: Union[str, None] = ""
    distributed_nrml_id: Union[str, None] = ""
    inversion_solution_id: Union[str, None] = ""
    inversion_solution_type: Union[str, None] = ""


class SetOperationEnum(Enum):
    """Enumerated type for common set operations."""

    UNION = 1
    INTERSECTION = 2
    DIFFERENCE = 3
    SYMMETRIC_DIFFERENCE = 4
