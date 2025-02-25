r"""
This module provides a class for filtering solution parent faults.

Classes:
 FilterParentFaultIds: a chainable filter for parent faults, returning qualifying fault ids.
 ParentFaultMapping: a namedtuple representing id and name of a parent fault.

Functions:
 parent_fault_name_id_mapping: a method yielding ParentFaultMappings.
 valid_parent_fault_names: to check parent_fault_names are valid.

Examples:
    ```py
    >>> solution = InversionSolution.from_archive(filename)
    >>> parent_fault_ids = FilterParentFaultIds(solution)\
            .for_parent_fault_names(['Alpine: Jacksons to Kaniere', 'BooBoo'])

    >>> # chained with rutpure id filter
    >>> rupture_ids = FilterRuptureIds(solution)\
            .for_magnitude(min_mag=5.75, max_mag=6.25)\

    >>> parent_fault_ids = FilterParentFaultIds(solution)\
            .for_parent_fault_names(['Alpine: Jacksons to Kaniere'])\
            .for_rupture_ids(rupture_ids)
    ```
"""

from typing import TYPE_CHECKING, Iterable, Iterator, List, NamedTuple, Set, Union

import shapely.geometry

from ..solution import named_fault
from ..solution.typing import SetOperationEnum
from .chainable_set_base import ChainableSetBase

if TYPE_CHECKING:
    from solvis import InversionSolution


class ParentFaultMapping(NamedTuple):
    """A mapping class for ParentFault id -> name."""

    parent_id: int
    parent_fault_name: str


def parent_fault_name_id_mapping(
    solution: 'InversionSolution', parent_fault_ids: Iterable[int]
) -> Iterator[ParentFaultMapping]:
    """For each unique parent_fault_id yield a ParentFaultMapping object.

    Args:
        parent_fault_ids: A list of `parent_fault_is`.

    Yields:
        A mapping object.
    """
    df0 = solution.solution_file.fault_sections
    df1 = df0[df0['ParentID'].isin(list(parent_fault_ids))][['ParentID', 'ParentName']]
    unique_ids = list(df1.ParentID.unique())
    unique_names = list(df1.ParentName.unique())
    for idx, parent_id in enumerate(unique_ids):
        yield ParentFaultMapping(parent_id, unique_names[idx])


def valid_parent_fault_names(solution, validate_names: Iterable[str]) -> Set[str]:
    """Check that parent_fault_names are valid for the given solution.

    Args:
        validate_names: A list of `parent_fault_names` to check.

    Returns:
        The set of valid fault names.

    Raises:
        ValueError: If any member of `validate_names` argument is not valid.
    """
    unknown = set(validate_names).difference(set(solution.model.parent_fault_names))
    if unknown:
        raise ValueError(f"The solution model {solution.model} does not contain the parent_fault_names: {unknown}.")
    return set(validate_names)


class FilterParentFaultIds(ChainableSetBase):
    """A helper class to filter parent faults, returning qualifying fault_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).

    Examples:
        ```py
        >>> solution = InversionSolution.from_archive(filename)
        >>> parent_fault_ids = FilterParentFaultIds(solution)\
                .for_parent_fault_names(['Alpine: Jacksons to Kaniere'])
                .
        ```
    """

    def __init__(self, solution: 'InversionSolution'):
        """Instantiate a new filter.

        Args:
            solution: The solution instance to filter on.
        """
        self._solution = solution

    def all(self) -> ChainableSetBase:
        """Convenience method returning ids for all solution parent faults.

        NB the usual `join_prior` argument is not implemented as it doesn't seem useful here.

        Returns:
            the parent_fault_ids.
        """
        result = set(self._solution.solution_file.fault_sections['ParentID'].tolist())
        return self.new_chainable_set(result, self._solution)

    def tolist(self) -> List[int]:
        """
        Returns the filtered parent fault ids as a list of integers.

        Returns:
            A list of integers representing the filtered parent fault ids.
        """
        return list(self)

    def for_named_fault_names(
        self, named_fault_names: Iterable[str], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find parent fault ids for the given parent fault names.

        Args:
            named_fault_name: one or more valid named fault names.
            join_prior: How to join this methods' result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of fault_ids matching the filter.

        Raises:
            ValueError: If any `named_fault_names` value is not valid.
        """
        pids: Iterable[int] = []
        for nf_name in named_fault_names:
            pids += named_fault.named_fault_table().loc[nf_name].parent_fault_ids
        return self.new_chainable_set(set(pids), self._solution, join_prior=join_prior)

    def for_parent_fault_names(
        self, parent_fault_names: Iterable[str], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find parent fault ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.
            join_prior: How to join this methods' result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of fault_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._solution.solution_file.fault_sections
        ids = df0[df0['ParentName'].isin(list(valid_parent_fault_names(self._solution, parent_fault_names)))][
            'ParentID'
        ].tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_subsection_ids(
        self, fault_section_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find parent fault ids that contain any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.
            join_prior: How to join this methods' result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of fault_ids matching the filter.
        """
        df0 = self._solution.solution_file.fault_sections
        ids = df0[df0['FaultID'].isin(list(fault_section_ids))]['ParentID'].unique().tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)

    def for_polygon(self, polygon: shapely.geometry.Polygon, contained: bool = True):
        raise NotImplementedError()

    def for_rupture_ids(
        self, rupture_ids: Iterable[int], join_prior: Union[SetOperationEnum, str] = 'intersection'
    ) -> ChainableSetBase:
        """Find parent_fault_ids for the given rupture_ids.

        Args:
            rupture_ids: A list of one or more rupture ids.
            join_prior: How to join this methods' result with the prior chain (if any) (default = 'intersection').

        Returns:
            A chainable set of parent fault_ids matching the filter.
        """
        # df0 = self._solution.solution_file.rupture_sections
        df0 = self._solution.model.fault_sections_with_rupture_rates
        ids = df0[df0['Rupture Index'].isin(list(rupture_ids))].ParentID.unique().tolist()
        result = set([int(id) for id in ids])
        return self.new_chainable_set(result, self._solution, join_prior=join_prior)
