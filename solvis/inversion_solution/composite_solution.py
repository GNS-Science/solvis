# import zipfile
# from pathlib import Path
from typing import Dict

import geopandas as gpd
import pandas as pd

from .fault_system_solution import FaultSystemSolution

# from .typing import CompositeSolutionProtocol
from .inversion_solution_operations import CompositeSolutionOperations


class CompositeSolution(CompositeSolutionOperations):

    _solutions: Dict[str, FaultSystemSolution] = {}

    # def __init__(self):

    def add_fault_system_solution(self, fault_system: str, fault_system_solution: FaultSystemSolution):
        assert fault_system not in self._solutions.keys()
        self._solutions[fault_system] = fault_system_solution
        return self

    @property
    def rates(self) -> pd.DataFrame:
        """
        Calculate (and cache) the rates.

        :return: a gpd.GeoDataFrame
        """
        # if self._fs_with_rates is not None:
        #     return self._fs_with_rates

        all_rates = [sol.rates for sol in self._solutions.values()]
        all_rates_df = pd.concat(all_rates, ignore_index=True)
        return all_rates_df

    @property
    def composite_rates(self) -> pd.DataFrame:
        """
        Calculate (and cache) the composite_rates.

        :return: a gpd.GeoDataFrame
        """
        # if self._fs_with_rates is not None:
        #     return self._fs_with_rates

        all_rates = [sol.composite_rates for sol in self._solutions.values()]
        all_rates_df = pd.concat(all_rates, ignore_index=True)
        return all_rates_df

    @property
    def fault_sections_with_rates(self) -> pd.DataFrame:
        all = [gpd.GeoDataFrame(sol.fault_sections_with_rates).to_crs("EPSG:4326") for sol in self._solutions.values()]
        all_df = pd.concat(all, ignore_index=True)
        return all_df
