from typing import Iterable, Optional, Set

from solvis.inversion_solution import FaultSystemSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

from .subsection_id_filter import FilterSubsectionIds


class FilterRuptureIds:
    """
    A class to filter ruptures, returning the qualifying rupture_ids.
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution
        self.filter_subsection_ids = FilterSubsectionIds(solution)

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

    def for_parent_fault_names(self, parent_fault_names: Iterable[str], drop_zero_rates: bool = True) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True)

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._solution.fault_sections
        # this is split out in fss_helper in ....
        ids = df0[df0['ParentName'].isin(list(parent_fault_names))]['ParentID'].tolist()
        return self.for_parent_fault_ids(parent_fault_ids=ids, drop_zero_rates=drop_zero_rates)

    def for_parent_fault_ids(self, parent_fault_ids: Iterable[str], drop_zero_rates: bool = True) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True)

        Returns:
            The rupture_ids matching the filter.
        """
        subsection_ids = self.filter_subsection_ids.for_parent_fault_ids(parent_fault_ids)
        df0 = self._solution.rupture_sections

        # TODO this is needed becuase the rupture rate concept differs between IS and FSS classes
        rate_column = "rate_weighted_mean" if isinstance(self._solution, FaultSystemSolution) else "Annual Rate"
        if drop_zero_rates:
            df0 = df0.join(self._solution.rupture_rates.set_index("Rupture Index"), on='rupture', how='inner')[
                [rate_column, "rupture", "section"]
            ]
            df0 = df0[df0[rate_column] > 0]

        ids = df0[df0['section'].isin(list(subsection_ids))]['rupture'].tolist()
        return set([int(id) for id in ids])

    def for_subsections(self, fault_section_ids: Iterable[int]) -> Set[int]:
        """Find ruptures that occur on any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The rupture_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.section.isin(list(fault_section_ids))].rupture.tolist()
        return set([int(id) for id in ids])

    def for_fault_sections(self, fault_section_ids: Iterable[int]) -> Set[int]:
        '''alias'''
        return self.for_subsections(fault_section_ids)

    def for_rupture_rate(self, min_rate: Optional[float] = None, max_rate: Optional[float] = None):
        """Find ruptures that occur within given rates bounds.

        Args:
            min_rate: The minumum rupture _rate bound.
            max_rate: The maximum rupture _rate bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        raise NotImplementedError()

    def for_magnitude(self, min_mag: Optional[float] = None, max_mag: Optional[float] = None):
        """Find ruptures that occur within given magnitude bounds.

        Args:
            min_mag: The minumum rupture magnitude bound.
            max_mag: The maximum rupture magnitude bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        raise NotImplementedError()

    def ids_within_polygon(self, polygon, contained=True):
        raise NotImplementedError()
