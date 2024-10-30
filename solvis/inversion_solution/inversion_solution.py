"""
This module handles the standard output of an OpenSHA grand inversion.

Classes:
    InversionSolution: A python interface for an OpenSHA Inversion Solution archive.
    BranchInversionSolution: A subclass of InversionSolution with some logic tree branch attributes.

Examples:
    ```py
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>> model = solution.model

    >>> rupture_ids = solvis.filter.FilterRuptureIds(model)\\
            .for_magnitude(min_mag=5.75, max_mag=6.25)
    >>>
    >>> rates = model.section_participation_rates(rupture_ids)
    >>> rates
    ```
"""
import io
import zipfile
from inspect import getmembers
from pathlib import Path
from typing import Iterable, Optional, Union

import geopandas as gpd

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_model import InversionSolutionModel
from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import ModelLogicTreeBranch


def inherit_docstrings(cls):
    """A decorator function hoisting docstrings from superclass methods

    taken from: https://stackoverflow.com/a/17393254
    see also: https://github.com/rcmdnk/inherit-docstring for a pypi package
    """
    for name, method in getmembers(cls, lambda o: isinstance(o, property)):
        # print(f"inherit_docstrings {method} {name}")
        if method.__doc__:
            continue
        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                method.__doc__ = getattr(parent, name).__doc__
    # assert 0
    return cls


@inherit_docstrings
class InversionSolution:
    """A python interface for an OpenSHA Inversion Solution archive.

    Attributes:
     model: the dataframes model of the solution
     solution_file: the archive file handler

    Methods:
     from_archive: deserialise an instance from zip archive.
     filter_solution: get a new InversionSolution instance, filtered by rupture ids.
     to_archive: serialise an instance to a zip archive.


    """

    def __init__(self, solution_file: Optional[InversionSolutionFile] = None):
        """dont crash"""
        self._solution_file = solution_file or InversionSolutionFile()
        self._dataframe_operations = InversionSolutionModel(self._solution_file)

    @property
    def model(self) -> InversionSolutionModel:
        return self._dataframe_operations

    @property
    def solution_file(self) -> InversionSolutionFile:
        # """
        # An InversionSolutionFile instance

        # Returns:
        #     instance: the InversionSolutionFile
        # """
        return self._solution_file

    @property
    def fault_regime(self):
        return self._solution_file.fault_regime

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        """Write the current solution to a new zip archive."""
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolution':
        """
        Read and return an inversion solution from an OpenSHA archive file or byte-stream.

        Archive validity is checked with the presence of a `ruptures/indices.csv` file.

        Parameters:
            instance_or_path: a Path object, filename or in-memory binary IO stream

        Returns:
            An InversionSolution instance.
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
    def filter_solution(solution: 'InversionSolution', rupture_ids: Iterable) -> 'InversionSolution':
        """
        Filter an InversionSolution by a subset of its rupture IDs, returing a new smaller InversionSolution.

        NB. this is an utility method primarily for produicing test fixtures.

        Parameters:
            solution: an inversion solution instance.
            rupture_ids: a sequence of rupture ids.

        Returns:
            A new InversionSolution containing data for the rupture IDs specified.
        """
        model = solution.model
        rr = model.ruptures
        ra = model.rupture_rates
        ri = model.indices
        avs = model.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        ns = InversionSolution()

        ns.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), average_slips
        )
        ns.solution_file._archive_path = solution.solution_file._archive_path

        return ns


class BranchInversionSolution(InversionSolution):
    """Extend InversionSolution with the branch attributes:

    Attributes:
        branch: a logic tree branch instance.
        fault_system: A string representing the fault System (e.g `CRU`, 'HIK`).
        rupture_set_id: a string ID for the rupture_set_id.

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
        model = solution.model
        ruptures = model.ruptures.copy()
        rates = model.rupture_rates.copy()
        indices = model.indices.copy()

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
