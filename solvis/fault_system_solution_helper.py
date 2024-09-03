from typing import Dict, Iterable, Iterator, List, Optional

from solvis.filter import FilterSubsectionIds
from solvis.inversion_solution import InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

"""
NAMES

    - `subsection`   => Opensha:Fault/Section/Subsection = CFM:n/a
    - `parent_fault`     => Opensha:Fault => CFM:FaultSection??
    - `named_fault` => Opensha:NamedFault => CFM: ??
    - `rupture`      => Opensha:Rupture => CFM: n/a
"""


def section_participation_rates(
    solution: InversionSolutionProtocol, section_ids: Iterable[int], rupture_ids: Optional[Iterable[int]] = None
):
    # ALERT: does this actually work if we have FSS. what is the sum of rate_weighted_mean ??
    rate_column = "Annual Rate" if isinstance(solution, InversionSolution) else "rate_weighted_mean"

    df0 = solution.rs_with_rupture_rates
    df0 = df0[df0["section"].isin(section_ids)]
    if rupture_ids:
        df0 = df0[df0["Rupture Index"].isin(rupture_ids)]
    return df0.pivot_table(values=rate_column, index=['section'], aggfunc='sum')


def fault_participation_rates(
    solution: InversionSolution, fault_names: Iterable[str], rupture_ids: Optional[Iterable[int]] = None
):
    """
    get the 'participation rate" of a given parent fault.

    That is, the sum of rates for all ruptures that involve the requested parent fault .
    """
    # subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names(fault_names)
    # return section_participation_rates(solution, subsection_ids, rupture_ids)
    # rate_column = "Annual Rate" if isinstance(solution, InversionSolution) else "rate_weighted_mean"
    # print(f'Rate column: {rate_column}')
    subsection_ids = FilterSubsectionIds(solution).for_parent_fault_names(fault_names)

    # print(f'subsection_ids: {subsection_ids}')

    df0 = solution.rs_with_rupture_rates
    df0 = df0[df0["section"].isin(subsection_ids)]

    # print(df0)
    if rupture_ids:
        df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

    df1 = df0.join(solution.fault_sections[['ParentID']], on='section')
    return df1.groupby(["ParentID", "Rupture Index"]).agg('first').groupby("ParentID").agg('sum')


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
