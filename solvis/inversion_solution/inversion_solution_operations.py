import logging
import time
import warnings
from typing import Iterable, List, Optional, Set

import geopandas as gpd
import pandas as pd
import shapely.geometry
from nzshm_common.location.location import location_by_id

from solvis.filter import FilterSubsectionIds
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.geometry import circle_polygon

from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import CompositeSolutionProtocol, InversionSolutionProtocol, SetOperationEnum

# from .inversion_solution import InversionSolution

log = logging.getLogger(__name__)


class InversionSolutionOperations(InversionSolutionProtocol):
    """
    helper methods for analysis of InversionSolutionProtocol subtypes.

    Deprecated:
     the following methods are replaced by solvis.filter classes.

     - get_rupture_ids_for_fault_names
     - get_rupture_ids_for_location_radius
     - get_rupture_ids_for_parent_fault
     - get_rupture_ids_intersecting
     - get_ruptures_for_parent_fault
     - get_ruptures_intersecting
     - get_solution_slip_rates_for_parent
    """

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> pd.DataFrame:
        """
        get the 'participation rate' for fault subsections.

        That is, the sum of rupture rates on the requested fault sections.
        """

        rate_column = "Annual Rate" if self.__class__.__name__ == "InversionSolution" else "rate_weighted_mean"

        t0 = time.perf_counter()
        df0 = self.rs_with_rupture_rates

        log.info(f"df0 shape: {df0.shape}")

        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        t1 = time.perf_counter()
        log.info(f'apply section filter took : {t1-t0} seconds')

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        t2 = time.perf_counter()
        log.info(f'apply rupture_ids filter took : {t2-t1} seconds')

        # result = df0.pivot_table(values=rate_column, index=['section'], aggfunc='sum')
        result = df0[["section", "Rupture Index", rate_column]].groupby("section").agg('sum')

        t3 = time.perf_counter()
        log.info(f'dataframe aggregation took : {t3-t2} seconds')
        return result.rename(columns={rate_column: 'participation_rate'})

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        """
        get the 'participation rate' for parent faults.

        That is, the sum of rupture rates on the requested parent faults.
        """
        subsection_ids = FilterSubsectionIds(self).for_parent_fault_ids(parent_fault_ids) if parent_fault_ids else None

        rate_column = "Annual Rate" if self.__class__.__name__ == "InversionSolution" else "rate_weighted_mean"
        df0 = self.rs_with_rupture_rates
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self.fault_sections[['ParentID']], on='section')
        return (
            df1[["ParentID", "Rupture Index", rate_column]]
            .rename(columns={rate_column: 'participation_rate'})
            .reset_index(drop=True)
            .groupby(["ParentID", "Rupture Index"])
            .agg('first')
            .groupby("ParentID")
            .agg('sum')
        )

    # def parent_fault_names(self) -> List[str]:
    #     fault_names = list(set(list(self.fault_sections['ParentName'])))
    #     fault_names.sort()
    #     return fault_names

    @property
    def parent_fault_names(self) -> List[str]:
        return sorted(self.fault_sections.ParentName.unique())

    def get_rupture_ids_intersecting(self, polygon: shapely.geometry.Polygon) -> pd.Series:
        """Return IDs for any ruptures intersecting the polygon.

        Warning:
         Deprecated: please use solvis.filter.*.for_polygons method instead
        """
        warnings.warn("Please use solvis.filter.*.for_polygons method instead", DeprecationWarning)
        return pd.Series(list(FilterRuptureIds(self).for_polygon(polygon)))

    def get_rupture_ids_for_location_radius(
        self,
        location_ids: Iterable[str],
        radius_km: float,
        location_join_type: SetOperationEnum = SetOperationEnum.UNION,
    ) -> Set[int]:
        """Return IDs for ruptures within a radius around one or more locations.

        Warning:
         Deprecated: please use solvis.filter.*.for_polygons method instead

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
            Get all rupture IDs from the solution that are within 50km of Blenheim
            or Wellington:
            ```py
                intersect_rupture_ids = sol.get_rupture_ids_for_location_radius(
                    location_ids=["BHE", "WLG"],
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
        warnings.warn("Please use solvis.filter.classes *.for_polygons method instead.", DeprecationWarning)
        log.info('get_rupture_ids_for_location_radius: %s %s %s' % (self, radius_km, location_ids))
        polygons = []
        for loc_id in location_ids:
            loc = location_by_id(loc_id)
            polygons.append(circle_polygon(radius_km * 1000, lon=loc['longitude'], lat=loc['latitude']))
        return set(FilterRuptureIds(self).for_polygons(polygons, location_join_type))

    def get_rupture_ids_for_parent_fault(self, parent_fault_name: str) -> pd.Series:
        """
        Return rupture IDs from fault sections for a given parent fault.

        Warning:
         Deprecated: please use solvis.filter.* instead

        Parameters:
            parent_fault_name: The name of the parent fault, e.g. "Alpine Jacksons to Kaniere"

        Returns:
            a Pandas series of rupture IDs
        """
        warnings.warn("Please use solvis.filter.classes instead.", DeprecationWarning)
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

        Warning:
         Deprecated: please use solvis.filter.*.for_polygons method instead


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
        warnings.warn("Please use solvis.filter.classes instead.", DeprecationWarning)

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
        warnings.warn("Please use solvis.filter.classes instead.", DeprecationWarning)
        # warnings.warn("Please use updated method name: get_rupture_ids_for_parent_fault", category=DeprecationWarning)
        return self.get_rupture_ids_for_parent_fault(parent_fault_name)

    def get_ruptures_intersecting(self, polygon) -> pd.Series:
        """Deprecated signature for get_rupture_ids_intersecting."""
        warnings.warn("Please use solvis.filter.classes instead.", DeprecationWarning)
        # warnings.warn("Please use updated method name: get_rupture_ids_intersecting", category=DeprecationWarning)
        return self.get_rupture_ids_intersecting(polygon)

    def get_solution_slip_rates_for_parent_fault(self, parent_fault_name: str) -> pd.DataFrame:

        return self.IO.fault_sections_with_solution_slip_rates[
            self.IO.fault_sections_with_solution_slip_rates['ParentName'] == parent_fault_name
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
