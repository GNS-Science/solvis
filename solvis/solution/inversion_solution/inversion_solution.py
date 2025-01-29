r"""
This module handles the standard output of an OpenSHA grand inversion.

Classes:
    InversionSolution: A python interface for an OpenSHA Inversion Solution archive.
    BranchInversionSolution: A subclass of InversionSolution with some logic tree branch attributes.

Examples:
    ```py
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>> rupture_ids = solvis.filter\
            .FilterRuptureIds(solution)\
            .for_magnitude(min_mag=5.75, max_mag=6.25)
    >>>
    >>> rates = solution.section_participation_rates(rupture_ids)
    ```
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Union

import geopandas as gpd

from solvis.dochelper import inherit_docstrings

from ..solution_surfaces_builder import SolutionSurfacesBuilder
from ..typing import InversionSolutionProtocol, ModelLogicTreeBranch
from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_model import InversionSolutionModel

log = logging.getLogger(__name__)


@inherit_docstrings
class InversionSolution(InversionSolutionProtocol):
    """A python interface for an OpenSHA Inversion Solution archive.

    Attributes:
     model: the dataframes model of the solution.
     solution_file: the archive file instance.
     fault_regime: the type of fault system.

    Methods:
     from_archive: deserialise an instance from zip archive.
     to_archive: serialise an instance to a zip archive.
     filter_solution: get a new InversionSolution instance, filtered by rupture ids.
     rupture_surface: get a geopandas dataframe representing a rutpure surface.
     fault_surfaces: get a geopandas dataframe representing the fault surfaces.
    """

    # Docstrings for most methods are found in the `InversionSolutionProtocol` class.

    def __init__(self, solution_file: Optional[InversionSolutionFile] = None):
        """Instantiuate a new instance.

        Args:
            solution_file: a solution archive file instance.
        """
        self._solution_file = solution_file or InversionSolutionFile()
        self._model = InversionSolutionModel(self._solution_file)

    @property
    def model(self) -> InversionSolutionModel:
        return self._model

    @property
    def solution_file(self) -> InversionSolutionFile:
        return self._solution_file

    @property
    def fault_regime(self) -> str:
        return self._solution_file.fault_regime

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolution':
        new_solution_file = InversionSolutionFile()

        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/indices.csv' in zf.namelist()
            new_solution_file._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            new_solution_file._archive_path = Path(instance_or_path)
        return InversionSolution(new_solution_file)

    @staticmethod
    def filter_solution(solution: 'InversionSolutionProtocol', rupture_ids: Iterable[int]) -> 'InversionSolution':
        # model = solution.model
        rr = solution.solution_file.ruptures
        ra = solution.solution_file.rupture_rates
        ri = solution.solution_file.indices
        avs = solution.solution_file.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        ns = InversionSolution()

        ns.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), average_slips
        )

        ## TODO:  there should be a new in-memory archive ??
        ns.solution_file._archive_path = solution.solution_file.archive_path

        return ns


class BranchInversionSolution(InversionSolution):
    """Extend InversionSolution with the branch attributes.

    Attributes:
        branch: a logic tree branch instance.
        fault_system: A string representing the fault System (e.g `CRU`, 'HIK`).
        rupture_set_id: a string ID for the rupture_set_id.

    Methods:
        new_branch_solution: produce a new `BranchInversionSolution` instance.

    Todo:
        - can this functionality be done more simply and/or
        - can we make better use of latest `nzshm_model` and its' dataclasses.

    """

    branch: ModelLogicTreeBranch
    fault_system: Union[str, None] = ""
    rupture_set_id: Union[str, None] = ""

    @staticmethod
    def new_branch_solution(
        solution: InversionSolution, branch: ModelLogicTreeBranch, fault_system: str, rupture_set_id: str
    ) -> 'BranchInversionSolution':
        """Produce a new `BranchInversionSolution` instance with the given arguments.

        Args:
            solution: a solution instance.
            branch: a Logic tree branch instance (including branch metadata, weight, sources, etc).
            fault_system: a string representing the fault system (e.g `CRU`, 'HIK`).
            rupture_set_id: id for the rupture_set_id.
        """
        ruptures = solution.solution_file.ruptures.copy()
        rates = solution.solution_file.rupture_rates.copy()
        indices = solution.solution_file.indices.copy()

        # print(solution.solution_file.fault_sections)
        # assert 0

        bis = BranchInversionSolution()
        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), solution.solution_file.average_slips
        )
        bis.solution_file._archive_path = solution.solution_file._archive_path
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
