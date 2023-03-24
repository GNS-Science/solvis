import zipfile
from pathlib import Path
from typing import Union

import numpy.typing as npt

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import InversionSolutionProtocol, ModelLogicTreeBranch


class InversionSolution(InversionSolutionFile, InversionSolutionOperations):
    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, zipfile.ZipFile]) -> 'InversionSolution':
        new_solution = InversionSolution()

        if isinstance(instance_or_path, zipfile.ZipFile):
            assert 'ruptures/indices.csv' in instance_or_path.namelist()
            new_solution._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            new_solution._archive_path = Path(instance_or_path)
        return new_solution

    @staticmethod
    def filter_solution(solution: InversionSolutionProtocol, rupture_ids: npt.ArrayLike) -> 'InversionSolution':
        rr = solution.ruptures
        ra = solution.rates
        ri = solution.indices
        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

        # all other solution properties are derived from those above
        ns = InversionSolution()
        ns.set_props(rates, ruptures, indices, solution.fault_sections.copy())
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
        rates = solution.rates.copy()
        indices = solution.indices.copy()

        bis = BranchInversionSolution()
        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.set_props(rates, ruptures, indices, solution.fault_sections.copy())
        bis._archive_path = solution._archive_path
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
