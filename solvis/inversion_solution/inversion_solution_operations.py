"""
This module defines the ~mixin~ class `InversionSolutionOperations`.

The `InversionSolutionOperations` class provides methods to build pandas dataframes
from the raw dataframes available via the `InversionSolutionFile` class.
"""
import logging
import time
import warnings
from typing import TYPE_CHECKING, Iterable, List, Optional, Set, cast

import geopandas as gpd
import pandas as pd
import shapely.geometry
from nzshm_common.location.location import location_by_id

from solvis.filter import FilterSubsectionIds
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.geometry import circle_polygon

from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import CompositeSolutionProtocol, InversionSolutionProtocol, SetOperationEnum
from .inversion_solution_file import InversionSolutionFile

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from pandera.typing import DataFrame

    from .dataframe_models import (
        FaultSectionRuptureRateSchema,
        FaultSectionSchema,
        FaultSectionWithSolutionSlipRate,
        ParentFaultParticipationSchema,
        RuptureSectionSchema,
        RuptureSectionsWithRuptureRatesSchema,
        RupturesWithRuptureRatesSchema,
        SectionParticipationSchema,
    )

log = logging.getLogger(__name__)


class InversionSolutionOperations:
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

    def __init__(self, solution_file: InversionSolutionFile) -> None:
        self._solution_file = solution_file
        self._rs_with_rupture_rates: Optional[pd.DataFrame] = None
        self._ruptures_with_rupture_rates: Optional[pd.DataFrame] = None
        self._rupture_sections: Optional[gpd.GeoDataFrame] = None
        self._fs_with_rates: Optional[pd.DataFrame] = None
        self._fs_with_soln_rates: Optional[pd.DataFrame] = None
        self._fault_sections: Optional[pd.DataFrame] = None

    @property
    def solution_file(self) -> InversionSolutionFile:
        return self._solution_file

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    ###
    # These attrbutes are 'hoisted' from the _solution_file isntance
    #
    # those that return dataframes may be migrated to the model -> InversionSolutionOperations
    ####
    @property
    def average_slips(self):
        return self._solution_file.average_slips

    @property
    def section_target_slip_rates(self):
        return self._solution_file.section_target_slip_rates

    @property
    def fault_sections(self):
        return self._solution_file.fault_sections

    @property
    def fault_regime(self):
        return self._solution_file.fault_regime

    @property
    def logic_tree_branch(self):
        return self._solution_file.logic_tree_branch

    @property
    def indices(self):
        return self._solution_file.indices

    @property
    def ruptures(self):
        return self._solution_file.ruptures

    @property
    def rupture_rates(self):
        return self._solution_file.rupture_rates

    def rate_column_name(self) -> str:
        """Get the appropriate rate_column name

        Returns:
            rate_column: "Annual Rate" or rate_weighted_mean"
        """
        return (
            "Annual Rate" if self._solution_file.__class__.__name__ == "InversionSolutionFile" else "rate_weighted_mean"
        )

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[SectionParticipationSchema]':
        """Calculate the 'participation rate' for fault subsections.

        Participation rate for each section is the the sum of rupture rates for the ruptures involving that section.

        Args:
            subsection_ids: the list of subsection_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka `Conditional Participation`).

        Notes:
         - Passing a non empty `subsection_ids` will not affect the rates, only the subsections for
           which rates are returned.
         - Passing a non empty `rupture_ids` will affect the rates, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in the rates of e.g. ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        rate_column = self.rate_column_name()
        t0 = time.perf_counter()
        df0 = cast(pd.DataFrame, self.rs_with_rupture_rates)

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
        result = result[[rate_column]]
        t3 = time.perf_counter()
        log.info(f'dataframe aggregation took : {t3-t2} seconds')
        result = result.rename(columns={rate_column: 'participation_rate'})
        return cast('DataFrame[SectionParticipationSchema]', result)

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[ParentFaultParticipationSchema]':
        """Calculate the 'participation rate' for parent faults.

        Participation rate for each parent fault is the the sum of rupture rates for the
        ruptures involving that parent fault.

        Args:
            parent_fault_ids: the list of parent_fault_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka Conditional Participation).

        Notes:
         - Passing `parent_fault_ids` will not affect the rate calculation, only the parent faults
           for which rates are returned.
         - Passing `rupture_ids` will affect the rates, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in e.g. the rates of ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        subsection_ids = FilterSubsectionIds(self).for_parent_fault_ids(parent_fault_ids) if parent_fault_ids else None

        rate_column = self.rate_column_name()

        df0 = cast(pd.DataFrame, self.rs_with_rupture_rates)
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self.solution_file.fault_sections[['ParentID']], on='section')
        result = (
            df1[["ParentID", "Rupture Index", rate_column]]
            .rename(columns={rate_column: 'participation_rate'})
            .reset_index(drop=True)
            .groupby(["ParentID", "Rupture Index"])
            .agg('first')
            .groupby("ParentID")
            .agg('sum')
        )
        return cast('DataFrame[ParentFaultParticipationSchema]', result)

    @property
    def rupture_sections(self) -> 'DataFrame[RuptureSectionSchema]':
        """
        Calculate and cache the permutations of rupture_id and section_id.

        Returns:
            pd.DataFrame: a pandas dataframe
        """
        if self._rupture_sections is not None:
            return cast('DataFrame[RuptureSectionSchema]', self._rupture_sections)

        self._rupture_sections = self.build_rupture_sections()
        return cast('DataFrame[RuptureSectionSchema]', self._rupture_sections)

    def build_rupture_sections(self) -> 'DataFrame[RuptureSectionSchema]':

        tic = time.perf_counter()

        rs = self.solution_file.indices  # _dataframe_from_csv(self._rupture_sections, 'ruptures/indices.csv').copy()

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
        return cast('DataFrame[RuptureSectionSchema]', df2)

    @property
    def fault_sections_with_rupture_rates(self) -> 'DataFrame[FaultSectionRuptureRateSchema]':
        """
        Calculate and cache the fault sections and their rupture rates.

        Returns:
            a gpd.GeoDataFrame
        """
        # assert 0
        if self._fs_with_rates is not None:
            print(self._fs_with_rates.columns)
            # assert 0
            return cast('DataFrame[FaultSectionRuptureRateSchema]', self._fs_with_rates)

        tic = time.perf_counter()
        print(self.rs_with_rupture_rates)
        assert self.rs_with_rupture_rates is not None
        self._fs_with_rates = self.rs_with_rupture_rates.join(self.solution_file.fault_sections, 'section', how='inner')
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
        return cast('DataFrame[FaultSectionRuptureRateSchema]', self._fs_with_rates)

    @property
    def parent_fault_names(self) -> List[str]:
        return sorted(self.solution_file.fault_sections.ParentName.unique())

    @property
    def fault_sections_with_solution_slip_rates(self) -> 'DataFrame[FaultSectionWithSolutionSlipRate]':
        """Calculate and cache fault sections and their solution slip rates.

        Solution slip rate combines the inversion inputs (avg slips), and the inversion solution (rupture rates).

        Returns:
            a gpd.GeoDataFrame
        """
        if self._fs_with_soln_rates is not None:
            return cast('DataFrame[FaultSectionWithSolutionSlipRate]', self._fs_with_soln_rates)

        tic = time.perf_counter()
        self._fs_with_soln_rates = self._get_soln_rates()
        toc = time.perf_counter()
        log.debug('fault_sections_with_soilution_rates: time to calculate solution rates: %2.3f seconds' % (toc - tic))
        return cast('DataFrame[FaultSectionWithSolutionSlipRate]', self._fs_with_soln_rates)

    def _get_soln_rates(self) -> 'DataFrame[FaultSectionWithSolutionSlipRate]':
        """Get a dataframe joining ruptures and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        average_slips = self.solution_file.average_slips
        # for every subsection, find the ruptures on it
        fault_sections_wr = self.solution_file.fault_sections.copy()
        for idx, fault_section in self.solution_file.fault_sections.iterrows():
            fault_id = fault_section['FaultID']
            fswr_gt0 = self.fault_sections_with_rupture_rates[
                (self.fault_sections_with_rupture_rates['FaultID'] == fault_id)
                & (self.fault_sections_with_rupture_rates['Annual Rate'] > 0.0)
            ]
            fault_sections_wr.loc[idx, 'Solution Slip Rate'] = sum(  # type: ignore
                fswr_gt0['Annual Rate'] * average_slips.loc[fswr_gt0['Rupture Index']]['Average Slip (m)']
            )

        return cast('DataFrame[FaultSectionWithSolutionSlipRate]', fault_sections_wr)

    @property
    def rs_with_rupture_rates(self) -> 'DataFrame[RuptureSectionsWithRuptureRatesSchema]':
        """Get a dataframe joining rupture_sections and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._rs_with_rupture_rates is not None:
            return cast('DataFrame[RuptureSectionsWithRuptureRatesSchema]', self._rs_with_rupture_rates)

        tic = time.perf_counter()
        # df_rupt_rate = self.ruptures.join(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._rs_with_rupture_rates = self.ruptures_with_rupture_rates.join(
            self.rupture_sections.set_index("rupture"),
            on=self.ruptures_with_rupture_rates["Rupture Index"],  # type: ignore
        )

        toc = time.perf_counter()
        log.info(
            (
                'rs_with_rupture_rates: time to load ruptures_with_rupture_rates '
                'and join with rupture_sections: %2.3f seconds'
            )
            % (toc - tic)
        )
        return cast('DataFrame[RuptureSectionsWithRuptureRatesSchema]', self._rs_with_rupture_rates)

    @property
    def ruptures_with_rupture_rates(self) -> 'DataFrame[RupturesWithRuptureRatesSchema]':
        """Get a dataframe joining ruptures and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._ruptures_with_rupture_rates is not None:
            return cast('DataFrame[RupturesWithRuptureRatesSchema]', self._ruptures_with_rupture_rates)

        tic = time.perf_counter()
        # print(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._ruptures_with_rupture_rates = self.solution_file.rupture_rates.join(
            self.solution_file.ruptures.drop(columns="Rupture Index"),
            on=self.solution_file.rupture_rates["Rupture Index"],
        )
        if 'key_0' in self._ruptures_with_rupture_rates.columns:
            self._ruptures_with_rupture_rates.drop(columns=['key_0'], inplace=True)
        toc = time.perf_counter()
        log.debug(
            'ruptures_with_rupture_rates(): time to load rates and join with ruptures: %2.3f seconds' % (toc - tic)
        )
        return cast('DataFrame[RupturesWithRuptureRatesSchema]', self._ruptures_with_rupture_rates)

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

    def get_rupture_ids_for_parent_fault(self, parent_fault_name: str) -> 'NDArray':
        """
        Return rupture IDs from fault sections for a given parent fault.

        Parameters:
            parent_fault_name: The name of the parent fault, e.g. "Alpine Jacksons to Kaniere"

        Returns:
            a Pandas series of rupture IDs
        """
        warnings.warn("Please use solvis.filter.classes instead.", DeprecationWarning)
        # sr = sol.rs_with_rupture_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.solution_file.fault_sections[self.solution_file.fault_sections['ParentName'] == parent_fault_name]
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

    def get_ruptures_for_parent_fault(self, parent_fault_name: str) -> 'NDArray':
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

        return self.fault_sections_with_solution_slip_rates[
            self.fault_sections_with_solution_slip_rates['ParentName'] == parent_fault_name
        ]


class CompositeSolutionOperations(CompositeSolutionProtocol):
    def rupture_surface(self, fault_system: str, rupture_id: int) -> gpd.GeoDataFrame:
        return self._solutions[fault_system].model.rupture_surface(rupture_id)

    def fault_surfaces(self):
        surfaces = []
        for fault_system, sol in self._solutions.items():
            solution_df = sol.model.fault_surfaces().to_crs("EPSG:4326")
            solution_df.insert(0, 'fault_system', fault_system)
            surfaces.append(solution_df)
        all_surfaces_df = pd.concat(surfaces, ignore_index=True)
        return gpd.GeoDataFrame(all_surfaces_df)
