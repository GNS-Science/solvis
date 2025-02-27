"""This module provides the CompositeSolution class.

Classes:
    CompositeSolution: a container class collecting FaultSystemSolution instances.
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

import geopandas as gpd
import pandas as pd
from nzshm_model import logic_tree

from solvis.solution.inversion_solution.inversion_solution_file import data_to_zip_direct

from .fault_system_solution import FaultSystemSolution

log = logging.getLogger(__name__)


class CompositeSolution:
    """A container class collecting FaultSystemSolution instances and a source_logic_tree.

    Methods:
        add_fault_system_solution:
        archive_path:
        from_archive:
        get_fault_system_codes:
        get_fault_system_solution:
        source_logic_tree:
        to_archive:
    """

    _solutions: Dict[str, FaultSystemSolution]
    _source_logic_tree: 'logic_tree.SourceLogicTree'
    _archive_path: Optional[Path] = None

    def __init__(self, source_logic_tree: 'logic_tree.SourceLogicTree'):
        """Instantiate a new instance.

        Args:
            source_logic_tree: the logic tree instance.
        """
        self._source_logic_tree = source_logic_tree
        self._solutions = {}
        # print('__init__', self._solutions)

    def add_fault_system_solution(self, fault_system: str, fault_system_solution: FaultSystemSolution):
        """Add a new FaultSystemSolution instance."""
        # print(">>> add_fault_system_solution", self, fault_system)
        if fault_system in self._solutions.keys():
            raise ValueError(
                f"fault system with key: {fault_system} exists already. {self._solutions.keys()}"
            )  # pragma: no cover
        self._solutions[fault_system] = fault_system_solution
        return self

    def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
        return self._solutions[fault_system].rupture_surface(rupture_id)

    def fault_surfaces(self):
        surfaces = []
        for fault_system, sol in self._solutions.items():
            solution_df = sol.fault_surfaces().to_crs("EPSG:4326")
            solution_df.insert(0, 'fault_system', fault_system)
            surfaces.append(solution_df)
        all_surfaces_df = pd.concat(surfaces, ignore_index=True)
        return gpd.GeoDataFrame(all_surfaces_df)

    @property
    def archive_path(self) -> Union[Path, None]:
        """Get the path of the instance."""
        return self._archive_path

    @property
    def source_logic_tree(self):
        """Get the source_logic_tree instance."""
        return self._source_logic_tree

    @property
    def rupture_rates(self) -> pd.DataFrame:
        """
        Calculate (and cache) the rupture rates.

        Returns:
            a `pandas.DataFrame` with columns: </br>
                fault_system,
                Rupture Index,
                rate_max,
                rate_min,
                rate_count,
                rate_weighted_mean
        """
        # if self._fs_with_rates is not None:
        #     return self._fs_with_rates

        all_rates = [sol.solution_file.rupture_rates for sol in self._solutions.values()]
        all_rates_df = pd.concat(all_rates, ignore_index=True)
        return all_rates_df

    @property
    def composite_rates(self) -> pd.DataFrame:
        """
        Calculate (and cache) the composite rates.

        Returns:
            a `pandas.DataFrame` with columns: <br/>
                Rupture Index,
                fault_system,
                weight,
                rupture_set_id,
                solution_id,
                Annual Rate
        """
        # if self._fs_with_rates is not None:
        #     return self._fs_with_rates

        all_rates = [sol.model.composite_rates for sol in self._solutions.values()]
        all_rates_df = pd.concat(all_rates, ignore_index=True)
        return all_rates_df

    @property
    def fault_sections_with_rupture_rates(self) -> pd.DataFrame:
        """Get a dataframe containing the fault sections for all fault_system_solutions.

        Returns:
            a `pandas.DataFrame` with columns: <br/>
                fault_system,
                ...
                rate_count,
                rate_weighted_mean
        """
        all = [
            gpd.GeoDataFrame(sol.model.fault_sections_with_rupture_rates).to_crs("EPSG:4326")
            for sol in self._solutions.values()
        ]
        print(all)
        all_df = pd.concat(all, ignore_index=True)
        return all_df

    def to_archive(self, archive_path: Union[Path, str]):
        """Serialize a CompositeSolution instance to a zip archive.

        Args:
            archive_path: a valid target file path.
        """
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for key, fss in self._solutions.items():
                fss_name = f"{key}_fault_system_solution.zip"
                fss_file = fss.solution_file
                if fss_file._archive:
                    # serialise the 'in-memory' archive
                    fss_file._archive.seek(0)
                    data_to_zip_direct(zout, fss_file._archive.read(), fss_name)
                else:  # pragma: no cover
                    raise RuntimeError("_archive is not defined")
        self._archive_path = Path(archive_path)

    @staticmethod
    def from_archive(archive_path: Path, source_logic_tree: 'logic_tree.SourceLogicTree') -> 'CompositeSolution':
        """Deserialize a CompositeSolution instance from an archive path.

        Args:
            archive_path: a valid target file path.
            source_logic_tree: a source_logic_tree instance.
        """
        new_solution = CompositeSolution(source_logic_tree)

        for fault_system_lt in source_logic_tree.branch_sets:
            if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
                assert zipfile.Path(archive_path, at=f'{fault_system_lt.short_name}_fault_system_solution.zip').exists()
                fss = FaultSystemSolution.from_archive(
                    io.BytesIO(
                        zipfile.Path(
                            archive_path, at=f'{fault_system_lt.short_name}_fault_system_solution.zip'
                        ).read_bytes()
                    )
                )
                new_solution.add_fault_system_solution(fault_system_lt.short_name, fss)

        new_solution._archive_path = archive_path
        return new_solution

    def get_fault_system_codes(self) -> Iterable[str]:
        """
        List fault systems contained within the composite solution.

        For the NSHM model this will typically be **PUY** for Puysegur,
        **HIK** for Hikurangi, **CRU** for Crustal.

        Returns:
            A list of fault system keys.
        """
        return list(self._solutions.keys())

    def get_fault_system_solution(self, fault_system_code: str) -> FaultSystemSolution:
        """Retrieve a `FaultSystemSolution` from within the composite solution.

        Codes can be retrieved with
        [`get_fault_system_codes`][solvis.solution.composite_solution.CompositeSolution.get_fault_system_codes]

        Args:
            fault_system_code: a named fault system code

        Returns:
            a specific FaultSystemSolution
        """
        return self._solutions[fault_system_code]
