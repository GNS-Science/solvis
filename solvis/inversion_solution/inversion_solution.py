import zipfile
from pathlib import Path
from typing import Union

import geopandas as gpd
import numpy.typing as npt

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import InversionSolutionProtocol


class InversionSolution(InversionSolutionFile, InversionSolutionOperations, InversionSolutionProtocol):
    def __init__(self) -> None:
        super().__init__()

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(archive_path: Union[Path, str]) -> InversionSolutionProtocol:
        new_solution = InversionSolution()
        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        new_solution._archive_path = Path(archive_path)
        return new_solution

    @staticmethod
    def new_solution(sol: 'InversionSolution', rupture_ids: npt.ArrayLike) -> 'InversionSolution':
        rr = sol.ruptures
        ra = sol.rates
        ri = sol.indices
        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

        # all other props are derived from these ones
        ns = InversionSolution()
        ns.set_props(rates, ruptures, indices, sol.fault_sections.copy())
        ns._archive_path = sol._archive_path
        # ns._surface_builder = SolutionSurfacesBuilder(ns)
        return ns
