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

from ..solution_surfaces_builder import SolutionSurfacesBuilder
from ..typing import ModelLogicTreeBranch
from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_model import InversionSolutionModel

log = logging.getLogger(__name__)


# @inherit_docstrings
class InversionSolution:
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

    def __init__(self, solution_file: Optional[InversionSolutionFile] = None):
        """Instantiate a new instance.

        Args:
            solution_file: A solution archive file instance.
        """
        self._solution_file = solution_file or InversionSolutionFile()
        self._model = InversionSolutionModel(self._solution_file)

    @property
    def model(self) -> InversionSolutionModel:
        """Get the pandas dataframes API model of the solution.

        Returns:
            An instance of type InversionSolutionModel containing fault sections, rupture rates,
            and other relevant data.
        """
        return self._model

    @property
    def solution_file(self) -> InversionSolutionFile:
        """Get the solution file instance for the solution.

        Returns:
            an instance of type InversionSolutionFile.
        """
        return self._solution_file

    @property
    def fault_regime(self) -> str:
        """Get the fault regime label."""
        return self._solution_file.fault_regime

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        """Write the current solution to a new zip archive.

        Optionally cloning data from a base archive.

        In non-compatible mode (the default) rupture ids may not be a contiguous, 0-based sequence,
        so the archive will not be suitable for use with opensha. Compatible mode will reindex rupture tables,
        so that the original rutpure ids are lost.

        Args:
            archive_path: path or buffrer to write.
            base_archive_path: path to an InversionSolution archive to clone data from.
            compat: if True reindex the dataframes so that the archive remains compatible with opensha.
        """
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """Get the geometry of the solution fault surfaces projected onto the earth surface.

        Returns:
            A geopandas dataframe with fault surface information.
        """
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """Get the geometry of the rupture surface projected onto the earth surface.

        Args:
            rupture_id: The ID of the rupture whose surface is desired.

        Returns:
            A geopandas dataframe with the rupture surface information.
        """
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolution':
        """Deserialise an inversion solution instance from a zip archive.

        Archive validity is checked with the presence of a `ruptures/indices.csv` file.

        Args:
            instance_or_path: a Path object, filename or in-memory binary IO stream

        Returns:
            An instance of `InversionSolution`.
        """
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
    def filter_solution(solution: 'InversionSolution', rupture_ids: Iterable[int]) -> 'InversionSolution':
        """
        Filter the given solution by the specified rupture ids.

        This method doesn't modify any other parts of the solution (e.g trimming fault section tables or geojsons).

        Args:
            solution (InversionSolution): The input inversion solution to be filtered.
            rupture_ids (Iterable[int]): A collection of rupture ids to include in the filtered solution.

        Returns:
            InversionSolution: A new instance of InversionSolution containing only the ruptures with the given ids.
        """
        rr = solution.solution_file.ruptures
        ra = solution.solution_file.rupture_rates
        ri = solution.solution_file.indices
        avs = solution.solution_file.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        new_solution = InversionSolution()

        new_solution.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), average_slips
        )

        # TODO:  there should be a new in-memory archive ??
        new_solution.solution_file._archive_path = solution.solution_file.archive_path
        return new_solution

    @staticmethod
    def scale_rupture_rates(
        solution: 'InversionSolution',
        scale: float,
        rupture_ids: Optional[Iterable[int]] = None,
    ) -> 'InversionSolution':
        """
        Scale the rupture rates by a given factor.

        Args:
            solution (InversionSolution): The input inversion solution.
            scale (float): The scaling factor to apply to the rupture rates.
            rupture_ids (Optional[Iterable[int]], optional): Optional collection of specific rupture ids to scale.
                If provided, only these ruptures will be scaled. Defaults to None.

        Returns:
            InversionSolution: A new instance of InversionSolution with the scaled rupture rates.
        """
        # Retrieve the current rupture rates
        rr = solution.solution_file.rupture_rates.copy()

        # If specific rupture ids are provided, filter the data before scaling
        if rupture_ids is not None:
            rr_filter = rr["Rupture Index"].isin(rupture_ids)
            rr.loc[rr_filter, 'Annual Rate'] = rr[rr_filter]['Annual Rate'] * scale
        else:
            rr['Annual Rate'] = rr['Annual Rate'] * scale

        # Create a new InversionSolution instance
        new_solution = InversionSolution()

        # Update the rupture rates in the new solution
        new_solution.solution_file.set_props(
            rates=rr,
            ruptures=solution.solution_file.ruptures.copy(),
            indices=solution.solution_file.indices.copy(),
            fault_sections=solution.solution_file.fault_sections.copy(),
            average_slips=solution.solution_file.average_slips.copy(),
        )

        # Set the archive path for the new solution
        new_solution.solution_file._archive_path = solution.solution_file.archive_path

        return new_solution


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
