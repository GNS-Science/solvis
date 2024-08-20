from collections import namedtuple
from typing import Iterable, Iterator, Set

from solvis.inversion_solution.typing import InversionSolutionProtocol

ParentFaultMapping = namedtuple('ParentFaultMapping', ['id', 'parent_fault_name'])


def parent_fault_name_id_mapping(
    solution: InversionSolutionProtocol, parent_fault_ids: Iterable[int]
) -> Iterator[ParentFaultMapping]:
    df0 = solution.fault_sections
    df1 = df0[df0['ParentID'].isin(list(parent_fault_ids))][['ParentID', 'ParentName']]
    unique_ids = list(df1.ParentID.unique())
    unique_names = list(df1.ParentName.unique())
    for idx, parent_id in enumerate(unique_ids):
        yield ParentFaultMapping(parent_id, unique_names[idx])


def valid_parent_fault_names(solution, parent_fault_names: Iterable[str]) -> Set[str]:
    # validate the names ....
    df0 = solution.fault_sections
    all_parent_names = set(df0['ParentName'].unique().tolist())
    unknown = set(parent_fault_names).difference(all_parent_names)
    if unknown:
        raise ValueError(f"the solution {solution} does not contain the parent_fault_names: {unknown}.")
    return set(parent_fault_names)


class FilterParentFaultIds:
    """
    A helper class to filter parentfaults, returning qualifying fault_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution

    def for_named_faults(self, named_fault_names: Iterable[str]):
        raise NotImplementedError()

    def for_parent_fault_names(self, parent_fault_names: Iterable[str]) -> Set[int]:
        """Find parent fault ids for the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The fault_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._solution.fault_sections
        ids = df0[df0['ParentName'].isin(list(valid_parent_fault_names(self._solution, parent_fault_names)))][
            'ParentID'
        ].tolist()
        return set([int(id) for id in ids])

    def for_subsection_ids(self, fault_section_ids: Iterable[int]) -> Set[int]:
        """Find parent fault ids that contain any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The rupture_ids matching the filter.
        """
        df0 = self._solution.rupture_sections
        ids = df0[df0.section.isin(list(fault_section_ids))]['ParentName'].unique().tolist()
        return set([int(id) for id in ids])

    def for_polygon(self, polygon, contained=True):
        raise NotImplementedError()
