import json
import time
import zipfile
from pathlib import Path
from typing import Any, List, Union

import geopandas as gpd
import numpy.typing as npt
import pandas as pd

from .solution_surfaces_builder import SolutionSurfacesBuilder


def data_to_zip_direct(z, data, name):
    zinfo = zipfile.ZipInfo(name, time.localtime()[:6])
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zinfo, data)


WARNING = """
# Attention

This Inversion Solution archive has been modified
using the solvis python library.

Data may have been filtered out of an original
Inversion Solution archive file:
 - 'solution/rates.csv'
 - 'ruptures/properties.csv'
 - 'ruptures/indices.csv'

"""


class InversionSolution:
    """
    Class to handle the opensha modular archive form
    """

    RATES_PATH = 'solution/rates.csv'
    RUPTS_PATH = 'ruptures/properties.csv'
    INDICES_PATH = 'ruptures/indices.csv'
    FAULTS_PATH = 'ruptures/fault_sections.geojson'
    METADATA_PATH = 'metadata.json'
    LOGIC_TREE_PATH = 'ruptures/logic_tree_branch.json'

    def __init__(self) -> None:
        # self._init_props()
        self._rates = None
        self._ruptures = None
        self._rupture_props = None
        self._indices = None
        self._rs_with_rates = None
        self._fs_with_rates = None
        self._ruptures_with_rates = None
        self._logic_tree_branch: List[Any] = []
        self._fault_regime: str = ''
        self._fault_sections = None
        self._rupture_sections = None
        self._archive_path: Union[Path, str]
        # self._surface_builder: SolutionSurfacesBuilder

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

    @staticmethod
    def from_archive(archive_path: Union[Path, str]):
        ns = InversionSolution()

        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        ns._archive_path = Path(archive_path)
        # ns._surface_builder = SolutionSurfacesBuilder(ns)
        # ns._metadata = json.load(METADATA_PATH)
        return ns

    def to_archive(self, archive_path, base_archive_path, compat=True):
        """
        Writes the current solution to a new zip archive, optionally cloning data from a base archive
        Note this is not well tested, use with caution!

        """
        if compat:
            self._to_compatible_archive(archive_path, base_archive_path)
        else:
            self._to_non_compatible_archive(archive_path, base_archive_path)

    def _to_compatible_archive(self, archive_path, base_archive_path):
        """
        compatible because it does reindex the tables from 0 as required by opensha.
        assume that self is some altered
        """
        zout = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)

        # this copies in memory, skipping the datframe files we want to overwrite
        zin = zipfile.ZipFile(base_archive_path, 'r')

        for item in zin.infolist():
            if item.filename in [self.RATES_PATH, self.RUPTS_PATH, self.INDICES_PATH]:
                continue
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        def reindex_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
            new_df = dataframe.copy().reset_index(drop=True).drop(columns=['Rupture Index'])
            new_df.index = new_df.index.rename('Rupture Index')
            return new_df

        # write out the `self` dataframes
        data_to_zip_direct(zout, reindex_dataframe(self._rates).to_csv(), self.RATES_PATH)
        data_to_zip_direct(zout, reindex_dataframe(self._ruptures).to_csv(), self.RUPTS_PATH)
        data_to_zip_direct(zout, reindex_dataframe(self._indices).to_csv(), self.INDICES_PATH)
        # and the warning notice
        data_to_zip_direct(zout, WARNING, "WARNING.md")

    def _to_non_compatible_archive(self, archive_path, base_archive_path):
        """
        It' non-compatible because it does not reindex the tables from 0 as required by opensha. So it cannot be
        used to produce opensha reports etc.

        Writes the current solution to a new zip archive, optionally cloning data from a base archive
        Note this is not well tested, use with caution!

        """
        zout = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)

        # this copies in memory, skipping the datframe files we want to overwrite
        zin = zipfile.ZipFile(base_archive_path, 'r')
        for item in zin.infolist():
            if item.filename in [self.RATES_PATH, self.RUPTS_PATH, self.INDICES_PATH]:
                continue
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        # write out the `self` dataframes
        data_to_zip_direct(zout, self._rates.to_csv(index=False), self.RATES_PATH)
        data_to_zip_direct(zout, self._ruptures.to_csv(), self.RUPTS_PATH)
        data_to_zip_direct(zout, self._indices.to_csv(), self.INDICES_PATH)

        # and the warning notice
        data_to_zip_direct(zout, WARNING, "WARNING.md")

    def _dataframe_from_csv(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = pd.read_csv(zipfile.Path(self._archive_path, at=path).open()).convert_dtypes()
        return prop

    def _geodataframe_from_geojson(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = gpd.read_file(zipfile.Path(self._archive_path, at=path).open())
        return prop

    @property
    def logic_tree_branch(self) -> list:
        """
        get values from the opensha logic_tree_branch data file.

        :return: list of value objects
        """
        if not self._logic_tree_branch:
            ltb = json.load(zipfile.Path(self._archive_path, at=self.LOGIC_TREE_PATH).open())
            if type(ltb) == list:
                self._logic_tree_branch = ltb
            elif type(ltb.get('values')) == list:
                self._logic_tree_branch = ltb.get('values')
            else:  # pragma: no cover
                raise ValueError(f"unhandled logic_tree_branch: {ltb}")
        return self._logic_tree_branch

    @property
    def fault_regime(self) -> str:
        """
        get the fault regime as defined in the opensha logic_tree_branch data file.

        :return: "CRUSTAL" or "SUBDUCTION"
        """

        def get_regime() -> str:
            for obj in self.logic_tree_branch:  # .get('values'):
                val = obj.get('value')
                if val:
                    name = val.get('name')
                    if name == 'Fault Regime':
                        return val.get('enumName')
            raise ValueError(
                f"expected Fault Regime missing in solution logic tree, see {self.LOGIC_TREE_PATH}."
            )  # pragma: no cover

        if not self._fault_regime:
            self._fault_regime = get_regime()
        return self._fault_regime

    @property
    def rates(self):
        return self._dataframe_from_csv(self._rates, self.RATES_PATH)

    @property
    def ruptures(self):
        return self._dataframe_from_csv(self._ruptures, self.RUPTS_PATH)

    @property
    def indices(self):
        """
        Rupture Index,Num Sections,# 1,# 2,# 3,# 4,# 5,# 6,# 7,# 8,# 9,# 10,# 11,# 12,# 13,# 14,# 15,# 16,# 17,# 18,# 19,# 20,# 21,# 22,# 23,# 24,# 25,# 26,# 27,# 28,# 29,# 30,# 31,# 32,# 33,# 34,# 35,# 36,# 37,# 38,# 39,# 40,# 41,# 42,# 43,# 44,# 45,# 46,# 47,# 48,# 49,# 50,# 51,# 52,# 53,# 54,# 55,# 56,# 57,# 58,# 59,# 60,# 61,# 62,# 63,# 64,# 65,# 66,# 67,# 68,# 69,# 70,# 71,# 72,# 73,# 74,# 75,# 76,# 77,# 78,# 79,# 80,# 81,# 82,# 83,# 84,# 85,# 86,# 87,# 88,# 89,# 90,# 91,# 92,# 93,# 94,# 95,# 96,# 97,# 98,# 99,# 100,# 101,# 102,# 103,# 104,# 105,# 106,# 107,# 108,# 109  # noqa
        0,2,0,1
        1,4,0,1,1081,1080
        2,5,0,1,1081,1080,1079
        3,7,0,1,1081,1080,1079,1078,1077
        4,8,0,1,1081,1080,1079,1078,1077,1076
        5,9,0,1,1081,1080,1079,1078,1077,1076,1075
        etc
        """
        return self._dataframe_from_csv(self._indices, self.INDICES_PATH)

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        return fault_sections

    def set_props(self, rates, ruptures, indices, fault_sections):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices

    @property
    def rupture_sections(self):

        if self._rupture_sections is not None:
            return self._rupture_sections  # pragma: no cover

        rs = self.indices  # _dataframe_from_csv(self._rupture_sections, 'ruptures/indices.csv').copy()

        # remove "Rupture Index, Num Sections" column
        df_table = rs.drop(rs.iloc[:, :2], axis=1)

        # convert to relational table, turning headings index into plain column
        df2 = df_table.stack().reset_index()

        # remove the headings column
        df2.drop(df2.iloc[:, 1:2], inplace=True, axis=1)
        df2 = df2.set_axis(['rupture', 'section'], axis='columns', copy=False)

        # set property
        self._rupture_sections = df2
        return self._rupture_sections

    @property
    def fault_sections_with_rates(self) -> gpd.GeoDataFrame:
        """
        Calculate and cache the fault sections and their rupture rates.

        :return: a gpd.GeoDataFrame
        """
        if self._fs_with_rates is not None:
            return self._fs_with_rates
        self._fs_with_rates = self.rs_with_rates.join(self.fault_sections, 'section', how='inner')
        return self._fs_with_rates

    @property
    def rs_with_rates(self):
        if self._rs_with_rates is not None:
            return self._rs_with_rates  # pragma: no cover
        # df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.rupture_sections.join(self.ruptures_with_rates, 'rupture')
        return self._rs_with_rates

    @property
    def ruptures_with_rates(self):
        if self._ruptures_with_rates is not None:
            return self._ruptures_with_rates  # pragma: no cover
        self._ruptures_with_rates = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        return self._ruptures_with_rates

    # return the rupture ids for any ruptures intersecting the polygon
    def get_ruptures_intersecting(self, polygon):
        q0 = gpd.GeoDataFrame(self.fault_sections)
        q1 = q0[q0['geometry'].intersects(polygon)]  # whitemans_0)]
        sr = self.rs_with_rates
        qdf = sr.join(q1, 'section', how='inner')
        return qdf.rupture.unique()

    def get_ruptures_for_parent_fault(self, parent_fault_name: str):
        # sr = sol.rs_with_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.fault_sections[self.fault_sections['ParentName'] == parent_fault_name]
        qdf = self.rupture_sections.join(sects, 'section', how='inner')
        return qdf.rupture.unique()
