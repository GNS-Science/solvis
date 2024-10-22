"""
This module handles the standard output of an OpenSHA grand inversion.

Classes:
    InversionSolution: A python interface for an OpenSHA Inversion Solution archive.
    BranchInversionSolution: A subclass of InversionSolution with some logic tree branch attributes.

Examples:
    ```py
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>>
    >>> rupture_ids = solvis.filter.FilterRuptureIds(solution)\\
            .for_magnitude(min_mag=5.75, max_mag=6.25)
    >>>
    >>> rates = solution.section_participation_rates(rupture_ids)
    >>> rates
    ```
"""
import io
import zipfile
from pathlib import Path
from typing import Iterable, Union, Optional

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import ModelLogicTreeBranch, InversionSolutionProtocol

from inspect import getmembers, isfunction, ismethod

def inherit_docstrings(cls):
    for name, method in getmembers(cls, lambda o: isinstance(o, property)):
        # print(f"inherit_docstrings {method} {name}")
        if method.__doc__: continue
        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                method.__doc__ = getattr(parent, name).__doc__
    # assert 0
    return cls

@inherit_docstrings
class InversionSolution(InversionSolutionProtocol, InversionSolutionOperations):
    """A python interface for an OpenSHA Inversion Solution archive.

    Methods:
     from_archive: deserialise an instance from zip archive.
     filter_solution: get a new InversionSolution instance, filtered by rupture ids.
     to_archive: serialise an instance to a zip archive.

    """

    def __init__(self, solution_file: Optional[InversionSolutionFile] = None):
        """dont crash"""
        self._solution_file = solution_file or InversionSolutionFile()
        super().__init__(self._solution_file)

    @property
    def average_slips(self):
        return self._solution_file.average_slips

    @property
    def section_target_slip_rates(self):
        return self._solution_file.section_target_slip_rates

    @property
    def fault_sections(self):
        return self._solution_file.fault_sections

    @property
    def fault_regime(self):
        return self._solution_file.fault_regime

    @property
    def logic_tree_branch(self):
        return self._solution_file.logic_tree_branch

    @property
    def solution_file(self) -> Optional[InversionSolutionFile]:
        """
        An InversionSolutionFile instance

        Returns:
            instance: the InversionSolutionFile
        """
        return self._solution_file

    @property
    def indices(self):
        return self._solution_file.indices

    @property
    def ruptures(self):
        return self._solution_file.ruptures

    @property
    def rupture_rates(self):
        return self._solution_file.rupture_rates

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        """Write the current solution to a new zip archive.
        """
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

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
        rr = solution.ruptures
        ra = solution.rupture_rates
        ri = solution.indices
        avs = solution.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        ns = InversionSolution()

        ns.solution_file.set_props(rates, ruptures, indices,
            solution.solution_file.fault_sections.copy(),
            solution.solution_file.average_slips)
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
        ruptures = solution.ruptures.copy()
        rates = solution.rupture_rates.copy()
        indices = solution.indices.copy()

        # print(solution.solution_file.fault_sections)
        # assert 0

        bis = BranchInversionSolution()
        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.solution_file.set_props(rates, ruptures, indices,
            solution.solution_file.fault_sections.copy(),
            solution.solution_file.average_slips)
        bis.solution_file._archive_path = solution.solution_file._archive_path
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
