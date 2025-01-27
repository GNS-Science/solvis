r"""
This module provides a class for filtering solution parent faults.

Classes:
 FilterParentFaultIds: a filter for parent faults, returning qualifying fault_ids.
 ParentFaultMapping: a namedtuple representing id and name of a parent fault.

Functions:
 parent_fault_name_id_mapping: a method yielding ParentFaultMappings.
 valid_parent_fault_names: to check parent_fault_names are valid.

Examples:
    ```py
    >>> model = InversionSolution.from_archive(filename).model
    >>> parent_fault_ids = FilterParentFaultIds(model)\
            .for_parent_fault_names(['Alpine Jacksons to Kaniere', 'BooBoo'])
    ```

TODO:
  - make FilterParentFaultIds chainable
"""

from typing import Iterable, Iterator, NamedTuple, Set

import shapely.geometry

from ..solution.typing import InversionSolutionProtocol


class ParentFaultMapping(NamedTuple):
    """A mapping class for ParentFault id -> name."""

    parent_id: int
    parent_fault_name: str


def parent_fault_name_id_mapping(
    solution: InversionSolutionProtocol, parent_fault_ids: Iterable[int]
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


class FilterParentFaultIds:
    """A helper class to filter parent faults, returning qualifying fault_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).

    Examples:
        ```py
        >>> solution = InversionSolution.from_archive(filename)
        >>> parent_fault_ids = FilterParentFaultIds(solution)\
                .for_parent_fault_names(['Alpine Jacksons to Kaniere'])
        ```
    """

    def __init__(self, solution: InversionSolutionProtocol):
        """Instantiate a new filter.

        Args:
            solution: The solution instance to filter on.
        """
        self._solution = solution

    def for_named_faults(self, named_fault_names: Iterable[str]):
        raise NotImplementedError()

    def all(self) -> Set[int]:
        """Convenience method returning ids for all solution parent faults.

        NB the usual `join_prior` argument is not implemented as it doesn't seem useful here.

        Returns:
            the parent_fault_ids.
        """
        result = set(self._solution.solution_file.fault_sections['ParentID'].tolist())
        return result

    def for_parent_fault_names(self, parent_fault_names: Iterable[str]) -> Set[int]:
        """Find parent fault ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The fault_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._solution.solution_file.fault_sections
        ids = df0[df0['ParentName'].isin(list(valid_parent_fault_names(self._solution, parent_fault_names)))][
            'ParentID'
        ].tolist()
        return set([int(id) for id in ids])

    def for_subsection_ids(self, fault_section_ids: Iterable[int]) -> Set[int]:
        """Find parent fault ids that contain any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The fault_ids matching the filter.
        """
        df0 = self._solution.solution_file.fault_sections
        ids = df0[df0['FaultID'].isin(list(fault_section_ids))]['ParentID'].unique().tolist()
        return set([int(id) for id in ids])

    def for_polygon(self, polygon: shapely.geometry.Polygon, contained: bool = True):
        raise NotImplementedError()

    def for_rupture_ids(self, rupture_ids: Iterable[int]) -> Set[int]:
        """Find parent_fault_ids for the given rupture_ids.

        Args:
            rupture_ids: A list of one or more rupture ids.

        Returns:
            The parent_fault_ids matching the filter.
        """
        # df0 = self._solution.solution_file.rupture_sections
        df0 = self._solution.model.fault_sections_with_rupture_rates
        ids = df0[df0['Rupture Index'].isin(list(rupture_ids))].ParentID.unique().tolist()
        return set([int(id) for id in ids])
