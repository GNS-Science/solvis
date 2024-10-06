"""
This module handles the standard output of an OpenSHA grand inversion.

Classes:
    InversionSolution: A python interface for an OpenSHA Inversion Solution archive.
    BranchInversionSolution: A subclass of InversionSolution with some logic tree branch
     attributes.

Examples:
    ```py
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>>
    >>> rids = solvis.filter.FilterRuptureIds(solution)\\
            .for_magnitude(min_mag=5.75, max_mag=6.25)
    >>>
    >>> rates = solution.section_participation_rates(rupture_ids=rids)
    >>> rates
    ```
"""
import io
import zipfile
from pathlib import Path
from typing import Union

import numpy.typing as npt
import pandas as pd

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import ModelLogicTreeBranch


class InversionSolution(InversionSolutionOperations):
    """A python interface for an OpenSHA Inversion Solution archive.

    Methods:
     from_archive: deserialise an instance from zip archive.
     filter_solution: get a new InversionSolution instance, filtered by rupture ids.
    """

    _inversion_solution_file: InversionSolutionFile

    @property
    def IO(self) -> InversionSolutionFile:
        """
        Entry point for the io methods of InversionSolutionFile
        """
        return self._inversion_solution_file

    """
    @property
    def archive(self) -> self.IO.archive:
        return self.IO.archive

    @property
    def archive_path(self):
        return self.IO.archive_path

    @property
    def rupture_rates(self):
        return self.IO.rupture_rates

    @property
    def ruptures(self):
        return self.IO.ruptures

    @property
    def indices(self):
        return self.IO.indices

    @property
    def fault_regime(self):
        return self.IO.fault_regime

    @property
    def logic_tree_branch(self):
        return self.IO.logic_tree_branch

    @property
    def average_slips(self):
        return self.IO.average_slips

    @property
    def section_target_slip_rates(self):
        return self.IO.section_target_slip_rates

    @property
    def fault_sections(self):
        return self.IO.fault_sections

    @property
    def rupture_sections(self):
        return self.IO.rupture_sections

    @property
    def ruptures_with_rupture_rates(self):
        return self.IO.ruptures_with_rupture_rates

    @property
    def rs_with_rupture_rates(self):
        return self.IO.rs_with_rupture_rates

    @property
    def fault_sections_with_solution_slip_rates(self):
        return self.IO.fault_sections_with_solution_slip_rates

    @property
    def fault_sections_with_rupture_rates(self):
        return self.IO.fault_sections_with_rupture_rates
    """

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        return self.IO.to_archive(archive_path, base_archive_path, compat)

    def set_props(
        self,
        rates: pd.DataFrame,
        ruptures: pd.DataFrame,
        indices: pd.DataFrame,
        fault_sections: pd.DataFrame,
        average_slips: pd.DataFrame,
    ):
        return self.IO.set_props(rates, ruptures, indices, fault_sections, average_slips)

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

        inversion_solution_file = InversionSolutionFile.from_archive(instance_or_path)

        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/indices.csv' in zf.namelist()
            inversion_solution_file._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            inversion_solution_file._archive_path = Path(instance_or_path)

        solution = InversionSolution()
        solution._inversion_solution_file = inversion_solution_file
        return solution

    @staticmethod
    def filter_solution(solution: 'InversionSolution', rupture_ids: npt.ArrayLike) -> 'InversionSolution':
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
        ns._inversion_solution_file = InversionSolutionFile()
        ns.set_props(rates, ruptures, indices, solution.fault_sections.copy(), average_slips)
        ns._inversion_solution_file._archive_path = solution.archive_path
        return ns


class BranchInversionSolution(InversionSolution):
    """Extend InversionSolution with the branch attributes:

    Attributes:
        branch: a logic tree branch instance.
        fault_system: A string representing the fault System (e.g `CRU`, 'HIK`).
        rupture_set_id: a string ID for the rupture_set_id.

    Todo:
        - can this functionality be done more simply and/or
        - can we make better use of latest `nzshm_model` and it's dataclasses.

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

        bis = BranchInversionSolution()
        bis._inversion_solution_file = InversionSolutionFile()
        # print(solution._inversion_solution_file.archive_path)
        bis._inversion_solution_file._archive_path = solution._inversion_solution_file.archive_path

        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.set_props(rates, ruptures, indices, solution.fault_sections.copy(), solution.average_slips.copy())
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
