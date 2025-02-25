r"""
This module provides a class for filtering solution ruptures.

Classes:
    FilterRuptureIds: a chainable filter for ruptures, returning qualifying rupture ids.

Examples:
    ```py
    >>> # ruptures within 50km of Hamilton with magnitude between 5.75 and 6.25.
    >>> ham50 = solvis.circle_polygon(50000, -37.78, 175.28)  # 50km radius around Hamilton
    <POLYGON ((175.849 -37.779, 175.847 -37.823, 175.839 -37.866, 175.825 -37.90...>
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>> rupture_ids = FilterRuptureIds(solution)\
            .for_magnitude(min_mag=5.75, max_mag=6.25)\
            .for_polygon(ham50)

    >>> # ruptures on any of faults A, B, with magnitude and rupture rate limits
    >>> rupture_ids = FilterRuptureIds(solution)\
    >>>    .for_parent_fault_names(['Alpine: Jacksons to Kaniere', 'Vernon 1' ])\
    >>>    .for_magnitude(7.0, 8.0)\
    >>>    .for_rupture_rate(1e-6, 1e-2)

    >>> # ruptures on fault A that do not involve fault B:
    >>> rupture_ids = FilterRuptureIds(solution)\
    >>>    .for_parent_fault_names(['Alpine: Jacksons to Kaniere'])\
    >>>    .for_parent_fault_names(['Vernon 1'], join_prior='difference')
    ```
"""

from typing import TYPE_CHECKING, Iterable, List, Optional, Set, Union

import geopandas as gpd
import shapely.geometry

import solvis.solution

from ..solution import named_fault
from ..solution.typing import SetOperationEnum
from .chainable_set_base import ChainableSetBase
from .parent_fault_id_filter import FilterParentFaultIds
from .subsection_id_filter import FilterSubsectionIds

if TYPE_CHECKING:
    import pandas as pd

    from solvis import InversionSolution


class FilterRuptureIds(ChainableSetBase):
    """A helper class to filter solution ruptures, returning the qualifying rupture_ids."""

    def __init__(
        self,
        solution: 'InversionSolution',
        drop_zero_rates: bool = True,
    ):
        """Instantiate a new filter.

        Args:
            solution: The solution instance to filter on.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True).
        """
        self._solution = solution
        self._drop_zero_rates = drop_zero_rates
        self._filter_subsection_ids = FilterSubsectionIds(solution)
        self._filter_parent_fault_ids = FilterParentFaultIds(solution)
        self.__rupture_sections: Optional['pd.DataFrame'] = None

    def _ruptures_with_or_without_rupture_rates(self, drop_zero_rates: bool = False) -> 'pd.DataFrame':
        """Get ruptures with or without rupture rates.

        Catering for the difference in rates structure of InversionSolution subclasses.

        Args:
            drop_zero_rates: If True, exclude ruptures with zero rupture rate.

        Returns:
            DataFrame containing ruptures with and without rupture rates.
        """
        if isinstance(self._solution, solvis.solution.fault_system_solution.FaultSystemSolution):
            df_rr: pd.DataFrame = self._solution.solution_file.rupture_rates.drop(
                columns=["Rupture Index", "fault_system"]
            )
            df_rr.index = df_rr.index.droplevel(0)  # so we're indexed by "Rupture Index" without " ault_system"
        else:
            df_rr = self._solution.solution_file.rupture_rates.drop(columns=["Rupture Index"])

        if drop_zero_rates:
            rate_column = self._solution.model.rate_column_name()
            nonzero = df_rr[rate_column] > 0
            df_rr = df_rr[nonzero]

        return self._solution.solution_file.ruptures.join(df_rr, on="Rupture Index", rsuffix='_r', how='inner')

    def _adapted_rupture_sections(self) -> 'pd.DataFrame':
        """Get adapted rupture sections based on the drop_zero_rates flag.

        The adaption caches for better performance in client functions

        Returns:
            DataFrame containing adapted rupture sections.
        """
        if self.__rupture_sections is not None:
            return self.__rupture_sections

        df0: pd.DataFrame = self._solution.model.rupture_sections
        rate_column = self._solution.model.rate_column_name()
        if self._drop_zero_rates:
            df1 = self._ruptures_with_or_without_rupture_rates(drop_zero_rates=self._drop_zero_rates)
            df0 = df0.join(df1.set_index("Rupture Index"), on='rupture', how='inner')[
                [rate_column, "rupture", "section"]
            ]

        self.__rupture_sections = df0
        return self.__rupture_sections

    def _get_rupture_ids_for_subsection_ids(self, subsection_ids: Iterable[int]) -> Set[int]:
        """Get rupture ids for given subsection ids.

        Args:
            subsection_ids (Iterable[int]): A collection of subsection ids.

        Returns:
            Set[int]: A set containing the rupture ids that correspond to the provided subsection ids.
        """
        df0 = self._adapted_rupture_sections()
        ids = df0[df0['section'].isin(list(subsection_ids))]['rupture'].tolist()
        return set([int(id) for id in ids])

    def tolist(self) -> List[int]:
        """
        Returns the filtered rupture ids as a list of integers.

        Returns:
            A list of integers representing the filtered rupture ids.
        """
        return list(self)

    def all(self) -> ChainableSetBase:
        """Convenience method returning ids for all solution ruptures.

        NB the usual `join_prior` argument is not implemented as it doesn't seem useful here.

        Returns:
            A chainable set of all the rupture_ids.
        """
        result = set(self._solution.solution_file.ruptures['Rupture Index'].to_list())
        return self.new_chainable_set(result, self._solution)

    def for_named_fault_names(
        self,
        named_fault_names: Iterable[str],
        join_type: Union[SetOperationEnum, str] = 'union',
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Filter rupture ids based on named fault names.

        This method filters the rupture ids for given named fault names. It supports
        both intersection and union operations to combine results from multiple named
        faults. The `join_type` parameter determines how the sets of rupture ids are
        combined, while the `join_prior` parameter specifies how these sets are combined
        with any existing filters.

        Args:
            named_fault_names (Iterable[str]): A collection of named fault names.
            join_type (Union[SetOperationEnum, str], optional): The type of set operation to use for
                combining results from multiple named faults. It can be either 'union' or 'intersection'.
            join_prior (Union[SetOperationEnum, str], optional): The type of set operation to use when
                combining the filtered rupture ids with any existing filters. It can be either 'intersection'
                or 'difference'.

        Returns:
            ChainableSetBase: A chainable set containing the filtered rupture ids.

        Raises:
            ValueError: If an unsupported join_type is provided.
        """
        if isinstance(join_type, str):
            join_type = SetOperationEnum[join_type.upper()]

        rupture_id_sets: List[Set[int]] = []
        for named_fault_name in named_fault_names:
            parent_fault_ids = named_fault.named_fault_table().loc[named_fault_name].parent_fault_ids
            rupture_ids = self.for_parent_fault_ids(parent_fault_ids, join_prior=join_prior).chained_set
            rupture_id_sets.append(rupture_ids)

        if join_type == SetOperationEnum.INTERSECTION:
            rupture_ids = set.intersection(*rupture_id_sets)
        elif join_type == SetOperationEnum.UNION:
            rupture_ids = set.union(*rupture_id_sets)
        else:
            raise ValueError("Only INTERSECTION and UNION operations are supported for option 'join_type'")
        return self.new_chainable_set(rupture_ids, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_parent_fault_names(
        self,
        parent_fault_names: Iterable[str],
        join_type: Union[SetOperationEnum, str] = 'union',
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Filter rupture ids based on parent fault names.

        This method filters the rupture ids for given parent fault names. It supports
        both intersection and union operations to combine results from multiple parent
        faults. The `join_type` parameter determines how the sets of rupture ids are
        combined, while the `join_prior` parameter specifies how these sets are combined
        with any existing filters.

        Args:
            parent_fault_names (Iterable[str]): A collection of parent fault names.
            join_type (Union[SetOperationEnum, str], optional): The type of set operation to use for
                combining results from multiple parent faults. It can be either 'union' or 'intersection'.
            join_prior (Union[SetOperationEnum, str], optional): The type of set operation to use when
                combining the filtered rupture ids with any existing filters. It can be either 'intersection'
                or 'difference'.

        Returns:
            ChainableSetBase: A chainable set containing the filtered rupture ids.

        Raises:
            ValueError: If an unsupported join_type is provided.
        """
        if isinstance(join_type, str):
            join_type = SetOperationEnum[join_type.upper()]

        parent_fault_ids = self._filter_parent_fault_ids.for_parent_fault_names(parent_fault_names)
        return self.for_parent_fault_ids(parent_fault_ids=parent_fault_ids, join_type=join_type, join_prior=join_prior)

    def for_parent_fault_id(
        self,
        parent_fault_id: int,
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """
        Find ruptures that occur on the given parent fault id.

        Args:
            parent_fault_id: The parent fault id to filter by.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter.
        """
        subsection_ids = self._filter_subsection_ids.for_parent_fault_ids([parent_fault_id])
        rupture_ids = self._get_rupture_ids_for_subsection_ids(subsection_ids)
        return self.new_chainable_set(rupture_ids, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_parent_fault_ids(
        self,
        parent_fault_ids: Iterable[int],
        join_type: Union[SetOperationEnum, str] = 'union',
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures that occur on the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.
            join_type: The type of set operation to perform when combining results from multiple parent_fault_ids.
                Options are 'union' and 'intersection'.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter.
        """
        if isinstance(join_type, str):
            join_type = SetOperationEnum[join_type.upper()]

        rupture_id_sets: List[Set[int]] = []
        for fault_id in parent_fault_ids:
            rupture_id_sets.append(self.for_parent_fault_id(fault_id, join_prior=join_prior).chained_set)

        if join_type == SetOperationEnum.INTERSECTION:
            rupture_ids = set.intersection(*rupture_id_sets)
        elif join_type == SetOperationEnum.UNION:
            rupture_ids = set.union(*rupture_id_sets)
        else:
            raise ValueError("Only INTERSECTION and UNION operations are supported for option 'join_type'")
        return self.new_chainable_set(rupture_ids, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_subsection_ids(
        self,
        fault_section_ids: Iterable[int],
        join_type: Union[SetOperationEnum, str] = 'union',
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures that occur on any of the given fault_section_ids.

        Return the Union of all rupture ids involvcedin te `fault_section_ids`.

        Args:
            fault_section_ids: A list of one or more fault_section ids.
            join_type: The type of set operation to perform when combining results from multiple fault_section_ids.
                Options are 'union' and 'intersection'.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter.
        """
        if isinstance(join_type, str):
            join_type = SetOperationEnum[join_type.upper()]

        rupture_id_sets: List[Set[int]] = []
        for fault_section_id in fault_section_ids:
            rupture_id_sets.append(self._get_rupture_ids_for_subsection_ids([fault_section_id]))
        if join_type == SetOperationEnum.INTERSECTION:
            rupture_ids = set.intersection(*rupture_id_sets)
        elif join_type == SetOperationEnum.UNION:
            rupture_ids = set.union(*rupture_id_sets)
        else:
            raise ValueError("Only INTERSECTION and UNION operations are supported for option 'join_type'")
        return self.new_chainable_set(rupture_ids, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_rupture_rate(
        self,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures that occur within given rates bounds.

        Args:
            min_rate: The minumum rupture _rate bound.
            max_rate: The maximum rupture _rate bound.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').


        Returns:
            A chainable set of rupture_ids matching the filter arguments.
        """
        index = "Rupture Index"
        df0 = self._ruptures_with_or_without_rupture_rates(drop_zero_rates=self._drop_zero_rates)

        rate_column = self._solution.model.rate_column_name()

        # rate col is different for InversionSolution
        df0 = df0 if not max_rate else df0[df0[rate_column] <= max_rate]
        df0 = df0 if not min_rate else df0[df0[rate_column] > min_rate]
        result = set(df0[index].tolist())
        return self.new_chainable_set(result, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_magnitude(
        self,
        min_mag: Optional[float] = None,
        max_mag: Optional[float] = None,
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures that occur within given magnitude bounds.

        Args:
            min_mag: The minumum rupture magnitude bound.
            max_mag: The maximum rupture magnitude bound.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter arguments.
        """
        index = "Rupture Index"
        df0 = self._ruptures_with_or_without_rupture_rates(drop_zero_rates=self._drop_zero_rates)

        df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
        df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
        result = set(df0[index].tolist())
        return self.new_chainable_set(result, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_polygons(
        self,
        polygons: Iterable[shapely.geometry.Polygon],
        join_type: Union[SetOperationEnum, str] = SetOperationEnum.UNION,
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures involving several polygon areas.

        Each polygon will return a set of matching rupture ids, so the user may choose to override the
        default set operation (UNION) between these using the `join_type' argument.

        This method

        Args:
            polygons: Polygons defining the areas of interest.
            join_type: How to join the polygon results (default = 'union').
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter arguments.
        """
        if isinstance(join_type, str):
            try:
                join_type = SetOperationEnum[join_type.upper()]
            except KeyError:
                raise ValueError(f'Unsupported set operation `{join_type}` for `join_type` argument.')

        rupture_id_sets: List[Set[int]] = []
        for polygon in polygons:
            rupture_id_sets.append(self.for_polygon(polygon, join_prior=join_prior).chained_set)

        if join_type == SetOperationEnum.INTERSECTION:
            rupture_ids = set.intersection(*rupture_id_sets)
        elif join_type == SetOperationEnum.UNION:
            rupture_ids = set.union(*rupture_id_sets)
        elif join_type == SetOperationEnum.DIFFERENCE:
            rupture_ids = set.difference(*rupture_id_sets)
        else:
            raise ValueError(
                "Only INTERSECTION, UNION & DIFFERENCE operations are supported for `join_type`"
            )  # pragma: no cover
        return self.new_chainable_set(rupture_ids, self._solution, self._drop_zero_rates, join_prior=join_prior)

    def for_polygon(
        self,
        polygon: shapely.geometry.Polygon,
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find ruptures that involve a single polygon area.

        Args:
            polygon: The polygon defining the area of intersection.
            join_prior: How to join this result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of rupture_ids matching the filter arguments.
        """
        fault_sections_df: pd.DataFrame = gpd.GeoDataFrame(self._solution.solution_file.fault_sections)

        # filter fault sections using the polygon geometry
        filtered_fault_sections_df = fault_sections_df[fault_sections_df['geometry'].intersects(polygon)]

        # filter ruptures by drop_zero_rates
        ruptures_df = self._ruptures_with_or_without_rupture_rates(drop_zero_rates=self._drop_zero_rates)

        # join filtered ruptures with rupture_sections
        rupture_sections_df = self._solution.model.rupture_sections
        rate_column = self._solution.model.rate_column_name()
        filtered_rupture_sections_df = rupture_sections_df.join(
            ruptures_df.set_index("Rupture Index"), on='rupture', how='inner'
        )[[rate_column, "rupture", "section"]]

        # join filtered rupture sections  and fault sections
        geom_flt_df = filtered_rupture_sections_df.join(filtered_fault_sections_df, 'section', how='inner')
        result = set(geom_flt_df["rupture"].tolist())
        return self.new_chainable_set(result, self._solution, self._drop_zero_rates, join_prior=join_prior)
