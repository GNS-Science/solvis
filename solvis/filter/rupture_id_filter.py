from typing import Iterable, List, Optional, Set

import geopandas as gpd
import shapely.geometry

import solvis.inversion_solution
from solvis.inversion_solution.typing import InversionSolutionProtocol, SetOperationEnum

from .parent_fault_id_filter import FilterParentFaultIds
from .subsection_id_filter import FilterSubsectionIds


class FilterRuptureIds:
    """
    A helper class to filter ruptures, returning the qualifying rupture_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).
    """

    def __init__(self, solution: InversionSolutionProtocol, drop_zero_rates: bool = True):
        """
        Args:
            solution: The solution instance to act on.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True)
        """
        self._solution = solution
        self._drop_zero_rates = drop_zero_rates
        self.filter_subsection_ids = FilterSubsectionIds(solution)
        self.filter_parent_fault_ids = FilterParentFaultIds(solution)

    def for_named_faults(self, named_fault_names: Set[str]) -> Set[int]:
        """Find ruptures that occur on any of the given named_fault names.

        Args:
            named_fault_names: A list of one or more `named_fault` names.

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `named_fault_names` argument is not valid.
        """
        ### get the parent_fault_names from the mapping
        ### return self.ids_for_parent_faults(parent_fault_names)
        raise NotImplementedError()

    def for_parent_fault_names(self, parent_fault_names: Iterable[str]) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True)

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        parent_fault_ids = self.filter_parent_fault_ids.for_parent_fault_names(parent_fault_names)
        return self.for_parent_fault_ids(parent_fault_ids=parent_fault_ids)

    def for_parent_fault_ids(self, parent_fault_ids: Iterable[int]) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.

        Returns:
            The rupture_ids matching the filter.
        """
        subsection_ids = self.filter_subsection_ids.for_parent_fault_ids(parent_fault_ids)
        df0 = self._solution.rupture_sections

        # TODO: this is needed becuase the rupture rate concept differs between IS and FSS classes
        rate_column = (
            "rate_weighted_mean"
            if isinstance(self._solution, solvis.inversion_solution.FaultSystemSolution)
            else "Annual Rate"
        )
        if self._drop_zero_rates:
            df0 = df0.join(self._solution.rupture_rates.set_index("Rupture Index"), on='rupture', how='inner')[
                [rate_column, "rupture", "section"]
            ]
            df0 = df0[df0[rate_column] > 0]

        ids = df0[df0['section'].isin(list(subsection_ids))]['rupture'].tolist()
        return set([int(id) for id in ids])

    def for_subsection_ids(self, fault_section_ids: Iterable[int]) -> Set[int]:
        """Find ruptures that occur on any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The rupture_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.section.isin(list(fault_section_ids))].rupture.tolist()
        return set([int(id) for id in ids])

    def _ruptures_with_and_without_rupture_rates(self):
        """Helper method
        # TODO this dataframe could be cached?? And used by above??
        """
        df_rr = self._solution.rupture_rates.drop(columns=["Rupture Index", "fault_system"])
        df_rr.index = df_rr.index.droplevel(0)  # so we're indexed by "Rupture Index" without "fault_system"
        return self._solution.ruptures.join(df_rr, on=self._solution.ruptures["Rupture Index"], rsuffix='_r')

    def for_rupture_rate(self, min_rate: Optional[float] = None, max_rate: Optional[float] = None):
        """Find ruptures that occur within given rates bounds.

        Args:
            min_rate: The minumum rupture _rate bound.
            max_rate: The maximum rupture _rate bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        index = "Rupture Index"
        if self._drop_zero_rates:
            df0 = self._solution.ruptures_with_rupture_rates
        else:
            df0 = self._ruptures_with_and_without_rupture_rates()

        # rate col is different for InversionSolution
        df0 = df0 if not max_rate else df0[df0.rate_weighted_mean <= max_rate]
        df0 = df0 if not min_rate else df0[df0.rate_weighted_mean > min_rate]
        return set(df0[index].tolist())

    def for_magnitude(self, min_mag: Optional[float] = None, max_mag: Optional[float] = None):
        """Find ruptures that occur within given magnitude bounds.

        Args:
            min_mag: The minumum rupture magnitude bound.
            max_mag: The maximum rupture magnitude bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        index = "Rupture Index"
        if self._drop_zero_rates:
            df0 = self._solution.ruptures_with_rupture_rates
        else:
            df0 = self._ruptures_with_and_without_rupture_rates()

        df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
        df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
        return set(df0[index].tolist())

    def for_polygons(
        self, polygons: Iterable[shapely.geometry.Polygon], join_type: SetOperationEnum = SetOperationEnum.UNION
    ) -> Set[int]:
        """Find ruptures that involve several polygon areas.

        Args:
            polygons: Polygons defining the areas of interest.
            join_type: How to join the polygon results.
        Returns:
            The rupture_ids matching the filter arguments.
        """
        rupture_id_sets: List[Set[int]] = []
        for polygon in polygons:
            rupture_id_sets.append(self.for_polygon(polygon))

        if join_type == SetOperationEnum.INTERSECTION:
            rupture_ids = set.intersection(*rupture_id_sets)
        elif join_type == SetOperationEnum.UNION:
            rupture_ids = set.union(*rupture_id_sets)
        else:
            raise ValueError("Only INTERSECTION and UNION operations are supported for `join_type`")
        return rupture_ids

    def for_polygon(self, polygon: shapely.geometry.Polygon) -> Set[int]:
        """Find ruptures that involve a polygon area.

        Args:
            polygon: The polygon defining the area of intersection.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        # if contained:
        #     raise NotImplementedError()

        df0 = gpd.GeoDataFrame(self._solution.fault_sections)
        df0 = df0[df0['geometry'].intersects(polygon)]

        if self._drop_zero_rates:
            index = "Rupture Index"
            df1 = self._solution.rs_with_rupture_rates
        else:
            index = "rupture"
            df1 = self._solution.rupture_sections

        df2 = df1.join(df0, 'section', how='inner')
        return set(df2[index].unique())