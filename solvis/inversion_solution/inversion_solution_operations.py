import zipfile
from typing import Union

import geopandas as gpd
import pandas as pd


class InversionSolutionOperations:
    _fs_with_rates = None
    _rupture_sections = None
    _fs_with_rates = None
    _rs_with_rates = None
    _fault_sections = None
    _ruptures_with_rates: pd.DataFrame = None

    indices: gpd.GeoDataFrame = None
    ruptures: gpd.GeoDataFrame = None
    rates: gpd.GeoDataFrame = None

    FAULTS_PATH: Union[str, None] = None

    def _geodataframe_from_geojson(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = gpd.read_file(zipfile.Path(self._archive_path, at=path).open())
        return prop

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        return fault_sections

    @property
    def rupture_sections(self) -> gpd.GeoDataFrame:

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
    def rs_with_rates(self) -> gpd.GeoDataFrame:
        if self._rs_with_rates is not None:
            return self._rs_with_rates  # pragma: no cover
        # df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.rupture_sections.join(self.ruptures_with_rates, 'rupture')
        return self._rs_with_rates

    @property
    def ruptures_with_rates(self) -> pd.DataFrame:
        if self._ruptures_with_rates is not None:
            return self._ruptures_with_rates  # pragma: no cover

        print(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._ruptures_with_rates = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        return self._ruptures_with_rates

    # return the rupture ids for any ruptures intersecting the polygon
    def get_ruptures_intersecting(self, polygon) -> pd.Series:
        q0 = gpd.GeoDataFrame(self.fault_sections)
        q1 = q0[q0['geometry'].intersects(polygon)]  # whitemans_0)]
        sr = self.rs_with_rates
        qdf = sr.join(q1, 'section', how='inner')
        return qdf.rupture.unique()

    def get_ruptures_for_parent_fault(self, parent_fault_name: str) -> pd.Series:
        # sr = sol.rs_with_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.fault_sections[self.fault_sections['ParentName'] == parent_fault_name]
        qdf = self.rupture_sections.join(sects, 'section', how='inner')
        return qdf.rupture.unique()
