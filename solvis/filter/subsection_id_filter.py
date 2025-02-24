r"""
This module provides a class for filtering solution fault sections (subsections).

Classes:
 FilterSubsectionIds: a chainable filter for fault sections, returning qualifying fault section ids.

Examples:
    ```py
    >>> ham50 = solvis.circle_polygon(50000, -37.78, 175.28)  # 50km radius around Hamilton
    <POLYGON ((175.849 -37.779, 175.847 -37.823, 175.839 -37.866, 175.825 -37.90...>
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>> rupture_ids = FilterRuptureIds(solution)\
            .for_magnitude(min_mag=5.75, max_mag=6.25)\
            .for_polygon(ham50)

    >>> subsection_ids = FilterSubsectionIds(solution)\
    >>>     .for_rupture_ids(rupture_ids)
    ```
"""

from typing import TYPE_CHECKING, Iterable, List, Union

from solvis.solution.typing import SetOperationEnum

from ..solution import named_fault
from .chainable_set_base import ChainableSetBase
from .parent_fault_id_filter import FilterParentFaultIds

if TYPE_CHECKING:
    from solvis import InversionSolution


class FilterSubsectionIds(ChainableSetBase):
    """A helper class to filter subsections, returning qualifying section_ids."""

    def __init__(self, solution: 'InversionSolution'):
        """Instantiate a new filter.

        Args:
            solution: The solution instance to filter on.
        """
        self._solution = solution
        self._filter_parent_fault_ids = FilterParentFaultIds(solution)

    def all(self) -> ChainableSetBase:
        """Convenience method returning ids for all solution fault subsections.

        NB the usual `join_prior` argument is not implemented as it doesn't seem useful here.

        Returns:
            A chainable set of all the subsection_ids.
        """
        result = set(self._solution.solution_file.fault_sections.index.to_list())
        return self.new_chainable_set(result, self._solution)

    def tolist(self) -> List[int]:
        """
        Returns the fault subsection id as a list of integers.

        Returns:
            A list of integers representing the filtered fault subsection ids.
        """
        return list(self)

    def for_named_fault_names(
        self,
        named_fault_names: Iterable[str],
        join_prior: Union[SetOperationEnum, str] = 'intersection',
    ) -> ChainableSetBase:
        """Find subsection ids that occur on any of the given named_fault names.

        Args:
            named_fault_names: A list of one or more `named_fault` names.

        Returns:
            The subsection_ids matching the filter.

        Raises:
            ValueError: If any `named_fault_names` argument is not valid.
        """
        parent_fault_ids: Iterable[int] = []
        for nf_name in named_fault_names:
            parent_fault_ids += named_fault.named_fault_table().loc[nf_name].parent_fault_ids
        return self.for_parent_fault_ids(parent_fault_ids, join_prior=join_prior)

    def for_parent_fault_names(
        self, parent_fault_names: Iterable[str], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find fault subsection ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The fault_subsection_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        parent_ids = self._filter_parent_fault_ids.for_parent_fault_names(parent_fault_names)
        return self.for_parent_fault_ids(parent_ids, join_prior=join_prior)

    def for_parent_fault_ids(
        self, parent_fault_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find fault subsection ids for the given parent_fault ids.

        Args:
            parent_fault_ids: A list of one or more `parent_fault` ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.solution_file.fault_sections
        ids = df0[df0['ParentID'].isin(list(parent_fault_ids))]['FaultID'].tolist()

        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_rupture_ids(
        self, rupture_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find fault subsection ids for the given rupture_ids.

        Args:
            rupture_ids: A list of one or more rupture ids.

        Returns:
            The fault_subsection_ids matching the filter.
        """
        df0 = self._solution.model.rupture_sections
        ids = df0[df0.rupture.isin(list(rupture_ids))].section.tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_polygon(self, polygon, contained=True) -> ChainableSetBase:
        raise NotImplementedError()
