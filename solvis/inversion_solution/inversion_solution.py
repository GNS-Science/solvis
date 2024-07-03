import io
import zipfile
from pathlib import Path
from typing import Union

import numpy.typing as npt

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import InversionSolutionProtocol, ModelLogicTreeBranch


class InversionSolution(InversionSolutionFile, InversionSolutionOperations):
    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolution':
        """
        Read an inversion solution from an archive zipfile.

        Archive validity is checked with the presence of a `ruptures/indices.csv` file within.

        Parameters:
            instance_or_path: a Path object, filename or in-memory binary IO stream

        Returns:
            A new InversionSolution with the archive location associated.
        """
        new_solution = InversionSolution()

        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/indices.csv' in zf.namelist()
            new_solution._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            new_solution._archive_path = Path(instance_or_path)
        return new_solution

    @staticmethod
    def filter_solution(solution: InversionSolutionProtocol, rupture_ids: npt.ArrayLike) -> 'InversionSolution':
        """
        Filter an InversionSolution by a subset of its rupture IDs.

        Parameters:
            solution: inversion solution data
            rupture_ids: A NumPy sequence of rupture ID numbers

        Returns:
            A new InversionSolution only containing data for the rupture IDs specified.
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
        ns.set_props(rates, ruptures, indices, solution.fault_sections.copy(), average_slips)
        ns._archive_path = solution._archive_path
        return ns


class BranchInversionSolution(InversionSolution):
    """Just an ordinary InversionSolution with branch attribute added"""

    branch: ModelLogicTreeBranch
    fault_system: Union[str, None] = ""
    rupture_set_id: Union[str, None] = ""

    @staticmethod
    def new_branch_solution(
        solution: InversionSolutionProtocol, branch: ModelLogicTreeBranch, fault_system: str, rupture_set_id: str
    ) -> 'BranchInversionSolution':
        ruptures = solution.ruptures.copy()
        rates = solution.rupture_rates.copy()
        indices = solution.indices.copy()

        bis = BranchInversionSolution()
        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.set_props(rates, ruptures, indices, solution.fault_sections.copy(), solution.average_slips.copy())
        bis._archive_path = solution._archive_path
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
