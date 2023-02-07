import json
import time
import zipfile

import geopandas as gpd

# import numpy as np
import numpy.typing as npt
import pandas as pd
from shapely import get_coordinates
from shapely.geometry import LineString, Point

from solvis.geometry import create_surface, dip_direction


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


def create_subduction_section_surface(section: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    def calc_dip_dir(section: gpd.GeoDataFrame) -> float:
        assert type(section.geometry) == LineString
        flat_geom = LineString(get_coordinates(section.geometry))

        point_a = Point(reversed(flat_geom.coords[0]))
        point_b = Point(reversed(flat_geom.coords[-1]))

        return dip_direction(point_a, point_b)

    return create_surface(
        section["geometry"], calc_dip_dir(section), section["DipDeg"], section["UpDepth"], section["LowDepth"]
    )


def create_crustal_section_surface(section: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return create_surface(
        section["geometry"], section["DipDir"], section["DipDeg"], section["UpDepth"], section["LowDepth"]
    )


class InversionSolution:

    RATES_PATH = 'solution/rates.csv'
    RUPTS_PATH = 'ruptures/properties.csv'
    INDICES_PATH = 'ruptures/indices.csv'
    FAULTS_PATH = 'ruptures/fault_sections.geojson'
    METADATA_PATH = 'metadata.json'
    LOGIC_TREE_PATH = 'ruptures/logic_tree_branch.json'

    def __init__(self):
        """
        create an opensha modular archive
        """
        self._init_props()

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
        return ns

    def from_archive(self, archive_path):
        self._init_props()
        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        self._archive_path = archive_path
        # self._metadata = json.load(METADATA_PATH)
        return self

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

        zout = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)

        # this copies in memory, skipping the datframe files we want to overwrite
        zin = zipfile.ZipFile(base_archive_path, 'r')

        for item in zin.infolist():
            if item.filename in [self.RATES_PATH]:
                continue
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        # rebuild rates
        base_archive = InversionSolution().from_archive(base_archive_path)
        base_rates_df = base_archive.rates.copy()
        # print('base before reset:', base_rates_df[base_rates_df['Annual Rate']>0])
        # print()

        # set all base rates to zero (slow)
        for row in base_rates_df.itertuples(name=None):
            base_rates_df.iat[row[0], 1] = 0

        print('self._rates', self.rates[self.rates['Annual Rate'] > 0])
        print()

        # copy rates into new rates_df
        for row in self.rates.itertuples(name=None):
            # old_rate = str(base_rates_df.iat[row[0],1])
            base_rates_df.iat[row[0], 1] = row[2]
            # print("replacing: ", old_rate, row[2], row)

        print('base_after reset:', base_rates_df[base_rates_df['Annual Rate'] > 0])
        # print()
        assert base_rates_df[base_rates_df['Annual Rate'] > 0].size == self.rates[self.rates['Annual Rate'] > 0].size
        self._rates = base_rates_df

        # write out the `self` dataframes
        data_to_zip_direct(zout, self._rates.to_csv(index=False), self.RATES_PATH)
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

    def _init_props(self):
        self._rates = None
        self._ruptures = None
        self._rupture_props = None
        self._rupture_sections = None
        self._indices = None
        self._fault_sections = None
        self._rs_with_rates = None
        self._fs_with_rates = None
        self._ruptures_with_rates = None
        self._logic_tree_branch = None
        self._fault_regime = None

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
            else:
                raise ValueError(f"unhandled logic_tree_branch: {ltb}")
        return self._logic_tree_branch

    @property
    def fault_regime(self) -> str:
        """
        get the fault regime as defined in the opensha logic_tree_branch data file.

        :return: "CRUSTAL" or "SUBDUCTION"
        """

        def get_regime():
            for obj in self.logic_tree_branch:  # .get('values'):
                val = obj.get('value')
                if val:
                    name = val.get('name')
                    if name == 'Fault Regime':
                        return val.get('enumName')
            raise ValueError(f"expected Fault Regime missing in solution logic tree, see {self.LOGIC_TREE_PATH}.")

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

    @property
    def fault_sections(self):
        fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        return fault_sections

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the solution fault surfaces projected onto the earth surface.

        :param refine_dip_dir: option to override the dip_directon supplied, only applies to CRUSTAL
        :return: a gpd.GeoDataFrame
        """
        if self.fault_regime == 'SUBDUCTION':
            return self.fault_sections.set_geometry(
                [create_subduction_section_surface(section) for i, section in self.fault_sections.iterrows()]
            )
        if self.fault_regime == 'CRUSTAL':
            return self.fault_sections.set_geometry(
                [create_crustal_section_surface(section) for i, section in self.fault_sections.iterrows()]
            )

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the rupture fault surfaces projected onto the earth surface.

        :param rupture_id: ID of the rupture
        :return: a gpd.GeoDataFrame
        """
        df0 = self.fault_sections_with_rates
        rupt = df0[df0["Rupture Index"] == rupture_id]
        if self.fault_regime == 'SUBDUCTION':
            return rupt.set_geometry([create_subduction_section_surface(section) for i, section in rupt.iterrows()])
        if self.fault_regime == 'CRUSTAL':
            return rupt.set_geometry([create_crustal_section_surface(section) for i, section in rupt.iterrows()])

    def set_props(self, rates, ruptures, indices, fault_sections):
        self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices

    @property
    def rupture_sections(self):

        if self._rupture_sections is not None:
            return self._rupture_sections

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
            return self._rs_with_rates
        # df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.rupture_sections.join(self.ruptures_with_rates, 'rupture')
        return self._rs_with_rates

    @property
    def ruptures_with_rates(self):
        if self._ruptures_with_rates is not None:
            return self._ruptures_with_rates
        self._ruptures_with_rates = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        return self._ruptures_with_rates

    # return get the rupture ids for any ruptures intersecting the polygon
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
