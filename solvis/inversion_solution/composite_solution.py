import io
import zipfile
from pathlib import Path
from typing import Any, Dict, Union

import geopandas as gpd
import pandas as pd

from .fault_system_solution import FaultSystemSolution

# from .typing import CompositeSolutionProtocol
from .inversion_solution_operations import CompositeSolutionOperations


class CompositeSolution(CompositeSolutionOperations):

    _solutions: Dict[str, FaultSystemSolution] = {}
    _source_logic_tree: Any

    def __init__(self, source_logic_tree):
        self._source_logic_tree = source_logic_tree
        self._solutions = {}
        # print('__init__', self._solutions)

    def add_fault_system_solution(self, fault_system: str, fault_system_solution: FaultSystemSolution):
        # print(">>> add_fault_system_solution", self, fault_system)
        if fault_system in self._solutions.keys():
            raise ValueError(f"fault system with key: {fault_system} exists already. {self._solutions.keys()}")
        self._solutions[fault_system] = fault_system_solution
        return self

    @property
    def archive_path(self):
        return self._archive_path

    @property
    def source_logic_tree(self):
        return self._source_logic_tree

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

    def to_archive(self, archive_path: Union[Path, str]):
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for key, fss in self._solutions.items():
                if fss.archive_path is None:
                    raise RuntimeError("archive_path is not defined")
                else:
                    zout.write(fss.archive_path, arcname=f"{key}_fault_system_solution.zip")
        self._archive_path = archive_path

    @staticmethod
    def from_archive(archive_path: Path, source_logic_tree: Any) -> 'CompositeSolution':
        new_solution = CompositeSolution(source_logic_tree)

        # print("NEW_SOL", new_solution, new_solution._solutions, new_solution.archive_path)
        # zout = zipfile.ZipFile(archive_path)
        # zout.extractall(archive_path.parent)

        for fault_system_lt in source_logic_tree.fault_system_lts:
            if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:

                assert zipfile.Path(archive_path, at=f'{fault_system_lt.short_name}_fault_system_solution.zip').exists()

                # print(f"fault_system_lt.short_name: {fault_system_lt.short_name }")
                fss = FaultSystemSolution.from_archive(
                    zipfile.ZipFile(
                        io.BytesIO(
                            zipfile.Path(
                                archive_path, at=f'{fault_system_lt.short_name}_fault_system_solution.zip'
                            ).read_bytes()
                        )
                    )
                    # Path(archive_path.parent, f"{fault_system_lt.short_name}_fault_system_solution.zip")
                )
                new_solution.add_fault_system_solution(fault_system_lt.short_name, fss)

        new_solution._archive_path = archive_path
        return new_solution
