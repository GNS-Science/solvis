from typing import Iterable, Set

from solvis.inversion_solution.typing import InversionSolutionProtocol


class FilterSubsectionIds:
    """
    A class to filter fault subsections, returning qualifying section_ids
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution

    def for_named_faults(self, named_fault_names: Iterable[str]):
        raise NotImplementedError()

    def for_parent_fault_names(self, parent_fault_names: Set[str]):
        """Find fault subsection ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The fault_subsection_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._solution.fault_sections

        # validate the names ....
        all_parent_names = set(df0['ParentName'].unique().tolist())
        unknown = set(parent_fault_names).difference(all_parent_names)
        if unknown:
            raise ValueError(f"the solution {self._solution} does not contain the parent_fault_names: {unknown}.")

        ids = df0[df0['ParentName'].isin(list(parent_fault_names))]['FaultID'].tolist()
        return set([int(id) for id in ids])

    def for_parent_fault_ids(self, parent_fault_ids: Iterable[str]):
        """Find fault subsection ids for the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.fault_sections
        ids = df0[df0['ParentID'].isin(list(parent_fault_ids))]['FaultID'].tolist()
        return set([int(id) for id in ids])

    def for_ruptures(self, rupture_ids: Iterable[int]):
        """Find fault subsection ids for the given rupture_ids.

        Args:
            rupture_ids: A list of one or more rupture ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.rupture.isin(list(rupture_ids))].section.tolist()
        return set([int(id) for id in ids])

    def within_polygon(self, polygon, contained=True):
        raise NotImplementedError()
