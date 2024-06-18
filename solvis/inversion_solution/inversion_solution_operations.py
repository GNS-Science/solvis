import logging
import time
import warnings
from typing import Iterable, List, Set

import geopandas as gpd
import pandas as pd
from nzshm_common.location.location import location_by_id

from solvis.geometry import circle_polygon

from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import CompositeSolutionProtocol, InversionSolutionProtocol, SetOperationEnum

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
        """
        Get the fault sections and replace slip rates from rupture set with target rates from inverison.
        Cache result.
        """
        if self._fault_sections is not None:
            return self._fault_sections

        tic = time.perf_counter()
        self._fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        self._fault_sections = self._fault_sections.join(self.section_target_slip_rates)
        self._fault_sections.drop(columns=["SlipRate", "SlipRateStdDev", "Section Index"], inplace=True)
        mapper = {
            "Slip Rate (m/yr)": "Target Slip Rate",
            "Slip Rate Standard Deviation (m/yr)": "Target Slip Rate StdDev",
        }
        self._fault_sections.rename(columns=mapper, inplace=True)
        toc = time.perf_counter()
        log.debug('fault_sections: time to load fault_sections: %2.3f seconds' % (toc - tic))
        return self._fault_sections

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
    def fault_sections_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """
        Calculate and cache the fault sections and their rupture rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._fs_with_rates is not None:
            return self._fs_with_rates

        tic = time.perf_counter()
        self._fs_with_rates = self.rs_with_rupture_rates.join(self.fault_sections, 'section', how='inner')
        toc = time.perf_counter()
        log.debug(
            (
                'fault_sections_with_rupture_rates: time to load rs_with_rupture_rates '
                'and join with fault_sections: %2.3f seconds'
            )
            % (toc - tic)
        )

        # self._fs_with_rates = self.fault_sections.join(self.ruptures_with_rupture_rates,
        #     on=self.fault_sections["Rupture Index"] )
        return self._fs_with_rates

    @property
    def parent_fault_names(self) -> List[str]:
        fault_names = list(set(list(self.fault_sections['ParentName'])))
        fault_names.sort()
        return fault_names

    @property
    def fault_sections_with_solution_slip_rates(self) -> gpd.GeoDataFrame:
        """
        Calculate and cache fault sections and their solution slip rates.
        Solution slip rate combines input (avg slips) and solution (rupture rates).

        Returns:
            a gpd.GeoDataFrame
        """
        if self._fs_with_soln_rates is not None:
            return self._fs_with_soln_rates

        tic = time.perf_counter()
        self._fs_with_soln_rates = self._get_soln_rates()
        toc = time.perf_counter()
        log.debug('fault_sections_with_soilution_rates: time to calculate solution rates: %2.3f seconds' % (toc - tic))
        return self._fs_with_soln_rates

    def _get_soln_rates(self):

        average_slips = self.average_slips
        # for every subsection, find the ruptures on it
        fault_sections_wr = self.fault_sections.copy()
        for ind, fault_section in self.fault_sections.iterrows():
            fault_id = fault_section['FaultID']
            fswr_gt0 = self.fault_sections_with_rupture_rates[
                (self.fault_sections_with_rupture_rates['FaultID'] == fault_id)
                & (self.fault_sections_with_rupture_rates['Annual Rate'] > 0.0)
            ]
            fault_sections_wr.loc[ind, 'Solution Slip Rate'] = sum(
                fswr_gt0['Annual Rate'] * average_slips.loc[fswr_gt0['Rupture Index']]['Average Slip (m)']
            )

        return fault_sections_wr

    @property
    def rs_with_rupture_rates(self) -> gpd.GeoDataFrame:
        if self._rs_with_rupture_rates is not None:
            return self._rs_with_rupture_rates  # pragma: no cover

        tic = time.perf_counter()
        # df_rupt_rate = self.ruptures.join(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._rs_with_rupture_rates = self.ruptures_with_rupture_rates.join(
            self.rupture_sections.set_index("rupture"), on=self.ruptures_with_rupture_rates["Rupture Index"]
        )

        toc = time.perf_counter()
        log.debug(
            (
                'rs_with_rupture_rates: time to load ruptures_with_rupture_rates '
                'and join with rupture_sections: %2.3f seconds'
            )
            % (toc - tic)
        )
        return self._rs_with_rupture_rates

    @property
    def ruptures_with_rupture_rates(self) -> pd.DataFrame:
        if self._ruptures_with_rupture_rates is not None:
            return self._ruptures_with_rupture_rates  # pragma: no cover

        tic = time.perf_counter()
        # print(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._ruptures_with_rupture_rates = self.rupture_rates.join(
            self.ruptures.drop(columns="Rupture Index"), on=self.rupture_rates["Rupture Index"]
        )
        if 'key_0' in self._ruptures_with_rupture_rates.columns:
            self._ruptures_with_rupture_rates.drop(columns=['key_0'], inplace=True)
        toc = time.perf_counter()
        log.debug(
            'ruptures_with_rupture_rates(): time to load rates and join with ruptures: %2.3f seconds' % (toc - tic)
        )
        return self._ruptures_with_rupture_rates

    # return the rupture ids for any ruptures intersecting the polygon
    def get_rupture_ids_intersecting(self, polygon) -> pd.Series:
        """Return IDs for any ruptures intersecting the polygon."""
        q0 = gpd.GeoDataFrame(self.fault_sections)
        q1 = q0[q0['geometry'].intersects(polygon)]  # whitemans_0)]
        sr = self.rs_with_rupture_rates
        qdf = sr.join(q1, 'section', how='inner')
        return qdf["Rupture Index"].unique()

    def get_rupture_ids_for_location_radius(
        self,
        location_ids: Iterable[str],
        radius_km: float,
        location_join_type: SetOperationEnum = SetOperationEnum.UNION,
    ) -> Set[int]:
        """
        Return IDs for ruptures within a radius around one or more locations.

        Where there are multiple locations, the rupture IDs represent a set joining
        of the specified radii.

        Locations are resolved using [`nzshm-common`](https://pypi.org/project/nzshm-common/)
        location ID values.

        Parameters:
            location_ids: one or more defined location IDs
            radius_km: radius around the point(s) in kilometres
            location_join_type: UNION or INTERSECTION

        Returns:
            a Set of rupture IDs

        Examples:
            Get all rupture IDs from the solution that are within 100km of Blenheim:
            ```py
                bhe_rupture_ids = sol.get_rupture_ids_for_location_radius(
                    location_ids=["BHE"],
                    radius_km=100,
                )
            ```
            Get all rupture IDs from the solution that are within 50km of Blenheim
            or within 50km of Wellington:
            ```py
                intersect_rupture_ids = sol.get_rupture_ids_for_location_radius(
                    location_ids=["BHE"],
                    radius_km=50,
                    location_joint_type=SetOperationEnum.UNION,
                )
            ```

        Note:
            If you want to do this kind of joining between locations with different
            radii or points that are not defined by location IDs, consider using
            [circle_polygon][solvis.geometry.circle_polygon] and
            [get_rupture_ids_intersecting][solvis.inversion_solution.inversion_solution_operations.InversionSolutionOperations.get_rupture_ids_intersecting]
            then use set operations to join each rupture ID set.
        """
        log.info('get_rupture_ids_for_location_radius: %s %s %s' % (self, radius_km, location_ids))
        first = True
        rupture_ids: Set[int]
        for loc_id in location_ids:
            loc = location_by_id(loc_id)
            polygon = circle_polygon(radius_km * 1000, lon=loc['longitude'], lat=loc['latitude'])
            location_rupture_ids = set(self.get_rupture_ids_intersecting(polygon))

            if first:
                rupture_ids = location_rupture_ids
                first = False
            else:
                log.debug('location_join_type %s' % location_join_type)
                if location_join_type == SetOperationEnum.INTERSECTION:
                    rupture_ids = rupture_ids.intersection(location_rupture_ids)
                elif location_join_type == SetOperationEnum.UNION:
                    rupture_ids = rupture_ids.union(location_rupture_ids)
                else:
                    raise ValueError("unsupported SetOperation")
        return rupture_ids

    def get_rupture_ids_for_parent_fault(self, parent_fault_name: str) -> pd.Series:
        """
        Return rupture IDs from fault sections for a given parent fault.

        Parameters:
            parent_fault_name: The name of the parent fault, e.g. "Alpine Jacksons to Kaniere"

        Returns:
            a Pandas series of rupture IDs
        """
        # sr = sol.rs_with_rupture_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.fault_sections[self.fault_sections['ParentName'] == parent_fault_name]
        qdf = self.rupture_sections.join(sects, 'section', how='inner')
        return qdf.rupture.unique()

    def get_rupture_ids_for_fault_names(
        self,
        corupture_fault_names: Iterable[str],
        fault_join_type: SetOperationEnum = SetOperationEnum.UNION,
    ) -> Set[int]:
        """
        Retrieve a set of rupture IDs for the specified corupture fault names.

        Where there are multiple faults, the rupture IDs represent a set joining
        of the specified faults.

        Parameters:
            corupture_fault_names: a collection of corupture fault names
            fault_join_type: UNION or INTERSECTION

        Raises:
            ValueError: on an unsupported fault join type

        Returns:
            a Set of rupture IDs

        Examples:
            ```py
            rupture_ids = solution.get_rupture_ids_for_fault_names(
                corupture_fault_names=[
                    "Alpine Jacksons to Kaniere",
                    "Alpine Kaniere to Springs Junction",
                ],
                fault_joint_type=SetOperationEnum.INTERSECTION,
                }
            )
            ```
            Returns a set of 1440 rupture IDs in the intersection of the two datasets.
        """
        first = True
        rupture_ids: Set[int]
        for fault_name in corupture_fault_names:
            if fault_name not in self.parent_fault_names:
                raise ValueError("Invalid fault name: %s" % fault_name)
            tic22 = time.perf_counter()
            fault_rupture_ids = self.get_rupture_ids_for_parent_fault(fault_name)
            tic23 = time.perf_counter()
            log.debug('get_ruptures_for_parent_fault %s: %2.3f seconds' % (fault_name, (tic23 - tic22)))

            if first:
                rupture_ids = set(fault_rupture_ids)
                first = False
            else:
                log.debug(f"fault_join_type {fault_join_type}")
                if fault_join_type == SetOperationEnum.INTERSECTION:
                    rupture_ids = rupture_ids.intersection(fault_rupture_ids)
                elif fault_join_type == SetOperationEnum.UNION:
                    rupture_ids = rupture_ids.union(fault_rupture_ids)
                else:
                    raise ValueError(
                        "Only INTERSECTION and UNION operations are supported for option 'multiple_faults'"
                    )

        return rupture_ids

    def get_ruptures_for_parent_fault(self, parent_fault_name: str) -> pd.Series:
        """Deprecated signature for get_rupture_ids_for_parent_fault."""
        warnings.warn("Please use updated method name: get_rupture_ids_for_parent_fault", category=DeprecationWarning)
        return self.get_rupture_ids_for_parent_fault(parent_fault_name)

    def get_ruptures_intersecting(self, polygon) -> pd.Series:
        """Deprecated signature for get_rupture_ids_intersecting."""
        warnings.warn("Please use updated method name: get_rupture_ids_intersecting", category=DeprecationWarning)
        return self.get_rupture_ids_intersecting(polygon)

    def get_solution_slip_rates_for_parent_fault(self, parent_fault_name: str) -> pd.DataFrame:

        return self.fault_sections_with_solution_slip_rates[
            self.fault_sections_with_solution_slip_rates['ParentName'] == parent_fault_name
        ]


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
