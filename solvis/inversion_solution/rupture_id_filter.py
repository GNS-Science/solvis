from typing import Set, Optional
from solvis.inversion_solution.typing import InversionSolutionProtocol


class FilterRuptureIds():
    """
    A class to filter ruptures, returning the qualifying rupture_ids.
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution


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
        pass

    def for_parent_faults(self, parent_fault_names: Set[str]) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        pass


    def for_fault_sections(self, fault_section_ids: Set[int]) -> Set[int]:
        '''alias'''
        return self.for_fault_sections(fault_section_ids)

    def for_subsections(self, fault_section_ids: Set[int]) -> Set[int]:
        """Find ruptures that occur on any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The rupture_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.section.isin(list(fault_section_ids))].rupture.tolist()
        return set([int(id) for id in ids])

    def for_rupture_rate(self, min_rate: Optional[float] = None, max_rate: Optional[float] = None):
        """Find ruptures that occur within given rates bounds.

        Args:
            min_rate: The minumum rupture _rate bound.
            max_rate: The maximum rupture _rate bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        pass

    def for_magnitude(self, min_mag: Optional[float] = None, max_mag: Optional[float] = None):
        """Find ruptures that occur within given magnitude bounds.

        Args:
            min_mag: The minumum rupture magnitude bound.
            max_mag: The maximum rupture magnitude bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        pass

    def ids_within_polygon(self, polygon, contained=True):
        pass


