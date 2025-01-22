from typing import Dict, Iterator, List, Optional

from solvis.solution.typing import InversionSolutionProtocol

"""
NAMES

    - `subsection`   => Opensha:Fault/Section/Subsection = CFM:n/a
    - `parent_fault`     => Opensha:Fault => CFM:FaultSection??
    - `named_fault` => Opensha:NamedFault => CFM: ??
    - `rupture`      => Opensha:Rupture => CFM: n/a
"""


def build_rupture_groups(
    solution: InversionSolutionProtocol, rupture_ids: Optional[List[int]] = None, min_overlap: float = 0.8
) -> Iterator[Dict]:
    dfrs = solution.model.rupture_sections
    rupture_ids = rupture_ids or dfrs['rupture'].unique().tolist()
    print(f"there are {len(rupture_ids)} unique ruptures")
    count = 0
    sample_sections = None
    sample_rupt = None
    sample_ruptures: List[int] = []

    for rupt_id in rupture_ids:
        sections = dfrs[dfrs.rupture == rupt_id]['section'].tolist()

        # first or reset
        if sample_rupt is None:
            sample_ruptures = []
            sample_rupt = rupt_id
            sample_sections = set(sections)
            sample_len = len(sections)
            continue

        sample_ruptures.append(rupt_id)

        # compare section overlap
        section_overlap = len(set(sections).intersection(sample_sections))

        if section_overlap:  # and there must be some non-zero score
            section_diff_count = len(set(sections).symmetric_difference(sample_sections))
            score = (sample_len - section_diff_count) / sample_len
            if score >= min_overlap:
                continue
            else:
                count += 1
                yield {'rupture': sample_rupt, 'ruptures': sample_ruptures, 'sample_sections': sample_len}

        # signal reset
        sample_rupt = None

    print(f"built {count} rupture groups from {len(rupture_ids)} unique ruptures.")
