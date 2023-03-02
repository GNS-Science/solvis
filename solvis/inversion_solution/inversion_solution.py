import zipfile
from pathlib import Path
from typing import Union

import numpy.typing as npt

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import InversionSolutionProtocol, ModelLogicTreeBranch


class InversionSolution(InversionSolutionFile, InversionSolutionOperations):
    @staticmethod
    def from_archive(archive_path: Union[Path, str]) -> 'InversionSolution':
        new_solution = InversionSolution()
        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        new_solution._archive_path = Path(archive_path)
        return new_solution

    @staticmethod
    def filter_solution(solution: InversionSolutionProtocol, rupture_ids: npt.ArrayLike) -> 'InversionSolution':
        rr = solution.ruptures
        ra = solution.rates
        ri = solution.indices
        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

        # all other props are derived from these ones
        ns = InversionSolution()
        ns.set_props(rates, ruptures, indices, solution.fault_sections.copy())
        ns._archive_path = solution._archive_path
        # ns._surface_builder = SolutionSurfacesBuilder(ns)
        return ns


class BranchInversionSolution(InversionSolution):
    """Just an ordinary InversionSolution with branch attribute added"""

    branch: ModelLogicTreeBranch

    @staticmethod
    def new_branch_solution(
        solution: InversionSolutionProtocol, branch: ModelLogicTreeBranch
    ) -> 'BranchInversionSolution':
        ruptures = solution.ruptures.copy()
        rates = solution.rates.copy()
        indices = solution.indices.copy()

        # all other props are derived from these ones
        bis = BranchInversionSolution()
        bis.branch = branch
        bis.set_props(rates, ruptures, indices, solution.fault_sections.copy())
        bis._archive_path = solution._archive_path
        return bis
