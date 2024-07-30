from collections import namedtuple
from typing import Dict, Iterator, Set

from solvis.inversion_solution import FaultSystemSolution, InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

"""
NAMES

    - `subsection`   => Opensha:Fault/Section/Subsection = CFM:n/a
    - `parent_fault`     => Opensha:Fault => CFM:FaultSection??
    - `named_fault` => Opensha:NamedFault => CFM: ??
    - `rupture`      => Opensha:Rupture => CFM: n/a
"""

ParentFaultMapping = namedtuple('ParentFaultMapping', ['id', 'parent_fault_name'])


class FaultSystemSolutionHelper:
    """
    A helper class for solvis.InversionSolutionProtocol instances providing
      set analysis functions on major fss attribute

    NB these functions might be added to the class itself eventually

    """

    def __init__(self, fault_system_solution: InversionSolutionProtocol):
        self._fss = fault_system_solution

    def subsections_for_ruptures(self, rupture_ids: Set[int]) -> Set[int]:
        """get all subsections for the given rupture_ids"""
        df0 = self._fss.rupture_sections
        ids = df0[df0.rupture.isin(list(rupture_ids))].section.tolist()
        return set([int(id) for id in ids])

    def ids_for_parent_fault_names(self, fault_names: Set[str]):
        """
        get Parent_fault_ids for the given parent fault names
        """
        df0 = self._fss.fault_sections
        # print("fault_sections")
        # print(df0[["ParentID", "ParentName"]])
        ids = df0[df0['ParentName'].isin(list(fault_names))]['ParentID'].tolist()
        return set([int(id) for id in ids])

    def parent_fault_name_id_mapping(self, parent_ids: Set[int]) -> Iterator[ParentFaultMapping]:
        df0 = self._fss.fault_sections
        # print("fault_sections")
        # print(df0[["ParentID", "ParentName"]])
        df1 = df0[df0['ParentID'].isin(list(parent_ids))][['ParentID', 'ParentName']]
        unique_ids = list(df1.ParentID.unique())
        unique_names = list(df1.ParentName.unique())
        for idx, parent_id in enumerate(unique_ids):
            # print(idx, parent_id, unique_names[idx])
            yield ParentFaultMapping(parent_id, unique_names[idx])

    def fault_names_as_ids(self, fault_names: Set[str]):
        '''alias fn'''
        return self.ids_for_parent_fault_names(fault_names)

    def subsections_for_faults(self, parent_ids: Set[int]) -> Set[int]:
        df0 = self._fss.fault_sections
        ids = df0[df0['ParentID'].isin(list(parent_ids))]['FaultID'].tolist()
        return set([int(id) for id in ids])

    def subsections_for_parent_fault_names(self, fault_names: Set[str]):
        """
        get all subsections (by id) for the given parent fault names

        convenience function that resolves fault names before
        calling self.subsections_for_faults.
        """
        fault_ids = self.fault_names_as_ids(fault_names)
        return self.subsections_for_faults(fault_ids)

    def ruptures_for_faults(self, parent_ids: Set[int], drop_zero_rates: bool = True) -> Set[int]:
        """
        get all ruptures (by id) on the given faults

        TODO: any (INTERSECTION) or all (UNION)
        """
        subsection_ids = self.subsections_for_faults(parent_ids)
        df0 = self._fss.rupture_sections
        # print(df0)
        # print(self._fss.rupture_rates)

        # TODO this is needed becuase the rupture rate concept differs between IS and FSS classes
        rate_column = "rate_weighted_mean" if isinstance(self._fss, FaultSystemSolution) else "Annual Rate"
        if drop_zero_rates:
            df0 = df0.join(self._fss.rupture_rates.set_index("Rupture Index"), on='rupture', how='inner')[
                [rate_column, "rupture", "section"]
            ]
            df0 = df0[df0[rate_column] > 0]

        ids = df0[df0['section'].isin(list(subsection_ids))]['rupture'].tolist()
        return set([int(id) for id in ids])

    def ruptures_for_parent_fault_names(self, fault_names: Set[str], drop_zero_rates: bool = True) -> Set[int]:
        """
        get all ruptures (by id) for the given parent fault names

        convenience function that resolves fault names before
        calling self.ruptures_for_faults.
        """
        fault_ids = self.fault_names_as_ids(fault_names)
        return self.ruptures_for_faults(fault_ids, drop_zero_rates)

    def ruptures_for_subsections(self, subsection_ids: Set[int]):
        """
        get all ruptures (by id) on the given subsections (any match is enough)

        any (INTERSECTION) or all (UNION)
        """
        df0 = self._fss.rupture_sections
        ids = df0[df0.section.isin(list(subsection_ids))].rupture.tolist()
        return set([int(id) for id in ids])


def section_participation_rate(solution: InversionSolution, section: int):
    """
    get the 'participation rate" of a (sub)section.

    That is, the sum of rates for all ruptures that involve the requested section.
    """
    helper = FaultSystemSolutionHelper(solution)
    ruptures = helper.ruptures_for_subsections([section])
    # ruptures = {5,6}  # mocking helper.ruptures_given_subsections()
    df = solution.ruptures_with_rupture_rates[["Rupture Index", "Annual Rate"]]
    return df[df["Rupture Index"].isin(list(ruptures))]["Annual Rate"].sum()


def fault_participation_rate(solution: InversionSolution, fault_name: str):
    """
    get the 'participation rate" of a given parent fault.

    That is, the sum of rates for all ruptures that involve the requested parent fault .
    """
    helper = FaultSystemSolutionHelper(solution)
    ruptures = helper.ruptures_for_parent_fault_names([fault_name])
    # ruptures = {8, 9, 10}  # mocking helper.ruptures_given_subsections()
    df = solution.ruptures_with_rupture_rates[["Rupture Index", "Annual Rate"]]
    return df[df["Rupture Index"].isin(list(ruptures))]["Annual Rate"].sum()


def build_rupture_groups(solution: InversionSolutionProtocol) -> Iterator[Dict]:
    dfrs = solution.rupture_sections
    ruptures = dfrs['rupture'].unique().tolist()
    print(f"there are {len(ruptures)} unique ruptures")
    count = 0
    sample_sections = None
    sample_rupt = None
    sample_ruptures = []

    for rupt_id in ruptures:
        sections = dfrs[dfrs.rupture == rupt_id]['section'].tolist()
        # first or reset
        if sample_rupt is None:
            sample_ruptures = []
            sample_rupt = rupt_id
            sample_sections = set(sections)
            sample_len = len(sections)
            continue

        if rupt_id is not sample_rupt:
            sample_ruptures.append(rupt_id)

        # otherwise compare overlap
        diff = len(set(sections).symmetric_difference(sample_sections))
        overlap = len(set(sections).intersection(sample_sections))

        if overlap:  # and there must be some non-zero score
            score = (sample_len - diff) / sample_len

        # print(f'rupt_id {rupt_id} score {score} overlap {overlap} sample_len: {sample_len} diff {diff}')
        if (score < 0.7) or not overlap:  # (overlap < 0.8 * sample_len):
            yield {'rupture': sample_rupt, 'ruptures': sample_ruptures, 'sample_sections': sample_len}

            # signal reset
            sample_rupt = None
            count += 1

    print(f"built {count} rupture groups")
