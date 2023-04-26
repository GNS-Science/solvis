import logging
import time

import geopandas as gpd
import pandas as pd

from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import CompositeSolutionProtocol, InversionSolutionProtocol

log = logging.getLogger(__name__)


class InversionSolutionOperations(InversionSolutionProtocol):
    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    def _geodataframe_from_geojson(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = gpd.read_file(self.archive.open(path))
        return prop

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        tic = time.perf_counter()
        fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        toc = time.perf_counter()
        log.debug('fault_sections: time to load fault_sections: %2.3f seconds' % (toc - tic))

        return fault_sections

    @property
    def rupture_sections(self) -> gpd.GeoDataFrame:

        if self._rupture_sections is not None:
            return self._rupture_sections  # pragma: no cover

        self._rupture_sections = self.build_rupture_sections()
        return self._rupture_sections

    def build_rupture_sections(self) -> gpd.GeoDataFrame:

        tic = time.perf_counter()

        rs = self.indices  # _dataframe_from_csv(self._rupture_sections, 'ruptures/indices.csv').copy()

        # remove "Rupture Index, Num Sections" column
        df_table = rs.drop(rs.iloc[:, :2], axis=1)
        tic0 = time.perf_counter()

        # convert to relational table, turning headings index into plain column
        df2 = df_table.stack().reset_index()

        tic1 = time.perf_counter()
        log.debug('rupture_sections(): time to convert indiced to table: %2.3f seconds' % (tic1 - tic0))

        # remove the headings column
        df2.drop(df2.iloc[:, 1:2], inplace=True, axis=1)
        df2 = df2.set_axis(['rupture', 'section'], axis='columns', copy=False)

        toc = time.perf_counter()
        log.debug('rupture_sections(): time to load and conform rupture_sections: %2.3f seconds' % (toc - tic))
        return df2

    @property
    def fault_sections_with_rates(self) -> gpd.GeoDataFrame:
        """
        Calculate and cache the fault sections and their rupture rates.

        :return: a gpd.GeoDataFrame
        """
        if self._fs_with_rates is not None:
            return self._fs_with_rates

        tic = time.perf_counter()
        self._fs_with_rates = self.rs_with_rates.join(self.fault_sections, 'section', how='inner')
        toc = time.perf_counter()
        log.debug(
            'fault_sections_with_rates: time to load rs_with_rates and join with fault_sections: %2.3f seconds'
            % (toc - tic)
        )

        # self._fs_with_rates = self.fault_sections.join(self.ruptures_with_rates,
        #     on=self.fault_sections["Rupture Index"] )
        return self._fs_with_rates

    @property
    def rs_with_rates(self) -> gpd.GeoDataFrame:
        if self._rs_with_rates is not None:
            return self._rs_with_rates  # pragma: no cover

        tic = time.perf_counter()
        # df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.ruptures_with_rates.join(
            self.rupture_sections.set_index("rupture"), on=self.ruptures_with_rates["Rupture Index"]
        )

        toc = time.perf_counter()
        log.debug(
            'rs_with_rates: time to load ruptures_with_rates and join with rupture_sections: %2.3f seconds'
            % (toc - tic)
        )
        return self._rs_with_rates

    @property
    def ruptures_with_rates(self) -> pd.DataFrame:
        if self._ruptures_with_rates is not None:
            return self._ruptures_with_rates  # pragma: no cover

        tic = time.perf_counter()
        # print(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._ruptures_with_rates = self.rates.join(
            self.ruptures.drop(columns="Rupture Index"), on=self.rates["Rupture Index"]
        )
        toc = time.perf_counter()
        log.debug('ruptures_with_rates(): time to load rates and join with ruptures: %2.3f seconds' % (toc - tic))
        return self._ruptures_with_rates

    # return the rupture ids for any ruptures intersecting the polygon
    def get_ruptures_intersecting(self, polygon) -> pd.Series:
        q0 = gpd.GeoDataFrame(self.fault_sections)
        q1 = q0[q0['geometry'].intersects(polygon)]  # whitemans_0)]
        sr = self.rs_with_rates
        qdf = sr.join(q1, 'section', how='inner')
        return qdf["Rupture Index"].unique()

    def get_ruptures_for_parent_fault(self, parent_fault_name: str) -> pd.Series:
        # sr = sol.rs_with_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.fault_sections[self.fault_sections['ParentName'] == parent_fault_name]
        qdf = self.rupture_sections.join(sects, 'section', how='inner')
        return qdf.rupture.unique()


class CompositeSolutionOperations(CompositeSolutionProtocol):
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
