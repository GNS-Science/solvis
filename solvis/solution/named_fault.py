"""A module to produce a named_fault for use with filtering crustal ruptures.

for NSHM_V1.* the Crustal Rupture Sets all use the same Fault Model (form the NZ CFM)
"""

import csv
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from pandera.typing import DataFrame  # noqa

    from solvis.solution import dataframe_models  # noqa

CFM_1_0A_DOM_SANSTVZ_MAP = 'resources/named_faults/cfm_1_0A_no_tvz.xml.FaultsByNameAlt.txt'


@lru_cache
def named_fault_table() -> pd.DataFrame:
    """Build a dataframe from the resoource file."""
    csv_rows = csv.reader(open(CFM_1_0A_DOM_SANSTVZ_MAP, mode='r', encoding='utf-8-sig'), delimiter='\t')

    def reform(row):
        return (row[0], [int(x) for x in row[1:]])

    reformed = [reform(row) for row in csv_rows]
    return pd.DataFrame(reformed, columns=['named_fault_name', 'parent_fault_ids']).set_index('named_fault_name')


@lru_cache
def named_fault_for_parent_ids_table():
    return named_fault_table().explode('parent_fault_ids').reset_index().set_index('parent_fault_ids')


@lru_cache
def get_named_fault_for_parent(parent_fault_id: int) -> Optional[str]:
    """Get a named fault name, given a parent_fault_id.

    Args:
        parent_fault_id: the id of the parent fault,

    Returns:
        named_fault_name: the named fault name.
    """
    df0 = named_fault_for_parent_ids_table()
    try:
        res = df0.loc[parent_fault_id]
        return res.named_fault_name
    except KeyError:
        return None
