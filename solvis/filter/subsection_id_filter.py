from typing import Iterable, Set, Union

from solvis.inversion_solution.typing import InversionSolutionProtocol, SetOperationEnum

from .chainable_set_base import ChainableSetBase
from .parent_fault_id_filter import FilterParentFaultIds


class FilterSubsectionIds(ChainableSetBase):
    """
    A helper class to filter subsections, returning qualifying section_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution
        self.filter_parent_fault_ids = FilterParentFaultIds(solution)

    def for_named_faults(self, named_fault_names: Iterable[str]):
        raise NotImplementedError()

    def for_parent_fault_names(
        self, parent_fault_names: Iterable[str], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> Set[int]:
        """Find fault subsection ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The fault_subsection_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        parent_ids = self.filter_parent_fault_ids.for_parent_fault_names(parent_fault_names)
        return self.for_parent_fault_ids(parent_ids, join_prior=join_prior)

    def for_parent_fault_ids(
        self, parent_fault_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> Set[int]:
        """Find fault subsection ids for the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.fault_sections
        ids = df0[df0['ParentID'].isin(list(parent_fault_ids))]['FaultID'].tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_rupture_ids(
        self, rupture_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> Set[int]:
        """Find fault subsection ids for the given rupture_ids.

        Args:
            rupture_ids: A list of one or more rupture ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.rupture.isin(list(rupture_ids))].section.tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_polygon(self, polygon, contained=True):
        raise NotImplementedError()
