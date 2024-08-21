from typing import Dict, Iterator, List

from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.inversion_solution import InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

"""
NAMES

    - `subsection`   => Opensha:Fault/Section/Subsection = CFM:n/a
    - `parent_fault`     => Opensha:Fault => CFM:FaultSection??
    - `named_fault` => Opensha:NamedFault => CFM: ??
    - `rupture`      => Opensha:Rupture => CFM: n/a
"""


def section_participation_rate(solution: InversionSolution, section: int):
    """
    get the 'participation rate' of a (sub)section.

    That is, the sum of rates for all ruptures that involve the requested section.
    """
    filter_rupture_ids = FilterRuptureIds(solution)
    ruptures = filter_rupture_ids.for_subsection_ids([section])
    df = solution.ruptures_with_rupture_rates[["Rupture Index", "Annual Rate"]]
    return df[df["Rupture Index"].isin(list(ruptures))]["Annual Rate"].sum()


def fault_participation_rate(solution: InversionSolution, fault_name: str):
    """
    get the 'participation rate" of a given parent fault.

    That is, the sum of rates for all ruptures that involve the requested parent fault .
    """
    ruptures = FilterRuptureIds(solution).for_parent_fault_names([fault_name])
    df = solution.ruptures_with_rupture_rates[["Rupture Index", "Annual Rate"]]
    return df[df["Rupture Index"].isin(list(ruptures))]["Annual Rate"].sum()


def build_rupture_groups(solution: InversionSolutionProtocol) -> Iterator[Dict]:
    dfrs = solution.rupture_sections
    ruptures = dfrs['rupture'].unique().tolist()
    print(f"there are {len(ruptures)} unique ruptures")
    count = 0
    sample_sections = None
    sample_rupt = None
    sample_ruptures: List[int] = []

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
